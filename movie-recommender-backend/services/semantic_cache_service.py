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
            
            if not query_embedding or sum(map(abs, query_embedding)) < 1e-9:
                print("⚠️ Skipping semantic cache (invalid query embedding)")
                return None
            
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.97,
                "match_count": 1
            }
            
            # Note: This assumes the match_queries RPC exists handles VECTOR(384)
            response = self.supabase.rpc("match_queries", params).execute()
            
            if response.data:
                cached = response.data[0]
                import math
                similarity = float(cached.get('similarity', 0))
                
                # Check for NaN or non-finite similarity which indicates a vector match error
                if not math.isfinite(similarity) or similarity < 0.97:
                    print(f"⚠️ Invalid cache similarity ({similarity}), ignoring.")
                    return None

                print(f"✨ Semantic Cache Hit! (Similarity: {similarity:.4f})")
                
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
            
            if not query_embedding or sum(map(abs, query_embedding)) < 1e-9:
                print("⚠️ Cannot save to cache: invalid embedding")
                return
                
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
