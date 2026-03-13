"""
Backend Configuration Constants
"""

from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

# Load environment variables explicitly from the backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    load_dotenv() # Fallback to default behavior
    print(f"ℹ️  No .env found at {env_path}, using system environment variables")

# API Configuration
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '120b28e3a6abbe3a6837a90885401cb8')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
TMDB_API_URL = os.getenv('TMDB_API_URL', 'https://api.themoviedb.org/3')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Debug prints (sanitized)
if not SUPABASE_URL: print("⚠️ SUPABASE_URL is missing in environment.")
if not SUPABASE_KEY: print("⚠️ SUPABASE_KEY is missing in environment.")

# Server Configuration
SERVER_CONFIG = {
    'host': os.getenv('HOST', '0.0.0.0'),      # Changed default to 0.0.0.0 for container support
    'port': int(os.getenv('PORT', 8000)),
    'reload': os.getenv('RELOAD', 'True').lower() == 'true',
    'title': 'Movie Recommender API - Complete with Global Search'
}

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"  # Allow all origins for Vercel deployment
]

# Content Mappings - FIXED: Separate genre maps for movies and TV shows
MOVIE_GENRE_MAP = {
    'action': 28,
    'adventure': 12,
    'animation': 16,
    'comedy': 35,
    'crime': 80,
    'documentary': 99,
    'drama': 18,
    'family': 10751,
    'fantasy': 14,
    'history': 36,
    'horror': 27,
    'music': 10402,
    'mystery': 9648,
    'romance': 10749,
    'sci-fi': 878,
    'science fiction': 878,
    'thriller': 53,
    'war': 10752,
    'western': 37,
    'tv movie': 10770
}

TV_GENRE_MAP = {
    'action': 10759,  # Action & Adventure
    'adventure': 10759,
    'animation': 16,
    'comedy': 35,
    'crime': 80,
    'documentary': 99,
    'drama': 18,
    'family': 10751,
    'fantasy': 10765,
    'sci-fi': 10765,
    'science fiction': 10765,
    'mystery': 9648,
    'western': 37,
    'kids': 10762,
    'news': 10763,
    'reality': 10764,
    'soap': 10766,
    'talk': 10767,
    'war': 10768,
    'politics': 10768,
    'romance': 18, # Fallback to Drama for TV (TMDB doesn't have 10749 for TV)
}

# Combined mapping for easy lookup (defaults to movie genres)
GENRE_MAP = MOVIE_GENRE_MAP.copy()

def get_genre_id(genre: str, content_type: str) -> int:
    """Get genre ID based on content type (movie or tv)"""
    genre_lower = genre.lower()
    
    if genre_lower == 'all':
        return None
        
    if content_type == 'tv':
        # Special case: Romance doesn't exist for TV in TMDB, usually mapped to Soap or Drama
        if genre_lower == 'romance':
            return 18 # Drama
        return TV_GENRE_MAP.get(genre_lower, MOVIE_GENRE_MAP.get(genre_lower, 18))
    else:  # movie or both
        return MOVIE_GENRE_MAP.get(genre_lower, 28)

LANGUAGE_MAP = {
    'any': None, 'Any': None, 'ANY': None,
    'hindi': 'hi', 'Hindi': 'hi',
    'english': 'en', 'English': 'en',
    'tamil': 'ta', 'Tamil': 'ta',
    'telugu': 'te', 'Telugu': 'te',
    'malayalam': 'ml', 'kannada': 'kn', 'bengali': 'bn', 'marathi': 'mr',
    'gujarati': 'gu', 'punjabi': 'pa', 'urdu': 'ur',
    'hi': 'hi', 'en': 'en', 'ta': 'ta', 'te': 'te', 'ml': 'ml', 'kn': 'kn', 'bn': 'bn', 'mr': 'mr', 'gu': 'gu', 'pa': 'pa', 'ur': 'ur'
}

# OTT Platform Configuration
INDIAN_OTT_PLATFORMS = {
    8: {"name": "Netflix", "logo": "netflix.png", "color": "#E50914"},
    119: {"name": "Amazon Prime", "logo": "prime.png", "color": "#00A8E1"},
    377: {"name": "Disney+ Hotstar", "logo": "hotstar.png", "color": "#1F80E0"},
    315: {"name": "Hotstar", "logo": "hotstar.png", "color": "#1F80E0"},
    232: {"name": "Jio Cinema", "logo": "jiocinema.png", "color": "#8B2874"},
    282: {"name": "Sony LIV", "logo": "sonyliv.png", "color": "#0066CC"},
    233: {"name": "Sony LIV", "logo": "sonyliv.png", "color": "#0066CC"},
    251: {"name": "Zee5", "logo": "zee5.png", "color": "#6C2483"},
    237: {"name": "Voot", "logo": "voot.png", "color": "#FF6600"},
    283: {"name": "Eros Now", "logo": "erosnow.png", "color": "#FF0000"},
    531: {"name": "Alt Balaji", "logo": "altbalaji.png", "color": "#FF8C00"},
    484: {"name": "Apple TV+", "logo": "appletv.png", "color": "#000000"},
    350: {"name": "Apple TV", "logo": "appletv.png", "color": "#000000"},
    2: {"name": "Apple iTunes", "logo": "apple.png", "color": "#A855F7"},
    3: {"name": "Google Play", "logo": "google.png", "color": "#4285F4"},
    2100: {"name": "Amazon Prime (Ads)", "logo": "prime.png", "color": "#00A8E1"},
}

# API Limits and Timeouts
API_CONFIG = {
    'TIMEOUT': 30.0,
    'MAX_RESULTS_PER_TYPE': 50,
    'MAX_STREAMING_PLATFORMS': 4,
    'MAX_SEARCH_RESULTS': 15,
    'MIN_VOTE_COUNT': {
        'POPULAR': 5,
        'RECENT': 0,
        'SEARCH': 0
    }
}

# Date Range Configuration
def get_date_range(release_period: str):
    """Calculate date range based on release period"""
    today = datetime.now()
    
    date_ranges = {
        '6months': timedelta(days=180),
        '1year': timedelta(days=365),
        '2years': timedelta(days=730),
        '3years': timedelta(days=1095)
    }
    
    if release_period in date_ranges:
        start_date = today - date_ranges[release_period]
    else:  # 'all' or any other value
        start_date = datetime(2000, 1, 1)  # Very old date for "all time"
    
    # End date slightly in the future to catch brand new releases
    end_date = today + timedelta(days=7)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

# Default Values
DEFAULTS = {
    'GENRE': 'all',
    'LANGUAGE': 'any', 
    'CONTENT_TYPE': 'both',
    'RELEASE_PERIOD': '6months'
}

# Response Messages
MESSAGES = {
    'API_RUNNING': 'Movie Recommender API - Complete with Global Search',
    'HEALTH_OK': 'Complete OTT API with global search is working correctly',
    'SEARCH_TOO_SHORT': 'Query too short. Please enter at least 2 characters.',
    'NO_CONTENT_FOUND': 'No OTT content found. Try different filters.',
    'SEARCH_NO_RESULTS': 'No OTT content found for search. Try a different search term.'
}

# Content Processing Keywords
CONTENT_TYPE_KEYWORDS = {
    'MOVIE': ['movie', 'movies', 'film', 'films'],
    'TV': ['show', 'shows', 'tv', 'series', 'television']
}

# Image Configuration
IMAGE_CONFIG = {
    'TMDB_BASE_URL': 'https://image.tmdb.org/t/p/w500',
    'POSTER_SIZE': 'w500',
    'REQUIRE_POSTER': True  # Only include content with posters in search results
}
