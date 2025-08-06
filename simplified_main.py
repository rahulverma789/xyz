from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from fastapi.responses import JSONResponse
import requests
import logging
from typing import List, Optional
from pydantic import BaseModel
import json

app = FastAPI()

# CORS: allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)

# TMDB API configuration
TMDB_API_KEY = "3d3b5cbc09e66409a5686373a4c110e7"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Cache for TMDB API calls
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_tmdb_data_cached(movie_id: int):
    """Cached TMDB API call"""
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.warning(f"TMDB API error for movie {movie_id}: {e}")
    return {}

# Sample movie data
SAMPLE_MOVIES = [
    {"id": 565770, "title": "Blue Beetle", "release_date": "2023-08-16", "runtime": 128, "adult": 0, "overview": "Recent college grad Jaime Reyes returns home full of aspirations for his future...", "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "all_languages": ["en"], "vote_average_5": 3.6, "popularity_norm": 1.0},
    {"id": 980489, "title": "Gran Turismo", "release_date": "2023-08-09", "runtime": 135, "adult": 0, "overview": "The ultimate wish-fulfillment tale of a teenage Gran Turismo player...", "genres": [{"id": 12, "name": "Adventure"}, {"id": 28, "name": "Action"}], "all_languages": ["en"], "vote_average_5": 4.0, "popularity_norm": 0.89},
    {"id": 968051, "title": "The Nun II", "release_date": "2023-09-06", "runtime": 110, "adult": 0, "overview": "In 1956 France, a priest is violently murdered...", "genres": [{"id": 27, "name": "Horror"}], "all_languages": ["en"], "vote_average_5": 3.3, "popularity_norm": 0.56},
    {"id": 615656, "title": "Meg 2: The Trench", "release_date": "2023-08-02", "runtime": 116, "adult": 0, "overview": "An exploratory dive into the deepest depths...", "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "all_languages": ["en"], "vote_average_5": 3.5, "popularity_norm": 0.52},
    {"id": 346698, "title": "Barbie", "release_date": "2023-07-19", "runtime": 114, "adult": 0, "overview": "Barbie and Ken are having the time of their lives...", "genres": [{"id": 35, "name": "Comedy"}, {"id": 12, "name": "Adventure"}], "all_languages": ["en"], "vote_average_5": 3.6, "popularity_norm": 0.36},
    {"id": 976573, "title": "Elemental", "release_date": "2023-06-14", "runtime": 102, "adult": 0, "overview": "In a city where fire, water, land and air residents live together...", "genres": [{"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"}], "all_languages": ["en"], "vote_average_5": 3.9, "popularity_norm": 0.34},
    {"id": 298618, "title": "The Flash", "release_date": "2023-06-14", "runtime": 144, "adult": 0, "overview": "When Barry Allen travels back in time...", "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "all_languages": ["en"], "vote_average_5": 3.4, "popularity_norm": 0.31},
    {"id": 447365, "title": "Guardians of the Galaxy Vol. 3", "release_date": "2023-05-03", "runtime": 150, "adult": 0, "overview": "Peter Quill, still reeling from the loss of Gamora...", "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 12, "name": "Adventure"}], "all_languages": ["en"], "vote_average_5": 4.1, "popularity_norm": 0.29},
    {"id": 502356, "title": "The Super Mario Bros. Movie", "release_date": "2023-04-05", "runtime": 92, "adult": 0, "overview": "While working underground to fix a water main...", "genres": [{"id": 16, "name": "Animation"}, {"id": 10751, "name": "Family"}], "all_languages": ["en"], "vote_average_5": 3.7, "popularity_norm": 0.27},
    {"id": 677179, "title": "Creed III", "release_date": "2023-03-01", "runtime": 116, "adult": 0, "overview": "After dominating the boxing world...", "genres": [{"id": 18, "name": "Drama"}, {"id": 28, "name": "Action"}], "all_languages": ["en"], "vote_average_5": 3.8, "popularity_norm": 0.25},
    # Add more high-rated movies
    {"id": 238, "title": "The Godfather", "release_date": "1972-03-14", "runtime": 175, "adult": 0, "overview": "The aging patriarch of an organized crime dynasty...", "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}], "all_languages": ["en"], "vote_average_5": 4.6, "popularity_norm": 0.15},
    {"id": 278, "title": "The Shawshank Redemption", "release_date": "1994-09-23", "runtime": 142, "adult": 0, "overview": "Framed in the 1940s for the double murder...", "genres": [{"id": 18, "name": "Drama"}], "all_languages": ["en"], "vote_average_5": 4.7, "popularity_norm": 0.14},
    {"id": 240, "title": "The Godfather Part II", "release_date": "1974-12-20", "runtime": 202, "adult": 0, "overview": "In the continuing saga of the Corleone crime family...", "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}], "all_languages": ["en"], "vote_average_5": 4.6, "popularity_norm": 0.13},
    {"id": 424, "title": "Schindler's List", "release_date": "1993-12-15", "runtime": 195, "adult": 0, "overview": "The true story of how businessman Oskar Schindler...", "genres": [{"id": 18, "name": "Drama"}, {"id": 36, "name": "History"}], "all_languages": ["en"], "vote_average_5": 4.6, "popularity_norm": 0.12},
    {"id": 389, "title": "12 Angry Men", "release_date": "1957-04-10", "runtime": 96, "adult": 0, "overview": "The defense and the prosecution have rested...", "genres": [{"id": 18, "name": "Drama"}], "all_languages": ["en"], "vote_average_5": 4.6, "popularity_norm": 0.11}
]

# Create DataFrame
movies_df = pd.DataFrame(SAMPLE_MOVIES)

# Add computed fields
movies_df['genre_ids'] = movies_df['genres'].apply(lambda x: [g['id'] for g in x])
movies_df['vote_average'] = movies_df['vote_average_5'] * 2

# Pydantic model for user profile
class UserProfile(BaseModel):
    user_id: str
    age: int
    safe_mode: bool
    language: List[str]
    mood: str
    region: str
    watchlist: List[int] = []
    history: List[int] = []
    liked_movies: List[int] = []
    disliked_movies: List[int] = []

def apply_filters(df, genres=None, languages=None, safe_mode=True):
    """Apply filters to the dataframe"""
    filtered_df = df.copy()
    
    # Safe mode filter
    if safe_mode:
        filtered_df = filtered_df[filtered_df['adult'] == 0]
    
    # Language filter
    if languages:
        language_filter = filtered_df['all_languages'].apply(
            lambda x: any(lang in x for lang in languages) if x else False
        )
        filtered_df = filtered_df[language_filter]
    
    # Genre filter
    if genres:
        genre_filter = filtered_df['genres'].apply(
            lambda x: any(genre.lower() in str(x).lower() for genre in genres) if x else False
        )
        filtered_df = filtered_df[genre_filter]
    
    return filtered_df

def enrich_movie_data(movie_row):
    """Enrich movie data with TMDB poster and other info"""
    movie = movie_row.to_dict()
    
    # Convert numpy types to native Python types
    for key, value in movie.items():
        if isinstance(value, (np.integer, np.floating)):
            movie[key] = value.item()
        elif isinstance(value, np.ndarray):
            movie[key] = value.tolist()
    
    # Get TMDB data
    tmdb_data = get_tmdb_data_cached(int(movie_row["id"]))
    
    # Add poster path
    poster_path = tmdb_data.get('poster_path')
    movie["poster_path"] = (
        f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None
    )
    
    # Add vote average
    movie["vote_average"] = tmdb_data.get("vote_average", movie.get("vote_average", 0))
    
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
    return {"message": "Movie Recommendation API is running with sample data!"}

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
        
        # Apply filters and sort by popularity
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
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
        
        # Apply filters and sort by rating
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        top_rated = filtered_df.sort_values("vote_average_5", ascending=False).head(limit)
        
        enriched_results = []
        for _, row in top_rated.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)
    except Exception as e:
        logging.exception("Error in /top-rated")
        return JSONResponse(status_code=500, content={"error": str(e)})

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
        
        # Apply filters
        filtered_df = apply_filters(movies_df, genre_list, language_list, safe_mode)
        
        # Simple search by title
        search_results = filtered_df[
            filtered_df['title'].str.contains(query, case=False, na=False)
        ].head(limit)
        
        enriched_results = []
        for _, row in search_results.iterrows():
            enriched_results.append(enrich_movie_data(row))

        return JSONResponse(content=enriched_results)
    except Exception as e:
        logging.exception("Error in /search")
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
        
        # Get mood-based genre preferences
        mood_genres = get_mood_based_genres(profile.mood)
        
        recommendations = []
        
        # Method 1: Mood-based recommendations
        if mood_genres:
            mood_filtered = filtered_df[
                filtered_df['genres'].apply(
                    lambda x: any(genre.lower() in str(x).lower() for genre in mood_genres) if x else False
                )
            ]
            
            if not mood_filtered.empty:
                # Exclude disliked movies
                mood_filtered = mood_filtered[~mood_filtered['id'].isin(profile.disliked_movies)]
                
                # Sort by rating and popularity
                mood_sorted = mood_filtered.sort_values(['vote_average_5', 'popularity_norm'], ascending=False)
                for _, row in mood_sorted.head(5).iterrows():
                    recommendations.append(row.to_dict())
        
        # Method 2: Popular movies as fallback
        if len(recommendations) < 10:
            popular_movies = filtered_df.sort_values('popularity_norm', ascending=False)
            existing_ids = [m['id'] for m in recommendations]
            popular_movies = popular_movies[~popular_movies['id'].isin(existing_ids)]
            popular_movies = popular_movies[~popular_movies['id'].isin(profile.disliked_movies)]
            
            needed = 10 - len(recommendations)
            for _, row in popular_movies.head(needed).iterrows():
                recommendations.append(row.to_dict())
        
        # Enrich and format results
        enriched_results = []
        for movie in recommendations[:10]:
            movie_row = pd.Series(movie)
            enriched_results.append(enrich_movie_data(movie_row))
        
        return JSONResponse(content=enriched_results)

    except Exception as e:
        logging.exception("Error in /personalized-recommendations")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)