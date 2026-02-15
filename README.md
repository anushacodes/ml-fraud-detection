# Real-Time Fraud Detection Pipeline

This project implements a production-style real-time fraud detection system using the PaySim dataset (~6.3M transactions).

The system ingests transaction events through Kafka, scores them using a hybrid rule-based and machine learning approach, stores flagged transactions, monitors drift, and supports automated retraining.

The primary goal of this project is to design and benchmark a low-latency fraud scoring pipeline with proper observability and MLOps practices.


## High-Level Flow

1. A Kafka producer simulates streaming transactions from the PaySim test dataset.

2. A consumer service processes each transaction.

3. Transactions are scored using:

    - LightGBM (primary supervised model)

    - Isolation Forest (shadow model)

    - Rule-based logic

4. Scores are combined into a final fraud risk score.

5. Flagged transactions are stored in Postgres.

6. Relationships are recorded in Neo4j for graph analysis.

7. Metrics are exported to Prometheus and visualized in Grafana.

8. Drift is detected using Evidently.

9. Prefect triggers retraining if drift exceeds threshold.



