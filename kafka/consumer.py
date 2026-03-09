import json
import yaml
from kafka import KafkaConsumer

def test_consumer(topic: str, broker: str = 'localhost:9092'):
    print(f"Connecting to Kafka Broker at {broker} to listen on '{topic}'...")
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[broker],
        auto_offset_reset='latest',  # Read new messages as they come in
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    try:
        for message in consumer:
            # message.value is our parsed python dictionary
            txn = message.value
            print(f"Received Transaction | Card: {txn.get('cc_num', 'N/A')} | Amount: ${txn.get('amt', 0.0)} | Time: {txn.get('trans_date_trans_time', 'N/A')}")
            
    except KeyboardInterrupt:
        print("\nStopping consumer")
    finally:
        consumer.close()

if __name__ == "__main__":
    # Load config settings, similar to the producer
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)["kafka"]

    test_consumer(
        topic=config["topic"],
        broker=config["broker"]
    )
