
CONDA_RUN = conda run -n mlops --no-capture-output

.PHONY: infra-up infra-down train svc monitor producer dashboard

# Boot all infrastructure (Kafka, Redis, MLflow, MinIO, Postgres, Prometheus, Grafana)
infra-up:
	docker compose up -d

# Tear down all infrastructure
infra-down:
	docker compose down

# Train initial XGBoost model and register it in MLflow
train:
	MLFLOW_TRACKING_URI=http://localhost:5001 \
	MLFLOW_S3_ENDPOINT_URL=http://localhost:9000 \
	AWS_ACCESS_KEY_ID=minioadmin \
	AWS_SECRET_ACCESS_KEY=minioadmin \
	$(CONDA_RUN) python -m src.flows.retrain_flow

# Start the FastAPI inference service (Kafka consumer + scorer + Prometheus metrics on :8001)
svc:
	MLFLOW_TRACKING_URI=http://localhost:5001 \
	MLFLOW_S3_ENDPOINT_URL=http://localhost:9000 \
	AWS_ACCESS_KEY_ID=minioadmin \
	AWS_SECRET_ACCESS_KEY=minioadmin \
	$(CONDA_RUN) uvicorn src.inference.service:app --port 8000 --reload

# Start the drift monitor (30s windows, Evidently, Prefect retrain trigger)
monitor:
	MLFLOW_TRACKING_URI=http://localhost:5001 \
	$(CONDA_RUN) python -m src.monitoring.buffer_monitor

# Stream transactions from fraudTest.csv into Kafka
producer:
	$(CONDA_RUN) python kafka/producer.py

# Open the Streamlit model performance dashboard
dashboard:
	$(CONDA_RUN) streamlit run dash.py