from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.responses import JSONResponse
import requests
import logging
from rapidfuzz import fuzz, process
import ftfy  # fixes Hindi and other Unicode issues
import pickle
from typing import List, Optional
from pydantic import BaseModel
import ast

app = FastAPI()

# CORS: allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load assets
movies_df = pd.read_feather("final_movies_cleaned.feather")
movie_embeddings = np.load("movie_embeddings_float16.npy")

# Load LightFM model
try:
    with open("lightfm_model.pkl", "rb") as f:
        lightfm_model = pickle.load(f)
    print("LightFM model loaded successfully")
except FileNotFoundError:
    lightfm_model = None
    print("LightFM model not found. Personalized recommendations will use fallback method.")

# TMDB configuration
TMDB_API_KEY = "3d3b5cbc09e66409a5686373a4c110e7"
TMDB_API_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Pydantic models for request bodies
class UserProfile(BaseModel):
    user_id: Optional[str] = None
    age: Optional[int] = None
    safe_mode: bool = True
    language: List[str] = ["en"]
    mood: str = "happy"
    region: str = "US"
    watchlist: List[int] = []
    history: List[int] = []
    liked_movies: List[int] = []
    disliked_movies: List[int] = []

# Helper: Fetch movie details from TMDB using ID
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_tmdb_data_cached(movie_id: int):
    try:
        url = f"{TMDB_API_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"TMDB fetch failed: {e}")
    return {}

def apply_filters(df, genres=None, languages=None, safe_mode=True, region=None):
    """Apply filters to the movie dataframe"""
    filtered_df = df.copy()
    
    # Safe mode filter (adult content)
    if safe_mode:
        filtered_df = filtered_df[filtered_df['adult'] == 0]
    
    # Genre filter
    if genres:
        genre_mask = filtered_df['genres'].apply(
            lambda x: any(genre.lower() in str(x).lower() for genre in genres) if pd.notna(x) else False
        )
        filtered_df = filtered_df[genre_mask]
    
    # Language filter
    if languages:
        lang_mask = filtered_df['all_languages'].apply(
            lambda x: any(lang in str(x) for lang in languages) if pd.notna(x) else False
        )
        filtered_df = filtered_df[lang_mask]
    
    return filtered_df

def enrich_movie_data(movie_row):
    """Enrich movie data with TMDB information"""
    movie = {}
    
    # Convert numpy types to Python types
    for k, v in movie_row.items():
        if isinstance(v, (np.integer, np.floating)):
            movie[k] = v.item()
        elif isinstance(v, np.ndarray):
            movie[k] = v.tolist()
        else:
            movie[k] = v
    
    # Get TMDB data
    tmdb_data = get_tmdb_data_cached(int(movie_row["id"]))
    
    # Add poster path
    movie["poster_path"] = (
        tmdb_data.get('poster_path')
        if tmdb_data.get("poster_path") else None
    )
    
    # Add vote average
    movie["vote_average"] = tmdb_data.get("vote_average", movie.get("vote_average_5", 0) * 2)
    
    # Process genres
    if tmdb_data.get("genres"):
        movie["genres"] = tmdb_data.get("genres")
        movie["genre_ids"] = [g["id"] for g in tmdb_data.get("genres", [])]
    else:
        # Fallback to local genres
        local_genres = movie.get("genres", [])
        if isinstance(local_genres, str):
            try:
                local_genres = ast.literal_eval(local_genres)
            except:
                local_genres = []
        movie["genres"] = [{"name": g} for g in local_genres]
        movie["genre_ids"] = []
    
    # Add release date
    movie["release_date"] = movie.get("release_date", "")
    
    return movie

def get_mood_based_genres(mood):
    """Map moods to preferred genres"""
    mood_genre_map = {
        "happy": ["Comedy", "Animation", "Family", "Adventure"],
        "excited": ["Action", "Adventure", "Thriller", "Science Fiction"],
        "relaxed": ["Documentary", "Drama", "Romance", "Music"],
        "adventurous": ["Adventure", "Action", "Fantasy", "Science Fiction"],
        "romantic": ["Romance", "Drama", "Comedy"],
        "mysterious": ["Mystery", "Thriller", "Horror", "Crime"]
    }
    return mood_genre_map.get(mood, [])

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Enhanced Movie Recommendation API is running!"}

def normalize(text):
    if not isinstance(text, str):
        return ""
    return ftfy.fix_text(text).strip().lower()

