from fastapi import APIRouter, HTTPException
import asyncio
from datetime import datetime
import time
from utils.observability import observe, langfuse_context
from utils.analytics_tracker import tracker
from models.request_models import AIChatRequest
from services.ollama_service import OllamaService
from services.simple_recommender import SimpleRecommender
from routes.discovery import get_content_with_date_filtering
from routes.search import global_search_with_ott_filtering
from config.constants import LANGUAGE_MAP
from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from services.semantic_cache_service import SemanticCacheService
from services.user_preference_service import UserPreferenceService
from services.streaming_service import StreamingService
from services.evaluation_service import EvaluationService

router = APIRouter()
embedding_service = EmbeddingService()
vector_service = VectorService()
cache_service = SemanticCacheService()
pref_service = UserPreferenceService()

@router.post("/ai-chat")
@observe()
async def ai_chat_recommendation(request: AIChatRequest):
    """AI recommendations with proper content prioritization"""
    try:
        user_message = request.message.strip()
        conversation_history = request.conversation_history or []
        
        print(f"🤖 AI Chat request: '{user_message}'")
        _t0 = time.time()
        
        # 0. Check Semantic Cache
        cached_response = await cache_service.get_cached_response(user_message)
        if cached_response:
            latency_ms = (time.time() - _t0) * 1000
            tracker.record_trace(
                trace_type="ai_chat",
                query=user_message,
                latency_ms=latency_ms,
                cache_hit=True
            )
            return cached_response

        # Try AI first
        ai_data = None
        try:
            print("🔄 Trying AI response...")
            
            ai_prompt = f"""User request: "{user_message}"

Respond with EXACTLY this JSON format:
{{
    "response": "Your friendly response",
    "search_criteria": {{
        "genre": "action",
        "language": "english", 
        "content_type": "tv"
    }},
    "suggested_titles": ["Title1", "Title2", "Title3"]
}}

Use appropriate genre, language, and content_type based on the request."""

            ai_text = await OllamaService.get_ai_response(ai_prompt, temperature=0.1)
            
            if ai_text:
                fallback_data = SimpleRecommender.analyze_request(user_message)
                ai_data = OllamaService.parse_json_response(ai_text, fallback_data)
                print("✅ Using AI response")
            else:
                raise Exception("No AI response")
                
        except Exception as e:
            print(f"⚠️ AI failed, using smart fallback: {e}")
            ai_data = SimpleRecommender.analyze_request(user_message)
        
        # Extract search criteria
        search_criteria = ai_data.get('search_criteria', {})
        genre = search_criteria.get('genre', 'action')
        language = search_criteria.get('language', 'english')
        content_type = search_criteria.get('content_type', 'tv')
        
        print(f"🎯 Final params - Genre: '{genre}', Language: {language}, Content: {content_type}")
        
        # PRIORITIZE SPECIFIC SEARCH RESULTS OVER GENERIC RESULTS
        suggested_titles = ai_data.get('suggested_titles', [])
        specific_content = []
        
        if suggested_titles:
            print(f"🔎 Searching SPECIFIC titles first: {suggested_titles}")
            for title in suggested_titles:
                try:
                    title_results = await global_search_with_ott_filtering(title, request.user_id)
                    specific_content.extend(title_results)
                    print(f"  - '{title}': found {len(title_results)} results")
                    
                    if title_results:
                        found_titles = [item.get('title', 'Unknown') for item in title_results]
                        print(f"    Specific titles: {found_titles}")
                        
                except Exception as e:
                    print(f"  - '{title}': error {e}")
                    continue
        
        print(f"📊 SPECIFIC content found: {len(specific_content)} items")
        
        # Only add generic content if we don't have enough specific results
        generic_content = []
        if len(specific_content) < 10:  # Only if we need more
            print(f"🔍 Need more content, searching generic {genre} {content_type}...")
            language_code = LANGUAGE_MAP.get(language, 'en')
            generic_results = await get_content_with_date_filtering(
                language_code, content_type, genre, '2years', user_id=request.user_id
            )
            
            # Filter out generic results that aren't related to the search
            if 'marvel' in user_message.lower() or 'superhero' in user_message.lower():
                # For Marvel/superhero requests, filter generic content
                filtered_generic = []
                marvel_keywords = ['marvel', 'superhero', 'hero', 'comic', 'dc', 'batman', 'superman', 'avengers']
                
                for item in generic_results:
                    title_lower = item.get('title', '').lower()
                    overview_lower = item.get('overview', '').lower()
                    
                    if any(keyword in title_lower or keyword in overview_lower for keyword in marvel_keywords):
                        filtered_generic.append(item)
                
                generic_content = filtered_generic[:5]  # Limit generic results
                print(f"📊 FILTERED generic content: {len(generic_content)} items (Marvel-related only)")
            else:
                generic_content = generic_results[:8]  # Normal case
                print(f"📊 GENERIC content: {len(generic_content)} items")
        
        # 3. SEMANTIC SEARCH (RAG)
        semantic_content = []
        try:
            print(f"🧠 Performing semantic search for: '{user_message}'")
            query_embedding = embedding_service.generate_embedding(user_message)
            
            # Map language to code for filtering
            lang_code = LANGUAGE_MAP.get(language, 'any')
            
            semantic_results = await vector_service.semantic_search(
                query_embedding=query_embedding,
                limit=15,
                content_type=content_type if content_type != 'both' else 'both',
                language=lang_code
            )
            
            if semantic_results:
                print(f"✅ Semantic search found {len(semantic_results)} results")
                for item in semantic_results:
                    # Map semantic search result to standard content format
                    semantic_content.append({
                        "id": item['tmdb_id'],
                        "title": item['title'],
                        "poster": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get('poster_path') else None,
                        "rating": item['rating'],
                        "year": item.get('release_date', '')[:4] if item.get('release_date') else '',
                        "overview": item.get('overview', ''),
                        "content_type": item['content_type'],
                        "original_language": item['language'],
                        "source": "semantic"
                    })
                
                # Apply OTT availability and Subscription filtering to Semantic results
                print(f"🎬 Checking OTT availability for {len(semantic_content)} semantic items")
                semantic_content = await StreamingService.get_streaming_providers_batch(semantic_content, 'both')
                
                # Filter for at least one platform found in India
                semantic_content = [item for item in semantic_content if item.get("streaming", {}).get("platform_found")]
                
                if request.user_id:
                    try:
                        profile = await pref_service.get_user_profile(request.user_id)
                        sub_ids = set(profile.get("subscribed_providers", []))
                        if sub_ids:
                            filtered_semantic = []
                            for item in semantic_content:
                                all_platforms = item.get("streaming", {}).get("available_on", [])
                                user_platforms = [p for p in all_platforms if p.get("id") in sub_ids and not p.get("is_rent")]
                                if user_platforms:
                                    item["streaming"]["available_on"] = user_platforms
                                    filtered_semantic.append(item)
                            print(f"🎯 Semantic sub filter: {len(semantic_content)} -> {len(filtered_semantic)}")
                            semantic_content = filtered_semantic
                    except Exception as e:
                        print(f"⚠️ Semantic sub filter error: {e}")
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")

        # Combine results: Specific Titles + Semantic + Generic
        all_content = specific_content + semantic_content + generic_content
        print(f"📊 Combined: {len(specific_content)} specific + {len(semantic_content)} semantic + {len(generic_content)} generic = {len(all_content)} total")
        
        # Deduplication
        unique_content = []
        seen_ids = set()
        
        for item in all_content:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_content.append(item)
        
        print(f"📊 After deduplication: {len(unique_content)} items")
        
        # Sort with HEAVY preference for specific search results
        def sort_key(item):
            base_rating = item.get('rating', 0)
            title = item.get('title', '').lower()
            
            # Check if this was from specific search
            is_specific = any(
                suggested_title.lower() in title or 
                any(word in title for word in suggested_title.lower().split())
                for suggested_title in suggested_titles
            )
            
            if is_specific:
                boosted_rating = base_rating + 5  # HEAVY boost for specific results
                print(f"⭐⭐⭐ SPECIFIC MATCH '{item.get('title', 'Unknown')}': {base_rating} → {boosted_rating}")
                return boosted_rating
            
            return base_rating
        
        unique_content.sort(key=sort_key, reverse=True)
        
        # Limit final results
        final_recommendations = unique_content[:15]
        
        print(f"📈 Final breakdown:")
        print(f"  - Specific results prioritized: {len([item for item in final_recommendations if any(suggested_title.lower() in item.get('title', '').lower() for suggested_title in suggested_titles)])}")
        print(f"  - Generic results: {len(final_recommendations) - len([item for item in final_recommendations if any(suggested_title.lower() in item.get('title', '').lower() for suggested_title in suggested_titles)])}")
        
        # Log final titles
        if final_recommendations:
            final_titles = [f"{item.get('title', 'Unknown')} ({item.get('content_type', 'unknown')})" for item in final_recommendations]
            print(f"📤 FINAL TITLES: {final_titles}")
        
        final_res = {
            "ai_response": ai_data.get('response', ''),
            "recommendations": final_recommendations,
            "query_analysis": {
                "detected_genre": genre,
                "detected_language": language,
                "detected_content_type": content_type,
                "mood": "prioritized_search",
                "traits": [f"specific_titles: {suggested_titles}"]
            },
            "total_found": len(final_recommendations),
            "conversation_context": conversation_history + [{
                "ai": ai_data.get('response', ''),
                "timestamp": datetime.now().isoformat()
            }]
        }
        
        # Save to Cache for future
        await cache_service.set_cached_response(user_message, final_res)
        
        latency_ms = (time.time() - _t0) * 1000
        tokens_in, tokens_out = 0, 0
        try:
            tok = getattr(tracker, '_last_tokens', (0, 0))
            tokens_in, tokens_out = tok
        except Exception:
            pass

        tracker.record_trace(
            trace_type="ai_chat",
            query=user_message,
            latency_ms=latency_ms,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cache_hit=False
        )

        # 4. Fire and forget Quality Evaluation
        if request.user_id:
            try:
                # Mock a small profile context for evaluation
                eval_context = {"profile": {"subscribed_providers": []}}
                profile = await pref_service.get_user_profile(request.user_id)
                if profile:
                    eval_context["profile"]["subscribed_providers"] = profile.get("subscribed_providers", [])
                
                asyncio.create_task(
                    EvaluationService.evaluate_recommendations(
                        request.user_id, 
                        final_recommendations, 
                        eval_context,
                        query=user_message
                    )
                )
            except Exception as e:
                print(f"⚠️ Failed to start evaluation: {e}")

        return final_res
        
    except Exception as e:
        print(f"❌ Complete error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "ai_response": "I'm having some technical difficulties, but I can still help you find great content!",
            "recommendations": [],
            "query_analysis": {"detected_genre": "action", "detected_language": "english", "detected_content_type": "tv"},
            "total_found": 0,
            "conversation_context": conversation_history
        }
