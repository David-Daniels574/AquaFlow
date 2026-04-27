# Use Python 3.9 Slim as base
FROM python:3.9-slim-bookworm

# 1. Install Java (Required for Spark) and wget
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless wget procps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Download the Postgres JDBC Driver (Required for Spark to talk to DB)
# We place it in /app/postgresql.jar
RUN wget https://jdbc.postgresql.org/download/postgresql-42.7.8.jar -O /app/postgresql.jar

# 3. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your script
COPY process_data.py .

# 5. Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# 6. Run the script using spark-submit, pointing to the downloaded JAR
CMD ["spark-submit", "--jars", "/app/postgresql.jar", "--driver-class-path", "/app/postgresql.jar", "process_data.py"]