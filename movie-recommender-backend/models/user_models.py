from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class UserPreference(BaseModel):
    user_id: str
    content_id: int
    content_type: str  # movie or tv
    action: str  # liked, disliked, watchlisted, watched
    rating: Optional[float] = None
    timestamp: datetime

class UserProfile(BaseModel):
    user_id: str
    preferred_genres: List[str] = []
    preferred_languages: List[str] = []
    preferred_content_types: List[str] = []
    liked_actors: List[str] = []
    liked_directors: List[str] = []
    created_at: datetime
    updated_at: datetime

class ContentInteraction(BaseModel):
    user_id: str
    content_id: int
    content_type: str
    title: str
    action: str  # like, dislike, watchlist, watched
    rating: Optional[float] = None
    genres: List[str] = []
    language: str
    actors: List[str] = []
    directors: List[str] = []
    timestamp: datetime = datetime.now()

class RecommendationRequest(BaseModel):
    user_id: str
    limit: int = 15
    exclude_seen: bool = True
    mood: Optional[str] = None
    specific_request: Optional[str] = None
