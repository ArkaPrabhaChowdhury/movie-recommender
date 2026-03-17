from typing import List, Dict, Optional
from utils.observability import observe, langfuse_context
from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from supabase import Client, create_client
from config.constants import SUPABASE_URL, SUPABASE_KEY

class SemanticCacheService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    @observe()
    async def get_cached_response(self, query: str) -> Optional[Dict]:
        """
        Check if a similar query exists in the cache (threshold 0.95).
        """
        try:
            print(f"🧠 Checking semantic cache for: '{query}'")
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Use Supabase RPC to find similar queries
            # Table: query_cache, Function: match_queries
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.95,
                "match_count": 1
            }
            
            # Note: This assumes the match_queries RPC exists handles VECTOR(384)
            response = self.supabase.rpc("match_queries", params).execute()
            
            if response.data:
                cached = response.data[0]
                print(f"✨ Semantic Cache Hit! (Similarity: {cached.get('similarity', 0):.4f})")
                
                # Log hit to Langfuse
                langfuse_context.update_current_trace(
                    tags=["cache-hit"],
                    metadata={"cache_similarity": cached.get("similarity")}
                )
                
                return cached.get("response_json")
            
            print("❄️ Semantic Cache Miss.")
            return None
        except Exception as e:
            print(f"⚠️ Semantic Cache Error: {e}")
            return None

    @observe()
    async def set_cached_response(self, query: str, response_json: Dict):
        """
        Save a response into the semantic cache.
        """
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            
            data = {
                "query_text": query,
                "embedding": query_embedding,
                "response_json": response_json,
                "metadata": {"type": "ai_chat"}
            }
            
            self.supabase.table("query_cache").upsert(data, on_conflict="query_text").execute()
            print(f"💾 Saved query to semantic cache.")
        except Exception as e:
            print(f"⚠️ Failed to save to semantic cache: {e}")
