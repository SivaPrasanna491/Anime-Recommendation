import os
import sys
import numpy as np
import pandas as pd
import sklearn

from sklearn.model_selection import train_test_split
from dataclasses import dataclass
from src.exception import CustomException
from src.logger import logging
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer

@dataclass
class DataIngestionConfig:
    raw_path = os.path.join("artifacts", "raw.csv")

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()
    
    def initialize_data_ingestion(self, file_path):
        try:
            '''
                Steps to do
                1) Load the dataset
                2) divide the dataset into training and test datasets
                3) store the datasets by using in respective paths
            '''
            df = pd.read_csv(file_path, encoding='latin')
            logging.info("Dataset loaded successfully")
            os.makedirs(os.path.dirname(self.ingestion_config.raw_path), exist_ok=True)
            logging.info("Data ingestion initialized successfully")
            logging.info("Datasets loaded and stored successfully")
            
            return(
                self.ingestion_config.raw_path
            )
        except Exception as e:
            raise CustomException(e, sys)

    