@app.get("/search")
def search_movies(
    query: str = Query(...), 
    genres: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    safe_mode: bool = Query(True),
    limit: int = Query(10)
):
    try:
        # Parse filters
        genre_list = genres.split(',') if genres else None
        language_list = languages.split(',') if languages else None
        
        # Apply filters first
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        if filtered_df.empty:
            return JSONResponse(content=[])
        
        # Clean titles for search
        df = filtered_df.dropna(subset=["title"]).copy()
        df["title_clean"] = df["title"].astype(str).apply(normalize)
        
        query_norm = normalize(query)

        # Substring match (fast)
        substring_results = df[df["title_clean"].str.contains(query_norm, na=False)].head(limit)

        if not substring_results.empty:
            results = substring_results
        else:
            # Fallback to fuzzy matching
            titles_to_check = df[df["title_clean"].str.len() >= len(query_norm) - 1]
            if not titles_to_check.empty:
                title_map = {title: idx for idx, title in enumerate(titles_to_check["title_clean"])}
                fuzzy_matches = process.extract(query_norm, title_map.keys(), scorer=fuzz.token_set_ratio, limit=20)
                matched_indices = [
                    title_map[title] for title, score, _ in fuzzy_matches if score >= 70
                ]
                results = titles_to_check.iloc[matched_indices].head(limit)
            else:
                results = pd.DataFrame()

        # Enrich results
        enriched_results = []
        for _, row in results.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)

    except Exception as e:
        logging.exception("Error in /search")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/recommendations")
def recommend_by_movie_id(
    movie_id: int = Query(...),
    genres: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    safe_mode: bool = Query(True),
    limit: int = Query(10)
):
    try:
        # Parse filters
        genre_list = genres.split(',') if genres else None
        language_list = languages.split(',') if languages else None
        
        # Apply filters
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        # Find movie by ID in filtered dataset
        matched_movie = filtered_df[filtered_df["id"] == movie_id]
        if matched_movie.empty:
            return JSONResponse(status_code=404, content={"error": "Movie not found"})

        # Get original index for embeddings
        original_idx = movies_df[movies_df["id"] == movie_id].index[0]
        query_embedding = movie_embeddings[original_idx].reshape(1, -1)

        # Get indices of filtered movies in original dataset
        filtered_indices = filtered_df.index.tolist()
        filtered_embeddings = movie_embeddings[filtered_indices]

        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, filtered_embeddings)[0]
        
        # Get top recommendations (excluding the query movie itself)
        top_indices_filtered = similarities.argsort()[::-1]
        
        # Filter out the original movie if it exists in filtered results
        movie_idx_in_filtered = None
        try:
            movie_idx_in_filtered = list(filtered_df.index).index(original_idx)
        except ValueError:
            pass
        
        if movie_idx_in_filtered is not None:
            top_indices_filtered = top_indices_filtered[top_indices_filtered != movie_idx_in_filtered]
        
        # Get actual indices in original dataframe
        top_indices = [filtered_indices[i] for i in top_indices_filtered[:limit]]
        
        recommended = movies_df.iloc[top_indices].copy()

        # Enrich results
        enriched_results = []
        for _, row in recommended.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)

    except Exception as e:
        logging.exception("Error in /recommendations endpoint")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/personalized-recommendations")
