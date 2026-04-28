# Water Consumption Analytics Platform

### A Cloud-Native Distributed System for Utility Data Processing & Analytics

---

## Overview

The **Water Consumption Analytics Platform** is a cloud-native system for:

- low-latency transactional flows (auth, booking, payments, community)
- scheduled analytical processing of IoT water readings

The codebase was refactored from a monolith into **5 Flask microservices** behind an **Nginx API Gateway**.  
This separation isolates failures, improves scalability, and keeps Spark batch workloads from degrading API response times.

---

## Architecture & Key Design Decisions

### Why microservices over a monolith?

Transactional APIs require low latency, while Spark analytics are bursty and compute heavy. Splitting domains into services enables:

- independent deployment and scaling
- bounded blast radius
- domain ownership by capability (auth, supplier, booking, gamification, analytics)

### Why an Nginx API Gateway?

The gateway provides a single ingress (`:5001`) and handles:

- path-based routing to services
- request correlation ID generation/propagation (`X-Correlation-ID`)
- centralized edge behavior

### Why separate databases per service?

Each service owns its own schema/database (`auth_db`, `supplier_db`, `booking_db`, `gamification_db`, `iot_db`) to preserve autonomy and reduce coupling.  
Cross-service data joins are done via **inter-service HTTP APIs**, not foreign keys.

### Why Redis as shared infrastructure (not sidecar)?

Redis now runs as an independent shared service in Compose (and should be a shared infra service in production), which allows:

- independent scaling and lifecycle
- cleaner resource isolation
- shared caching across services when needed

### Why ephemeral Spark?

Spark runs in dedicated containers and can be scheduled/triggered independently. This keeps analytics compute separate from API compute and avoids 24/7 cluster cost.

---

## High-Level Deployment Diagram

```text
                                    +-----------------------+
                                    |    User Browser       |
                                    |  (Frontend / Vite)    |
                                    +-----------+-----------+
                                                |
                                                v
                                    +-----------------------+
                                    |   Nginx API Gateway   |
                                    |      (Port 5001)      |
                                    +--+----+----+----+-----+
                                       |    |    |    | 
                                       |    |    |    +-------------------+
                                       |    |    +------> iot_analytics   |
                                       |    +-----------> gamification     |
                                       +---------------> booking           |
                                                      +-> supplier         |
                                                      +-> auth             |

     +------------------+      +-------------------+      +------------------------+
     |  Redis (shared)  |<---->| Flask services    |<---->| PostgreSQL (5 DBs)     |
     +------------------+      +-------------------+      +------------------------+
                                                ^
                                                |
                                   +------------+------------+
                                   | Spark Master + Worker   |
                                   | Reads parquet, writes DB|
                                   +------------+------------+
                                                |
                                      +---------+---------+
                                      | data/raw parquet  |
                                      +-------------------+

              +---------------------+              +--------------------+
              | Prometheus (+redis) | <----------  | Flask /metrics     |
              +----------+----------+              +--------------------+
                         |
                         v
                    +----+----+
                    | Grafana |
                    +---------+
```

---

## Microservices & Route Mapping

1. **Auth Service** (`/auth/*`)
   - `GET /`
   - `GET /ping`
   - `POST /register`
   - `POST /login`
   - `GET|PUT /profile`

2. **Supplier Service** (`/supplier/*`)
   - `GET /suppliers`
   - `POST /tankers`
   - `GET /tankers/owner`
   - `PUT /tankers/<id>`
   - `DELETE /tankers/<id>`
   - `PATCH /tankers/<id>/status`
   - `GET /owner/dashboard`
   - `GET /owner/earnings`

3. **Booking Service** (`/bookings/*`)
   - `POST /book_tanker`
   - `GET /track_order/<id>`
   - `PUT /update_order/<id>`
   - `POST /bookings`
   - `GET /bookings/owner`
   - `PATCH /bookings/<id>/status`
   - `POST /society_bulk_order`
   - `POST /create-payment-intent`

4. **IoT Analytics Service** (`/analytics/*`)
   - `POST /log_reading`
   - `GET /consumption_report`
   - `GET /society_dashboard`
   - `GET /conservation_summary`

5. **Gamification Service** (`/gamification/*`)
   - `GET /conservation_tips`
   - `GET /challenges`
   - `POST /start_challenge/<id>`
   - `GET /user_challenges`
   - `PUT /update_challenge_progress/<id>`
   - `GET|POST /community/broadcasts`
   - `GET|POST /community/threads`
   - `GET|POST /community/threads/<id>/comments`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| API | Flask microservices |
