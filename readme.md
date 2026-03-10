# Real-Time Fraud Detection Pipeline

A completely decoupled, event-driven real-time fraud detection pipeline. This repository streams transactions through Kafka, calculates real-time velocity features via Redis, scores them with an XGBoost model tracked by MLflow, monitors for data drift using Evidently AI, and visualizes system latency/fraud rates in Grafana. Retraining is handled via Prefect orchestration.

**Stack:** Kafka · Redis · XGBoost · MLflow · Evidently · Prefect · Prometheus · Grafana · Streamlit

## How It Works

1. **`kafka/producer.py`** reads `data/fraudTest.csv` and streams rows into a `raw-transactions` Kafka topic at a configurable rate (`config.yaml`).

2. **`src/inference/service.py`** (FastAPI) consumes `raw-transactions`, builds features using Redis velocity counts, scores each transaction with the registered XGBoost model, and publishes results to a `fraud-scores` topic. Prometheus metrics (latency, fraud rate) are exposed on `:8001`.

3. **`src/monitoring/buffer_monitor.py`** also consumes `raw-transactions` in parallel, buffers 30 seconds of data, and runs an Evidently drift report against training reference data. If drift > 30%, it logs the score to MLflow and triggers a Prefect retrain.

4. **`src/flows/retrain_flow.py`** trains a new XGBoost model, logs it to MLflow (backed by MinIO S3), and promotes it if PR-AUC ≥ 0.8.

5. **`dash.py`** is a Streamlit dashboard showing model performance metrics (accuracy, precision, recall) over time with event markers for drift and retrain events.



## Architecture

<img width="4743" height="1944" alt="Untitled-2026-03-09-2024" src="https://github.com/user-attachments/assets/c98a0413-c103-467a-aec1-4628d71fb48b" />



## Running It

All commands use a conda environment. Each long-running process needs its own terminal.

**Step 1 — Start infrastructure**
```bash
make up
```
This boots Kafka, Zookeeper, Redis, MinIO (S3), Postgres, MLflow, Prometheus, and Grafana. Wait a few seconds for `setup-minio` to finish creating the S3 bucket.

**Step 2 — Train the initial model**
```bash
make train
```
This trains XGBoost on the clean dataset and registers `fraud-detector` in MLflow. You need to do this before starting the inference service.

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
make down
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

The prometheus dashboard:


https://github.com/user-attachments/assets/545bfb7f-6dbd-453a-ad80-14b72c87156e



Streamlit dashboard:

<img width="1449" height="821" alt="Screenshot 2026-03-09 at 9 02 32 PM" src="https://github.com/user-attachments/assets/2ee5e63e-ef3f-441d-b514-5ed3bc4d49dc" />


