# Water Consumption Analytics Platform

### A Cloud-Native Distributed System for Utility Data Processing & Analytics

---

## Overview

The **Water Consumption Analytics Platform** is a scalable, cloud-native system that manages and analyzes water usage data for large residential societies, while serving as a marketplace layer between water tanker operators and society admins.

The platform handles two fundamentally different workload profiles under one system:

- **Transactional workloads** — low-latency, user-facing operations: authentication, tanker booking, payments via Stripe, and a gamified eco-challenges system
- **Analytical workloads** — high-throughput, scheduled batch processing of IoT sensor data for consumption aggregation and anomaly detection

These are intentionally separated into independent compute layers so that a heavy Spark job cannot degrade API response times, and so each layer can be scaled, monitored, and deployed independently.

---

## Architecture & Key Design Decisions

### Why Microservices over a Monolith?

The transactional and analytical workloads have opposing SLA requirements. The API must respond in milliseconds; the Spark jobs process potentially millions of IoT records and run for minutes. A monolith would force them to share resources, risking latency spikes during batch runs. Separating them allows independent scaling, failure isolation, and cost control.

### Why AWS ECS (Fargate) over EC2 or Lambda?

Fargate was chosen to avoid EC2 instance management overhead while retaining container-level control. Lambda was ruled out because Spark jobs exceed Lambda's execution time and memory limits. Fargate provides the right middle ground: serverless infrastructure with long-running container support.

### Why Ephemeral Spark over a Persistent Cluster?

Running a persistent Spark cluster 24/7 would be cost-prohibitive for batch workloads that only run three times a day. Using AWS EventBridge to trigger an ECS Task on a schedule means compute spins up, processes data, writes results to RDS, and terminates — paying only for actual processing time.

### Why the Sidecar Pattern for Redis?

Redis runs as a sidecar container within the same ECS Task as the Flask API, communicating over `localhost`. This eliminates network hops for cache reads, which are on the hot path for every authenticated request. The trade-off is that Redis is not independently scalable in this configuration — an acceptable constraint given the session-caching use case.

### Why PostgreSQL (RDS) as the Unified Store?

Both the API (OLTP) and the Spark jobs (OLAP writes) target the same RDS PostgreSQL instance. This avoids a separate analytics store and simplifies the data model, at the cost of some query isolation. For the current scale this is acceptable; a future evolution would introduce read replicas or a dedicated data warehouse (e.g., Redshift) for heavier analytical queries.

---

## High-Level Deployment Diagram

```text
                                    +-----------------------+
                                    |    User Browser       |
                                    |  (Frontend on Vercel) |
                                    +-----------+-----------+
                                                | HTTPS
                                                v
                                    +-----------------------+
                                    | AWS App Load Balancer |
                                    +-----------+-----------+
                                                |
+-------------------+               +-----------v-----------+               +-------------------+
|  Stripe API       | <---HTTPS---> |    Flask Backend      | <-----------> |  Redis (Sidecar)  |
| (Payment Gateway) |               |  (AWS ECS Fargate)    |               |  localhost:6379   |
+-------------------+               +-----------+-----------+               +-------------------+
                                                |
                                                v
+-------------------+               +-----------------------+               +-------------------+
| IoT Sensor Data   |               |   Amazon RDS          |               | Prometheus &      |
| (S3 / Data Store) | <-----------> |   (PostgreSQL)        | <-----------> | Grafana           |
+---------+---------+               +-----------+-----------+               | (Monitoring)      |
          |                                     ^                           +-------------------+
          |                                     |
          |                 +-------------------v-------------------+
          +---------------> |   Apache Spark Analytics Job          |
                            |   ECS Task — triggered by EventBridge |
                            |   3x daily schedule (ephemeral)       |
                            +---------------------------------------+
```

**Data flow summary:**

1. IoT sensors write raw consumption records to S3
2. EventBridge triggers the Spark ECS Task on schedule
3. Spark reads from S3, aggregates by unit/society/time window, detects anomalies
4. Aggregated results are written back to RDS PostgreSQL
5. The Flask API serves pre-aggregated data to the frontend with sub-millisecond Redis cache hits on hot queries

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React / Next.js / TypeScript on Vercel | SSR support, zero-config CDN deployment |
| API | Python / Flask on ECS Fargate | Lightweight, fits team familiarity, horizontally scalable |
| Auth | JWT (JSON Web Tokens) | Stateless — scales horizontally without session affinity |
| Payments | Stripe API | Handles fractional currency, PCI compliance out of the box |
| Cache | Redis (sidecar) | Sub-millisecond session and query caching on the hot path |
| Primary DB | Amazon RDS PostgreSQL | ACID compliance, strong ORM support via SQLAlchemy |
| Batch Processing | Apache Spark (PySpark) | Distributed processing for large IoT datasets |
| Containerization | Docker & Docker Compose | Environment parity between local dev and cloud |
| IaC | Terraform | Reproducible, version-controlled AWS infrastructure |
| CI/CD | Jenkins + SonarQube + Pytest | Automated test, quality gate, and security scan pipeline |
| Monitoring | Prometheus + Grafana | Real-time metrics and alerting on API and infrastructure |

---

## Architectural Patterns Applied

**Sidecar Pattern** — Redis is co-located with the Flask API in the same ECS Task, communicating over `localhost`. This eliminates inter-container network latency on the session and cache hot path.

