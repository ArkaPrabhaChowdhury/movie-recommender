from supabase import create_client, Client
from typing import List, Dict, Optional
from config.constants import SUPABASE_URL, SUPABASE_KEY
import json

class VectorService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def upsert_embeddings(self, items: List[Dict]):
        """
        Bulk upsert embeddings and metadata to Supabase.
        Items should have tmdb_id, content_type, embedding, etc.
        """
        if not items:
            return
            
        try:
            # We use Postgres ON CONFLICT via supabase-py
            # The schema unique constraint is (tmdb_id, content_type)
            response = self.supabase.table("movie_embeddings").upsert(
                items, 
                on_conflict="tmdb_id,content_type"
            ).execute()
            return response
        except Exception as e:
            print(f"❌ Supabase Upsert Error: {e}")
            raise e

    async def semantic_search(self, query_embedding: List[float], limit: int = 10, content_type: str = 'both', language: str = 'any'):
        """
        Execute semantic search using the match_movies RPC function.
        """
        try:
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.35, # Adjust based on testing
                "match_count": limit,
                "filter_content_type": content_type,
                "filter_language": language
            }
            
            response = self.supabase.rpc("match_movies", params).execute()
            return response.data
        except Exception as e:
            print(f"❌ Semantic Search Error: {e}")
            return []

    async def get_existing_ids(self, tmdb_ids: List[int], content_type: str) -> set:
        """Fetch IDs that already exist to avoid unnecessary vectorization."""
        if not tmdb_ids:
            return set()
            
        try:
            response = self.supabase.table("movie_embeddings") \
                .select("tmdb_id") \
                .filter("content_type", "eq", content_type) \
                .in_("tmdb_id", tmdb_ids) \
                .execute()
            
            return {row["tmdb_id"] for row in response.data}
        except Exception as e:
            print(f"⚠️ Error checking existing IDs: {e}")
            return set()
