from fastapi import APIRouter, HTTPException
import asyncio
from models.request_models import SearchRequest
from services.tmdb_service import TMDBService
from services.streaming_service import StreamingService
from config.constants import MESSAGES

router = APIRouter()

async def global_search_with_ott_filtering(query: str):
    """Perform global search and filter for OTT availability"""
    print(f"Starting global search for: {query}")
    
    # Search both movies and TV shows in parallel
    movies_task = TMDBService.search_movies_globally(query)
    tv_shows_task = TMDBService.search_tv_shows_globally(query)
    
    movies, tv_shows = await asyncio.gather(movies_task, tv_shows_task)
    
    all_content = []
    all_content.extend(movies)
    all_content.extend(tv_shows)
    
    print(f"Global search found {len(all_content)} total items before OTT filtering")
    
    # Check OTT availability for search results
    movies_to_check = [item for item in all_content if item['content_type'] == 'movie']
    tv_shows_to_check = [item for item in all_content if item['content_type'] == 'tv']
    
    ott_content = []
    
    if movies_to_check:
        print(f"Checking OTT availability for {len(movies_to_check)} searched movies...")
        movie_ott = await StreamingService.get_streaming_providers_batch(movies_to_check, 'movie')
        ott_content.extend(movie_ott)
        print(f"Found {len(movie_ott)} movies with OTT availability")
    
    if tv_shows_to_check:
        print(f"Checking OTT availability for {len(tv_shows_to_check)} searched TV shows...")
        tv_ott = await StreamingService.get_streaming_providers_batch(tv_shows_to_check, 'tv')
        ott_content.extend(tv_ott)
        print(f"Found {len(tv_ott)} TV shows with OTT availability")
    
    # Sort by rating and popularity
    ott_content.sort(key=lambda x: (x.get('rating', 0), x.get('release_date', '')), reverse=True)
    
    print(f"Global search returning {len(ott_content)} OTT-available items")
    return ott_content

@router.post("/search")
async def global_search(request: SearchRequest):
    """Global search endpoint - searches across all content regardless of filters"""
    try:
        query = request.query.strip()
        
        if len(query) < 2:
            return {
                "content": [],
                "total": 0,
                "message": MESSAGES['SEARCH_TOO_SHORT']
            }
        
        print(f"Global search request: '{query}'")
        
        # Perform global search with OTT filtering
        content = await global_search_with_ott_filtering(query)
        
        print(f"Global search returning {len(content)} results")
        
        return {
            "content": content[:20],  # Limit to top 20 results
            "total": len(content),
            "query": query,
            "search_type": "global",
            "content_breakdown": {
                "movies": len([item for item in content if item['content_type'] == 'movie']),
                "tv_shows": len([item for item in content if item['content_type'] == 'tv'])
            }
        }
        
    except Exception as e:
        print(f"Error in global_search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
