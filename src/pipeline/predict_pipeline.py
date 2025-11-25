import os
import sys
import numpy as np
import pandas as pd
import sklearn

from src.exception import CustomException
from src.logger import logging
from src.utils import *

class PredictPipeline:
    def __init__(self):
        pass
        
    def suggestAnimes(self, features):
        try:
            dataset_path = os.path.join('artifacts', 'raw.csv')
            preprocessor_file_path = os.path.join('artifacts', 'preprocessor.pkl')
            binarizer_file_path = os.path.join('artifacts', 'binarizer.pkl')
            model_file_path = os.path.join('artifacts', 'model_trainer.pkl')
            
            dataset = pd.read_csv(dataset_path, encoding='latin')
            preprocessor = load_object(file_path=preprocessor_file_path)
            binarizer = load_object(file_path=binarizer_file_path)
            model = load_object(file_path=model_file_path)
            
            # Handle englishTitle embedding
            english_title_value = features['englishTitle'].iloc[0]
            if english_title_value is not None and english_title_value != '':
                # Generate embeddings for the title
                title_df = pd.DataFrame({'englishTitle': [english_title_value]})
                english_embedding = generateEmbeddings(title_df).numpy()
            else:
                # Use zeros if no title provided (100 dimensions)
                english_embedding = np.zeros((1, 100))
            
            # Handle genre transformation
            genre_value = features['genre'].iloc[0]
            if genre_value is not None and genre_value != [None]:
                # MultiLabelBinarizer expects a list of samples, so wrap in another list
                # genre_value is ['Action', 'Comedy'], we need [['Action', 'Comedy']]
                genre_encoded = binarizer.transform([genre_value])
            else:
                # Use zeros if no genre provided
                genre_encoded = np.zeros((1, len(binarizer.classes_)))
            
            # Drop englishTitle and genre from features before preprocessing
            # The preprocessor only handles: rating, episodes, type
            features_for_preprocessing = features.drop(columns=['englishTitle', 'genre'])
            
            # Transform the remaining features (rating, episodes, type)
            # The SimpleImputer in the pipeline will handle None values
            features_transformed = preprocessor.transform(features_for_preprocessing)
            
            print(f"English embedding shape: {english_embedding.shape}")
            print(f"Genre encoded shape: {genre_encoded.shape}")
            print(f"Features transformed shape: {features_transformed.shape}")
            
            # Concatenate all features in the correct order: [embedding, genre, other_features]
            # This should match the order used during training
            final_features = np.concatenate([english_embedding, genre_encoded, features_transformed], axis=1)
            
            print(f"Final features shape: {final_features.shape}")
            
            # Get recommendations
            # Request more neighbors to account for potential filtering
            n_neighbors = min(20, len(dataset))  # Don't request more than dataset size
            distances, indices = model.kneighbors(final_features, n_neighbors=n_neighbors)
            
            # Convert to list of dictionaries and filter out invalid entries
            recommended_animes = []
            for indice in indices[0]:
                anime = dataset.iloc[indice]
                
                # Skip if englishTitle is missing or NaN
                if pd.isna(anime.get('englishTitle')) or anime.get('englishTitle') == '':
                    continue
                
                # Get the anime title for image scraping
                anime_title = anime.get('englishTitle', 'Unknown Title')
                
                # Fetch the image URL using web scraping
                print(f"Fetching image for: {anime_title}")
                image_url = get_anime_image_url_alternative(anime_title)
                
                # Use a placeholder if image not found
                if not image_url:
                    image_url = "https://via.placeholder.com/300x450/1a1033/a78bfa?text=No+Image"
                
                # Convert Series to dictionary and handle NaN values
                anime_dict = {
                    'id': int(anime.get('id')) if not pd.isna(anime.get('id')) else 'N/A',
                    'englishTitle': anime_title,
                    'type': anime.get('type', 'Unknown') if not pd.isna(anime.get('type')) else 'Unknown',
                    'rating': anime.get('rating', 'N/A') if not pd.isna(anime.get('rating')) else 'N/A',
                    'episodes': anime.get('episodes', 'N/A') if not pd.isna(anime.get('episodes')) else 'N/A',
                    'genre': anime.get('genre', '[]') if not pd.isna(anime.get('genre')) else '[]',
                    'imageUrl': image_url
                }
                
                recommended_animes.append(anime_dict)
                
                # Stop once we have 10 valid recommendations
                if len(recommended_animes) >= 10:
                    break
            
            print(f"Returning {len(recommended_animes)} recommendations")
            return recommended_animes
        except Exception as e:
            raise CustomException(e, sys)
        

class CustomData:
    def __init__(self, features, values):
        self.features = features
        self.values = values
    
    def generate_data_frame(self):
        try:
            dict = {
                'englishTitle': [None],
                'genre': [None],
                'episodes': [0],
                'rating': [0],
                'type': [0]
            }
            for k, v in zip(self.features, self.values):
                if k in ['englishTitle', 'genre'] and v != '':
                    dict[k] = [v]
                if k in ['englishTitle', 'genre'] and v == '':
                    dict[k] = [None]
                if v != '':
                    dict[k] = [v]
            return pd.DataFrame(dict)
        except Exception as e:
            raise CustomException(e, sys)