import os
import sys
import numpy as np
import pandas as pd
import sklearn
import torch
import tensorflow as tf
import nltk

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer, StandardScaler, FunctionTransformer
from dataclasses import dataclass
from src.exception import CustomException
from src.logger import logging
from src.utils import *

@dataclass
class DataTransformationConfig:
    preprocessor_file_path = os.path.join("artifacts", "preprocessor.pkl")

class DataTransformation:
    def __init__(self):
        self.transformation_config = DataTransformationConfig()
        
    def get_preprocessor_object(self):
        try:
            mean_numerical_cols = ['rating']
            median_numerical_cols = ['episodes']
            one_hot_categorical_cols = ['type']
        
            mean_numerical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy='mean')),
                    ("scaler", StandardScaler())
                ]
            )
            
            median_numerical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy='median')),
                    ("scaler", StandardScaler())
                ]
            )
            
            one_hot_categorical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder())
                ]
            )
            
            preprocessor = ColumnTransformer(
                [
                    ("mean_numerical_pipeline", mean_numerical_pipeline, mean_numerical_cols),
                    ("median_numerical_pipeline", median_numerical_pipeline, median_numerical_cols),
                    ("one_hot_categorical_pipeline", one_hot_categorical_pipeline, one_hot_categorical_cols)
                ]
            )
            return preprocessor
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def initiate_data_transformation(self, train_path, test_path):
        try:
            train_data = pd.read_csv(train_path, encoding='latin')
            test_data = pd.read_csv(test_path, encoding='latin')
            logging.info("Train and test datasets have been loaded successfully")
            
            preprocessor_obj = self.get_preprocessor_object()
            logging.info("Preprocessor object created successfully")
            
            train_data['englishTitle'] = train_data['englishTitle'].fillna(train_data['title_userPreferred'])
            test_data['englishTitle'] = test_data['englishTitle'].fillna(test_data['title_userPreferred'])
            logging.info("All null values filled successfully")
            
            binarizer = MultiLabelBinarizer()
            train_data['genre'] = binarizer.fit_transform(train_data['genre'])
            test_data['genre'] = binarizer.transform(test_data['genre'])
             
            train_embedding, test_embedding = generateEmbeddings(train_data, test_data)
            independent_train_data = train_data.drop(columns=["englishTitle", "theme"], axis=1)
            independent_test_data = test_data.drop(columns=["englishTitle", "theme"], axis=1)
            logging.info("Independent features have been extracted successfully")
            
            independent_train_data = preprocessor_obj.fit_transform(independent_train_data)
            independent_test_data = preprocessor_obj.transform(independent_test_data)
            
            train_arr = np.concatenate((pd.DataFrame(train_embedding.numpy()), independent_train_data), axis=1)
            test_arr = np.concatenate((pd.DataFrame(test_embedding.numpy()), independent_test_data), axis=1)
            logging.info("Feature engineering handled successfully")
            
            save_object(
                file_path = self.transformation_config.preprocessor_file_path,
                obj = preprocessor_obj
            ) 
            logging.info("Preprocessor object saved successfully")
            return(
                train_arr,
                test_arr,
                self.transformation_config.preprocessor_file_path
            )
        except Exception as e:
            raise CustomException(e, sys)