**Decoupled Compute** — The API and the analytics pipeline are fully independent ECS Tasks. A Spark job failure does not affect API availability, and neither workload can starve the other of CPU or memory.

**Ephemeral Batch Processing** — Spark compute is provisioned only when needed. EventBridge triggers the ECS Task on a cron schedule; the container exits after completion. Infrastructure costs remain proportional to actual workload.

**Application Load Balancer as Edge** — All public traffic enters through an ALB, enabling health-check-based routing, SSL termination, and a single ingress point for future horizontal scaling of the Flask service.

---

## Project Structure

```bash
.
├── README.md                      # Project documentation
├── docker-compose.yml             # Local dev environment orchestration
├── docker-compose.cicd.yml        # CI/CD-specific orchestration
├── prometheus.yml                 # Prometheus scrape configuration
├── .gitignore
│
├── analytics/                     # Spark batch processing layer
│   ├── Dockerfile
│   ├── process_data.py            # PySpark: ingest S3, aggregate, write to RDS
│   ├── requirements.txt
│   └── data/                      # Local volume mount for IoT data
│
├── backend/                       # Flask API layer
│   ├── app.py                     # Application entrypoint
│   ├── auth.py                    # JWT authentication logic
│   ├── routes.py                  # Endpoints: tankers, bulk orders, challenges
│   ├── models.py                  # SQLAlchemy ORM schemas
│   ├── config.py                  # Environment configuration
│   ├── utils.py                   # Shared helpers
│   ├── populate_db.py             # Seed script: users, societies, suppliers, challenges
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── Jenkinsfile                # CI/CD pipeline definition
│   ├── sonar-project.properties   # SonarQube configuration
│   └── tests/
│       ├── conftest.py            # Pytest fixtures
│       └── test_business_logic.py # Unit tests: API, Stripe, state machines
│
├── frontend/                      # React / Next.js web client
├── data/                          # Shared volume: DB and analytics
└── spark_libs/
    └── postgresql-42.7.8.jar      # JDBC driver for Spark → RDS writes
```

---

## Local Setup & Development Guide

### Prerequisites

- **Docker & Docker Compose** (daemon must be running)
- **Python 3.10+**
- **Git**

---

### Step 1: Clone & Configure

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

Create `backend/.env`:

```env
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://user:password@db:5432/waterdb
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=super-secret-key-change-this-in-prod-make-it-32-chars
STRIPE_SECRET_KEY=sk_test_your_stripe_test_key
```

---

### Step 2: Start All Services

```bash
docker-compose up -d --build
```

> Drop `-d` or run `docker-compose logs -f` to tail live logs.

```bash
docker ps   # verify all containers are healthy
```

This starts: PostgreSQL, Redis, Flask API, Spark Master + Worker, Prometheus, Grafana.

---

### Step 3: Seed the Database

```bash
docker exec -it water_mgmt_backend python populate_db.py
```

Creates tables and populates initial data: users, societies, tanker suppliers, and eco-challenges.

---

### Step 4: Trigger a Spark Analytics Run

```bash
docker exec -it spark_master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars_external/postgresql-42.7.8.jar \
  /opt/analytics/process_data.py
```

Simulates the EventBridge-triggered batch job. Reads from `analytics/data/`, aggregates IoT metrics, and writes results to PostgreSQL.

---

### Step 5: Access Services

| Service | URL | Credentials |
|---|---|---|
| Flask API | `http://localhost:5001` | — |
| Prometheus | `http://localhost:9090` | — |
| Grafana | `http://localhost:3000` | `admin` / `admin` |
| Spark UI | `http://localhost:8080` | — |

To connect Grafana to Prometheus: add a data source pointed at `http://prometheus:9090`.

---

### Step 6: Run Tests & Quality Checks Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-flask pytest-cov flake8 bandit
```

```bash
pytest tests/ -v --cov=. --cov-report=xml   # generates coverage.xml for SonarQube
flake8 .                                     # style and lint
bandit -r .                                  # security scan
```

---

### Step 7: CI/CD Pipeline (Jenkins + SonarQube)

This project includes a fully containerized local CI/CD environment. On push, Jenkins uses the `Jenkinsfile` to spin up isolated test containers, run the Pytest suite, generate a `coverage.xml` report, and submit it to SonarQube for quality gate evaluation using `sonar-project.properties`.

To run and manage the local CI/CD stack:

**1. Spin up the CI/CD Environment**
Start Jenkins and SonarQube in the background using the dedicated CI/CD compose file:
```bash
docker-compose -f docker-compose.cicd.yml up -d
```

**2. Unlock Jenkins**
On the very first run, Jenkins will be locked. Fetch the initial admin password directly from the container:
```bash
docker exec -it water_cicd_jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

**3. Access the Dashboards**
Once the services are healthy, you can access the UI for both tools:
```bash
    Jenkins: http://localhost:8080 (Use the password fetched above to complete setup).
    SonarQube: http://localhost:9000 (Default login is usually admin / admin).
```
---

### Teardown

```bash
docker-compose down        # stop and remove containers
docker-compose down -v     # also wipe volumes (full reset)
docker-compose -f docker-compose.cicd.yml down -v # shut down the CI/CD environment
```

### To test use
**User**
```bash
john_1
pass123
```

**Tanker owner**
```bash
owner_raj
owner123
```
