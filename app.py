import sys

from src.exception import CustomException
from src.logger import logging
from flask import Flask, render_template, redirect, url_for, request
from src.pipeline.predict_pipeline import CustomData, PredictPipeline
from src.utils import *

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return render_template('index.html')

@app.route("/findanime", methods=['GET', 'POST'])
def findAnime():
    try:
        if(request.method == 'GET'):
            return render_template('form.html')
        else:
            englishTitle = request.form.get("englishTitle", "")
            genre = request.form.getlist("genre")
            episodes = request.form.get("episodes", "")
            rating = request.form.get("rating", "")
            type = request.form.get("type", "")
            # logging.info("All features captured successfully")
            
            # Always include all features in the correct order
            features = ['englishTitle', 'genre', 'episodes', 'rating', 'type']
            values = [
                englishTitle if englishTitle else None,
                genre if genre else None,
                episodes if episodes else 0,
                rating if rating else 0,
                type if type else 0
            ]
            
            obj = CustomData(features, values)
            df = obj.generate_data_frame()
            
            print("The data frame is: ",df)
            predict_obj = PredictPipeline()
            animes = predict_obj.suggestAnimes(df)
            
            return render_template('anime.html', animes=animes) 
    except Exception as e:
        raise CustomException(e, sys)

if __name__=="__main__":
    app.run(debug=True)