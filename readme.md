# Real-Time Fraud Detection Pipeline

Streams credit card transactions through Kafka, scores them with XGBoost in real-time, and monitors for data drift. When drift crosses a threshold, Prefect triggers a retrain automatically.

**Stack:** Kafka · Redis · XGBoost · MLflow · Evidently · Prefect · Prometheus · Grafana

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

**1. Start infrastructure** (Kafka, Redis, MinIO, MLflow, Prometheus, Grafana)
```bash
docker compose up -d
```
Wait a few seconds for `setup-minio` to finish initializing buckets.

**2. Train the initial model**
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
python -m src.flows.retrain_flow
```

**3. Start the inference service**
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin

uvicorn src.inference.service:app --port 8000 --reload
```

**4. Start the drift monitor**
```bash
python -m src.monitoring.buffer_monitor
```

**5. Start streaming transactions**
```bash
python -m kafka.producer
```

## Dashboards
- **Streamlit:** `streamlit run dash.py`
- **MLflow:** http://localhost:5000
- **Grafana:** http://localhost:3000 (admin / admin — connect Prometheus datasource to `http://prometheus:9090`)
- **Prometheus:** http://localhost:9090
- **MinIO:** http://localhost:9001 (minioadmin / minioadmin)
