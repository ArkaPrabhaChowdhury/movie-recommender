from fastapi import APIRouter, HTTPException
import asyncio
from models.request_models import SearchRequest
from services.tmdb_service import TMDBService
from services.streaming_service import StreamingService
from services.user_preference_service import UserPreferenceService
from config.constants import MESSAGES

router = APIRouter()
_pref_service = UserPreferenceService()

async def global_search_with_ott_filtering(query: str, user_id: str = None):
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
            print(f"⚠️ Subscription filter error in search: {sub_err}")

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
        content = await global_search_with_ott_filtering(query, request.user_id)
        
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
