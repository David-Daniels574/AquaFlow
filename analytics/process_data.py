# process_data.py
import os
import sys
import traceback

from pyspark.sql import SparkSession
from pyspark.sql.functions import coalesce, col, lag, max as _max, to_date
from pyspark.sql.window import Window

jar_path = "/app/postgresql.jar"
jdbc_url = os.environ.get("SPARK_JDBC_URL")
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")

if not all([jdbc_url, db_user, db_pass]):
    print("ERROR: Missing DB credentials.")
    sys.exit(1)

spark = (
    SparkSession.builder
    .appName("WaterConsumptionBatchJob")
    .master("local[2]")
    # Backward compatibility for parquet files written with TIMESTAMP(NANOS)
    .config("spark.sql.legacy.parquet.nanosAsLong", "true")
    .config("spark.driver.memory", "384m")
    .config("spark.ui.enabled", "false")
    .getOrCreate()
)

db_props = {"user": db_user, "password": db_pass, "driver": "org.postgresql.Driver"}

# 1. Read Raw IoT Data
parquet_path = os.environ.get("SPARK_RAW_PARQUET_PATH", "/opt/analytics/data/raw/water_readings/")
print(f">>> Looking for Parquet data at: {parquet_path}")
use_parquet = os.path.exists(parquet_path) and any(os.scandir(parquet_path))

if use_parquet:
    print(">>> Reading Parquet Data Lake...")
    # Spark automatically discovers the 'date' column from the folder structure.
    try:
        df_raw = spark.read.parquet(parquet_path)
    except Exception as exc:
        print(f"ERROR: Failed reading parquet source: {exc}")
        spark.stop()
        sys.exit(1)
else:
    print(">>> Parquet data not found. Falling back to PostgreSQL table: water_readings")
    try:
        df_raw = (
            spark.read.jdbc(jdbc_url, "water_readings", properties=db_props)
            .withColumn("date", to_date(col("timestamp")))
        )
    except Exception as exc:
        print(f"WARNING: Unable to read source table water_readings: {exc}")
        print("No source data available for analytics run. Exiting successfully.")
        spark.stop()
        sys.exit(0)

if df_raw.rdd.isEmpty():
    print("No raw readings found. Skipping aggregation.")
    spark.stop()
    sys.exit(0)

# 2. Get End-of-Day Readings
# Since meters only go up, daily usage = Max(reading today) - Max(reading yesterday)
daily_max = df_raw.groupBy("user_id", "society_id", "date") \
                  .agg(_max("reading").alias("end_of_day_reading"))

# 3. Calculate Deltas (Usage)
window_spec = Window.partitionBy("user_id").orderBy("date")
df_with_lag = daily_max.withColumn("prev_reading", lag("end_of_day_reading").over(window_spec))

# For the very first day in the dataset, if prev_reading is NULL, 
# in a real production system we would join with the UserMeterState table here.
# For historical backfill processing, we assume 0 or drop the first day's delta.
df_usage = df_with_lag.withColumn("total_usage_liters", col("end_of_day_reading") - coalesce(col("prev_reading"), col("end_of_day_reading"))) \
                      .filter(col("total_usage_liters") > 0)

df_final = df_usage.select("user_id", "society_id", "date", "total_usage_liters")

# 4. Write to Postgres Serving Layer
print(">>> Writing Daily Aggregations to DB...")
try:
    # mode="append" is better for daily batch, but "overwrite" is safe for local testing
    df_final.write.jdbc(jdbc_url, "user_daily_usage", mode="overwrite", properties=db_props)
    
    # 5. Update State Table (Max reading across all processed data)
    latest_state = daily_max.groupBy("user_id").agg(_max("end_of_day_reading").alias("last_reading"), _max("date").alias("last_updated"))
    latest_state.write.jdbc(jdbc_url, "user_meter_state", mode="overwrite", properties=db_props)

    print(">>> Batch Processing Complete!")
except Exception as e:
    print(f"Error writing to DB: {e}")
    traceback.print_exc()
    sys.exit(1)

spark.stop()
