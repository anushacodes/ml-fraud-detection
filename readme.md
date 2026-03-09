# Real-Time Fraud Detection MLOps Pipeline 

A completely decoupled, event-driven real-time fraud detection pipeline. This repository streams transactions through Kafka, calculates real-time velocity features via Redis, scores them with an XGBoost model tracked by MLflow, monitors for data drift using Evidently AI, and visualizes system latency/fraud rates in Grafana. Retraining is handled via Prefect orchestration.

## Architecture
```text
fraudTest.csv
     │
     ▼
producer.py ──────────────────► raw-transactions topic
                                        │
                          ┌─────────────┘
                          ▼
                   inference/service.py
                   ├── inference_prep.py   (feature construction)
                   ├── model_loader.py     (cached MLflow model)
                   ├── redis_client.py     (velocity features)
                   └── metrics.py          (Prometheus :8001)
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
      fraud-scores               high-confidence-fraud
              │
              ▼
   monitoring/buffer_monitor.py
   ├── 30s windows
   ├── Evidently drift check
   ├── MLflow metric logging
   └── Prefect retrain trigger 
              │
              ▼
   flows/retrain_flow.py (Prefect)
```

## Setup & Running

**1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the Infrastructure**
This boots Kafka, Zookeeper, Redis, MinIO (S3), Postgres, MLflow, Prometheus, and Grafana.
```bash
docker compose up -d
```
*Wait a few seconds for the `setup-minio` container to finish creating the buckets.*

**3. Initial Model Training**
Before you can run the inference service, it needs a model to load!
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
python -m src.flows.retrain_flow
```
*This will train the initial XGBoost model and register `fraud-detector` in MLflow.*

**4. Start the Inference Service (FastAPI)**
In a new terminal window:
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin

uvicorn src.inference.service:app --port 8000 --reload
```
*(This service opens Prometheus metrics on `:8001` so Grafana can scrape them).*

**5. Start the Drift Monitor**
In a new terminal window:
```bash
python -m src.monitoring.buffer_monitor
```

**6. Start the Kafka Producer (Stream Data)**
Now that everything is listening, turn on the firehose! 
```bash
python -m kafka.producer
```

## Dashboards
- **MLflow UI:** http://localhost:5000
- **MinIO Storage:** http://localhost:9001 (minioadmin / minioadmin)
- **Grafana:** http://localhost:3000 (admin/admin -> connect Prometheus to `http://prometheus:9090`)
- **Prometheus:** http://localhost:9090
