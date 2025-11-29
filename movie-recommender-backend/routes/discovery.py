from fastapi import APIRouter, HTTPException
import asyncio
from models.request_models import DiscoverRequest
from services.tmdb_service import TMDBService
from services.streaming_service import StreamingService
from config.constants import LANGUAGE_MAP, get_date_range, get_genre_id, DEFAULTS
from utils.helpers import extract_filters_from_prompt

router = APIRouter()

async def get_content_with_date_filtering(language_code: str, content_type: str, genre: str, release_period: str):
    """Get content with date range filtering and correct genre IDs"""
    date_from, date_to = get_date_range(release_period)
    print(f"Date filtering: {date_from} to {date_to} (period: {release_period})")
    
    all_content = []
    
    # Handle content type properly with correct genre IDs
    if content_type == 'both':
        print("Fetching BOTH movies and TV shows with date filtering...")
        
        movies_task = TMDBService.fetch_movies(language_code, genre, date_from, date_to)
        tv_shows_task = TMDBService.fetch_tv_shows(language_code, genre, date_from, date_to)
        
        movies, tv_shows = await asyncio.gather(movies_task, tv_shows_task)
        
        print(f"Fetched {len(movies)} movies and {len(tv_shows)} TV shows")
        all_content.extend(movies)
        all_content.extend(tv_shows)
        
    elif content_type == 'movie':
        print("Fetching ONLY movies with date filtering...")
        movies = await TMDBService.fetch_movies(language_code, genre, date_from, date_to)
        all_content.extend(movies)
        
    elif content_type == 'tv':
        print("Fetching ONLY TV shows with date filtering...")
        tv_shows = await TMDBService.fetch_tv_shows(language_code, genre, date_from, date_to)
        all_content.extend(tv_shows)
    
    print(f"Total content found before OTT filtering: {len(all_content)}")
    
    # Check OTT availability
    movies = [item for item in all_content if item['content_type'] == 'movie']
    tv_shows = [item for item in all_content if item['content_type'] == 'tv']
    
    ott_content = []
    
    if movies:
        print(f"Checking OTT availability for {len(movies)} movies...")
        movie_ott = await StreamingService.get_streaming_providers_batch(movies, 'movie')
        ott_content.extend(movie_ott)
        print(f"Found {len(movie_ott)} movies with OTT availability")
    
    if tv_shows:
        print(f"Checking OTT availability for {len(tv_shows)} TV shows...")
        tv_ott = await StreamingService.get_streaming_providers_batch(tv_shows, 'tv')
        ott_content.extend(tv_ott)
        print(f"Found {len(tv_ott)} TV shows with OTT availability")
    
    # Sort by release date (newest first) and rating
    ott_content.sort(key=lambda x: (x.get('release_date', ''), x.get('rating', 0)), reverse=True)
    
    print(f"Final OTT content: {len(ott_content)} items")
    return ott_content

@router.post("/discover")
async def discover_content(request: DiscoverRequest):
    """Complete endpoint with correct genre IDs for movies and TV shows"""
    try:
        print(f"Received request: {request.prompt}")
        
        # Use explicit parameters if provided
        if request.genre and request.language and request.content_type:
            genre = request.genre
            language = request.language
            content_type = request.content_type
            release_period = request.release_period or DEFAULTS['RELEASE_PERIOD']
            print(f"Using explicit parameters - Genre: {genre}, Language: {language}, Content: {content_type}, Period: {release_period}")
        else:
            # Fallback to extraction
            genre, language, content_type = extract_filters_from_prompt(request.prompt)
            release_period = DEFAULTS['RELEASE_PERIOD']
            print(f"Extracted from prompt - Genre: {genre}, Language: {language}, Content: {content_type}")
        
        # Get language code
        language_code = LANGUAGE_MAP.get(language, 'hi')
        
        # Get genre IDs for debugging
        movie_genre_id = get_genre_id(genre, 'movie')
        tv_genre_id = get_genre_id(genre, 'tv')
        
        print(f"Using language code: {language_code}")
        print(f"Movie genre ID: {movie_genre_id}, TV genre ID: {tv_genre_id}")
        
        # Get content with date filtering and correct genre IDs
        content = await get_content_with_date_filtering(language_code, content_type, genre, release_period)
        
        print(f"Returning {len(content)} OTT-available items")
        
        return {
            "content": content[:25],
            "total": len(content),
            "detected": {
                "genre": genre,
                "language": language,
                "content_type": content_type,
                "release_period": release_period
            },
            "debug": {
                "language_code": language_code,
                "movie_genre_id": movie_genre_id,
                "tv_genre_id": tv_genre_id,
                "date_range": get_date_range(release_period),
                "explicit_params": bool(request.genre and request.language and request.content_type),
                "content_breakdown": {
                    "movies": len([item for item in content if item['content_type'] == 'movie']),
                    "tv_shows": len([item for item in content if item['content_type'] == 'tv'])
                }
            }
        }
        
    except Exception as e:
        print(f"Error in discover_content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
