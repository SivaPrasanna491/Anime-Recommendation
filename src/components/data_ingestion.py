import os
import sys
import numpy as np
import pandas as pd
import sklearn

from sklearn.model_selection import train_test_split
from dataclasses import dataclass
from src.exception import CustomException
from src.logger import logging

@dataclass
class DataIngestionConfig:
    train_path = os.path.join("artifacts", "train.csv")
    test_path = os.path.join("artifacts", "test.csv")
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
            dataset = pd.read_csv(file_path, encoding='latin')
            logging.info("Dataset loaded successfully")
            os.makedirs(os.path.dirname(self.ingestion_config.train_path), exist_ok=True)
            
            logging.info("Data ingestion initialized successfully")
            train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=0)
            
            train_data.to_csv(self.ingestion_config.train_path, index=False, header=True)
            test_data.to_csv(self.ingestion_config.test_path, index=False, header=True)
            dataset.to_csv(self.ingestion_config.raw_path, index=False, header=True)
            logging.info("Datasets loaded and stored successfully")
            
            return(
                self.ingestion_config.train_path,
                self.ingestion_config.test_path
            )
        except Exception as e:
            raise CustomException(e, sys)


if __name__=="__main__":
    obj = DataIngestion()
    train_path, test_path = obj.initialize_data_ingestion(r'C:\Users\shiva\OneDrive\Documents\Anime Recommendation Modular\notebooks\anilist_anime_data_complete.csv')
    
    