import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, month, year, sum as _sum, lag, to_date
from pyspark.sql.window import Window

# --- CONFIGURATION ---
# Ensure this matches the file you downloaded
jar_path = "/opt/spark/jars_external/postgresql-42.7.8.jar"

# --- INIT SPARK ---
spark = SparkSession.builder \
    .appName("WaterConsumptionAnalytics") \
    .config("spark.jars", jar_path) \
    .config("spark.driver.extraClassPath", jar_path) \
    .config("spark.executor.extraClassPath", jar_path) \
    .getOrCreate()

# --- DB CONNECTION ---
db_url = "jdbc:postgresql://db:5432/waterdb"
db_props = {
    "user": "user", 
    "password": "password", 
    "driver": "org.postgresql.Driver"
}

print(">>> Reading data from PostgreSQL...")
try:
    df_readings = spark.read.jdbc(db_url, "water_reading", properties=db_props)
    # We don't even need the user table anymore for this specific calculation
    # df_users = spark.read.jdbc(db_url, "\"user\"", properties=db_props) 
except Exception as e:
    print(f"Error reading from DB: {e}")
    sys.exit(1)

# ---------------------------------------------------------
# 1. PRE-PROCESSING: Calculate Usage (Delta)
# ---------------------------------------------------------
print(">>> Calculating Usage Deltas...")
window_spec = Window.partitionBy("user_id").orderBy("timestamp")

df_with_lag = df_readings.withColumn("prev_reading", lag("reading").over(window_spec))

# Calculate usage
df_usage = df_with_lag.withColumn("usage", col("reading") - col("prev_reading")) \
                      .filter((col("usage") >= 0) & (col("usage").isNotNull()))

# ---------------------------------------------------------
# 2. AGGREGATION: Society Monthly Dashboard Summary
# ---------------------------------------------------------
print(">>> Processing Society Monthly Summary...")

# FIX IS HERE: We use df_usage directly. It already has 'society_id'.
# No join needed -> No ambiguity -> Faster performance.
society_summary = df_usage.withColumn("month", month("timestamp")) \
                          .withColumn("year", year("timestamp")) \
                          .groupBy("society_id", "year", "month") \
                          .agg(_sum("usage").alias("total_consumption"))

print(">>> Writing to Database...")
society_summary.write.jdbc(db_url, "society_monthly_summary", mode="overwrite", properties=db_props)

print(">>> Batch Processing Complete!")
spark.stop()