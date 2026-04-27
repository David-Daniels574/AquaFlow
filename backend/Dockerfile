# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for building Python packages (like psycopg2)
# libpq-dev is specifically for PostgreSQL communication
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application using Gunicorn (Production Server)
# -w 4: Spawns 4 worker processes (Parallelism)
# -b 0.0.0.0:5000: Binds to all network interfaces
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]