import json
import time
import pandas as pd
import yaml
from kafka import KafkaProducer

# Kafka expects values as bytes, so we need to serialize the data.
def stream_transactions(csv_path, topic, broker='localhost:9092', msg_per_sec=100):
    producer = KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    print(f"Connected to Kafka Broker at {broker}")

    df = pd.read_csv("data/fraudTest.csv")
    sleep_time = 1.0 / msg_per_sec
    topic = "raw-transactions"

    try:
        for _, row in df.iterrows():
            producer.send(topic, value=row.to_dict())
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        pass

    finally:
        producer.flush()
        producer.close()
        print("Kafka connection closed.")

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)["kafka"]

    stream_transactions(
        topic=config['topic'], 
        broker=config['broker'],
        msg_per_sec=config['msg_per_sec']
    )