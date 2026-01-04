import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, month, year, sum as _sum, lag
from pyspark.sql.window import Window

# --- CONFIGURATION ---
# In our new Dockerfile, we downloaded the JAR to /app/
jar_path = "/app/postgresql.jar"

# --- ENVIRONMENT VARIABLES ---
# Get credentials from AWS Task Definition (or local .env)
jdbc_url = os.environ.get("SPARK_JDBC_URL")
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")

# Safety check
if not all([jdbc_url, db_user, db_pass]):
    print("ERROR: Missing database environment variables (SPARK_JDBC_URL, DB_USER, DB_PASS).")
    print("Ensure these are set in your AWS ECS Task Definition.")
    sys.exit(1)

# --- INIT SPARK ---
spark = SparkSession.builder \
    .appName("WaterConsumptionAnalytics") \
    .config("spark.jars", jar_path) \
    .config("spark.driver.extraClassPath", jar_path) \
    .config("spark.executor.extraClassPath", jar_path) \
    .getOrCreate()

# --- DB PROPERTIES ---
db_props = {
    "user": db_user, 
    "password": db_pass, 
    "driver": "org.postgresql.Driver"
}

print(f">>> Connecting to Database: {jdbc_url.split('@')[0]}...") # Print safely (hide password)

try:
    df_readings = spark.read.jdbc(jdbc_url, "water_reading", properties=db_props)
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

# Logic: Group by society, year, month -> Sum usage
society_summary = df_usage.withColumn("month", month("timestamp")) \
                          .withColumn("year", year("timestamp")) \
                          .groupBy("society_id", "year", "month") \
                          .agg(_sum("usage").alias("total_consumption"))

print(">>> Writing to Database...")
try:
    society_summary.write.jdbc(jdbc_url, "society_monthly_summary", mode="overwrite", properties=db_props)
    print(">>> Success! Batch Processing Complete.")
except Exception as e:
    print(f"Error writing to DB: {e}")
    sys.exit(1)

spark.stop()