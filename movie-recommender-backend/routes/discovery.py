from fastapi import APIRouter, HTTPException
import asyncio
from models.request_models import DiscoverRequest
from services.tmdb_service import TMDBService
from services.streaming_service import StreamingService
from services.user_preference_service import UserPreferenceService
from config.constants import LANGUAGE_MAP, get_date_range, get_genre_id, DEFAULTS
from utils.helpers import extract_filters_from_prompt

router = APIRouter()
_pref_service = UserPreferenceService()

async def get_content_with_date_filtering(
    language_code: str, content_type: str, genre: str,
    release_period: str, sort_by: str = 'rating',
    page: int = 1, user_id: str = None
):
    """Get content with date range filtering and correct genre IDs"""
    date_from, date_to = get_date_range(release_period)
    print(f"Date filtering: {date_from} to {date_to} (period: {release_period})")
    
    all_content = []
    
    # Handle content type properly with correct genre IDs
    if content_type == 'both':
        print("Fetching BOTH movies and TV shows with date filtering...")
        
        movies_task = TMDBService.fetch_movies(language_code, genre, date_from, date_to, page)
        tv_shows_task = TMDBService.fetch_tv_shows(language_code, genre, date_from, date_to, page)
        
        movies, tv_shows = await asyncio.gather(movies_task, tv_shows_task)
        
        print(f"Fetched {len(movies)} movies and {len(tv_shows)} TV shows")
        all_content.extend(movies)
        all_content.extend(tv_shows)
        
    elif content_type == 'movie':
        print("Fetching ONLY movies with date filtering...")
        movies = await TMDBService.fetch_movies(language_code, genre, date_from, date_to, page)
        all_content.extend(movies)
        
    elif content_type == 'tv':
        print("Fetching ONLY TV shows with date filtering...")
        tv_shows = await TMDBService.fetch_tv_shows(language_code, genre, date_from, date_to, page)
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
    
    # Mandatory filter: Only show content available on OTT in India
    before_filter = len(ott_content)
    ott_content = [item for item in ott_content if item.get("streaming", {}).get("platform_found")]
    print(f"🛡️ OTT Filter: {before_filter} -> {len(ott_content)} items available on streaming")

    # --- Subscription filter (Sub-filter of OTT) -----------------------
    if user_id:
        try:
            profile_data = await _pref_service.get_user_profile(user_id)
            sub_ids = set(profile_data.get("subscribed_providers", []))
            if sub_ids:
                filtered_content = []
                for item in ott_content:
                    all_platforms = item.get("streaming", {}).get("available_on", [])
                    user_platforms = [
                        p for p in all_platforms 
                        if p.get("id") in sub_ids and not p.get("is_rent")
                    ]
                    if user_platforms:
                        new_item = item.copy()
                        new_item["streaming"] = item["streaming"].copy()
                        new_item["streaming"]["available_on"] = user_platforms
                        filtered_content.append(new_item)
                
                print(f"🎯 Subscription filter: {len(ott_content)} → {len(filtered_content)} items")
                ott_content = filtered_content
        except Exception as sub_err:
            print(f"⚠️ Subscription filter error: {sub_err}")

    # Sort based on parameter
    if sort_by == 'rating':
        print("Sorting by rating (highest first)...")
        ott_content.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == 'release_date':
        print("Sorting by release date (newest first)...")
        ott_content.sort(key=lambda x: x.get('release_date', ''), reverse=True)
    else:
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
            genre = request.genre.lower()
            language = request.language.lower()
            content_type = request.content_type.lower()
            release_period = request.release_period or DEFAULTS['RELEASE_PERIOD']
            print(f"Using explicit parameters - Genre: {genre}, Language: {language}, Content: {content_type}, Period: {release_period}")
        else:
            # Fallback to extraction
            genre, language, content_type = extract_filters_from_prompt(request.prompt)
            genre = genre.lower()
            language = language.lower()
            release_period = DEFAULTS['RELEASE_PERIOD']
            print(f"Extracted from prompt - Genre: {genre}, Language: {language}, Content: {content_type}")
        
        # Get language code safely, default to None (Any) if not found
        language_code = LANGUAGE_MAP.get(language, None)
        
        # Get genre IDs for debugging
        movie_genre_id = get_genre_id(genre, 'movie')
        tv_genre_id = get_genre_id(genre, 'tv')
        
        print(f"Using language code: {language_code}")
        print(f"Movie genre ID: {movie_genre_id}, TV genre ID: {tv_genre_id}")
        
        # Get content with date filtering and correct genre IDs
        content = await get_content_with_date_filtering(
            language_code,
            content_type,
            genre,
            release_period,
            request.sort_by or 'rating',
            request.page or 1,
            request.user_id
        )
        
        print(f"Returning {len(content)} OTT-available items")
        
        return {
            "content": content,
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
