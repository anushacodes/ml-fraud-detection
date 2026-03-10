import mlflow
import os
from mlflow.tracking import MlflowClient

def load_model(model_name: str = "fraud-detector", stage: str = "Production"):
    """
    Loads the MLflow model. Tries the Production stage first, then falls back
    to the latest registered version so the service works right after training.
    """
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(tracking_uri)

    # Try Production stage first
    try:
        model_uri = f"models:/{model_name}/{stage}"
        print(f"Loading model {model_name} from {model_uri}")
        return mlflow.xgboost.load_model(model_uri)
    except Exception:
        pass

    # Fall back to latest version
    try:
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        if not versions:
            print(f"No registered versions found for model '{model_name}'")
            return None
        latest = max(versions, key=lambda v: int(v.version))
        model_uri = f"models:/{model_name}/{latest.version}"
        print(f"No Production model found. Loading latest version: {latest.version}")
        return mlflow.xgboost.load_model(model_uri)
    except Exception as e:
        print(f"Could not load MLflow model. Exception: {e}")
        return None
