# Real-Time Fraud Detection Pipeline

Streams credit card transactions through Kafka, scores them in real-time with XGBoost, and watches for data drift. When drift exceeds 30%, Prefect kicks off a retrain automatically. Everything runs in Docker — you just need the `mlops` conda env for the Python processes.

**Stack:** Kafka · Redis · XGBoost · MLflow · Evidently · Prefect · Prometheus · Grafana · Streamlit

## How It Works

1. **`kafka/producer.py`** reads `data/fraudTest.csv` and streams rows into a `raw-transactions` Kafka topic at a configurable rate (`config.yaml`).

2. **`src/inference/service.py`** (FastAPI) consumes `raw-transactions`, builds features using Redis velocity counts, scores each transaction with the registered XGBoost model, and publishes results to a `fraud-scores` topic. Prometheus metrics (latency, fraud rate) are exposed on `:8001`.

3. **`src/monitoring/buffer_monitor.py`** also consumes `raw-transactions` in parallel, buffers 30 seconds of data, and runs an Evidently drift report against training reference data. If drift > 30%, it logs the score to MLflow and triggers a Prefect retrain.

4. **`src/flows/retrain_flow.py`** trains a new XGBoost model, logs it to MLflow (backed by MinIO S3), and promotes it if PR-AUC ≥ 0.8.

5. **`dash.py`** is a Streamlit dashboard showing model performance metrics (accuracy, precision, recall) over time with event markers for drift and retrain events.

## Architecture
```text
fraudTest.csv
     │
     ▼
kafka/producer.py ───────────────────────────────► raw-transactions topic
                                                           │
                                         ┌─────────────────┴──────────────────────┐
                                         ▼                                         ▼
                              inference/service.py                    monitoring/buffer_monitor.py
                              ├── inference_prep.py (features)        ├── 30s sliding windows
                              ├── model_loader.py  (MLflow model)     ├── Evidently drift check
                              ├── redis_client.py  (velocity)         ├── MLflow metric logging
                              └── metrics.py       (Prometheus :8001) └── Prefect retrain trigger
                                         │                                         │
                                         ▼                                         ▼
                                  fraud-scores topic                   flows/retrain_flow.py (Prefect)
```

## Running It

All commands use the `mlops` conda environment. Each long-running process needs its own terminal.

**Step 1 — Start infrastructure**
```bash
make infra-up
```
Boots Kafka, Redis, MLflow (port 5001), MinIO, Postgres, Prometheus, and Grafana. Wait a few seconds for `setup-minio` to finish creating the S3 bucket.

**Step 2 — Train the initial model**
```bash
make train
```
Trains XGBoost on the clean dataset and registers `fraud-detector` in MLflow. You need to do this before starting the inference service.

**Step 3 — Start the inference service** *(new terminal)*
```bash
make svc
```
FastAPI app on `:8000`. Consumes transactions, scores them, and exposes Prometheus metrics on `:8001`.

**Step 4 — Start the drift monitor** *(new terminal)*
```bash
make monitor
```
Runs Evidently drift checks every 30 seconds and auto-triggers retraining via Prefect if needed.

**Step 5 — Start streaming transactions** *(new terminal)*
```bash
make producer
```
Reads `fraudTest.csv` and pumps rows into Kafka. This is what drives the whole pipeline.

**Step 6 — Open the dashboard** *(optional, new terminal)*
```bash
make dashboard
```

To shut everything down:
```bash
make infra-down
```

## Dashboards & UIs
| Service | URL | Credentials |
|---|---|---|
| Streamlit | `make dashboard` | — |
| MLflow | http://localhost:5001 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| MinIO | http://localhost:9001 | minioadmin / minioadmin |

> Grafana: add a Prometheus datasource pointing to `http://prometheus:9090`.

## Project Structure
```
kafka/
  producer.py          # Streams fraudTest.csv → Kafka
  consumer.py          # Debug consumer (for testing)
src/
  inference/
    service.py         # FastAPI: consumes, scores, publishes
    inference_prep.py  # Feature construction from raw txn + Redis velocity
    model_loader.py    # Loads registered MLflow model
    metrics.py         # Prometheus counter/histogram setup
  monitoring/
    buffer_monitor.py  # Drift detection + Prefect retrain trigger
  flows/
    retrain_flow.py    # Prefect flow: train → log → promote
  redis_client.py      # Velocity feature helpers
data/
  fraudTest.csv        # Streaming source data
  fraudTrain.csv       # Training source data
  clean/               # Preprocessed train/test splits (X_train, y_train, etc.)
dash.py                # Streamlit performance dashboard
config.yaml            # Kafka broker/topic/rate settings
docker-compose.yml     # All infrastructure
makefile               # Shortcuts for every step
```
