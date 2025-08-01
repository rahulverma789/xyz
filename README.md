# Movie Explorer - AI-Powered Movie Recommendation System

A beautiful, modern movie exploration platform that combines custom AI-powered recommendations with TMDB data for comprehensive movie information.

## Features

- **AI-Powered Search & Recommendations**: Uses your custom machine learning model for intelligent movie search and recommendations
- **Rich Movie Details**: Fetches comprehensive movie information from TMDB API including posters, trailers, and metadata
- **Modern UI**: Beautiful, responsive interface with glass morphism effects and smooth animations
- **Personal Watchlist**: Save movies to your personal watchlist with local storage
- **Hybrid Data Sources**: Combines custom recommendation engine with TMDB for the best of both worlds

## Architecture

The system uses a hybrid approach:

1. **Custom API** (`movie_api.py`): Handles movie search and recommendations using your trained ML model
2. **TMDB API**: Provides movie posters, trailers, and additional metadata
3. **Frontend** (`movie_explorer.html`): Beautiful single-page application that combines data from both sources

## Setup Instructions

### Prerequisites

- Python 3.8+
- Your movie dataset files:
  - `final_movies_cleaned.feather`
  - `movie_embeddings_float16.npy`
- TMDB API key (already included in the code)

### Backend Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Place Your Data Files**:
   - Copy `final_movies_cleaned.feather` to the project root
   - Copy `movie_embeddings_float16.npy` to the project root

3. **Start the API Server**:
   ```bash
   python movie_api.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn movie_api:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Verify API is Running**:
   Visit `http://localhost:8000` - you should see a welcome message with movie count
   Visit `http://localhost:8000/docs` to see the interactive API documentation

### Frontend Setup

1. **Open the HTML File**:
   - Simply open `movie_explorer.html` in a modern web browser
   - Or serve it using a local web server:
     ```bash
     # Using Python's built-in server
     python -m http.server 3000
     ```

2. **Configure API URL** (if needed):
   - If your API is running on a different port or host, update the `CUSTOM_API_BASE_URL` variable in the HTML file
   - Default is set to `http://localhost:8000`

## API Endpoints

### Custom Movie API

- `GET /` - API status and movie count
- `GET /health` - Health check with data loading status
- `GET /search?query={movie_title}` - Search movies by title
- `GET /recommend?query={movie_title}` - Get recommendations for a movie
- `GET /movie/{movie_id}` - Get detailed movie information
- `GET /random?count={number}` - Get random movies
- `GET /genres` - Get all available genres
- `GET /movies/by_genre?genre={genre_name}` - Get movies by genre
- `GET /tmdb_info/{movie_id}` - Get TMDB poster and trailer URLs

## How It Works

### Search Flow
1. User types a movie title in the search box
2. Frontend calls your custom `/search` API endpoint
3. Your API returns matching movies from your dataset
4. Frontend enriches each result with TMDB data (posters, trailers, etc.)
5. Results are displayed with beautiful movie cards

### Recommendation Flow
1. When a user searches for a movie, the frontend automatically gets recommendations
2. Frontend calls your custom `/recommend` API endpoint with the first search result
3. Your ML model returns similar movies based on embeddings
4. Frontend enriches recommendations with TMDB data
5. Recommendations are displayed in a separate section

### Movie Details Flow
1. User clicks "Details" on any movie card
2. Frontend calls TMDB API directly for full movie details
3. Modal displays comprehensive information including genres, runtime, overview, and trailer

## Data Sources

### Your Custom API Provides:
- Movie search functionality
- AI-powered recommendations using your embeddings
- Basic movie metadata from your cleaned dataset
- Genre filtering and random movie selection

### TMDB API Provides:
- High-quality movie posters and backdrops
- Movie trailers from YouTube
- Additional metadata (budget, revenue, production companies)
- Trending, top-rated, and now-playing movies for homepage sections

## Customization

### Updating the API URL
If you deploy your API to a different server, update the `CUSTOM_API_BASE_URL` in `movie_explorer.html`:

```javascript
const CUSTOM_API_BASE_URL = "https://your-api-domain.com"; // Update this
```

### Styling
The frontend uses Tailwind CSS and custom CSS variables. You can easily customize:
- Colors by modifying the gradient classes
- Animations by updating the custom keyframes
- Layout by modifying the grid classes

### Adding More Endpoints
You can extend the API by adding new endpoints in `movie_api.py`. The frontend can then consume these endpoints to provide additional functionality.

## Troubleshooting

### Common Issues

1. **API not connecting**: 
   - Ensure the backend is running on `http://localhost:8000`
   - Check browser console for CORS errors
   - Verify the `CUSTOM_API_BASE_URL` in the frontend

2. **No movie data**: 
   - Ensure `final_movies_cleaned.feather` and `movie_embeddings_float16.npy` are in the project root
   - Check the API logs for data loading errors
   - Visit `/health` endpoint to verify data is loaded

3. **TMDB images not loading**:
   - TMDB API key should be working (one is provided)
   - Check network connectivity
   - Some movies might not have posters in TMDB

4. **Search not working**:
   - Verify your movie dataset has a 'title' column
   - Check API logs for search errors
   - Try different search terms

### Performance Tips

- The API loads all data into memory on startup for fast responses
- Movie embeddings are stored in float16 format to reduce memory usage
- Frontend implements intelligent caching for TMDB requests
- Consider using a production ASGI server like Gunicorn for deployment

## Production Deployment

For production deployment:

1. **Backend**:
   ```bash
   pip install gunicorn
   gunicorn movie_api:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Frontend**:
   - Serve the HTML file using Nginx or Apache
   - Update API URLs to production endpoints
   - Enable HTTPS

3. **Security**:
   - Replace CORS `allow_origins=["*"]` with specific domains
   - Use environment variables for API keys
   - Implement rate limiting

## License

This project is provided as-is for educational and development purposes.