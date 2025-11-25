import os
import sys
import numpy as np
import pandas as pd
import sklearn

from dataclasses import dataclass
from sklearn.neighbors import NearestNeighbors
from src.exception import CustomException
from src.logger import logging
from src.utils import *

@dataclass
class ModelTrainerConfig:
    model_trainer_path = os.path.join("artifacts", "model_trainer.pkl")

class ModelTrainer:
    def __init__(self):
        self.trainer_config = ModelTrainerConfig()
    
    def initiate_model_trainer(self, train_arr):
        try:
            logging.info("Model training initiated successfully")
            model = NearestNeighbors(n_neighbors=10, metric='cosine')
            logging.info("Model loaded successfully")
        
            model.fit(train_arr)
            logging.info("Model trained successfully")
            
            save_object(
                file_path=self.trainer_config.model_trainer_path,
                obj=model
            )
            return model
        except Exception as e:
            raise CustomException(e, sys)