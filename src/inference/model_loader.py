import mlflow
import os

def load_model(model_name: str = "fraud-detector", stage: str = "Production"):
    """
    Loads MLflow model from the local tracking server.
    """
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(tracking_uri)
    
    try:
        model_uri = f"models:/{model_name}/{stage}"
        print(f"Loading model {model_name} from {model_uri}")
        return mlflow.xgboost.load_model(model_uri)
    except Exception as e:
        print(f"Could not load MLflow model. Exception: {e}")
        # Return none to fallback to a dummy/shadow mode if necessary
        return None
