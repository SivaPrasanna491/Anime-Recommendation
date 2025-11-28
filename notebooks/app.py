import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from src.exception import CustomException
from src.logger import logging
from notebooks.utils.SQL_Connection import getConnection, getUser
from src.pipeline.predict_pipeline import CustomData, PredictPipeline
from src.utils import *

app = Flask(__name__)
# Fixed secret key - DO NOT CHANGE THIS or sessions will be invalidated
app.secret_key = 'anime-recommendation-secret-key-keep-this-private-2024'

@app.route("/", methods=['GET'])
def home():
    return render_template('login.html')

@app.route("/findanime", methods=['GET', 'POST'])
def findAnime():
    try:
        if(request.method == 'GET'):
           email = session.get("email")
           if email is None:
               return render_template("signup.html")
           return render_template("form.html")
        else:
            englishTitle = request.form.get("englishTitle", "")
            genre = request.form.getlist("genre")
            episodes = request.form.get("episodes", "")
            rating = request.form.get("rating", "")
            type = request.form.get("type", "")
            
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

@app.route("/login", methods=['GET', 'POST'])
def login():
    try:
        if(request.method == 'GET'):
            return render_template('login.html')
        else:
            email = request.form.get('email')
            password = request.form.get("password")
            
            conn, cursor = getConnection()
            
            # Check if user exists
            query = "SELECT user_id, password FROM User WHERE email=%s"
            cursor.execute(query, (email, ))
            result = cursor.fetchone()
            
            # If user doesn't exist, show error or redirect to signup
            if result is None:
                cursor.close()
                conn.close()
                return render_template('signup.html')
            
            # User exists - verify password
            user_id, db_password = result[0], result[1]
            
            if db_password != password:
                # Password doesn't match
                cursor.close()
                conn.close()
                return render_template('login.html')
            
            # Store email in session
            session['email'] = email
            
            # Password is correct - check interaction count
            query = "SELECT COUNT(*) FROM UserAnimeInteraction WHERE user_id=%s"
            cursor.execute(query, (user_id, ))
            interaction_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Pass interaction_count to template
            return render_template('home.html', interaction_count=interaction_count)
            
    except Exception as e:
        raise CustomException(e, sys)
    
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    try:
        if(request.method == 'GET'):
            return render_template('signup.html')
        else:
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            conn, cursor = getConnection()
            query = "SELECT user_id, password FROM User WHERE email=%s"
            cursor.execute(query, (email, ))
            result = cursor.fetchone()
            if result is None:
                query = """
                    insert into User(name, email, password) values(%s, %s, %s)
                """
                d = {
                    "name": name,
                    "email": email,
                    "password": password
                }
                cursor.execute(query, (
                    d['name'], d['email'], d['password']
                ))
                session['email'] = email
                conn.commit()
                cursor.close()
                conn.close()  
                return render_template('index.html')
            return render_template('login.html')
    except Exception as e:
        raise CustomException(e, sys)

@app.route("/view", methods=['GET'])
def view():
    try:
        anime_title = request.args.get('anime_title')
        anime_id = request.args.get('anime_id')
        conn, cursor = getConnection()
        
        # Check if anime exists in database
        query = "SELECT anime_id FROM Anime WHERE anime_id=%s"
        cursor.execute(query, (anime_id, ))
        result = cursor.fetchone()
        
        if result is None:
            # Insert anime if it doesn't exist
            query = "INSERT INTO Anime(anime_id, anime_name) VALUES(%s, %s)"
            cursor.execute(query, (anime_id, anime_title,))
            conn.commit()
        
        # Get user_id from session email
        user_id = getUser(conn=conn, cursor=cursor, email=session.get("email"))
        
        # Insert interaction
        interaction = 'view'
        time = datetime.now()
        query = """
            INSERT INTO UserAnimeInteraction(user_id, anime_id, interaction_type, timestamp) 
            VALUES(%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, anime_id, interaction, time))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        raise CustomException(e, sys)

@app.route("/rating", methods=['GET'])
def rating():
    try:
        anime_title = request.args.get('anime_title')
        anime_id = request.args.get('anime_id')
        rating_value = request.args.get('rating', type=int)
        
        conn, cursor = getConnection()
        
        # Check if anime exists
        query = "SELECT anime_id FROM Anime WHERE anime_id=%s"
        cursor.execute(query, (anime_id, ))
        result = cursor.fetchone()
        
        if result is None:
            # Insert anime if it doesn't exist
            query = "INSERT INTO Anime(anime_id, anime_name) VALUES(%s, %s)"
            cursor.execute(query, (anime_id, anime_title,))
            conn.commit()
        
        # Get user_id from session email
        user_id = getUser(conn=conn, cursor=cursor, email=session.get("email"))
        
        # Insert rating interaction
        interaction = 'rated'
        time = datetime.now()
        query = """
            INSERT INTO UserAnimeInteraction(user_id, anime_id, interaction_type, rating, timestamp) 
            VALUES(%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, anime_id, interaction, rating_value, time))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'success': True, 'rating': rating_value}
    except Exception as e:
        raise CustomException(e, sys)

if __name__=="__main__":
    app.run(debug=True)