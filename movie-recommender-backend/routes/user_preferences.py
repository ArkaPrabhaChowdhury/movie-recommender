from fastapi import APIRouter, HTTPException, Header, Request
from typing import List
from models.user_models import ContentInteraction, RecommendationRequest
from services.user_preference_service import UserPreferenceService
from services.recommendation_engine import RecommendationEngine
from services.tmdb_service import TMDBService
from datetime import datetime
import asyncio
from typing import Optional
from utils.auth import authenticated_user, assert_owner
from utils.rate_limit import enforce_rate_limit

router = APIRouter()
preference_service = UserPreferenceService()
recommendation_engine = RecommendationEngine()

@router.post("/user/interaction")
async def record_user_interaction(interaction: ContentInteraction, authorization: Optional[str] = Header(None), request: Request = None):
    """Record user interaction (like, dislike, watchlist, watched)"""
    try:
        authenticated_id = authenticated_user(authorization)
        assert_owner(interaction.user_id, authenticated_id)
        if request:
            enforce_rate_limit(request)
        if interaction.action == "watching" and interaction.content_type != "tv":
            raise HTTPException(status_code=400, detail="Watching notifications are available for TV shows only")
        print(f"📝 Recording interaction: {interaction.action} for '{interaction.title}' by {interaction.user_id}")
        
        success = await preference_service.record_interaction(interaction)
        
        if success:
            return {
                "status": "success",
                "message": f"Recorded {interaction.action} for '{interaction.title}'",
                "user_id": interaction.user_id,
                "content_data": {
                    "id": interaction.content_id,
                    "title": interaction.title,
                    "genres": interaction.genres,
                    "language": interaction.language
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to record interaction")
            
    except Exception as e:
        print(f"❌ Error in record_user_interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str, authorization: Optional[str] = Header(None)):
    """Get user profile and preferences"""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        profile = await preference_service.get_user_profile(user_id)
        interactions = await preference_service.get_user_interactions(user_id)
        
        # Get detailed stats
        liked_interactions = [item for item in interactions if item["action"] == "liked"]
        watchlist_interactions = [item for item in interactions if item["action"] == "watchlisted"]
        watched_interactions = [item for item in interactions if item["action"] == "watched"]
        watching_interactions = [item for item in interactions if item["action"] == "watching"]
        
        # Calculate genre distribution
        genre_distribution = {}
        for interaction in liked_interactions:
            for genre in interaction.get("genres", []):
                genre_distribution[genre] = genre_distribution.get(genre, 0) + 1
        
        # Map all actions per content item (some items might have multiple actions like 'liked' and 'watched')
        interaction_map = {}
        for item in reversed(interactions): # Oldest to newest
            key = f"{item['content_type']}_{item['content_id']}"
            if key not in interaction_map:
                interaction_map[key] = []
            if item['action'] not in interaction_map[key]:
                interaction_map[key].append(item['action'])
                
        return {
            "profile": profile,
            "stats": {
                "total_interactions": len(interactions),
                "liked_content": len(liked_interactions),
                "watchlist_items": len(watchlist_interactions),
                "watched_items": len(watched_interactions),
                "watching_items": len(watching_interactions),
                "genre_distribution": genre_distribution
            },
            "recent_activity": interactions[:10],  # Newest 10 interactions
            "liked_content": liked_interactions[:5],  # Newest 5 liked items
            "interaction_map": interaction_map
        }
        
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/recommendations")
async def get_personalized_recommendations(request: RecommendationRequest, authorization: Optional[str] = Header(None)):
    """Get AI-powered personalized recommendations using the recommendation engine"""
    try:
        assert_owner(request.user_id, authenticated_user(authorization))
        user_id = request.user_id
        print(f"🎯 Getting personalized recommendations for user: {user_id}")
        
        # Use the new recommendation engine
        recommendation_result = await recommendation_engine.get_personalized_recommendations(
            user_id, request.limit
        )
        
        recommendations = recommendation_result.get("recommendations", [])
        algorithm_used = recommendation_result.get("algorithm", "unknown")
        personalization_level = recommendation_result.get("personalization_level", "none")
        
        print(f"✅ Generated {len(recommendations)} recommendations using {algorithm_used} algorithm")
        print(f"📊 Personalization level: {personalization_level}")
        
        # Log recommendation reasons for debugging
        if recommendations:
            sample_reasons = [rec.get("recommendation_reason", "No reason") for rec in recommendations[:3]]
            print(f"🎬 Sample recommendation reasons: {sample_reasons}")
        
        return {
            "recommendations": recommendations,
            "algorithm": algorithm_used,
            "personalization_level": personalization_level,
            "user_stats": recommendation_result.get("user_stats", {}),
            "total_found": len(recommendations)
        }
        
    except Exception as e:
        print(f"❌ Error getting personalized recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/liked")
async def get_user_liked_content(user_id: str, authorization: Optional[str] = Header(None)):
    """Get all content liked by the user"""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        interactions = await preference_service.get_user_interactions(user_id, action="liked")
        
        return {
            "liked_content": interactions,
            "total_count": len(interactions)
        }
        
    except Exception as e:
        print(f"❌ Error getting liked content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/watchlist")
async def get_user_watchlist(user_id: str, authorization: Optional[str] = Header(None)):
    """Get user's watchlist"""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        interactions = await preference_service.get_user_interactions(user_id, action="watchlisted")
        
        return {
            "watchlist": interactions,
            "total_count": len(interactions)
        }
        
    except Exception as e:
        print(f"❌ Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/history")
async def get_user_history(user_id: str, authorization: Optional[str] = Header(None)):
    """Get user's watch history"""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        interactions = await preference_service.get_user_interactions(user_id)
        
        return {
            "history": interactions,
            "total_count": len(interactions)
        }
        
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/data-export")
async def export_user_data(user_id: str, authorization: Optional[str] = Header(None)):
    assert_owner(user_id, authenticated_user(authorization))
    return await preference_service.export_user_data(user_id)

@router.delete("/user/{user_id}/data")
async def delete_user_data(user_id: str, authorization: Optional[str] = Header(None)):
    assert_owner(user_id, authenticated_user(authorization))
    if not await preference_service.delete_user_data(user_id):
        raise HTTPException(status_code=500, detail="Unable to delete user data")
    return {"status": "deleted", "user_id": user_id}

@router.delete("/user/{user_id}/interaction/{content_id}")
async def remove_user_interaction(user_id: str, content_id: int, content_type: str, action: str = None, authorization: Optional[str] = Header(None)):
    """Remove a specific user interaction from Supabase"""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        success = await preference_service.remove_interaction(user_id, content_id, content_type, action)
        
        if success:
            return {
                "status": "success",
                "message": f"Removed interaction for content ID {content_id}"
            }
        else:
            return {
                "status": "not_found",
                "message": "No interaction found to remove or user not found"
            }
            
    except Exception as e:
        print(f"❌ Error removing interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Watch Providers ──────────────────────────────────────────────────────────

@router.get("/watch/providers")
async def get_watch_providers(region: str = "IN"):
    """Return the list of streaming platforms available in the given region."""
    try:
        providers = await TMDBService.get_watch_providers(region)
        return providers
    except Exception as e:
        print(f"❌ Error fetching providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/subscriptions")
async def save_user_subscriptions(user_id: str, provider_ids: List[int], authorization: Optional[str] = Header(None)):
    """Save the OTT platforms a user is subscribed to."""
    try:
        assert_owner(user_id, authenticated_user(authorization))
        success = await preference_service.save_user_subscriptions(user_id, provider_ids)
        if success:
            return {"status": "success", "saved": len(provider_ids)}
        raise HTTPException(status_code=500, detail="Failed to save subscriptions")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
