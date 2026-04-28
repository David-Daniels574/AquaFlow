# process_data.py
import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max as _max, lag, coalesce, lit
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
    # Backward compatibility for parquet files written with TIMESTAMP(NANOS)
    .config("spark.sql.legacy.parquet.nanosAsLong", "true")
    .getOrCreate()
)

db_props = {"user": db_user, "password": db_pass, "driver": "org.postgresql.Driver"}

# 1. Read Raw IoT Data from Parquet
print(">>> Reading Parquet Data Lake...")
# Spark automatically discovers the 'date' column from the folder structure!
df_raw = spark.read.parquet("/opt/analytics/data/raw/water_readings/")

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
    sys.exit(1)

spark.stop()
