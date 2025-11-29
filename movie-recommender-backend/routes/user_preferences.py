from fastapi import APIRouter, HTTPException
from models.user_models import ContentInteraction, RecommendationRequest
from services.user_preference_service import UserPreferenceService
from services.recommendation_engine import RecommendationEngine
from services.tmdb_service import TMDBService
from datetime import datetime
import asyncio

router = APIRouter()
preference_service = UserPreferenceService()
recommendation_engine = RecommendationEngine()

@router.post("/user/interaction")
async def record_user_interaction(interaction: ContentInteraction):
    """Record user interaction (like, dislike, watchlist, watched)"""
    try:
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
async def get_user_profile(user_id: str):
    """Get user profile and preferences"""
    try:
        profile = await preference_service.get_user_profile(user_id)
        interactions = await preference_service.get_user_interactions(user_id)
        
        # Get detailed stats
        liked_interactions = [item for item in interactions if item["action"] == "liked"]
        watchlist_interactions = [item for item in interactions if item["action"] == "watchlisted"]
        watched_interactions = [item for item in interactions if item["action"] == "watched"]
        
        # Calculate genre distribution
        genre_distribution = {}
        for interaction in liked_interactions:
            for genre in interaction.get("genres", []):
                genre_distribution[genre] = genre_distribution.get(genre, 0) + 1
        
        return {
            "profile": profile,
            "stats": {
                "total_interactions": len(interactions),
                "liked_content": len(liked_interactions),
                "watchlist_items": len(watchlist_interactions),
                "watched_items": len(watched_interactions),
                "genre_distribution": genre_distribution
            },
            "recent_activity": interactions[-10:],  # Last 10 interactions
            "liked_content": liked_interactions[-5:]  # Last 5 liked items for display
        }
        
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/recommendations")
async def get_personalized_recommendations(request: RecommendationRequest):
    """Get AI-powered personalized recommendations using the recommendation engine"""
    try:
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
async def get_user_liked_content(user_id: str):
    """Get all content liked by the user"""
    try:
        interactions = await preference_service.get_user_interactions(user_id, action="liked")
        
        return {
            "liked_content": interactions,
            "total_count": len(interactions)
        }
        
    except Exception as e:
        print(f"❌ Error getting liked content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/watchlist")
async def get_user_watchlist(user_id: str):
    """Get user's watchlist"""
    try:
        interactions = await preference_service.get_user_interactions(user_id, action="watchlisted")
        
        return {
            "watchlist": interactions,
            "total_count": len(interactions)
        }
        
    except Exception as e:
        print(f"❌ Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/{user_id}/interaction/{content_id}")
async def remove_user_interaction(user_id: str, content_id: int, content_type: str):
    """Remove a specific user interaction"""
    try:
        preferences_data = preference_service._load_data(preference_service.preferences_file)
        
        if user_id in preferences_data:
            # Remove the interaction
            original_count = len(preferences_data[user_id])
            preferences_data[user_id] = [
                item for item in preferences_data[user_id]
                if not (item["content_id"] == content_id and item["content_type"] == content_type)
            ]
            removed_count = original_count - len(preferences_data[user_id])
            
            if removed_count > 0:
                preference_service._save_data(preference_service.preferences_file, preferences_data)
                await preference_service._update_user_profile(user_id)
                
                return {
                    "status": "success",
                    "message": f"Removed interaction for content ID {content_id}",
                    "removed_count": removed_count
                }
            else:
                return {
                    "status": "not_found",
                    "message": "No interaction found to remove"
                }
        else:
            return {
                "status": "not_found", 
                "message": "User not found"
            }
            
    except Exception as e:
        print(f"❌ Error removing interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
