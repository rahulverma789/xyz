#!/usr/bin/env python3
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

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

def apply_movie_filters(movies, query_params):
    """Apply filters to movie list"""
    filtered = movies.copy()
    
    # Safe mode filter
    safe_mode = query_params.get('safe_mode', ['true'])[0].lower() == 'true'
    if safe_mode:
        filtered = [m for m in filtered if m['adult'] == 0]
    
    # Genre filter  
    genres = query_params.get('genres', [])
    if genres and genres[0]:
        genre_list = [g.strip().lower() for g in genres[0].split(',') if g.strip()]
        if genre_list:
            new_filtered = []
            for movie in filtered:
                movie_genres = [g['name'].lower() for g in movie.get('genres', [])]
                if any(genre in movie_genres for genre in genre_list):
                    new_filtered.append(movie)
            filtered = new_filtered
    
    return filtered

class MovieHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        limit = int(query_params.get('limit', [10])[0])
        
        print(f"GET {path} with params: {dict(query_params)}")
        
        if path == '/':
            response = {"message": "Working Movie API is running!"}
        elif path == '/trending':
            filtered_movies = apply_movie_filters(MOVIES, query_params)
            sorted_movies = sorted(filtered_movies, key=lambda x: x['popularity_norm'], reverse=True)
            response = sorted_movies[:limit]
        elif path == '/top-rated':
            filtered_movies = apply_movie_filters(MOVIES, query_params)
            sorted_movies = sorted(filtered_movies, key=lambda x: x['vote_average_5'], reverse=True)
            response = sorted_movies[:limit]
        elif path == '/search':
            filtered_movies = apply_movie_filters(MOVIES, query_params)
            query = query_params.get('query', [''])[0].lower()
            if query:
                search_results = [m for m in filtered_movies if query in m['title'].lower()]
                response = search_results[:limit]
            else:
                response = []
        else:
            response = {"error": "Endpoint not found"}
        
        # Add genre_ids for compatibility
        if isinstance(response, list):
            for movie in response:
                if 'genres' in movie:
                    movie['genre_ids'] = [g['id'] for g in movie['genres']]
        
        print(f"Returning {len(response) if isinstance(response, list) else 1} items")
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if self.path == '/personalized-recommendations':
            try:
                profile = json.loads(post_data.decode('utf-8'))
                mood = profile.get('mood', 'happy')
                
                print(f"Personalized request for mood: {mood}")
                
                # Filter movies
                filtered_movies = MOVIES.copy()
                if profile.get('safe_mode', True):
                    filtered_movies = [m for m in filtered_movies if m['adult'] == 0]
                
                # Mood-based genres
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
                    movie_genres = [g['name'] for g in movie['genres']]
                    if any(genre in movie_genres for genre in preferred_genres):
                        recommended.append(movie)
                
                # Fill with popular movies if needed
                if len(recommended) < 10:
                    existing_ids = [m['id'] for m in recommended]
                    remaining = [m for m in filtered_movies if m['id'] not in existing_ids]
                    remaining = sorted(remaining, key=lambda x: x['popularity_norm'], reverse=True)
                    recommended.extend(remaining[:10-len(recommended)])
                
                # Add genre_ids
                for movie in recommended:
                    if 'genres' in movie:
                        movie['genre_ids'] = [g['id'] for g in movie['genres']]
                
                response = recommended[:10]
                print(f"Returning {len(response)} personalized movies")
                
            except Exception as e:
                print(f"Error: {e}")
                response = {"error": str(e)}
        else:
            response = {"error": "POST endpoint not found"}
        
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    PORT = 8000
    print(f"Starting Working Movie API server on http://localhost:{PORT}")
    print("Available endpoints:")
    print("  GET  / - Root")
    print("  GET  /trending?genres=Action&limit=10")
    print("  GET  /top-rated?genres=Comedy&limit=10") 
    print("  GET  /search?query=batman&genres=Action&limit=10")
    print("  POST /personalized-recommendations")
    
    with socketserver.TCPServer(("", PORT), MovieHandler) as httpd:
        httpd.serve_forever()