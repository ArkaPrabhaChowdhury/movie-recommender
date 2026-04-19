from fastapi import APIRouter, HTTPException
import asyncio
from datetime import datetime
import time
import json
from utils.observability import observe, langfuse_context
from utils.analytics_tracker import tracker
from models.request_models import AIChatRequest
from services.ollama_service import OllamaService
from services.simple_recommender import SimpleRecommender
from routes.discovery import get_content_with_date_filtering
from routes.search import global_search_with_ott_filtering
from config.constants import LANGUAGE_MAP, DEFAULTS
from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from services.semantic_cache_service import SemanticCacheService
from services.user_preference_service import UserPreferenceService
from services.streaming_service import StreamingService
from services.evaluation_service import EvaluationService
from services.tmdb_service import TMDBService

router = APIRouter()
embedding_service = EmbeddingService()
vector_service = VectorService()
cache_service = SemanticCacheService()
pref_service = UserPreferenceService()

@router.post("/ai-chat")
@observe()
async def ai_chat_recommendation(request: AIChatRequest):
    """AI recommendations with Smart Dispatching (Direct vs Semantic)"""
    try:
        user_message = request.message.strip()
        conversation_history = request.conversation_history or []
        
        print(f"🤖 AI Chat request: '{user_message}'")
        _t0 = time.time()

        # 1. SMART DISPATCHER
        # AI decides if we need a direct search (Director/Actor/Franchise) or semantic search (Vibe/Mood)
        dispatch_prompt = f"""
        User Message: "{user_message}"
        
        CLASSIFICATION RULES:
        - STRATEGY 'direct': Use this for Specific Directors (Nolan, Spielberg), Specific Actors (SRK, Tom Cruise), Specific Franchises (Avengers, Marvel, Harry Potter, Batman), or Exact Titles.
        - STRATEGY 'semantic': Use this for Vibe, Mood, Generic Genres, or Theme-based requests (e.g., "sad movies", "movies that make me cry", "epic action for family night").

        EXAMPLES:
        - "Christopher Nolan movies" -> {{"strategy": "direct", "query": "Christopher Nolan"}}
        - "Avengers movies" -> {{"strategy": "direct", "query": "Avengers"}}
        - "Movies like Interstellar" -> {{"strategy": "semantic", "query": "Mind-bending sci-fi movies about space and time"}}
        - "I want to be scared" -> {{"strategy": "semantic", "query": "Terrifying horror movies"}}

        Respond ONLY with a JSON object:
        {{
            "strategy": "direct" or "semantic",
            "query": "The most relevant entity name or search string",
            "reason": "short explanation"
        }}
        """
        
        dispatch_text = await OllamaService.get_ai_response(dispatch_prompt, temperature=0)
        try:
            import re
            json_match = re.search(r'\{.*\}', dispatch_text, re.DOTALL)
            dispatch_data = json.loads(json_match.group()) if json_match else {"strategy": "semantic", "query": user_message}
        except Exception:
            dispatch_data = {"strategy": "semantic", "query": user_message}
            
        strategy = dispatch_data.get("strategy", "semantic")
        search_query = dispatch_data.get("query", user_message)
        print(f"🔍 Dispatcher chose: {strategy.upper()} for '{search_query}'")

        final_recommendations = []
        
        # 2. EXECUTION PHASE
        if strategy == "direct":
            # Check cache for direct queries too (keyed on dispatcher's extracted query)
            cached_response = await cache_service.get_cached_response(search_query)
            if cached_response:
                latency_ms = (time.time() - _t0) * 1000
                tracker.record_trace(trace_type="ai_chat", query=user_message, latency_ms=latency_ms, cache_hit=True)
                return cached_response

            print(f"🎯 Performing DIRECT search for: '{search_query}'")
            final_recommendations = await global_search_with_ott_filtering(search_query, request.user_id)
            
            # ONLY fallback if we found absolutely nothing at all
            if not final_recommendations:
                print("⚠️ Direct search yielded zero results, trying semantic fallback...")
                strategy = "semantic" 
            else:
                print(f"✅ Found {len(final_recommendations)} direct matches. Skipping semantic search for precision.")

        if strategy == "semantic":
            # Expand intent ONLY if it doesn't look like a direct title/person request
            is_generic = len(user_message.split()) > 2 or any(word in user_message.lower() for word in ['movie', 'show', 'vibe', 'like'])

            if is_generic:
                expansion_prompt = f'Translate vibe into a descriptive search: "{user_message}". NO conversational filler.'
                expanded_query = await OllamaService.get_ai_response(expansion_prompt, temperature=0.1)
                search_query = expanded_query or user_message

            # Check semantic cache on the EXPANDED query so structurally similar phrases
            # with different titles (e.g. "like Vadh" vs "like Daredevil") don't collide
            cached_response = await cache_service.get_cached_response(search_query)
            if cached_response:
                latency_ms = (time.time() - _t0) * 1000
                tracker.record_trace(trace_type="ai_chat", query=user_message, latency_ms=latency_ms, cache_hit=True)
                return cached_response

            print(f"🧠 Performing SEMANTIC search for: '{search_query}'")
            try:
                query_embedding = embedding_service.generate_embedding(search_query)
                if query_embedding:
                    semantic_results = await vector_service.semantic_search(query_embedding=query_embedding, limit=30)
                else:
                    print("⚠️ Semantic search skipped: Failed to generate embedding")
                    semantic_results = []
                
                if semantic_results:
                    candidates = []
                    for item in semantic_results:
                        candidates.append({
                            "id": item['tmdb_id'], "title": item['title'],
                            "poster": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get('poster_path') else None,
                            "rating": item['rating'], "year": item.get('release_date', '')[:4] if item.get('release_date') else '',
                            "overview": item.get('overview', ''), "content_type": item['content_type'],
                            "original_language": item['language'], "source": "vector_chat"
                        })
                    
                    candidates = await StreamingService.get_streaming_providers_batch(candidates, 'both')
                    candidates = [c for c in candidates if c.get("streaming", {}).get("platform_found")]

                    seen_ids = {r['id'] for r in final_recommendations}
                    for c in candidates:
                        if c['id'] not in seen_ids:
                            final_recommendations.append(c)
                            seen_ids.add(c['id'])
            except Exception as e:
                print(f"⚠️ Semantic search failure: {e}")

            # TMDB Similar: when user says "like [title]", fetch TMDB /similar for that title
            # This gives diverse, precise results independent of vector DB coverage
            import re as _re
            like_match = _re.search(r'like\s+(.+?)(?:\s+but|\s+in\s|\s*$)', user_message, _re.IGNORECASE)
            if like_match:
                ref_title = like_match.group(1).strip()
                print(f"🎯 Fetching TMDB similar for reference title: '{ref_title}'")
                try:
                    tmdb_similar = await TMDBService.get_similar_by_title(ref_title)
                    if tmdb_similar:
                        tmdb_similar = await StreamingService.get_streaming_providers_batch(tmdb_similar, 'both')
                        tmdb_similar = [c for c in tmdb_similar if c.get("streaming", {}).get("platform_found")]
                        seen_ids = {r['id'] for r in final_recommendations}
                        for c in tmdb_similar:
                            if c['id'] not in seen_ids:
                                final_recommendations.append(c)
                                seen_ids.add(c['id'])
                except Exception as e:
                    print(f"⚠️ TMDB similar lookup failed: {e}")

        # 2.5 Fallback: Rule-based recommendations when semantic/direct yield nothing
        if not final_recommendations:
            try:
                rule_based = SimpleRecommender.analyze_request(user_message)
                print(f"âš ï¸ Fallback triggered. Using rule-based criteria: {rule_based.get('search_criteria', {})}")

                # 1) Try exact title searches for suggested titles
                suggested_titles = rule_based.get("suggested_titles", []) or []
                for title in suggested_titles:
                    results = await global_search_with_ott_filtering(title, request.user_id)
                    if results:
                        existing_ids = {x['id'] for x in final_recommendations}
                        for r in results:
                            if r['id'] not in existing_ids:
                                final_recommendations.append(r)
                                existing_ids.add(r['id'])

                # 2) If still empty, fall back to genre-based discovery
                if not final_recommendations:
                    criteria = rule_based.get("search_criteria", {})
                    genre = criteria.get("genre", DEFAULTS['GENRE'])
                    language = criteria.get("language", DEFAULTS['LANGUAGE'])
                    content_type = criteria.get("content_type", DEFAULTS['CONTENT_TYPE'])
                    language_code = LANGUAGE_MAP.get(language, None)

                    discovery_results = await get_content_with_date_filtering(
                        language_code=language_code,
                        content_type=content_type,
                        genre=genre,
                        release_period=DEFAULTS['RELEASE_PERIOD'],
                        sort_by='rating',
                        page=1,
                        user_id=request.user_id
                    )
                    final_recommendations.extend(discovery_results or [])
            except Exception as e:
                print(f"âš ï¸ Fallback recommendation failure: {e}")

        # 3. AI RESPONDER (STRICT MODE)
        final_recommendations = final_recommendations[:15]
        titles_context = ", ".join([r['title'] for r in final_recommendations[:5]])
        
        response_prompt = f"""
        SYSTEM RULE: You are a direct recommendation engine. 
        USER REQUEST: "{user_message}"
        TITLES WE FOUND: [{titles_context}]
        
        TASK:
        1. Write a 1-sentence response confirming these matches.
        2. DO NOT suggest, mention, or hallucinate ANY movies that are NOT in the list above.
        3. Keep it brief and factual.
        """
        chat_response = await OllamaService.get_ai_response(response_prompt, temperature=0.7)
        if not chat_response:
            chat_response = f"I found the best matches for '{user_message}'!"

        final_res = {
            "ai_response": chat_response,
            "recommendations": final_recommendations,
            "query_analysis": {
                "detected_genre": dispatch_data.get("strategy", "semantic"),
                "detected_language": "any",
                "detected_content_type": "both",
                "mood": dispatch_data.get("reason", "ai_dispatch")
            },
            "total_found": len(final_recommendations),
            "conversation_context": conversation_history + [{
                "ai": chat_response,
                "timestamp": datetime.now().isoformat()
            }]
        }
        
        # Save to Cache using the expanded query so future semantically-similar
        # but entity-distinct queries (e.g. "like Vadh" vs "like Daredevil") don't collide
        await cache_service.set_cached_response(search_query, final_res)
        
        # Analytics Tracking
        latency_ms = (time.time() - _t0) * 1000
        tokens_in, tokens_out = 0, 0
        try:
            tok = getattr(tracker, '_last_tokens', (0, 0))
            tokens_in, tokens_out = tok
        except Exception: pass

        trace_id = tracker.record_trace(
            trace_type="ai_chat",
            query=user_message,
            latency_ms=latency_ms,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cache_hit=False
        )
        # 4. Evaluation (Fire and Forget)
        if request.user_id:
            try:
                eval_context = {"profile": {"subscribed_providers": []}}
                profile = await pref_service.get_user_profile(request.user_id)
                if profile:
                    eval_context["profile"]["subscribed_providers"] = profile.get("subscribed_providers", [])
                
                asyncio.create_task(
                    EvaluationService.evaluate_recommendations(
                        request.user_id, 
                        final_recommendations, 
                        eval_context,
                        query=user_message,
                        trace_id=trace_id
                    )
                )
            except Exception: pass

        return final_res
        
    except Exception as e:
        print(f"❌ Complete error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ai_response": "I'm having some technical difficulties, but I can still help you find great content!",
            "recommendations": [],
            "query_analysis": {"detected_genre": "action", "detected_language": "english", "detected_content_type": "both"},
            "total_found": 0,
            "conversation_context": conversation_history
        }