def get_personalized_recommendations(profile: UserProfile):
    try:
        # Apply user filters
        filtered_df = apply_filters(
            movies_df, 
            safe_mode=profile.safe_mode,
            languages=profile.language
        )
        
        if filtered_df.empty:
            return JSONResponse(content=[])
        
        # Get mood-based genre preferences
        mood_genres = get_mood_based_genres(profile.mood)
        
        recommendations = []
        
        # Method 1: Content-based on user history and preferences
        if profile.liked_movies or profile.watchlist or profile.history:
            # Combine all user interactions
            user_movies = list(set(profile.liked_movies + profile.watchlist + profile.history))
            
            # Remove disliked movies
            user_movies = [mid for mid in user_movies if mid not in profile.disliked_movies]
            
            if user_movies:
                # Get embeddings for user's movies
                user_movie_indices = []
                for movie_id in user_movies:
                    movie_idx = movies_df[movies_df['id'] == movie_id].index
                    if not movie_idx.empty:
                        user_movie_indices.append(movie_idx[0])
                
                if user_movie_indices:
                    # Calculate average embedding
                    user_embeddings = movie_embeddings[user_movie_indices]
                    avg_embedding = np.mean(user_embeddings, axis=0).reshape(1, -1)
                    
                    # Get filtered movie indices
                    filtered_indices = filtered_df.index.tolist()
                    filtered_embeddings = movie_embeddings[filtered_indices]
                    
                    # Compute similarities
                    similarities = cosine_similarity(avg_embedding, filtered_embeddings)[0]
                    
                    # Remove already seen movies
                    for i, idx in enumerate(filtered_indices):
                        movie_id = movies_df.iloc[idx]['id']
                        if movie_id in user_movies or movie_id in profile.disliked_movies:
                            similarities[i] = -1
                    
                    # Get top recommendations
                    top_indices = similarities.argsort()[::-1][:15]
                    recommended_indices = [filtered_indices[i] for i in top_indices if similarities[i] > -1]
                    
                    recommendations.extend(movies_df.iloc[recommended_indices[:8]])
        
        # Method 2: Mood-based recommendations
        if mood_genres:
            mood_filtered = filtered_df[
                filtered_df['genres'].apply(
                    lambda x: any(genre.lower() in str(x).lower() for genre in mood_genres) if pd.notna(x) else False
                )
            ]
            
            if not mood_filtered.empty:
                # Exclude already recommended movies
                existing_ids = [m['id'] for m in recommendations] if recommendations else []
                mood_filtered = mood_filtered[~mood_filtered['id'].isin(existing_ids)]
                mood_filtered = mood_filtered[~mood_filtered['id'].isin(profile.disliked_movies)]
                
                # Sort by rating and popularity
                mood_sorted = mood_filtered.sort_values(['vote_average_5', 'popularity_norm'], ascending=False)
                recommendations.extend(mood_sorted.head(5).to_dict('records'))
        
        # Method 3: Popular movies as fallback
        if len(recommendations) < 10:
            popular_movies = filtered_df.sort_values('popularity_norm', ascending=False)
            existing_ids = [m['id'] if isinstance(m, dict) else m.get('id', m['id']) for m in recommendations]
            popular_movies = popular_movies[~popular_movies['id'].isin(existing_ids)]
            popular_movies = popular_movies[~popular_movies['id'].isin(profile.disliked_movies)]
            
            needed = 10 - len(recommendations)
            recommendations.extend(popular_movies.head(needed).to_dict('records'))
        
        # Enrich and format results
        enriched_results = []
        for movie in recommendations[:10]:
            if isinstance(movie, dict):
                movie_row = pd.Series(movie)
            else:
                movie_row = movie
            enriched_results.append(enrich_movie_data(movie_row))
        
        return JSONResponse(content=enriched_results)

    except Exception as e:
        logging.exception("Error in /personalized-recommendations")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/trending")
def get_trending_movies(
    genres: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    safe_mode: bool = Query(True),
    limit: int = Query(10)
):
    try:
        # Parse filters
        genre_list = genres.split(',') if genres else None
        language_list = languages.split(',') if languages else None
        
        # Apply filters
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        if filtered_df.empty:
            return JSONResponse(content=[])
        
        trending = filtered_df.sort_values("popularity_norm", ascending=False).head(limit)
        
        enriched_results = []
        for _, row in trending.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)
    except Exception as e:
        logging.exception("Error in /trending")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/top-rated")
def get_top_rated_movies(
    genres: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    safe_mode: bool = Query(True),
    limit: int = Query(10)
):
    try:
        # Parse filters
        genre_list = genres.split(',') if genres else None
        language_list = languages.split(',') if languages else None
        
        # Apply filters
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        if filtered_df.empty:
            return JSONResponse(content=[])
        
        top_rated = filtered_df.sort_values("vote_average_5", ascending=False).head(limit)
        
        enriched_results = []
        for _, row in top_rated.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)
    except Exception as e:
        logging.exception("Error in /top-rated")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/now-playing")
def get_now_playing_movies(
    genres: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    safe_mode: bool = Query(True),
    limit: int = Query(10)
):
    try:
        # Parse filters
        genre_list = genres.split(',') if genres else None
        language_list = languages.split(',') if languages else None
        
        # Apply filters
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        if filtered_df.empty:
            return JSONResponse(content=[])
        
        # Sort by release date (most recent first) and popularity
        current_year = pd.Timestamp.now().year
        filtered_df['release_year'] = pd.to_datetime(filtered_df['release_date'], errors='coerce').dt.year
        recent_movies = filtered_df[
            (filtered_df['release_year'] >= current_year - 2) & 
            (filtered_df['release_year'] <= current_year)
        ].sort_values(['release_year', 'popularity_norm'], ascending=[False, False])
        
        # If not enough recent movies, fill with popular ones
        if len(recent_movies) < limit:
            older_popular = filtered_df[
                ~filtered_df['id'].isin(recent_movies['id'])
            ].sort_values('popularity_norm', ascending=False)
            
            needed = limit - len(recent_movies)
            now_playing = pd.concat([recent_movies, older_popular.head(needed)])
        else:
            now_playing = recent_movies.head(limit)
        
        enriched_results = []
        for _, row in now_playing.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)
    except Exception as e:
        logging.exception("Error in /now-playing")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)