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


def generateEmbeddings(train_data, test_data):
    try:
        train_corpus = generateCorpus(train_data)
        test_corpus = generateCorpus(test_data)
        train_one_hot = generateOneHot(train_corpus)
        test_one_hot = generateOneHot(test_corpus)
        train_tokens = generateTokens(train_corpus)
        test_tokens = generateTokens(test_corpus)
        train_padding = generatePadding(train_tokens, train_one_hot)
        test_padding = generatePadding(test_tokens, test_one_hot)
        
        train_padding = torch.LongTensor(train_padding)
        test_padding = torch.LongTensor(test_padding)
        
        embedding_layer = Embedding(num_embeddings=500, embedding_dim=100)
    
        
        with torch.no_grad():
            train_embedding = embedding_layer(train_padding)
            test_embedding = embedding_layer(test_padding)
        return train_embedding.mean(dim=1), test_embedding.mean(dim=1)
       
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
    
def multilabel_encode(X):
    mlb = MultiLabelBinarizer()
    return mlb.fit_transform(X)