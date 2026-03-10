import json
import time
import pandas as pd
import asyncio
from aiokafka import AIOKafkaConsumer
import mlflow
from evidently import Report
from evidently.presets import DataDriftPreset
from src.inference.inference_prep import prepare_features
from src.redis_client import get_redis_client, get_velocity
import os

from prefect.deployments import run_deployment

REFERENCE_DATA_PATH = "data/clean/X_train.csv"
BUFFER_TIME_SEC = 30
MIN_SAMPLES = 50

async def monitor_drift():
    print(f"Loading reference data from {REFERENCE_DATA_PATH}")
    ref_df = pd.read_csv(REFERENCE_DATA_PATH)
    
    redis_client = get_redis_client()
    consumer = AIOKafkaConsumer(
        'raw-transactions',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    await consumer.start()
    print(f"Started monitoring drift on raw-transactions every {BUFFER_TIME_SEC}s...")
    
    buffer = []
    last_eval_time = time.time()
    
    try:
        async for msg in consumer:
            txn = msg.value
            user_id = str(txn["cc_num"])
            
            # Reconstruct features for drift detection
            velocity = get_velocity(redis_client, user_id)
            df = prepare_features(txn, velocity)
            buffer.append(df.iloc[0].to_dict())
            
            # Check if time window elapsed
            current_time = time.time()
            if current_time - last_eval_time >= BUFFER_TIME_SEC:
                if len(buffer) >= MIN_SAMPLES:
                    eval_df = pd.DataFrame(buffer)
                    eval_df = eval_df[ref_df.columns] # alignment
                    
                    report = Report(metrics=[DataDriftPreset()])
                    snap = report.run(reference_data=ref_df, current_data=eval_df)
                    drift_score = snap.dict()["metrics"][0]["value"]["share"]
                    
                    print(f"Evaluated {len(buffer)} samples. Drift score: {drift_score:.2f}")
                    
                    # Log to MLflow
                    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
                    mlflow.set_experiment("Data_Drift_Monitoring")
                    with mlflow.start_run():
                        mlflow.log_metric("drift_score", drift_score)
                        
                    # Trigger retrain if drift is > 30%
                    if drift_score > 0.3:
                        print("WARNING: Data drift threshold exceeded! Triggering retrain flow...")
                        try:
                            run_deployment(name="retrain-flow/default", timeout=0)
                            print("Retraining triggered successfully.")
                        except Exception as e:
                            print(f"Failed to trigger retrain (Prefect): {e}")
                
                # Reset buffer
                buffer = []
                last_eval_time = current_time

    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(monitor_drift())
