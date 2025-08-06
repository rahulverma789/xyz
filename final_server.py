#!/usr/bin/env python3
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import traceback

# Sample movie data with diverse genres
MOVIES = [
    {"id": 565770, "title": "Blue Beetle", "release_date": "2023-08-16", "adult": 0, "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "vote_average": 6.7, "poster_path": "https://image.tmdb.org/t/p/w500/mXLOHHc1Zeuwsl4xYKjKh2280oL.jpg", "popularity_norm": 1.0, "vote_average_5": 3.6},
    {"id": 980489, "title": "Gran Turismo", "release_date": "2023-08-09", "adult": 0, "genres": [{"id": 12, "name": "Adventure"}, {"id": 28, "name": "Action"}], "vote_average": 7.753, "poster_path": "https://image.tmdb.org/t/p/w500/51tqzRtKMMZEYUpSYkrUE7v9ehm.jpg", "popularity_norm": 0.89, "vote_average_5": 4.0},
    {"id": 155, "title": "The Dark Knight", "release_date": "2008-07-18", "adult": 0, "genres": [{"id": 28, "name": "Action"}, {"id": 80, "name": "Crime"}, {"id": 53, "name": "Thriller"}], "vote_average": 9.0, "poster_path": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "popularity_norm": 0.85, "vote_average_5": 4.5},
    {"id": 968051, "title": "The Nun II", "release_date": "2023-09-06", "adult": 0, "genres": [{"id": 27, "name": "Horror"}], "vote_average": 6.7, "poster_path": "https://image.tmdb.org/t/p/w500/5gzzkR7y3hnY8AD1wXjCnVlHba5.jpg", "popularity_norm": 0.56, "vote_average_5": 3.3},
    {"id": 694, "title": "The Shining", "release_date": "1980-05-23", "adult": 0, "genres": [{"id": 27, "name": "Horror"}, {"id": 53, "name": "Thriller"}], "vote_average": 8.2, "poster_path": "https://image.tmdb.org/t/p/w500/b6ko0IKC8MdYBBPkkA1aBPLe2yz.jpg", "popularity_norm": 0.40, "vote_average_5": 4.1},
    {"id": 346698, "title": "Barbie", "release_date": "2023-07-19", "adult": 0, "genres": [{"id": 35, "name": "Comedy"}, {"id": 12, "name": "Adventure"}], "vote_average": 6.971, "poster_path": "https://image.tmdb.org/t/p/w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg", "popularity_norm": 0.36, "vote_average_5": 3.6},
    {"id": 976573, "title": "Elemental", "release_date": "2023-06-14", "adult": 0, "genres": [{"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"}], "vote_average": 7.61, "poster_path": "https://image.tmdb.org/t/p/w500/4Y1WNkd88JXmGfhtWR7dmDAo1T2.jpg", "popularity_norm": 0.34, "vote_average_5": 3.9},
    {"id": 13, "title": "Forrest Gump", "release_date": "1994-07-06", "adult": 0, "genres": [{"id": 35, "name": "Comedy"}, {"id": 18, "name": "Drama"}, {"id": 10749, "name": "Romance"}], "vote_average": 8.5, "poster_path": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg", "popularity_norm": 0.42, "vote_average_5": 4.2},
    {"id": 278, "title": "The Shawshank Redemption", "release_date": "1994-09-23", "adult": 0, "genres": [{"id": 18, "name": "Drama"}], "vote_average": 9.3, "poster_path": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflyCy3FpVPaOzii.jpg", "popularity_norm": 0.14, "vote_average_5": 4.7},
    {"id": 238, "title": "The Godfather", "release_date": "1972-03-14", "adult": 0, "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}], "vote_average": 9.2, "poster_path": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "popularity_norm": 0.15, "vote_average_5": 4.6},
    {"id": 240, "title": "The Godfather Part II", "release_date": "1974-12-20", "adult": 0, "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}], "vote_average": 9.0, "poster_path": "https://image.tmdb.org/t/p/w500/hek3koDUyRQk7FIhPXsa6mT2Zc3.jpg", "popularity_norm": 0.13, "vote_average_5": 4.6},
    {"id": 603, "title": "The Matrix", "release_date": "1999-03-30", "adult": 0, "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "vote_average": 8.2, "poster_path": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", "popularity_norm": 0.50, "vote_average_5": 4.1},
    {"id": 11, "title": "Star Wars", "release_date": "1977-05-25", "adult": 0, "genres": [{"id": 12, "name": "Adventure"}, {"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}], "vote_average": 8.6, "poster_path": "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg", "popularity_norm": 0.60, "vote_average_5": 4.3},
    {"id": 597, "title": "Titanic", "release_date": "1997-11-18", "adult": 0, "genres": [{"id": 18, "name": "Drama"}, {"id": 10749, "name": "Romance"}], "vote_average": 7.9, "poster_path": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg", "popularity_norm": 0.55, "vote_average_5": 3.95},
    {"id": 680, "title": "Pulp Fiction", "release_date": "1994-09-10", "adult": 0, "genres": [{"id": 53, "name": "Thriller"}, {"id": 80, "name": "Crime"}], "vote_average": 8.9, "poster_path": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", "popularity_norm": 0.45, "vote_average_5": 4.45}
]

def safe_apply_filters(movies, query_params):
    """Safely apply filters to movie list with proper error handling"""
    try:
        # Start with all movies
        result = []
        
        # Get filter parameters
        safe_mode_param = query_params.get('safe_mode', ['true'])
        safe_mode = safe_mode_param[0].lower() == 'true' if safe_mode_param else True
        
        genres_param = query_params.get('genres', [])
        genre_filter = genres_param[0] if genres_param and genres_param[0] else None
        
        languages_param = query_params.get('languages', [])
        language_filter = languages_param[0] if languages_param and languages_param[0] else None
        
        print(f"Applying filters - Safe mode: {safe_mode}, Genres: {genre_filter}, Languages: {language_filter}")
        
        # Process each movie individually
        for movie in movies:
            include_movie = True
            
            # Safe mode filter
            if safe_mode:
                adult_value = movie.get('adult', 0)
                if adult_value != 0:
                    include_movie = False
                    continue
            
            # Genre filter
            if genre_filter and include_movie:
                movie_genres = movie.get('genres', [])
                if movie_genres:  # Check if genres exist
                    genre_names = []
                    for genre in movie_genres:
                        if isinstance(genre, dict) and 'name' in genre:
                            genre_names.append(genre['name'].lower())
                    
                    # Parse requested genres
                    requested_genres = [g.strip().lower() for g in genre_filter.split(',') if g.strip()]
                    
                    # Check if any requested genre matches movie genres
                    has_matching_genre = False
                    for req_genre in requested_genres:
                        for movie_genre in genre_names:
                            if req_genre in movie_genre:
                                has_matching_genre = True
                                break
                        if has_matching_genre:
                            break
                    
                    if not has_matching_genre:
                        include_movie = False
                        continue
            
            # Language filter (placeholder - all our sample movies are English)
            if language_filter and include_movie:
                # For now, assume all movies pass language filter
                pass
            
            # Add movie if it passes all filters
            if include_movie:
                result.append(movie)
        
        print(f"Filtered from {len(movies)} to {len(result)} movies")
        return result
        
    except Exception as e:
        print(f"Error in filtering: {e}")
        print(traceback.format_exc())
        # Return all movies if filtering fails
        return movies

class RobustMovieHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Get limit parameter
            limit_param = query_params.get('limit', ['10'])
            limit = int(limit_param[0]) if limit_param[0].isdigit() else 10
            limit = min(limit, 50)  # Cap at 50 movies
            
            print(f"GET {path} with params: {dict(query_params)}")
            
            if path == '/':
                response = {"message": "Final Movie API is running!", "status": "healthy"}
                
            elif path == '/trending':
                filtered_movies = safe_apply_filters(MOVIES, query_params)
                sorted_movies = sorted(filtered_movies, key=lambda x: x.get('popularity_norm', 0), reverse=True)
                response = sorted_movies[:limit]
                
            elif path == '/top-rated':
                filtered_movies = safe_apply_filters(MOVIES, query_params)
                sorted_movies = sorted(filtered_movies, key=lambda x: x.get('vote_average_5', 0), reverse=True)
                response = sorted_movies[:limit]
                
            elif path == '/search':
                query_param = query_params.get('query', [''])
                search_query = query_param[0].lower() if query_param else ''
                
                if search_query:
                    filtered_movies = safe_apply_filters(MOVIES, query_params)
                    search_results = []
                    for movie in filtered_movies:
                        title = movie.get('title', '').lower()
                        if search_query in title:
                            search_results.append(movie)
                    response = search_results[:limit]
                else:
                    response = []
                    
            else:
                response = {"error": "Endpoint not found", "available_endpoints": ["/", "/trending", "/top-rated", "/search", "/personalized-recommendations"]}
            
            # Add genre_ids for compatibility
            if isinstance(response, list):
                for movie in response:
                    if isinstance(movie, dict) and 'genres' in movie:
                        genres = movie.get('genres', [])
                        genre_ids = []
                        for genre in genres:
                            if isinstance(genre, dict) and 'id' in genre:
                                genre_ids.append(genre['id'])
                        movie['genre_ids'] = genre_ids
            
            print(f"Returning {len(response) if isinstance(response, list) else 1} items")
            self.send_json_response(response)
            
        except Exception as e:
            print(f"Error in GET request: {e}")
            print(traceback.format_exc())
            error_response = {"error": f"Internal server error: {str(e)}"}
            self.send_json_response(error_response, 500)
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if self.path == '/personalized-recommendations':
                try:
                    profile = json.loads(post_data.decode('utf-8'))
                    mood = profile.get('mood', 'happy')
                    
                    print(f"Personalized request for mood: {mood}")
                    
                    # Apply user filters
                    safe_mode = profile.get('safe_mode', True)
                    filtered_movies = []
                    
                    for movie in MOVIES:
                        if safe_mode and movie.get('adult', 0) != 0:
                            continue
                        filtered_movies.append(movie)
                    
                    # Mood-based genre mapping
                    mood_genres = {
                        "happy": ["Comedy", "Animation", "Family"],
                        "excited": ["Action", "Adventure", "Science Fiction"],
                        "relaxed": ["Drama", "Romance"],
                        "adventurous": ["Adventure", "Action", "Science Fiction"],
                        "romantic": ["Romance", "Drama", "Comedy"],
                        "mysterious": ["Horror", "Crime", "Drama"]
                    }
                    
                    preferred_genres = mood_genres.get(mood, ["Comedy"])
                    recommended = []
                    
                    # Find mood-based movies
                    for movie in filtered_movies:
                        movie_genres = movie.get('genres', [])
                        movie_genre_names = []
                        for genre in movie_genres:
                            if isinstance(genre, dict) and 'name' in genre:
                                movie_genre_names.append(genre['name'])
                        
                        # Check if movie matches preferred genres
                        matches_mood = False
                        for pref_genre in preferred_genres:
                            for movie_genre in movie_genre_names:
                                if pref_genre.lower() in movie_genre.lower():
                                    matches_mood = True
                                    break
                            if matches_mood:
                                break
                        
                        if matches_mood:
                            recommended.append(movie)
                    
                    # Fill with popular movies if needed
                    if len(recommended) < 10:
                        existing_ids = [m.get('id') for m in recommended]
                        remaining = [m for m in filtered_movies if m.get('id') not in existing_ids]
                        remaining = sorted(remaining, key=lambda x: x.get('popularity_norm', 0), reverse=True)
                        needed = 10 - len(recommended)
                        recommended.extend(remaining[:needed])
                    
                    # Add genre_ids
                    for movie in recommended:
                        if 'genres' in movie:
                            genres = movie.get('genres', [])
                            genre_ids = []
                            for genre in genres:
                                if isinstance(genre, dict) and 'id' in genre:
                                    genre_ids.append(genre['id'])
                            movie['genre_ids'] = genre_ids
                    
                    response = recommended[:10]
                    print(f"Returning {len(response)} personalized movies")
                    
                except json.JSONDecodeError as e:
                    response = {"error": f"Invalid JSON: {str(e)}"}
                    
            else:
                response = {"error": "POST endpoint not found"}
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"Error in POST request: {e}")
            print(traceback.format_exc())
            error_response = {"error": f"Internal server error: {str(e)}"}
            self.send_json_response(error_response, 500)
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"{self.address_string()} - {format % args}")

def main():
    PORT = 8000
    print(f"🎬 Starting Final Movie API Server on http://localhost:{PORT}")
    print("=" * 60)
    print("Available endpoints:")
    print("  GET  / - API status")
    print("  GET  /trending?genres=Action&safe_mode=true&limit=10")
    print("  GET  /top-rated?genres=Comedy&limit=5") 
    print("  GET  /search?query=batman&genres=Action&limit=10")
    print("  POST /personalized-recommendations")
    print("=" * 60)
    print("✅ Robust filtering implemented")
    print("✅ Error handling added")
    print("✅ CORS headers configured") 
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), RobustMovieHandler) as httpd:
            print(f"🚀 Server running! Test with: http://localhost:{PORT}/trending?genres=Action&limit=5")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()