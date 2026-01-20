# 💧 Water Consumption Analytics Platform

### A Cloud-Native Distributed System for Utility Data Processing & Analytics

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate%20%7C%20RDS-orange)
![Architecture](https://img.shields.io/badge/Architecture-Sidecar%20%26%20Batch-blueviolet)
![Tech Stack](https://img.shields.io/badge/Stack-Flask%20%7C%20PySpark%20%7C%20PostgreSQL-blue)

---

## 📖 Overview

The **Water Consumption Analytics Platform** is a scalable, cloud-native system designed to manage and analyze water usage data for large residential societies.

Unlike traditional monolithic systems, this platform follows a **Microservices-based architecture** deployed on AWS, cleanly separating:

- **Transactional workloads** (API, authentication, ingestion)
- **Analytical workloads** (batch processing, aggregation, anomaly detection)

This design ensures **high availability**, **cost efficiency**, and **performance isolation** between user-facing services and heavy computation.

---

## 🎯 Key Capabilities

- Secure user authentication & meter data ingestion
- High-throughput REST APIs
- Scheduled batch analytics using Apache Spark
- Consumption delta computation (current − previous)
- Monthly & daily aggregation reports
- Redis-based low-latency caching
- Cloud-native, containerized deployment

---

## 🏗️ Architecture & Cloud Design

The system is deployed on **AWS ECS (Fargate)** using a **containerized microservices architecture**.

### Architectural Patterns Used

- **Sidecar Pattern**
  - Redis runs alongside the Flask API inside the same ECS Task
  - Communication via `localhost` (zero network latency)

- **Decoupled Compute**
  - API handles real-time traffic
  - Analytics runs as an isolated batch job

- **Ephemeral Batch Processing**
  - Spark jobs are triggered on a schedule
  - Compute spins up, processes data, and shuts down automatically

---

## 🧱 High-Level Deployment Diagram

```text
                INTERNET
                    │
      [ Application Load Balancer ]
                    │
                    ▼
   ┌──────────────────────────────────────────────┐
   │        AWS ECS CLUSTER (Fargate)             │
   │                                              │
   │  ┌────────────────────────────────────────┐  │
   │  │ ECS SERVICE: Backend API               │  │
   │  │ (Always On)                            │  │
   │  │                                        │  │
   │  │ ┌──────────────┐      ┌────────────┐   │  │
   │  │ │ Flask App    │◀───▶│ Redis Cache│   │  │
   │  │ └──────────────┘      └────────────┘   │  │
   │  └────────────────────────────────────────┘  │
   │                                              │
   │  ┌────────────────────────────────────────┐  │
   │  │ ECS TASK: Analytics Job                │  │
   │  │ (Scheduled )                           │  │
   │  │                                        │  │
   │  │  ┌──────────────────────────────────┐  │  │
   │  │  │ PySpark Batch Processor          │  │  │
   │  │  │ (Reads Raw → Writes Aggregates)  │  │  │
   │  │  └──────────────────────────────────┘  │  │
   │  └────────────────────────────────────────┘  │
   └──────────────────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │ AWS RDS – PostgreSQL 16      │
         │ (Single Source of Truth)     │
         └──────────────────────────────┘

## 🛠️ Components & Tech Stack

---

### 1️⃣ Backend Microservice (API)

**Role**
- Authentication
- Meter reading ingestion
- Dashboard & reporting queries

**Tech Stack**
- Python 3.14
- Flask
- Gunicorn
- SQLAlchemy

**Deployment**
- AWS ECS Service (Fargate)
- Application Load Balancer
- Horizontal auto-scaling enabled

---

### 2️⃣ Caching Layer (Sidecar)

**Role**
- Cache high-frequency read operations (load avaiable tanker api) 

**Implementation**
- Redis container
- Deployed as a **sidecar** within the same ECS task as the Flask API

**Impact**
- ~40% reduction in database read load
- Sub-millisecond cache access latency

---

### 3️⃣ Analytics Engine (Batch Processor)

**Role**
- Compute water usage deltas (current − previous readings)
- Detect consumption anomalies
- Generate daily and monthly aggregate summaries

**Tech Stack**
- Apache Spark (PySpark)
- PostgreSQL JDBC Driver

**Execution Model**
- ECS one-off tasks
- Triggered via AWS EventBridge (Cron-based scheduling)

**Schedule**
- Executes every **4 hours**

**Output Tables**
- `DailyUsage`
- `SocietyMonthlySummary`

---

### 4️⃣ Database Layer

**Role**
- Persistent storage for transactional and analytical data

**Technology**
- AWS RDS
- PostgreSQL 16

**Characteristics**
- Managed backups
- High availability
- Fully ACID-compliant

---

## 📂 Project Structure

```bash
.
├── backend/                     # API Microservice
│   ├── app.py                   # Application factory & configuration
│   ├── models.py                # SQLAlchemy ORM models
│   ├── routes.py                # REST API endpoints
│   ├── Dockerfile               # Multi-stage Flask build
│   └── requirements.txt         # Python dependencies
│
├── analytics/                   # Spark Batch Processor
│   ├── process_data.py          # PySpark analytics logic
│   ├── Dockerfile               # Spark runtime (OpenJDK + Python)
│   └── postgresql.jar           # JDBC driver
│
└── docker-compose.yml           # Local development & testing
