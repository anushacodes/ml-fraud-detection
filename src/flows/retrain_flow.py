from prefect import flow, task
import pandas as pd
import xgboost as xgb
import mlflow
from sklearn.metrics import average_precision_score
import os

os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"

def extract_data_from_lake():
    """Pulls latest data from MinIO (simulated via local clean directory)."""
    print("Extracting data...")
    return {
        "x_train": "data/clean/X_train.csv",
        "y_train": "data/clean/y_train.csv",
        "x_test": "data/clean/X_test.csv",
        "y_test": "data/clean/y_test.csv"
    }

def prepare_training_data(paths: dict):
    """Loads CSVs into Pandas DataFrames."""
    return {
        "X_train": pd.read_csv(paths["x_train"]),
        "y_train": pd.read_csv(paths["y_train"]).squeeze(),
        "X_test": pd.read_csv(paths["x_test"]),
        "y_test": pd.read_csv(paths["y_test"]).squeeze()
    }

def train_model(data: dict):
    """Trains XGBoost and logs to MLflow."""
    mlflow.set_experiment("Fraud_Detection_Retraining")
    
    with mlflow.start_run() as run:
        clf = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=5, 
            learning_rate=0.1, 
            use_label_encoder=False, 
            eval_metric="logloss"
        )
        clf.fit(data["X_train"], data["y_train"])
        
        # Predict on test set
        preds = clf.predict_proba(data["X_test"])[:, 1]
        pr_auc = average_precision_score(data["y_test"], preds)
        
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.xgboost.log_model(clf, "model", registered_model_name="fraud-detector")
        
        print(f"Model trained. PR-AUC: {pr_auc:.4f}")
        return clf, pr_auc, run.info.run_id

def evaluate_and_promote(pr_auc: float, min_threshold: float = 0.8):
    """Promotes model if metrics exceed minimum threshold."""
    if pr_auc >= min_threshold:
        print(f"Model PR-AUC {pr_auc:.4f} >= {min_threshold}. Model promoted!")
    else:
        print(f"Model PR-AUC {pr_auc:.4f} < {min_threshold}. Not promoted.")

def retrain_flow():
    """
    Main DAG that extracts data, preps it, trains an XGBoost model,
    and conditionally promotes it based on PR-AUC.
    """
    paths = extract_data_from_lake()
    data = prepare_training_data(paths)
    model, pr_auc, run_id = train_model(data)
    evaluate_and_promote(pr_auc)

if __name__ == "__main__":
    retrain_flow()
