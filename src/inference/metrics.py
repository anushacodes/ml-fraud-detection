from prometheus_client import start_http_server, Counter, Histogram

# Initialize Prometheus metrics
TXN_COUNTER = Counter("fraud_txns_total", "Total transactions scored")
FRAUD_COUNTER = Counter("fraud_alerts_total", "Total transactions classified as fraud")
LATENCY_HISTOGRAM = Histogram("fraud_scoring_latency_seconds", "Latency of fraud scoring pipeline")

def init_metrics_server(port: int = 8001):
    """
    Starts the Prometheus metrics server.
    """
    print(f"Starting metrics server on port {port}")
    start_http_server(port)

def record_transaction(is_fraud: bool, latency: float):
    """
    Records a completed transaction scoring lifecycle.
    """
    TXN_COUNTER.inc()
    LATENCY_HISTOGRAM.observe(latency)
    if is_fraud:
        FRAUD_COUNTER.inc()
