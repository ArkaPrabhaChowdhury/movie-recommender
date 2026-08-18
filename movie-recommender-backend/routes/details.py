from fastapi import APIRouter, HTTPException, Path
import asyncio
from services.tmdb_service import TMDBService
from services.streaming_service import StreamingService
from services.similarity_service import rank_similar_content
from services.embedding_service import EmbeddingService


def _cosine_similarity(left, right):
    if not left or not right:
        return None
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if not left_norm or not right_norm:
        return None
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))

router = APIRouter()

@router.get("/details/{content_type}/{content_id}")
async def get_details(
    content_type: str = Path(..., description="Either 'movie' or 'tv'"),
    content_id: int = Path(..., description="TMDB ID of the content")
):
    """Get complete details including cast, videos, similar content, and streaming availability"""
    try:
        # First check if valid type
        if content_type not in ['movie', 'tv']:
            raise HTTPException(status_code=400, detail="content_type must be either 'movie' or 'tv'")
            
        print(f"Fetching full details for {content_type} with ID {content_id}")
        
        # 1. Fetch details from TMDB
        content_details = await TMDBService.get_content_details(content_id, content_type)
        if not content_details:
            raise HTTPException(status_code=404, detail="Content not found")
            
        # 2. Add streaming availability
        # StreamingService expects a list of items with 'id'
        streaming_results = await StreamingService.get_streaming_providers_batch([content_details], content_type)
        if streaming_results and len(streaming_results) > 0:
            content_details = streaming_results[0]
            
        # 3. For similar content, check their streaming availability (optional but helpful)
        if content_details.get('similar'):
            trending = await TMDBService.get_trending_content(content_type)
            candidates = content_details['similar'] + trending

            # Compare story meaning using overview embeddings only. Genre is
            # scored separately, and cast/director metadata is intentionally excluded.
            story_texts = [content_details.get('overview', '')] + [item.get('overview', '') for item in candidates]
            embeddings = await asyncio.to_thread(EmbeddingService().generate_batch_embeddings, story_texts)
            if embeddings and len(embeddings) == len(story_texts):
                source_embedding = embeddings[0]
                for candidate, candidate_embedding in zip(candidates, embeddings[1:]):
                    candidate['_story_similarity'] = _cosine_similarity(source_embedding, candidate_embedding)

            similar_movies = [s for s in candidates if s['content_type'] == 'movie']
            similar_tv = [s for s in candidates if s['content_type'] == 'tv']
            
            enrich_similar = []
            if similar_movies:
                enrich_similar.extend(await StreamingService.get_streaming_providers_batch(similar_movies, 'movie'))
            if similar_tv:
                enrich_similar.extend(await StreamingService.get_streaming_providers_batch(similar_tv, 'tv'))
                
            if enrich_similar:
                content_details['similar'] = rank_similar_content(content_details, enrich_similar, limit=12)
            else:
                content_details['similar'] = []
                
        return content_details
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_details route: {e}")
        raise HTTPException(status_code=500, detail=str(e))
