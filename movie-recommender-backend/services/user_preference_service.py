import json
import os
from typing import List, Dict
from datetime import datetime
from collections import defaultdict, Counter
from models.user_models import UserPreference, UserProfile, ContentInteraction

class UserPreferenceService:
    def __init__(self):
        # Check if we are in a read-only environment (like Vercel)
        self.data_dir = "user_data"
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            # Try writing a test file to verify write permissions
            test_file = os.path.join(self.data_dir, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except (OSError, PermissionError):
            # Fallback to /tmp for Vercel/Serverless environments
            print("⚠️ Read-only filesystem detected. Using /tmp for user data.")
            self.data_dir = "/tmp/user_data"
            
        self.preferences_file = "user_preferences.json"
        self.profiles_file = "user_profiles.json"
        self._ensure_data_directory()
        
        # Initialize Supabase if configured
        from config.constants import SUPABASE_URL, SUPABASE_KEY
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)
        if self.use_supabase:
            try:
                from supabase import create_client, Client
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("🚀 Connected to Supabase Successfully!")
            except Exception as e:
                print(f"⚠️ Failed to connect to Supabase: {e}. Falling back to local files.")
                self.use_supabase = False

        
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Failed to create data directory {self.data_dir}: {e}")
        
    def _load_data(self, filename: str) -> Dict:
        """Load data from JSON file or Supabase"""
        if self.use_supabase:
            try:
                # We store both profiles and preferences in a single Supabase table called 'user_data'
                # Columns: user_id (text PK), profile (jsonb), preferences (jsonb)
                response = self.supabase.table('user_data').select('*').execute()
                data_dict = {}
                for row in response.data:
                    user_id = row['user_id']
                    if filename == self.profiles_file and row.get('profile'):
                        data_dict[user_id] = row['profile']
                    elif filename == self.preferences_file and row.get('preferences'):
                        data_dict[user_id] = row['preferences']
                return data_dict
            except Exception as e:
                print(f"❌ Supabase load error: {e}")
                # Fallback to local files on error

        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_data(self, filename: str, data: Dict):
        """Save data to JSON file or Supabase"""
        if self.use_supabase:
            try:
                for user_id, content in data.items():
                    # Upsert each user's data into the Supabase table
                    update_payload = {"user_id": user_id}
                    if filename == self.profiles_file:
                        update_payload["profile"] = content
                    else:
                        update_payload["preferences"] = content
                        
                    self.supabase.table('user_data').upsert(update_payload).execute()
            except Exception as e:
                print(f"❌ Supabase save error: {e}")
                # Fallback to local files so data isn't lost
                
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    async def record_interaction(self, interaction: ContentInteraction) -> bool:
        """Record user interaction with enhanced data storage"""
        try:
            preferences_data = self._load_data(self.preferences_file)
            
            user_id = interaction.user_id
            if user_id not in preferences_data:
                preferences_data[user_id] = []
            
            # Convert to dict for storage with ALL the data
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
                
                # Additional data for better recommendations
                "release_date": getattr(interaction, 'release_date', ''),
                "tmdb_rating": getattr(interaction, 'tmdb_rating', 0),
                "overview": getattr(interaction, 'overview', ''),
                "popularity": getattr(interaction, 'popularity', 0),
                "poster": getattr(interaction, 'poster', None)
            }
            
            print(f"💾 Storing interaction data: {interaction_dict}")
            
            # Define mutually exclusive sets to ensure data integrity
            # E.g., You can't both like and dislike, and if you watch it, it usually leaves the watchlist
            exclusive_sets = [
                {"liked", "disliked"},
                {"watchlisted", "watched"}
            ]
            
            new_action = interaction.action
            actions_to_remove = {new_action} # Always update interactions of the same action type
            
            # If the action is part of an exclusive set, remove other actions from THAT set
            for s in exclusive_sets:
                if new_action in s:
                    actions_to_remove.update(s)

            # Remove existing interactions that are incompatible with the new one
            # This allows a piece of content to be both 'liked' AND 'watched' simultaneously
            preferences_data[user_id] = [
                item for item in preferences_data[user_id] 
                if not (item["content_id"] == interaction.content_id and 
                       item["content_type"] == interaction.content_type and
                       item["action"] in actions_to_remove)
            ]
            
            # Add new interaction
            preferences_data[user_id].append(interaction_dict)
            
            # Keep only last 200 interactions per user
            preferences_data[user_id] = preferences_data[user_id][-200:]
            
            self._save_data(self.preferences_file, preferences_data)
            
            # Update user profile
            await self._update_user_profile(user_id)
            
            print(f"✅ Recorded {interaction.action} for '{interaction.title}' by user {user_id}")
            print(f"📊 User now has {len(preferences_data[user_id])} total interactions")
            
            return True
            
        except Exception as e:
            print(f"❌ Error recording interaction: {e}")
            return False
    
    async def _update_user_profile(self, user_id: str):
        """Update user profile based on interactions with enhanced analysis"""
        try:
            preferences_data = self._load_data(self.preferences_file)
            profiles_data = self._load_data(self.profiles_file)
            
            user_interactions = preferences_data.get(user_id, [])
            if not user_interactions:
                return
            
            # Analyze different types of interactions
            liked_content = [item for item in user_interactions if item["action"] == "liked"]
            disliked_content = [item for item in user_interactions if item["action"] == "disliked"]
            watchlisted_content = [item for item in user_interactions if item["action"] == "watchlisted"]
            watched_content = [item for item in user_interactions if item["action"] == "watched"]
            
            print(f"📈 Profile analysis for {user_id}:")
            print(f"  Liked: {len(liked_content)}, Disliked: {len(disliked_content)}")
            print(f"  Watchlisted: {len(watchlisted_content)}, Watched: {len(watched_content)}")
            
            # ── Genre/actor/director: use liked + watchlisted (both signal intent)
            positive_content = liked_content + watchlisted_content

            # ── Language: Weighted signal from likes (3x), watched (2x), and watchlisted (1x).
            # This more accurately reflects the user's request to focus on all their history.
            language_signal_content = (
                [(item, 3) for item in liked_content] +
                [(item, 2) for item in watched_content] +
                [(item, 1) for item in watchlisted_content]
            )

            # Counters for analysis
            genre_counter = Counter()
            language_counter = Counter()
            content_type_counter = Counter()
            actor_counter = Counter()
            director_counter = Counter()

            for item in positive_content:
                # Count genres
                genres = item.get("genres", [])
                if isinstance(genres, list):
                    for genre in genres:
                        if genre and isinstance(genre, str):
                            genre_counter[genre.lower().strip()] += 1

                # Count content types
                content_type = item.get("content_type", "movie")
                if content_type:
                    content_type_counter[content_type] += 1

                # Count actors
                actors = item.get("actors", [])
                if isinstance(actors, list):
                    for actor in actors:
                        if actor and isinstance(actor, str):
                            actor_counter[actor.strip()] += 1

                # Count directors
                directors = item.get("directors", [])
                if isinstance(directors, list):
                    for director in directors:
                        if director and isinstance(director, str):
                            director_counter[director.strip()] += 1

            # Language preference — weighted by likes (2x) + watched (1x) only
            for item, weight in language_signal_content:
                language = item.get("language", "")
                if language and isinstance(language, str):
                    language_counter[language.lower().strip()] += weight

            print(f"  Language counts (likes×2 + watched×1): {dict(language_counter.most_common(5))}")

            # Create comprehensive profile
            profile = {
                "user_id": user_id,
                "preferred_genres": [genre for genre, count in genre_counter.most_common(10) if count >= 1],
                "preferred_languages": [lang for lang, count in language_counter.most_common(5) if count >= 1],
                "preferred_content_types": [ct for ct, count in content_type_counter.most_common(3)],
                "liked_actors": [actor for actor, count in actor_counter.most_common(20) if count >= 1],
                "liked_directors": [director for director, count in director_counter.most_common(10) if count >= 1],
                # Preserve manually-set subscription list
                "subscribed_providers": profiles_data.get(user_id, {}).get("subscribed_providers", []),
                
                # Statistics
                "total_interactions": len(user_interactions),
                "total_liked": len(liked_content),
                "total_disliked": len(disliked_content),
                "total_watchlisted": len(watchlisted_content),
                "total_watched": len(watched_content),
                
                # Metadata
                "created_at": profiles_data.get(user_id, {}).get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "last_activity": user_interactions[-1]["timestamp"] if user_interactions else None
            }
            
            profiles_data[user_id] = profile
            self._save_data(self.profiles_file, profiles_data)
            
            print(f"📊 Updated profile for user {user_id}:")
            print(f"  Top genres: {profile['preferred_genres'][:3]}")
            print(f"  Languages: {profile['preferred_languages']}")
            print(f"  Content types: {profile['preferred_content_types']}")
            
        except Exception as e:
            print(f"❌ Error updating profile: {e}")

    async def save_user_subscriptions(self, user_id: str, provider_ids: List[int]) -> bool:
        """Persist the user's chosen OTT platform IDs without touching other profile fields."""
        try:
            profiles_data = self._load_data(self.profiles_file)
            if user_id not in profiles_data:
                # Bootstrap a minimal profile so the key exists
                profiles_data[user_id] = {
                    "user_id": user_id,
                    "preferred_genres": [],
                    "preferred_languages": [],
                    "preferred_content_types": [],
                    "liked_actors": [],
                    "liked_directors": [],
                    "subscribed_providers": provider_ids,
                    "total_interactions": 0,
                    "total_liked": 0,
                    "total_disliked": 0,
                    "total_watchlisted": 0,
                    "total_watched": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                profiles_data[user_id]["subscribed_providers"] = provider_ids
                profiles_data[user_id]["updated_at"] = datetime.now().isoformat()
            self._save_data(self.profiles_file, profiles_data)
            print(f"✅ Saved {len(provider_ids)} subscriptions for {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error saving subscriptions: {e}")
            return False
    
    # ... rest of existing methods remain the same ...
    async def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile with preferences"""
        profiles_data = self._load_data(self.profiles_file)
        return profiles_data.get(user_id, {})
    
    async def get_user_interactions(self, user_id: str, action: str = None) -> List[Dict]:
        """Get user interactions, optionally filtered by action"""
        preferences_data = self._load_data(self.preferences_file)
        interactions = preferences_data.get(user_id, [])
        
        if action:
            interactions = [item for item in interactions if item["action"] == action]
        
        # Sort by timestamp (newest first)
        interactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return interactions
    
    async def get_recommendation_context(self, user_id: str) -> Dict:
        """Get enriched context for the recommendation engine."""
        profile = await self.get_user_profile(user_id)
        recent_interactions = await self.get_user_interactions(user_id)

        # Helper to extract items by action
        def get_items_by_action(action: str, limit: int = 50):
            return [
                {
                    "content_id": item["content_id"],
                    "content_type": item["content_type"],
                    "title": item["title"],
                    "overview": item.get("overview", ""),
                    "genres": item.get("genres", []),
                    "language": item.get("language", ""),
                    "actors": item.get("actors", []),
                    "directors": item.get("directors", []),
                    "timestamp": item.get("timestamp", ""),
                    "rating": item.get("rating", 0),
                }
                for item in recent_interactions
                if item["action"] == action
            ][:limit]

        return {
            "profile": profile,
            "liked": get_items_by_action("liked"),
            "watched": get_items_by_action("watched"),
            "disliked": get_items_by_action("disliked"),
            "watchlisted": get_items_by_action("watchlisted"),
            "total_interactions": len(recent_interactions),
            "has_preferences": bool(profile.get("preferred_genres", [])),
        }
