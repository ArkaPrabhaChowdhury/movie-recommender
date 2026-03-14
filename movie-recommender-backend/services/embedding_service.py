import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Union
import time

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            # Load the model only once (Singleton)
            # all-MiniLM-L6-v2 is 384 dimensions and very fast
            print("🧠 Loading SentenceTransformer model: all-MiniLM-L6-v2...")
            start_time = time.time()
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Use GPU if available
            if torch.cuda.is_available():
                cls._instance.model = cls._instance.model.to('cuda')
                print("🚀 Using CUDA for embeddings")
            else:
                print("💻 Using CPU for embeddings")
                
            print(f"✅ Model loaded in {time.time() - start_time:.2f} seconds")
        return cls._instance

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding for a string."""
        if not text:
            return [0.0] * 384
        embedding = self.model.encode(text)
        return embedding.tolist()

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of strings in one go (more efficient)."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def prepare_metadata_text(self, item: Dict) -> str:
        """
        Create a rich text representation of a movie/show for embedding.
        Includes title, year, genres, and overview.
        """
        title = item.get('title', '')
        overview = item.get('overview', '')
        genres = ", ".join(item.get('genres', [])) if isinstance(item.get('genres'), list) else ""
        year = item.get('year', '')
        lang = item.get('original_language', '')
        
        # Format: Title (Year). Lang: hi. Genres: Action, Drama. Overview: ...
        return f"Title: {title} ({year}). Language: {lang}. Genres: {genres}. Overview: {overview}"
