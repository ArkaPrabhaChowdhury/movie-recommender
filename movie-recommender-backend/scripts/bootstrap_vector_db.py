import asyncio
import httpx
from datetime import datetime
import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from config.constants import TMDB_API_KEY, TMDB_API_URL

# Configuration
LANGUAGES = ['hi', 'en', 'ta', 'te']
START_YEAR = 2000
END_YEAR = datetime.now().year
BATCH_SIZE = 20  # TMDB page size / Vectorization batch
MAX_PAGES_PER_COMBO = 10  # How deep to go per Year-Language-Type (10 pages = 200 items)

# Initialize Services
embedding_service = EmbeddingService()
vector_service = VectorService()

async def fetch_tmdb_page(client, url, params):
    try:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
        elif response.status_code == 429:
            print("⏳ Rate limited (429). Sleeping for 5s...")
            await asyncio.sleep(5)
            return await fetch_tmdb_page(client, url, params)
        else:
            print(f"⚠️ TMDB Error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return []

async def process_batch(items, content_type):
    if not items:
        return
    
    movie_data = []
    texts_to_embed = []
    
    # Check what already exists in Supabase
    tmdb_ids = [item['id'] for item in items]
    existing_ids = await vector_service.get_existing_ids(tmdb_ids, content_type)
    
    for item in items:
        if item['id'] in existing_ids:
            continue
            
        # Clean up data
        title = item.get('title') or item.get('name') or 'Unknown'
        release_date = item.get('release_date') or item.get('first_air_date') or None
        
        # Prepare item for database
        processed_item = {
            "tmdb_id": item['id'],
            "content_type": content_type,
            "title": title,
            "overview": item.get('overview', ''),
            "genres": [], # TMDB gives IDs, we'd need to map them or skip for now
            "language": item.get('original_language', ''),
            "poster_path": item.get('poster_path'),
            "release_date": release_date if release_date and len(release_date) == 10 else None,
            "rating": item.get('vote_average', 0),
            "metadata": {
                "popularity": item.get('popularity', 0),
                "vote_count": item.get('vote_count', 0)
            }
        }
        
        # Prep text for embedding
        year = release_date[:4] if release_date else ""
        text = f"Title: {title} ({year}). Overview: {processed_item['overview']}"
        
        movie_data.append(processed_item)
        texts_to_embed.append(text)
    
    if not movie_data:
        # print("⏭️ Batch already fully indexed. Skipping.")
        return 0

    try:
        # Vectorize
        print(f"🧠 Vectorizing {len(texts_to_embed)} items...")
        embeddings = embedding_service.generate_batch_embeddings(texts_to_embed)
        
        # Merge embeddings into items
        for i, item in enumerate(movie_data):
            item['embedding'] = embeddings[i]
        
        # Upsert
        await vector_service.upsert_embeddings(movie_data)
        print(f"✅ Successfully indexed {len(movie_data)} {content_type}s")
        return len(movie_data)
    except Exception as e:
        print(f"❌ Error in process_batch: {e}")
        return 0

async def main():
    print(f"🎬 Starting indexer from {START_YEAR} to {END_YEAR}")
    total_indexed = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Nested loop: Year -> Language -> Content Type -> Page
        for year in range(START_YEAR, END_YEAR + 1):
            for lang in LANGUAGES:
                for ctype in ['movie', 'tv']:
                    print(f"\n📁 Year: {year} | Lang: {lang} | Type: {ctype}")
                    
                    for page in range(1, MAX_PAGES_PER_COMBO + 1):
                        params = {
                            "api_key": TMDB_API_KEY,
                            "with_original_language": lang,
                            "sort_by": "popularity.desc",
                            "page": page
                        }
                        
                        if ctype == 'movie':
                            params["primary_release_year"] = year
                            url = f"{TMDB_API_URL}/discover/movie"
                        else:
                            params["first_air_date_year"] = year
                            url = f"{TMDB_API_URL}/discover/tv"
                        
                        results = await fetch_tmdb_page(client, url, params)
                        if not results:
                            break
                            
                        indexed_count = await process_batch(results, ctype)
                        total_indexed += indexed_count
                        
                        # Small break to be nice to CPUs and APIs
                        await asyncio.sleep(0.5)

    print(f"\n🏁 Finished! Total new items added to Vector DB: {total_indexed}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Indexer stopped by user.")
    except Exception as e:
        print(f"\n💀 FATAL ERROR: {e}")
