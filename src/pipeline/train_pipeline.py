from src.components.data_ingestion import DataIngestion, DataIngestionConfig
from src.components.data_transformation import DataTransformation, DataTransformationConfig
from src.components.model_trainer import ModelTrainer, ModelTrainerConfig


if __name__=="__main__":
    ingestionObj = DataIngestion()
    train_path = ingestionObj.initialize_data_ingestion(f"https://drive.google.com/uc?id=1uIKjoBdBOaSaASPXAmGA0qT7EUPzOTLb&export=download&confirm=t")
    
    transformationObj = DataTransformation()
    train_arr, file_path = transformationObj.initiate_data_transformation(train_path=train_path)
    
    trainerObj = ModelTrainer()
    # model = trainerObj.initiate_model_trainer(train_arr=train_arr)
    print(trainerObj.initiate_model_trainer(train_arr=train_arr))
    
    