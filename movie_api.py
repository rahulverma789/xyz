from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="Movie Recommendation API", version="1.0.0")

# Enable frontend connection (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for data
movies_df = None
movie_embeddings = None

# TMDB configuration
TMDB_API_KEY = "3d3b5cbc09e66409a5686373a4c110e7"
TMDB_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
YOUTUBE_BASE_URL = "https://www.youtube.com/watch?v="

def load_data():
    """Load movie data and embeddings"""
    global movies_df, movie_embeddings
    try:
        movies_df = pd.read_feather("final_movies_cleaned.feather")
        movie_embeddings = np.load("movie_embeddings_float16.npy")
        logging.info(f"Loaded {len(movies_df)} movies and {movie_embeddings.shape} embeddings")
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        # Create dummy data for testing if files don't exist
        movies_df = pd.DataFrame({
            'id': [1, 2, 3],
            'title': ['Test Movie 1', 'Test Movie 2', 'Test Movie 3'],
            'overview': ['Test overview 1', 'Test overview 2', 'Test overview 3'],
            'release_date': ['2023-01-01', '2023-02-01', '2023-03-01'],
            'runtime': [120, 150, 90],
            'adult': [False, False, True],
            'genres': [['Action'], ['Comedy'], ['Drama']],
            'all_languages': [['en'], ['en'], ['en']],
            'vote_average_5': [4.5, 3.8, 4.2],
            'popularity_norm': [0.8, 0.6, 0.7]
        })
        movie_embeddings = np.random.rand(len(movies_df), 100)

def safe_convert_movie(movie_row) -> Dict[str, Any]:
    """Convert movie row to safe JSON-serializable format"""
    safe_movie = {}
    for k, v in movie_row.items():
        if isinstance(v, (np.integer, np.floating)):
            safe_movie[k] = v.item()
        elif isinstance(v, np.ndarray):
            safe_movie[k] = v.tolist()
        elif pd.isna(v):
            safe_movie[k] = None
        else:
            safe_movie[k] = v
    return safe_movie

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup"""
    load_data()

@app.get("/")
def read_root():
    return {"message": "Movie Recommendation API is running!", "movies_count": len(movies_df) if movies_df is not None else 0}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "movies_loaded": movies_df is not None,
        "embeddings_loaded": movie_embeddings is not None,
        "data_shape": {
            "movies": len(movies_df) if movies_df is not None else 0,
            "embeddings": movie_embeddings.shape if movie_embeddings is not None else None
        }
    }

@app.get("/tmdb_info/{movie_id}")
def get_tmdb_info(movie_id: int):
    """Get TMDB poster and trailer information"""
    poster_url = ""
    trailer_url = ""

    try:
        # Get poster
        r = requests.get(f"{TMDB_BASE}/movie/{movie_id}?api_key={TMDB_API_KEY}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("poster_path"):
                poster_url = IMAGE_BASE_URL + data["poster_path"]

        # Get trailer
        r2 = requests.get(f"{TMDB_BASE}/movie/{movie_id}/videos?api_key={TMDB_API_KEY}", timeout=10)
        if r2.status_code == 200:
            for video in r2.json().get("results", []):
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    trailer_url = YOUTUBE_BASE_URL + video["key"]
                    break

    except requests.RequestException as e:
        logging.error(f"Error fetching TMDB info for movie {movie_id}: {e}")

    return {"poster": poster_url, "trailer": trailer_url}

@app.get("/search")
def search_movies(query: str = Query(..., min_length=1)) -> List[Dict[str, Any]]:
    """Search movies by title"""
    try:
        if movies_df is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        # Clean and search
        movies_df_clean = movies_df.dropna(subset=["title"]).copy()
        movies_df_clean["title"] = movies_df_clean["title"].astype(str)

        # Case-insensitive search
        mask = movies_df_clean["title"].str.contains(query, case=False, na=False)
        results = movies_df_clean[mask].head(10)

        if results.empty:
            return []

        # Convert to safe format
        safe_results = []
        for _, row in results.iterrows():
            safe_movie = safe_convert_movie(row)
            safe_results.append(safe_movie)

        return safe_results

    except Exception as e:
        logging.exception("Error in /search endpoint")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/recommend")
def recommend_movies(query: str = Query(..., min_length=1)) -> List[Dict[str, Any]]:
    """Get movie recommendations based on a movie title"""
    try:
        if movies_df is None or movie_embeddings is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        # Match by title first
        matched_movies = movies_df[movies_df["title"].str.contains(query, case=False, na=False)]

        if matched_movies.empty:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Use first matched movie
        idx = matched_movies.index[0]
        query_embedding = movie_embeddings[idx].reshape(1, -1)

        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, movie_embeddings)[0]
        top_indices = similarities.argsort()[::-1][1:11]  # Skip the input movie itself, get top 10

        recommended = movies_df.iloc[top_indices].copy()

        # Convert to safe format
        results = []
        for _, row in recommended.iterrows():
            safe_movie = safe_convert_movie(row)
            results.append(safe_movie)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error in /recommend endpoint")
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")

@app.get("/movie/{movie_id}")
def get_movie_details(movie_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific movie"""
    try:
        if movies_df is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        movie = movies_df[movies_df["id"] == movie_id]
        
        if movie.empty:
            raise HTTPException(status_code=404, detail="Movie not found")

        movie_row = movie.iloc[0]
        safe_movie = safe_convert_movie(movie_row)
        
        return safe_movie

    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error in /movie/{movie_id} endpoint")
        raise HTTPException(status_code=500, detail=f"Movie details error: {str(e)}")

@app.get("/random")
def get_random_movies(count: int = Query(10, ge=1, le=50)) -> List[Dict[str, Any]]:
    """Get random movies"""
    try:
        if movies_df is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        random_movies = movies_df.sample(n=min(count, len(movies_df))).copy()
        
        results = []
        for _, row in random_movies.iterrows():
            safe_movie = safe_convert_movie(row)
            results.append(safe_movie)

        return results

    except Exception as e:
        logging.exception("Error in /random endpoint")
        raise HTTPException(status_code=500, detail=f"Random movies error: {str(e)}")

@app.get("/genres")
def get_available_genres() -> List[str]:
    """Get list of all available genres"""
    try:
        if movies_df is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        all_genres = set()
        for genres_list in movies_df["genres"].dropna():
            if isinstance(genres_list, list):
                all_genres.update(genres_list)
        
        return sorted(list(all_genres))

    except Exception as e:
        logging.exception("Error in /genres endpoint")
        raise HTTPException(status_code=500, detail=f"Genres error: {str(e)}")

@app.get("/movies/by_genre")
def get_movies_by_genre(genre: str = Query(...), limit: int = Query(10, ge=1, le=50)) -> List[Dict[str, Any]]:
    """Get movies by genre"""
    try:
        if movies_df is None:
            raise HTTPException(status_code=500, detail="Movie data not loaded")

        # Filter movies that contain the specified genre
        filtered_movies = movies_df[
            movies_df["genres"].apply(
                lambda x: isinstance(x, list) and genre.lower() in [g.lower() for g in x]
            )
        ].head(limit)

        if filtered_movies.empty:
            return []

        results = []
        for _, row in filtered_movies.iterrows():
            safe_movie = safe_convert_movie(row)
            results.append(safe_movie)

        return results

    except Exception as e:
        logging.exception(f"Error in /movies/by_genre endpoint for genre {genre}")
        raise HTTPException(status_code=500, detail=f"Genre movies error: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)