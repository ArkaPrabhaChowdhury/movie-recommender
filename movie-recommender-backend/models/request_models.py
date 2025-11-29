from pydantic import BaseModel
from typing import List, Dict, Optional

class DiscoverRequest(BaseModel):
    prompt: str
    genre: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    release_period: Optional[str] = None

class SearchRequest(BaseModel):
    query: str

class AIChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
