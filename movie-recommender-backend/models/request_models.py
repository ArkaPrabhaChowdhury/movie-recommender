from pydantic import BaseModel
from typing import List, Dict, Optional

class DiscoverRequest(BaseModel):
    user_id: Optional[str] = None
    prompt: str
    genre: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    release_period: Optional[str] = None
    sort_by: Optional[str] = 'rating'
    page: Optional[int] = 1

class SearchRequest(BaseModel):
    user_id: Optional[str] = None
    query: str

class AIChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
