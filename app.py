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
    try:
        client = getConnection()
        if session.get("email") is None:
            return render_template("signup.html")
        response = (
            client.table("users")
            .select("user_id")
            .eq("email", session.get("email"))
            .execute()
        )
        if len(response.data) == 0:
            return render_template("signup.html")
        user_id = response.data[0]['user_id']
        response = (
                client.table("useranimeinteractions")
                .select("*", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
        interaction_count = response.count
        response = (
            client.table("useranimeinteractions")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .eq("interaction_type", "view")
            .execute()
        )
        
        seenCount = response.count
        if interaction_count == 0 or seenCount == 0:
            return render_template('home.html', animes=[])
    
    
        response = (
            client.table("useranimeinteractions")
            .select("anime_id")
            .eq("user_id", user_id)
            .eq("interaction_type", "view")
            .execute()
        )
        
        # Collect all genres from viewed animes
        all_genres = set()
        viewed_anime_ids = []
        
        for interaction in response.data:
            anime_id = interaction['anime_id']
            viewed_anime_ids.append(anime_id)
            
            # Get genre for this anime
            anime_response = (
                client.table("animes")
                .select("anime_genre")
                .eq("anime_id", anime_id)
                .execute()
            )
            
            if len(anime_response.data) > 0:
                anime_genre = anime_response.data[0]['anime_genre']
                if anime_genre is not None:
                    # Split and add all genres
                    genres = [g.strip() for g in anime_genre.split(',')]
                    all_genres.update(genres)
        
        # Now find animes with matching genres (excluding already viewed)
        animes = []
        for genre in list(all_genres)[:3]:  # Top 3 genres
            anime_response = (
                client.table("animes")
                .select("anime_name, anime_id")
                .ilike("anime_genre", f"%{genre}%")
                .not_.in_("anime_id", viewed_anime_ids)  # ✅ Exclude viewed animes
                .limit(10)
                .execute()
            )
            
            for anime_data in anime_response.data:
                anime_name = anime_data['anime_name']
                
                # Avoid duplicates
                if not any(a['anime_name'] == anime_name for a in animes):
                    image_url = get_anime_image_url_hybrid(anime_name)
                    
                    if not image_url:
                        image_url = f'https://via.placeholder.com/300x450/1a1033/a78bfa?text={anime_name}'
                    
                    animes.append({
                        'anime_name': anime_name,
                        'image_url': image_url
                    })
                    
                    # Limit total recommendations
                    if len(animes) >= 20:
                        break
            
            if len(animes) >= 20:
                break
            # Pass interaction_count to template
        return render_template('home.html', animes=animes)
    except Exception as e:
        raise CustomException(e, sys)

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
            
            client = getConnection()
            
            # Check if user exists
            result = (
                client.table("users")
                .select("user_id, password")
                .eq("email", email)
                .execute()
            )
            if len(result.data) == 0:
                return render_template('signup.html')
            
            user_id = result.data[0]['user_id']
            db_password = result.data[0]['password']
            
            # User exists - verify password
           
            if db_password != password:
                return render_template('login.html')
            
            # Store email in session
            session['email'] = email
            
            # Password is correct - check interaction count
            response = (
                client.table("useranimeinteractions")
                .select("*", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            interaction_count = response.count
            response = (
                client.table("useranimeinteractions")
                .select("*", count="exact")
                .eq("user_id", user_id)
                .eq("interaction_type", "view")
                .execute()
            )
        
            seenCount = response.count
            if interaction_count == 0 or seenCount == 0:
                return render_template('home.html', animes=[])
            
            response = (
                client.table("useranimeinteractions")
                .select("anime_id")
                .eq("user_id", user_id)
                .eq("interaction_type", "view")
                .execute()
            )
            
            # Collect all genres from viewed animes
            all_genres = set()
            viewed_anime_ids = []
            
            for interaction in response.data:
                anime_id = interaction['anime_id']
                viewed_anime_ids.append(anime_id)
                
                # Get genre for this anime
                anime_response = (
                    client.table("animes")
                    .select("anime_genre")
                    .eq("anime_id", anime_id)
                    .execute()
                )
                
                if len(anime_response.data) > 0:
                    anime_genre = anime_response.data[0]['anime_genre']
                    if anime_genre is not None:
                        # Split and add all genres
                        genres = [g.strip() for g in anime_genre.split(',')]
                        all_genres.update(genres)
            
            # Now find animes with matching genres (excluding already viewed)
            animes = []
            for genre in list(all_genres)[:3]:  # Top 3 genres
                anime_response = (
                    client.table("animes")
                    .select("anime_name, anime_id")
                    .ilike("anime_genre", f"%{genre}%")
                    .not_.in_("anime_id", viewed_anime_ids)  # ✅ Exclude viewed animes
                    .limit(10)
                    .execute()
                )
                
                for anime_data in anime_response.data:
                    anime_name = anime_data['anime_name']
                    
                    # Avoid duplicates
                    if not any(a['anime_name'] == anime_name for a in animes):
                        image_url = get_anime_image_url_hybrid(anime_name)
                        
                        if not image_url:
                            image_url = f'https://via.placeholder.com/300x450/1a1033/a78bfa?text={anime_name}'
                        
                        animes.append({
                            'anime_name': anime_name,
                            'image_url': image_url
                        })
                        
                        # Limit total recommendations
                        if len(animes) >= 20:
                            break
                
                if len(animes) >= 20:
                    break
            return render_template('home.html', animes=animes)
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
            client = getConnection()
            result = (
                client.table("users")
                .select("user_id")
                .eq("email", email)
                .execute()
            )
            if len(result.data) == 0:
                response = (
                    client.table("users")
                    .insert({"name": name, "email":email, "password": password})
                    .execute()
                )
                session['email'] = email
                return render_template('index.html')
            return render_template('login.html')
    except Exception as e:
        raise CustomException(e, sys)

@app.route("/view", methods=['GET'])
def view():
    try:
        anime_title = request.args.get('anime_title')
        anime_id = request.args.get('anime_id')
        anime_genre = request.args.get("anime_genre")
        client = getConnection()
        
        # Check if anime exists in database
        result = (
            client.table("animes")
            .select("anime_id")
            .eq("anime_name", anime_title)
            .execute()
        )
        if len(result.data) == 0:
            (
                client.table("animes")
                .insert({"anime_id": anime_id, "anime_name": anime_title, "anime_genre": anime_genre})
                .execute()
            )
        
        # Get user_id from session email
        result = (
            client.table("users")
            .select("user_id")
            .eq("email", session.get("email"))
            .execute()
        )
        user_id = result.data[0]['user_id']
        interaction = 'view'
        (
            client.table("useranimeinteractions")
            .insert({"user_id": user_id, "anime_id": anime_id, "interaction_type": interaction, "timestamp": datetime.now().isoformat()})
            .execute()
        )
        return {"status": "success", "message": "View tracked"}
    except Exception as e:
        raise CustomException(e, sys)

@app.route("/rating", methods=['GET'])
def rating():
    try:
        anime_title = request.args.get('anime_title')
        anime_id = request.args.get('anime_id')
        anime_genre = request.args.get("anime_genre")
        rating_value = request.args.get('rating', type=int)
        
        client = getConnection()
        
        # Check if anime exists
        response = (
            client.table("animes")
            .select("anime_id")
            .eq("anime_name", anime_title)
            .execute()
        )
        if len(response.data) == 0:
            (
                client.table("animes")
                .insert({"anime_id": anime_id, "anime_name": anime_title, "anime_genre": anime_genre, "anime_rating": rating_value})
                .execute()
            )
        response = (
            client.table("users")
            .select("user_id")
            .eq("email", session.get("email"))
            .execute()
        )
        user_id = response.data[0]['user_id']
        interaction = 'rated'
        time = datetime.now().isoformat()
        (
            client.table("useranimeinteractions")
            .insert({"user_id": user_id, "anime_id": anime_id, "interaction_type": interaction, "timestamp": time})
            .execute()
        )
        return {"status": "success", "message": "Rating tracked"}
    except Exception as e:
        raise CustomException(e, sys)

@app.route("/seenAnimes", methods=['GET'])
def seenAnimes():
    try:
        client = getConnection()
        response = (
            client.table("users")
            .select("user_id")
            .eq("email", session.get("email"))
            .execute()
        )
        if len(response.data) == 0:
            return render_template("signup.html")
        user_id = response.data[0]['user_id']
        type = 'view'
        response = (
            client.table("useranimeinteractions")
            .select("anime_id")
            .eq("user_id", user_id)
            .eq("interaction_type", type)
            .execute()
        )
        if len(response.data) == 0:
            return render_template("seenAnimes.html", animes=[])
        
        animes = []
        for interaction in response.data:
            anime_id = interaction['anime_id']
            anime_response = (
                client.table("animes")
                .select("anime_name")
                .eq("anime_id", anime_id)
                .execute()
            )
            
            if len(anime_response.data) > 0:
                anime_name = anime_response.data[0]['anime_name']
                
                # Scrape image URL using hybrid method (AniList + MAL fallback)
                image_url = get_anime_image_url_hybrid(anime_name)
                
                # Use placeholder if scraping fails
                if not image_url:
                    image_url = f'https://via.placeholder.com/300x450/1a1033/a78bfa?text={anime_name}'
                
                animes.append({
                    'anime_name': anime_name,
                    'image_url': image_url
                })
        
        return render_template('seenAnimes.html', animes=animes)
    except Exception as e:
        raise CustomException(e, sys)


if __name__=="__main__":
    app.run(debug=True)