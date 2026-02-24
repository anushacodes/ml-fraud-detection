# loads raw data, cleans it, and saves it
import os
import yaml
import pandas as pd
import datetime as dt

from logger import get_logger
logger = get_logger("DataPreparer")

class prepareData:

    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)

    def load_config(self, config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)["data"]

    def load_data(self):
        train = pd.read_csv(self.config["train_path"])
        test = pd.read_csv(self.config["test_path"])

        return train, test

    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df['age'] = dt.date.today().year - pd.to_datetime(df['dob']).dt.year
        df['hour'] = pd.to_datetime(df['trans_date_trans_time']).dt.hour
        df['day'] = pd.to_datetime(df['trans_date_trans_time']).dt.dayofweek
        df['month'] = pd.to_datetime(df['trans_date_trans_time']).dt.month

        return df


    def select_columns(self, train, test):
        cols = ['category', 'amt', 'zip', 'lat', 'long', 'city_pop', 'merch_lat', 'merch_long',
                'age', 'hour', 'day', 'month', 'is_fraud']

        train = train[[c for c in cols if c in train.columns]]
        test = test[[c for c in cols if c in test.columns]]

        return train, test


    def encode_categoricals(self, train, test):
        train = pd.get_dummies(train, drop_first=True)
        test = pd.get_dummies(test, drop_first=True)

        train, test = train.align(test, join='left', axis=1, fill_value=0)

        return train, test


    def split_features_labels(self, train, test):

        y_train = train['is_fraud']
        X_train = train.drop('is_fraud', axis='columns')

        y_test = test['is_fraud']
        X_test = test.drop('is_fraud', axis='columns')

        return X_train, X_test, y_train, y_test


    # orchestrates the full cleaning pipeline in order:
    # time features → column selection → encoding → split
    def clean_prepare_data(self, train, test):
        try:
            train = self.create_time_features(train)
            test = self.create_time_features(test)

            train, test = self.select_columns(train, test)
            train, test = self.encode_categoricals(train, test)
            X_train, X_test, y_train, y_test = self.split_features_labels(train, test)

        except Exception as e:
            logger.error(f"error during data cleaning: {e}")
            raise

        return X_train, X_test, y_train, y_test


    def save_data(self, X_train, X_test, y_train, y_test):
        for path_key in ["X_train_path", "X_test_path", "y_train_path", "y_test_path"]:
            os.makedirs(os.path.dirname(self.config[path_key]), exist_ok=True)

        X_train.to_csv(self.config["X_train_path"], index=False)
        X_test.to_csv(self.config["X_test_path"], index=False)
        y_train.to_csv(self.config["y_train_path"], index=False)
        y_test.to_csv(self.config["y_test_path"], index=False)


    def run(self):
        logger.info("starting data preparation pipeline")

        logger.info("loading raw data")
        train, test = self.load_data()

        logger.info("cleaning and extracting features")
        X_train, X_test, y_train, y_test = self.clean_prepare_data(train, test)

        logger.info("saving cleaned data to csv")
        self.save_data(X_train, X_test, y_train, y_test)

        logger.info("data preparation successfully completed.")


if __name__ == "__main__":
    preparer = prepareData()
    preparer.run()