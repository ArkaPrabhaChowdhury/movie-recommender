import os
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter
from models.user_models import UserProfile, ContentInteraction
from config.constants import SUPABASE_URL, SUPABASE_KEY

class UserPreferenceService:
    def __init__(self):
        """Initialize Supabase client. Local file storage has been removed for production-ready cloud deployment."""
        self.supabase = None
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️ WARNING: SUPABASE_URL and SUPABASE_KEY not configured. User services will fail.")
            return
        
        try:
            from supabase import create_client, Client
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("🚀 Connected to Supabase Successfully!")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")

    async def _get_user_record(self, user_id: str) -> Dict:
        """Fetch the full record for a user from Supabase."""
        if not self.supabase:
            return {}
        try:
            response = self.supabase.table('user_data').select('*').eq('user_id', user_id).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            print(f"❌ Supabase fetch error for user {user_id}: {e}")
            return {}

    async def record_interaction(self, interaction: ContentInteraction) -> bool:
        """Record user interaction directly to Supabase."""
        if not self.supabase:
            print("⚠️ Cannot record interaction: Supabase not configured.")
            return False
        try:
            user_id = interaction.user_id
            record = await self._get_user_record(user_id)
            preferences = record.get('preferences', []) if record else []
            
            # Convert interaction to dict for storage
            interaction_dict = {
                "user_id": interaction.user_id,
                "content_id": interaction.content_id,
                "content_type": interaction.content_type,
                "title": interaction.title,
                "action": interaction.action,
                "rating": interaction.rating,
                "genres": interaction.genres if interaction.genres else [],
                "language": interaction.language if interaction.language else "en",
                "actors": interaction.actors if interaction.actors else [],
                "directors": interaction.directors if interaction.directors else [],
                "timestamp": interaction.timestamp.isoformat(),
                "release_date": getattr(interaction, 'release_date', ''),
                "tmdb_rating": getattr(interaction, 'tmdb_rating', 0),
                "overview": getattr(interaction, 'overview', ''),
                "popularity": getattr(interaction, 'popularity', 0),
                "poster": getattr(interaction, 'poster', None)
            }
            
            # Logic for mutually exclusive actions
            exclusive_sets = [{"liked", "disliked"}, {"watchlisted", "watched"}]
            actions_to_remove = {interaction.action}
            for s in exclusive_sets:
                if interaction.action in s:
                    actions_to_remove.update(s)

            # Update preferences list safely
            updated_preferences = [
                item for item in preferences 
                if not (item["content_id"] == interaction.content_id and 
                       item["content_type"] == interaction.content_type and
                       item["action"] in actions_to_remove)
            ]
            updated_preferences.append(interaction_dict)
            updated_preferences = updated_preferences[-200:] # Keep recent 200
            
            # Upsert into Supabase
            self.supabase.table('user_data').upsert({
                "user_id": user_id,
                "preferences": updated_preferences
            }).execute()
            
            # Trigger profile update asynchronously
            await self._update_user_profile(user_id, updated_preferences)
            return True
        except Exception as e:
            print(f"❌ Error recording interaction in Supabase: {e}")
            return False

    async def _update_user_profile(self, user_id: str, interactions: List[Dict]):
        """Analyze interactions and update user profile in Supabase."""
        if not self.supabase:
            return
        try:
            if not interactions:
                return

            # Analysis for preferences
            liked = [i for i in interactions if i["action"] == "liked"]
            watched = [i for i in interactions if i["action"] == "watched"]
            watchlisted = [i for i in interactions if i["action"] == "watchlisted"]
            positive_content = liked + watchlisted
            
            # Language signaling (weighted)
            language_signals = ([(i, 3) for i in liked] + [(i, 2) for i in watched] + [(i, 1) for i in watchlisted])
            
            genre_counter = Counter()
            language_counter = Counter()
            content_type_counter = Counter()
            actor_counter = Counter()
            director_counter = Counter()

            for item in positive_content:
                for g in item.get("genres", []): genre_counter[g.lower().strip()] += 1
                content_type_counter[item.get("content_type", "movie")] += 1
                for a in item.get("actors", []): actor_counter[a.strip()] += 1
                for d in item.get("directors", []): director_counter[d.strip()] += 1

            for item, weight in language_signals:
                lang = item.get("language", "").lower().strip()
                if lang: language_counter[lang] += weight

            # Get existing record to preserve manual settings like OTT subscriptions
            record = await self._get_user_record(user_id)
            existing_profile = record.get('profile', {}) if record else {}

            profile = {
                "user_id": user_id,
                "preferred_genres": [g for g, c in genre_counter.most_common(10)],
                "preferred_languages": [l for l, c in language_counter.most_common(5)],
                "preferred_content_types": [ct for ct, c in content_type_counter.most_common(3)],
                "liked_actors": [a for a, c in actor_counter.most_common(20)],
                "liked_directors": [d for d, c in director_counter.most_common(10)],
                "subscribed_providers": existing_profile.get("subscribed_providers", []),
                "total_interactions": len(interactions),
                "created_at": existing_profile.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat()
            }
            
            self.supabase.table('user_data').upsert({
                "user_id": user_id,
                "profile": profile
            }).execute()
            
        except Exception as e:
            print(f"❌ Error updating profile in Supabase: {e}")

    async def remove_interaction(self, user_id: str, content_id: int, content_type: str, action: Optional[str] = None) -> bool:
        """Remove a specific interaction from Supabase."""
        if not self.supabase:
            return False
        try:
            record = await self._get_user_record(user_id)
            if not record:
                return False
                
            preferences = record.get('preferences', [])
            original_len = len(preferences)
            
            # Filter out the matching interaction
            updated_preferences = [
                item for item in preferences
                if not (item["content_id"] == content_id and 
                       item["content_type"] == content_type and 
                       (action is None or item["action"] == action))
            ]
            
            if len(updated_preferences) < original_len:
                # Save back to Supabase
                self.supabase.table('user_data').upsert({
                    "user_id": user_id,
                    "preferences": updated_preferences
                }).execute()
                
                # Update profile to reflect removal
                await self._update_user_profile(user_id, updated_preferences)
                return True
            return False
        except Exception as e:
            print(f"❌ Error removing interaction from Supabase: {e}")
            return False

    async def save_user_subscriptions(self, user_id: str, provider_ids: List[int]) -> bool:
        """Update only the subscription providers in the user's Supabase profile."""
        if not self.supabase:
            return False
        try:
            record = await self._get_user_record(user_id)
            profile = record.get('profile', {}) if record else {"user_id": user_id, "created_at": datetime.now().isoformat()}
            
            profile["subscribed_providers"] = provider_ids
            profile["updated_at"] = datetime.now().isoformat()
            
            self.supabase.table('user_data').upsert({
                "user_id": user_id,
                "profile": profile
            }).execute()
            return True
        except Exception as e:
            print(f"❌ Error saving subscriptions to Supabase: {e}")
            return False

    async def get_user_profile(self, user_id: str) -> Dict:
        """Fetch user profile from Supabase."""
        if not self.supabase:
            return {}
        record = await self._get_user_record(user_id)
        return record.get('profile', {}) if record else {}

    async def get_user_interactions(self, user_id: str, action: str = None) -> List[Dict]:
        """Fetch and optionally filter user interactions from Supabase."""
        if not self.supabase:
            return []
        record = await self._get_user_record(user_id)
        interactions = record.get('preferences', []) if record else []
        
        if action:
            interactions = [i for i in interactions if i["action"] == action]
        
        # Newest first
        interactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return interactions

    async def get_recommendation_context(self, user_id: str) -> Dict:
        """Gather context for recommendation engine exclusively from Supabase."""
        if not self.supabase:
            return {
                "profile": {},
                "liked": [],
                "watched": [],
                "disliked": [],
                "watchlisted": [],
                "total_interactions": 0,
                "has_preferences": False,
            }
        record = await self._get_user_record(user_id)
        profile = record.get('profile', {}) if record else {}
        interactions = record.get('preferences', []) if record else []

        def filter_by_action(act: str):
            return [i for i in interactions if i["action"] == act]

        return {
            "profile": profile,
            "liked": filter_by_action("liked"),
            "watched": filter_by_action("watched"),
            "disliked": filter_by_action("disliked"),
            "watchlisted": filter_by_action("watchlisted"),
            "total_interactions": len(interactions),
            "has_preferences": bool(profile.get("preferred_genres", [])),
        }