| Gateway | Nginx |
| Auth | JWT |
| Payments | Stripe |
| Cache | Redis |
| DB | PostgreSQL 13 (logical split DBs) |
| Analytics | Apache Spark (PySpark) |
| Monitoring | Prometheus + Grafana |
| CI/CD | Jenkins + SonarQube + Pytest |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```bash
.
├── README.md
├── docker-compose.yml
├── docker-compose.cicd.yml
├── prometheus.yml
├── analytics/
│   ├── Dockerfile
│   ├── process_data.py
│   └── requirements.txt
├── backend/
│   ├── api_gateway/nginx.conf
│   ├── auth_service/
│   ├── supplier_service/
│   ├── booking_service/
│   ├── gamification_service/
│   ├── iot_analytics_service/
│   ├── db_init/01-create-databases.sql
│   ├── populate_db.py
│   ├── Jenkinsfile
│   ├── sonar-project.properties
│   └── tests/
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── data/
└── spark_libs/
```

---

## Local Setup & Development Guide

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 18+
- PowerShell 7+

---

### Step 1: Clone & Configure

```powershell
git clone <your-repo-url>
cd <your-repo-folder>
```

Create/Update `backend/.env`:

```env
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-at-least-32-chars
STRIPE_SECRET_KEY=sk_test_your_stripe_test_key
INTERNAL_SERVICE_TOKEN=internal-dev-token
```

Create/Update `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:5001
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_key
```

---

### Step 2: Start all backend services

If you have old monolith data, run a full reset once:

```powershell
docker compose down -v
```

Then start:

```powershell
docker compose up -d --build
docker ps
```

---

### Step 3: Seed the databases (**inside Docker**)

The old command is no longer valid because `water_mgmt_backend` (monolith container) does not exist anymore.

Use:

```powershell
docker compose --profile tools run --rm db_seeder
```

This runs `backend/populate_db.py` inside a dedicated seeder container and populates:

- `auth_db`
- `supplier_db`
- `booking_db`
- `gamification_db`
- `iot_db`

---

### Step 4: Trigger Spark analytics run (**inside Docker**)

Use:

```powershell
docker exec -it spark_master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --jars /opt/spark/jars_external/postgresql-42.7.8.jar `
  /opt/analytics/process_data.py
```

This reads parquet under `/opt/analytics/data/raw/water_readings` and writes aggregated outputs to `iot_db`.

---

### Step 5: Start frontend

```powershell
cd frontend
npm install
npm run dev
```

---

### Step 6: Access services

| Service | URL | Notes |
|---|---|---|
| API Gateway | `http://localhost:5001` | all backend APIs |
| Prometheus | `http://localhost:9090` | metrics |
| Grafana | `http://localhost:3000` | `admin/admin` |
| Spark UI | `http://localhost:8080` | master UI |
| Jenkins | `http://localhost:8081` | from cicd compose |
| SonarQube | `http://localhost:9000` | from cicd compose |

---

### Step 7: Grafana quick guide (smart/default path)

Grafana is pre-provisioned from files under `grafana/provisioning` and `grafana/dashboards`:

- datasource: Prometheus (`http://prometheus:9090`)
- default dashboard: **Water Platform - Microservices Overview**

So you do **not** need to manually create datasources/panels each time.

If you want custom panels, these PromQL queries are good defaults:

```promql
sum by (job) (rate(flask_http_request_total[5m]))
histogram_quantile(0.95, sum by (le, job) (rate(flask_http_request_duration_seconds_bucket[5m])))
sum by (job) (rate(flask_http_request_exceptions_total[5m]))
sum(increase(flask_http_request_total[1h]))
redis_memory_used_bytes
redis_connected_clients
rate(redis_commands_processed_total[5m])
```

---

### Step 8: Tests and quality checks

Backend:

```powershell
python -m pip install pytest
python -m pytest backend\tests -q
python -m compileall backend\auth_service backend\supplier_service backend\booking_service backend\gamification_service backend\iot_analytics_service
```

Frontend:

```powershell
cd frontend
npx tsc -p tsconfig.app.json --noEmit
npm run build
```

---

## CI/CD Pipeline (Jenkins + SonarQube)

Yes, the CI/CD flow remains conceptually the same, but the pipeline is updated for microservices:

- installs dependencies per backend service
- compiles all 5 service packages
- runs `backend/tests`
- publishes `coverage.xml` to SonarQube

### 1) Start CI/CD stack

```powershell
docker compose -f docker-compose.cicd.yml up -d
```

### 2) Unlock Jenkins (first run only)

```powershell
docker exec -it water_cicd_jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### 3) Open dashboards

- Jenkins: `http://localhost:8081`
- SonarQube: `http://localhost:9000` (default usually `admin/admin`)

### 4) Jenkins job setup

1. Create a Pipeline job pointing to this repository.
2. Use repository `backend/Jenkinsfile`.
3. Configure SonarQube server in Jenkins as `SonarQube`.
4. Ensure `SonarQubeScanner` tool is installed in Jenkins global tools.

---

## Teardown

```powershell
docker compose down
docker compose down -v
docker compose -f docker-compose.cicd.yml down -v
```

---

## Seeded test credentials

**User**

```text
john_1
pass123
```

**Tanker owner**

```text
owner_raj
owner123
```
