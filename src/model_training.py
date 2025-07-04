import os
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from src.custom_exception import CustomException
from src.logger import get_logger
from config.model_params import *
from config.path_config import *
from utils.common_functions import read_yaml, load_data
from scipy.stats import randint

import mlflow
import mlflow.sklearn

logger = get_logger(__name__)

class ModelTraining:
    def __init__(self, train_path, test_path, model_output_path):
        self.train_path = train_path
        self.test_path = test_path
        self.model_output_path = model_output_path

        self.params_dist = LIGHTGM_PARAMS
        self.random_search_params = RANDOM_SEARCH_PARAMS

    def load_and_split_data(self):
        try:
            logger.info(f"Loading Data from {self.train_path}")
            train_df = load_data(self.train_path)

            logger.info(f"Loading Data from {self.test_path}")
            test_df = load_data(self.test_path)

            x_train = train_df.drop(columns=['booking_status'])
            y_train = train_df['booking_status']

            x_test = test_df.drop(columns=['booking_status'])
            y_test = test_df['booking_status']

            logger.info("Data Splitted Successfully for Model Traing")

            return x_train, y_train, x_test, y_test
        
        except Exception as e:
            logger.error(f"Error while Loading data {e}")
            raise CustomException("Failed to load data", e)
        
    def train_lgbm(self, x_train, y_train):
        try:
            logger.info("Initializing our Model")

            lgbm_model = lgb.LGBMClassifier(random_state=self.random_search_params["random_state"])

            logger.info("Starting our Model Training")

            random_search = RandomizedSearchCV(
                estimator=lgbm_model,
                param_distributions=self.params_dist,
                n_iter=self.random_search_params["n_iter"],
                cv=self.random_search_params["cv"],
                n_jobs=self.random_search_params["n_jobs"],
                verbose=self.random_search_params["verbose"],
                random_state=self.random_search_params["random_state"],
                scoring=self.random_search_params["scoring"],
            )

            logger.info("Starting our Hyperparameter Tuning")

            random_search.fit(x_train, y_train)

            logger.info("Hyperparameter Tuning Completed")

            best_params = random_search.best_params_
            best_lgbm_model = random_search.best_estimator_

            logger.info(f"Best Parameter are : {best_params}")

            return best_lgbm_model
        
        except Exception as e:
            logger.error(f"Error while Training Model {e}")
            raise CustomException("Failed to Train Model", e)
        
    def evaluate_model(self, model, x_test, y_test):
        try:
            logger.info("Evaluating our Model")

            y_pred = model.predict(x_test)

            accuracy = accuracy_score(y_test,y_pred)
            precision = precision_score(y_test,y_pred)
            recall = recall_score(y_test,y_pred)
            f1 = f1_score(y_test,y_pred)

            logger.info(f"Accuracy Score : {accuracy}")
            logger.info(f"Precision Score : {precision}")
            logger.info(f"Recall Score : {recall}")
            logger.info(f"F1 Score : {f1}")

            return {
                "Accuracy" : accuracy,
                "Precision" : precision,
                "Recall" : recall,
                "F1" : f1
            }
        
        except Exception as e:
            logger.error(f"Error while Evaluating Model {e}")
            raise CustomException("Failed to Evaluate Model", e)
        
    def save_model(self, model):
        try:
            os.makedirs(os.path.dirname(self.model_output_path), exist_ok=True)

            logger.info("Saving Model")

            joblib.dump(model, self.model_output_path)
            logger.info(f"Model saved to {self.model_output_path}")

        except Exception as e:
            logger.error(f"Error while Saving data {e}")
            raise CustomException("Failed to Save data", e)
        
    def run(self):
        try:
            with mlflow.start_run():
                logger.info("Staring our model Training Pipeline")

                logger.info("Starting our MLFLOW Experimentation")

                logger.info("Logging the Training and Testing Dataset to MLFLOW")

                mlflow.log_artifact(self.train_path, artifact_path="datasets")
                mlflow.log_artifact(self.test_path, artifact_path="datasets")

                x_train, y_train, x_test, y_test = self.load_and_split_data()
                best_lgbm_model = self.train_lgbm(x_train, y_train)
                metrics = self.evaluate_model(best_lgbm_model, x_test, y_test)
                self.save_model(best_lgbm_model)

                logger.info("Logging the model into MLFLOW")
                mlflow.log_artifact(self.model_output_path)

                logger.info("Logging the Params and Metrics into MLFLOW")
                mlflow.log_params(best_lgbm_model.get_params())
                mlflow.log_metrics(metrics)

                logger.info("Model Training Successfully Completed")

        except Exception as e:
            logger.error(f"Error while Model Training Pipeline {e}")
            raise CustomException("Failed during Model Training Pipeline", e)
        
if __name__ == "__main__":
    trainner = ModelTraining(PROCESSED_TRAIN_DATA_PATH, PROCESSED_TEST_DATA_PATH, MODEL_OUTPUT_PATH)
    trainner.run()