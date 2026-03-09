import json
import asyncio
import time
from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from src.redis_client import get_redis_client, get_velocity, update_velocity
from src.inference.inference_prep import prepare_features
from src.inference.model_loader import load_model
from src.inference.metrics import init_metrics_server, record_transaction

MODEL = None
REDIS = None

async def consume_raw_transactions():
    """
    Consumes transactions, calculates scores, and publishes to fraud-scores.
    """
    consumer = AIOKafkaConsumer(
        'raw-transactions',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda m: json.dumps(m).encode('utf-8')
    )
    
    await consumer.start()
    await producer.start()
    print("Inference service listening on raw-transactions...")
    
    try:
        async for msg in consumer:
            start_t = time.time()
            txn = msg.value
            user_id = str(txn["cc_num"])
            
            # Fetch and update velocity
            velocity = get_velocity(REDIS, user_id)
            update_velocity(REDIS, user_id)
            
            # Prepare ML features
            df = prepare_features(txn, velocity)
            
            # Score transaction
            is_fraud = False
            prob = 0.0
            if MODEL is not None:
                # Assuming model returns a list or array
                pred = MODEL.predict(df)
                prob = float(pred[0])
                is_fraud = prob > 0.8  # Probability threshold
            
            # Log metrics
            latency = time.time() - start_t
            record_transaction(is_fraud, latency)
            
            # Publish result
            result = {
                "cc_num": user_id,
                "trans_num": txn["trans_num"],
                "probability": prob,
                "is_fraud": is_fraud,
                "latency_sec": latency
            }
            await producer.send_and_wait("fraud-scores", result)
            
    finally:
        await consumer.stop()
        await producer.stop()

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_metrics_server(8001)
    global MODEL, REDIS
    MODEL = load_model()
    REDIS = get_redis_client()
    asyncio.create_task(consume_raw_transactions())

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": MODEL is not None}
