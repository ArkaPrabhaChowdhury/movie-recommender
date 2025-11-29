import json
import os
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from services.user_preference_service import UserPreferenceService
from services.tmdb_service import TMDBService
from routes.discovery import get_content_with_date_filtering
from config.constants import LANGUAGE_MAP
import asyncio

class RecommendationEngine:
    def __init__(self):
        self.user_service = UserPreferenceService()
        
    async def get_personalized_recommendations(self, user_id: str, limit: int = 15) -> Dict:
        """Main recommendation engine - combines multiple algorithms"""
        
        try:
            # Get user context
            context = await self.user_service.get_recommendation_context(user_id)
            
            if not context["has_preferences"]:
                return await self._get_popular_recommendations(limit)
            
            # Run multiple recommendation algorithms
            recommendations = await self._run_recommendation_algorithms(context, limit)
            
            return {
                "recommendations": recommendations,
                "algorithm": "hybrid_personalized",
                "personalization_level": self._get_personalization_level(context),
                "user_stats": {
                    "total_interactions": context["total_interactions"],
                    "total_liked": context["profile"].get("total_liked", 0),
                    "top_genres": context["profile"].get("preferred_genres", [])[:3]
                }
            }
            
        except Exception as e:
            print(f"❌ Error in recommendation engine: {e}")
            return await self._get_popular_recommendations(limit)
    
    async def _run_recommendation_algorithms(self, context: Dict, limit: int) -> List[Dict]:
        """Run multiple recommendation algorithms and combine results"""
        
        # Algorithm 1: Collaborative filtering (similar users)
        collaborative_recs = await self._collaborative_filtering(context, limit // 3)
        
        # Algorithm 2: Content-based filtering (similar content)
        content_based_recs = await self._content_based_filtering(context, limit // 3)
        
        # Algorithm 3: Popularity-based with user preferences
        popular_recs = await self._popularity_based_filtering(context, limit // 3)
        
        # Combine and deduplicate
        all_recommendations = collaborative_recs + content_based_recs + popular_recs
        
        # Remove duplicates
        seen_ids = set()
        unique_recommendations = []
        for rec in all_recommendations:
            rec_id = f"{rec['id']}_{rec['content_type']}"
            if rec_id not in seen_ids:
                seen_ids.add(rec_id)
                unique_recommendations.append(rec)
        
        # Sort by personalization score
        scored_recommendations = []
        for rec in unique_recommendations:
            score = self._calculate_personalization_score(rec, context)
            rec['personalization_score'] = score
            scored_recommendations.append(rec)
        
        scored_recommendations.sort(key=lambda x: x['personalization_score'], reverse=True)
        
        return scored_recommendations[:limit]
    
    async def _collaborative_filtering(self, context: Dict, limit: int) -> List[Dict]:
        """Find content liked by users with similar preferences"""
        try:
            user_genres = set(context["profile"].get("preferred_genres", []))
            user_languages = set(context["profile"].get("preferred_languages", []))
            
            # Load all user preferences to find similar users
            preferences_data = self.user_service._load_data(self.user_service.preferences_file)
            profiles_data = self.user_service._load_data(self.user_service.profiles_file)
            
            similar_users = []
            current_user_id = context["profile"].get("user_id")
            
            for user_id, profile in profiles_data.items():
                if user_id == current_user_id:
                    continue
                
                other_genres = set(profile.get("preferred_genres", []))
                other_languages = set(profile.get("preferred_languages", []))
                
                # Calculate similarity score
                genre_similarity = len(user_genres & other_genres) / max(len(user_genres | other_genres), 1)
                language_similarity = len(user_languages & other_languages) / max(len(user_languages | other_languages), 1)
                
                overall_similarity = (genre_similarity + language_similarity) / 2
                
                if overall_similarity > 0.3:  # Threshold for similarity
                    similar_users.append((user_id, overall_similarity))
            
            # Get content liked by similar users
            collaborative_content = []
            for user_id, similarity in sorted(similar_users, key=lambda x: x[1], reverse=True)[:5]:
                user_interactions = preferences_data.get(user_id, [])
                liked_content = [item for item in user_interactions if item["action"] == "liked"]
                
                for liked in liked_content[-10:]:  # Recent liked content
                    collaborative_content.append({
                        "id": liked["content_id"],
                        "content_type": liked["content_type"],
                        "title": liked["title"],
                        "genres": liked.get("genres", []),
                        "language": liked.get("language", "en"),
                        "similarity_score": similarity,
                        "recommendation_reason": f"Users with similar taste liked this"
                    })
            
            return collaborative_content[:limit]
            
        except Exception as e:
            print(f"❌ Error in collaborative filtering: {e}")
            return []
    
    async def _content_based_filtering(self, context: Dict, limit: int) -> List[Dict]:
        """Recommend content similar to what user has liked"""
        try:
            recent_liked = context["recent_liked"]
            if not recent_liked:
                return []
            
            preferred_genres = context["profile"].get("preferred_genres", [])[:3]
            preferred_languages = context["profile"].get("preferred_languages", [])[:2]
            
            recommendations = []
            
            # Get content based on user's preferred genres and languages
            for genre in preferred_genres:
                for language in preferred_languages:
                    language_code = LANGUAGE_MAP.get(language, 'en')
                    
                    # Get content for this genre/language combination
                    genre_content = await get_content_with_date_filtering(
                        language_code, "both", genre, "2years"
                    )
                    
                    # Filter out already seen content
                    seen_content_ids = [item["content_id"] for item in recent_liked]
                    unseen_content = [
                        item for item in genre_content 
                        if item["id"] not in seen_content_ids
                    ]
                    
                    # Add recommendation reason
                    for item in unseen_content[:3]:  # Top 3 per genre/language
                        item["recommendation_reason"] = f"You like {genre} content in {language}"
                        item["content_score"] = item.get("rating", 0) * item.get("popularity", 1)
                        recommendations.append(item)
            
            # Sort by content score and return top results
            recommendations.sort(key=lambda x: x.get("content_score", 0), reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            print(f"❌ Error in content-based filtering: {e}")
            return []
    
    async def _popularity_based_filtering(self, context: Dict, limit: int) -> List[Dict]:
        """Recommend popular content filtered by user preferences"""
        try:
            preferred_genres = context["profile"].get("preferred_genres", [])
            preferred_languages = context["profile"].get("preferred_languages", [])
            
            if not preferred_genres or not preferred_languages:
                return []
            
            # Get popular content in user's preferred genres/languages
            primary_genre = preferred_genres[0]
            primary_language = preferred_languages[0]
            language_code = LANGUAGE_MAP.get(primary_language, 'en')
            
            popular_content = await get_content_with_date_filtering(
                language_code, "both", primary_genre, "6months"
            )
            
            # Filter and enhance with recommendation reasons
            filtered_content = []
            for item in popular_content:
                item["recommendation_reason"] = f"Popular {primary_genre} content in {primary_language}"
                item["popularity_score"] = item.get("rating", 0) * item.get("vote_count", 1) / 1000
                filtered_content.append(item)
            
            # Sort by popularity score
            filtered_content.sort(key=lambda x: x.get("popularity_score", 0), reverse=True)
            return filtered_content[:limit]
            
        except Exception as e:
            print(f"❌ Error in popularity-based filtering: {e}")
            return []
    
    def _calculate_personalization_score(self, content: Dict, context: Dict) -> float:
        """Calculate how well content matches user preferences"""
        score = content.get("rating", 0)  # Base score from TMDB rating
        
        # Boost for preferred genres
        content_genres = [g.lower() for g in content.get("genres", [])]
        preferred_genres = [g.lower() for g in context["profile"].get("preferred_genres", [])]
        
        genre_matches = len(set(content_genres) & set(preferred_genres))
        score += genre_matches * 2.0
        
        # Boost for preferred language
        content_language = content.get("original_language", content.get("language", "")).lower()
        preferred_languages = [l.lower() for l in context["profile"].get("preferred_languages", [])]
        
        if content_language in preferred_languages:
            score += 1.5
        
        # Boost for recency (newer content gets slight boost)
        if content.get("release_date"):
            try:
                release_date = datetime.strptime(content["release_date"][:10], "%Y-%m-%d")
                days_old = (datetime.now() - release_date).days
                if days_old < 365:  # Less than a year old
                    score += 0.5
            except:
                pass
        
        # Add algorithm-specific scores
        if hasattr(content, 'similarity_score'):
            score += content.similarity_score * 2
        
        if hasattr(content, 'content_score'):
            score += content.content_score / 10
        
        if hasattr(content, 'popularity_score'):
            score += content.popularity_score
        
        return round(score, 2)
    
    def _get_personalization_level(self, context: Dict) -> str:
        """Determine the personalization level based on user data"""
        total_interactions = context["total_interactions"]
        total_liked = context["profile"].get("total_liked", 0)
        
        if total_interactions >= 20 and total_liked >= 10:
            return "high"
        elif total_interactions >= 5 and total_liked >= 3:
            return "medium"
        else:
            return "low"
    
    async def _get_popular_recommendations(self, limit: int) -> Dict:
        """Fallback recommendations for new users"""
        try:
            popular_content = await get_content_with_date_filtering('hi', 'both', 'drama', '6months')
            
            return {
                "recommendations": popular_content[:limit],
                "algorithm": "popular_fallback",
                "personalization_level": "none",
                "message": "Start liking content to get personalized recommendations!"
            }
            
        except Exception as e:
            print(f"❌ Error getting popular recommendations: {e}")
            return {"recommendations": [], "algorithm": "error", "personalization_level": "none"}
