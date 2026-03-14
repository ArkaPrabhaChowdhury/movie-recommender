import os
import httpx
import time
from typing import List, Dict, Optional
import numpy as np

# This service is now Vercel-friendly. 
# It uses the Hugging Face Inference API (Free) to generate embeddings.
# This avoids installing 'torch' and 'sentence-transformers' (7GB+ total size).

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model_id = "sentence-transformers/all-MiniLM-L6-v2"
            cls._instance.api_url = f"https://api-inference.huggingface.co/models/{cls._instance.model_id}"
            
            # Get token from environment
            from config.constants import SUPABASE_KEY # We can reuse keys if needed, but better to have HF_TOKEN
            cls._instance.hf_token = os.getenv('HF_TOKEN')
            
            # Local fallback for indexing script (checks if library is actually installed)
            cls._instance.local_model = None
            try:
                from sentence_transformers import SentenceTransformer
                print("🏠 Local SentenceTransformer detected. Using local mode for speed.")
                cls._instance.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("☁️ Local ML libs not found. Using Hugging Face Inference API.")
                
        return cls._instance

    def _get_headers(self):
        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        return headers

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding."""
        if not text:
            return [0.0] * 384
        
        # Use local model if available (for bootstrap script)
        if self.local_model:
            return self.local_model.encode(text).tolist()

        # Otherwise use API
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={"inputs": text, "options": {"wait_for_model": True}}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️ HF API Error {response.status_code}: {response.text}")
                    return [0.0] * 384
        except Exception as e:
            print(f"❌ Embedding API Error: {e}")
            return [0.0] * 384

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of strings."""
        if not texts:
            return []
            
        if self.local_model:
            return self.local_model.encode(texts, show_progress_bar=False).tolist()

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={"inputs": texts, "options": {"wait_for_model": True}}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️ HF Batch API Error {response.status_code}: {response.text}")
                    # Fallback to zeros to avoid crashing
                    return [[0.0] * 384 for _ in texts]
        except Exception as e:
            print(f"❌ Batch Embedding API Error: {e}")
            return [[0.0] * 384 for _ in texts]

    def prepare_metadata_text(self, item: Dict) -> str:
        """Create a rich text representation of a movie/show for embedding."""
        title = item.get('title', '')
        overview = item.get('overview', '')
        genres = ", ".join(item.get('genres', [])) if isinstance(item.get('genres'), list) else ""
        year = item.get('year', '')
        lang = item.get('original_language', '')
        return f"Title: {title} ({year}). Language: {lang}. Genres: {genres}. Overview: {overview}"
