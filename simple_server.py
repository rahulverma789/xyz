#!/usr/bin/env python3
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import random

# Sample movie data
MOVIES = [
    {
        "id": 565770,
        "title": "Blue Beetle",
        "release_date": "2023-08-16",
        "adult": 0,
        "overview": "Recent college grad Jaime Reyes returns home full of aspirations for his future...",
        "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
        "vote_average": 6.7,
        "poster_path": "https://image.tmdb.org/t/p/w500/mXLOHHc1Zeuwsl4xYKjKh2280oL.jpg",
        "popularity_norm": 1.0,
        "vote_average_5": 3.6
    },
    {
        "id": 980489,
        "title": "Gran Turismo",
        "release_date": "2023-08-09",
        "adult": 0,
        "overview": "The ultimate wish-fulfillment tale of a teenage Gran Turismo player...",
        "genres": [{"id": 12, "name": "Adventure"}, {"id": 28, "name": "Action"}],
        "vote_average": 7.753,
        "poster_path": "https://image.tmdb.org/t/p/w500/51tqzRtKMMZEYUpSYkrUE7v9ehm.jpg",
        "popularity_norm": 0.89,
        "vote_average_5": 4.0
    },
    {
        "id": 968051,
        "title": "The Nun II",
        "release_date": "2023-09-06",
        "adult": 0,
        "overview": "In 1956 France, a priest is violently murdered...",
        "genres": [{"id": 27, "name": "Horror"}],
        "vote_average": 6.7,
        "poster_path": "https://image.tmdb.org/t/p/w500/5gzzkR7y3hnY8AD1wXjCnVlHba5.jpg",
        "popularity_norm": 0.56,
        "vote_average_5": 3.3
    },
    {
        "id": 346698,
        "title": "Barbie",
        "release_date": "2023-07-19",
        "adult": 0,
        "overview": "Barbie and Ken are having the time of their lives...",
        "genres": [{"id": 35, "name": "Comedy"}, {"id": 12, "name": "Adventure"}],
        "vote_average": 6.971,
        "poster_path": "https://image.tmdb.org/t/p/w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg",
        "popularity_norm": 0.36,
        "vote_average_5": 3.6
    },
    {
        "id": 976573,
        "title": "Elemental",
        "release_date": "2023-06-14",
        "adult": 0,
        "overview": "In a city where fire, water, land and air residents live together...",
        "genres": [{"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"}],
        "vote_average": 7.61,
        "poster_path": "https://image.tmdb.org/t/p/w500/4Y1WNkd88JXmGfhtWR7dmDAo1T2.jpg",
        "popularity_norm": 0.34,
        "vote_average_5": 3.9
    },
    {
        "id": 278,
        "title": "The Shawshank Redemption",
        "release_date": "1994-09-23",
        "adult": 0,
        "overview": "Framed in the 1940s for the double murder...",
        "genres": [{"id": 18, "name": "Drama"}],
        "vote_average": 9.3,
        "poster_path": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflyCy3FpVPaOzii.jpg",
        "popularity_norm": 0.14,
        "vote_average_5": 4.7
    },
    {
        "id": 238,
        "title": "The Godfather",
        "release_date": "1972-03-14",
        "adult": 0,
        "overview": "The aging patriarch of an organized crime dynasty...",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
        "vote_average": 9.2,
        "poster_path": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "popularity_norm": 0.15,
        "vote_average_5": 4.6
    },
    {
        "id": 240,
        "title": "The Godfather Part II",
        "release_date": "1974-12-20",
        "adult": 0,
        "overview": "In the continuing saga of the Corleone crime family...",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
        "vote_average": 9.0,
        "poster_path": "https://image.tmdb.org/t/p/w500/hek3koDUyRQk7FIhPXsa6mT2Zc3.jpg",
        "popularity_norm": 0.13,
        "vote_average_5": 4.6
    },
    {
        "id": 424,
        "title": "Schindler's List",
        "release_date": "1993-12-15",
        "adult": 0,
        "overview": "The true story of how businessman Oskar Schindler...",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 36, "name": "History"}],
        "vote_average": 9.0,
        "poster_path": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
        "popularity_norm": 0.12,
        "vote_average_5": 4.6
    },
    {
        "id": 389,
        "title": "12 Angry Men",
        "release_date": "1957-04-10",
        "adult": 0,
        "overview": "The defense and the prosecution have rested...",
        "genres": [{"id": 18, "name": "Drama"}],
        "vote_average": 9.0,
        "poster_path": "https://image.tmdb.org/t/p/w500/ow3wq89wM8qd5X7hWKxiRfsFf9C.jpg",
        "popularity_norm": 0.11,
        "vote_average_5": 4.6
    }
]

class MovieHandler(http.server.BaseHTTPRequestHandler):
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
        
        # Get limit parameter
        limit = int(query_params.get('limit', [10])[0])
        
        if path == '/':
            response = {"message": "Simple Movie API is running!"}
        elif path == '/trending':
            # Sort by popularity
            sorted_movies = sorted(MOVIES, key=lambda x: x['popularity_norm'], reverse=True)
            response = sorted_movies[:limit]
        elif path == '/top-rated':
            # Sort by rating
            sorted_movies = sorted(MOVIES, key=lambda x: x['vote_average_5'], reverse=True)
            response = sorted_movies[:limit]
        elif path == '/search':
            query = query_params.get('query', [''])[0].lower()
            if query:
                filtered_movies = [m for m in MOVIES if query in m['title'].lower()]
                response = filtered_movies[:limit]
            else:
                response = []
        else:
            response = {"error": "Endpoint not found"}
        
        # Add genre_ids for compatibility
        if isinstance(response, list):
            for movie in response:
                if 'genres' in movie:
                    movie['genre_ids'] = [g['id'] for g in movie['genres']]
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        if self.path == '/personalized-recommendations':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                profile = json.loads(post_data.decode('utf-8'))
                
                # Simple recommendation based on mood
                mood = profile.get('mood', 'happy')
                
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
                
                # Filter movies by mood
                recommended = []
                for movie in MOVIES:
                    movie_genres = [g['name'] for g in movie['genres']]
                    if any(genre in movie_genres for genre in preferred_genres):
                        recommended.append(movie)
                
                # Add some random popular movies if not enough
                if len(recommended) < 10:
                    remaining = [m for m in MOVIES if m not in recommended]
                    recommended.extend(remaining[:10-len(recommended)])
                
                # Add genre_ids for compatibility
                for movie in recommended:
                    if 'genres' in movie:
                        movie['genre_ids'] = [g['id'] for g in movie['genres']]
                
                response = recommended[:10]
                
            except Exception as e:
                response = {"error": str(e)}
        else:
            response = {"error": "POST endpoint not found"}
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Reduce logging noise
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), MovieHandler) as httpd:
        print(f"Simple Movie API server running on http://localhost:{PORT}")
        print("Available endpoints:")
        print("  GET  /")
        print("  GET  /trending?limit=10")
        print("  GET  /top-rated?limit=10")
        print("  GET  /search?query=batman&limit=10")
        print("  POST /personalized-recommendations")
        httpd.serve_forever()