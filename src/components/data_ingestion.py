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
            
            df = pd.DataFrame({
                "id": df['id'],
                "englishTitle": df['title_english'],
                "title_userPreferred": df['title_userPreferred'],
                "type": df['format'],
                "genre": df['genres'],
                "theme": df['tags'],
                "type": df['format'],
                "episodes": df['episodes'],
                "rating": df['averageScore'] 
            })
            logging.info("Data ingestion initialized successfully")
            df.to_csv(self.ingestion_config.raw_path, index=False, header=True)
            logging.info("Datasets loaded and stored successfully")
            
            return(
                self.ingestion_config.raw_path
            )
        except Exception as e:
            raise CustomException(e, sys)


if __name__=="__main__":
    obj = DataIngestion()
    train_path = obj.initialize_data_ingestion(r'C:\Users\shiva\OneDrive\Documents\Anime Recommendation Modular\notebooks\anilist_anime_data_complete.csv')
    
    transformation_obj = DataTransformation()
    train_arr, file_path = transformation_obj.initiate_data_transformation(train_path)
    print(f"The shape is: ",train_arr.shape)
    
    model_obj = ModelTrainer()
    print(model_obj.initiate_model_trainer(train_arr))
    
    
    