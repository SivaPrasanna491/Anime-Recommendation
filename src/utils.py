from torch._inductor.scheduler import pick_loop_order
import os
import sys
import numpy as np
import pandas
import sklearn
import nltk
import torch
import tensorflow
import pickle

from torch.nn import Embedding
from sklearn.preprocessing import MultiLabelBinarizer
from tensorflow.keras.preprocessing.text import one_hot
from tensorflow.keras.utils import pad_sequences
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from src.exception import CustomException
from src.logger import logging


def generateEmbeddings(train_data):
    try:
        train_corpus = generateCorpus(train_data)
        train_one_hot = generateOneHot(train_corpus)
        train_tokens = generateTokens(train_corpus)
        train_padding = generatePadding(train_tokens, train_one_hot)
        
        train_padding = torch.LongTensor(train_padding)
        
        embedding_layer = Embedding(num_embeddings=500, embedding_dim=100)
    
        
        with torch.no_grad():
            train_embedding = embedding_layer(train_padding)
        return train_embedding.mean(dim=1)
    
    except Exception as e:
        raise CustomException(e, sys)
    
def generateCorpus(df):
    try:
        corpus = []
        lemmatizer = WordNetLemmatizer()
        
        for i in range(df.shape[0]):
            data = str(df['englishTitle'][i]).lower()
            data = data.split(" ")
            data = [word for word in data if word not in stopwords.words("english")]
            data = [lemmatizer.lemmatize(word) for word in data]
            corpus.append(' '.join(data))
        return corpus
    except Exception as e:
        raise CustomException(e, sys)
    
def generateTokens(corpus):
    try:
        word_tokens = []
        for word in corpus:
            word_tokens.append(nltk.word_tokenize(word))
        return word_tokens
    except Exception as e:
        raise CustomException(e, sys)

def generateOneHot(corpus):
    try:
        vocab_size = 500
        return [one_hot(word, vocab_size) for word in corpus]
    except Exception as e:
        raise CustomException(e, sys)

def generatePadding(tokens, one_hot_repr):
    try:
        max_length = 0
        for token in tokens:
            max_length = max(max_length, len(token))
        return pad_sequences(one_hot_repr, maxlen=max_length, padding='pre')
    except Exception as e:
        raise CustomException(e, sys)
    
def save_object(file_path, obj):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(obj, f)
    except Exception as e:
        raise CustomException(e, sys)

def load_object(file_path):
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
        
    except Exception as e:
        raise CustomException(e, sys)

import requests
from bs4 import BeautifulSoup
import time
import re

def get_anime_image_url(anime_title):
    """
    Scrape high-quality anime image from MyAnimeList
    Returns the highest quality image URL available
    """
    try:
        # Format search query
        search_query = anime_title.replace(" ", "%20")
        search_url = f"https://myanimelist.net/anime.php?q={search_query}&cat=anime"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Get search results page
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Search failed: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first anime result - look for the article tag or table row
        # MyAnimeList search results are in a table structure
        first_result = soup.find('a', class_='hoverinfo_trigger')
        
        if not first_result:
            # Alternative: Try finding by article or div structure
            print(f"No results found for: {anime_title}")
            return None
        
        # Get the anime page URL from the first result
        anime_url = first_result.get('href')
        
        if not anime_url:
            print("Could not extract anime URL")
            return None
        
        # Add delay to be respectful to the server
        time.sleep(0.5)
        
        # Visit the actual anime page to get high-quality image
        anime_response = requests.get(anime_url, headers=headers, timeout=10)
        
        if anime_response.status_code != 200:
            print(f"Failed to load anime page: {anime_response.status_code}")
            return None
        
        anime_soup = BeautifulSoup(anime_response.text, 'html.parser')
        
        # Method 1: Look for the main cover image in the leftside column
        img_tag = anime_soup.find('img', {'itemprop': 'image'})
        
        if img_tag:
            # Get data-src first (lazy loaded), then src
            image_url = img_tag.get('data-src') or img_tag.get('src')
            
            if image_url:
                # Replace thumbnail URLs with larger versions
                # MyAnimeList images: /r/96x136/ -> /images/ for full size
                # or /r/XXXxXXX/ patterns
                image_url = re.sub(r'/r/\d+x\d+/', '/', image_url)
                image_url = image_url.replace('.webp', '.jpg')  # Prefer JPG over WebP
                
                return image_url
        
        # Method 2: Try alternative selectors
        img_tag = anime_soup.select_one('div.leftside img[itemprop="image"]')
        if img_tag:
            image_url = img_tag.get('data-src') or img_tag.get('src')
            if image_url:
                image_url = re.sub(r'/r/\d+x\d+/', '/', image_url)
                return image_url
        
        # Method 3: Look for og:image meta tag (usually high quality)
        og_image = anime_soup.find('meta', property='og:image')
        if og_image:
            return og_image.get('content')
        
        print(f"Could not find image for: {anime_title}")
        return None
        
    except requests.exceptions.Timeout:
        print(f"Request timed out for: {anime_title}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for {anime_title}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {anime_title}: {e}")
        return None


def get_anime_image_url_alternative(anime_title):
    """
    Alternative method using AniList GraphQL API
    This provides very high quality images and is more reliable
    """
    try:
        query = '''
        query ($search: String) {
            Media(search: $search, type: ANIME) {
                id
                title {
                    romaji
                    english
                }
                coverImage {
                    extraLarge
                    large
                }
            }
        }
        '''
        
        variables = {
            'search': anime_title
        }
        
        url = 'https://graphql.anilist.co'
        
        response = requests.post(
            url, 
            json={'query': query, 'variables': variables},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and data['data'].get('Media'):
                media = data['data']['Media']
                # Get the highest quality image available
                image_url = media['coverImage'].get('extraLarge') or media['coverImage'].get('large')
                return image_url
        
        return None
        
    except Exception as e:
        print(f"AniList API error for {anime_title}: {e}")
        return None


def get_anime_image_url_hybrid(anime_title):
    """
    Hybrid approach: Try AniList first (better quality), fallback to MAL
    """
    # Try AniList first (usually better quality and more reliable)
    image_url = get_anime_image_url_alternative(anime_title)
    
    if image_url:
        return image_url
    
    # Fallback to MyAnimeList scraping
    print(f"AniList failed, trying MyAnimeList for: {anime_title}")
    return get_anime_image_url(anime_title)
