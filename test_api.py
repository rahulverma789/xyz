#!/usr/bin/env python3
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"\n{'='*50}")
        print(f"Testing: {method} {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Returned {len(result)} items")
            if result:
                print(f"Sample item keys: {list(result[0].keys())}")
                if 'title' in result[0]:
                    print(f"Sample titles: {[item.get('title', 'N/A') for item in result[:3]]}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("Testing Movie Recommendation API")
    
    # Test basic endpoints
    test_endpoint("")  # Root
    test_endpoint("trending")
    test_endpoint("top-rated")
    test_endpoint("now-playing")
    test_endpoint("search?query=batman")
    
    # Test personalized recommendations
    sample_profile = {
        "user_id": "test_user",
        "age": 25,
        "safe_mode": True,
        "language": ["en"],
        "mood": "happy",
        "region": "US",
        "watchlist": [],
        "history": [],
        "liked_movies": [],
        "disliked_movies": []
    }
    
    test_endpoint("personalized-recommendations", "POST", sample_profile)

if __name__ == "__main__":
    main()