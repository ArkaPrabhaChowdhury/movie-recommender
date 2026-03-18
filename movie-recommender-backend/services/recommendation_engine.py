"""
Recommendation Engine — v4 (AI-Powered)
=======================================
A fast, AI-first recommendation system that focuses on:
- User History: Likes, Watched, Watchlisted, and Disliked content.
- Language Agnostic: Dynamically adapts to any language preferences.
- AI Reranking: Uses Groq (via OllamaService) to analyze profile and rerank candidates.
- Efficiency: Minimizes external API calls by fetching broad candidate pools.
"""

import asyncio
import random
import httpx
import time
from typing import List, Dict, Set, Optional
from collections import defaultdict
from datetime import datetime
from utils.observability import observe, langfuse_context
from utils.analytics_tracker import tracker

from services.user_preference_service import UserPreferenceService
from services.ollama_service import OllamaService
from services.streaming_service import StreamingService
from services.tmdb_service import TMDBService
from config.constants import (
    TMDB_API_KEY, TMDB_API_URL, API_CONFIG, IMAGE_CONFIG, LANGUAGE_MAP
)
from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from services.evaluation_service import EvaluationService

class RecommendationEngine:
    def __init__(self):
        self.user_service = UserPreferenceService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()

    @observe()
    async def get_personalized_recommendations(self, user_id: str, limit: int = 20) -> Dict:
        _t0 = time.time()
        try:
            # 1. Gather Context
            context = await self.user_service.get_recommendation_context(user_id)
            if not context["has_preferences"]:
                return await self._get_trending_fallback(limit)

            profile = context["profile"]
            languages = profile.get("preferred_languages", ["en"])

            # 2. Extract Disliked and Watched IDs to exclude/deprioritize
            disliked_ids = {str(item["content_id"]) for item in context["disliked"]}
            watched_ids = {str(item["content_id"]) for item in context["watched"]}
            liked_ids = {str(item["content_id"]) for item in context["liked"]}
            watchlisted_ids = {str(item["content_id"]) for item in context["watchlisted"]}
            
            all_known_ids = disliked_ids | watched_ids | liked_ids | watchlisted_ids

            # 3. Gather Candidates (Fast & Broad)
            candidates = await self._gather_candidates(context)
            
            fresh_candidates = [
                c for c in candidates 
                if str(c.get("id")) not in all_known_ids
            ]

            if not fresh_candidates:
                fresh_candidates = [
                    c for c in candidates 
                    if str(c.get("id")) not in (disliked_ids | liked_ids)
                ]

            # 4. AI Reranking with Groq
            # Reduced pool size for better latency (60 instead of 100)
            recommended = await self._ai_rerank(context, fresh_candidates[:60], limit * 3)

            # 5. Check OTT Availability
            with_ott = await StreamingService.get_streaming_providers_batch(recommended, 'both')

            # 6. Strict Subscription Filter
            subscribed_ids = set(profile.get("subscribed_providers", []))
            
            if subscribed_ids:
                final_recommendations = []
                for item in with_ott:
                    all_platforms = item.get("streaming", {}).get("available_on", [])
                    user_platforms = [
                        p for p in all_platforms 
                        if p.get("id") in subscribed_ids and not p.get("is_rent")
                    ]
                    if user_platforms:
                        new_item = item.copy()
                        new_item["streaming"] = item["streaming"].copy()
                        new_item["streaming"]["available_on"] = user_platforms
                        final_recommendations.append(new_item)
                print(f"🎯 Subscription Filter: {len(with_ott)} -> {len(final_recommendations)}")
            else:
                final_recommendations = [
                    item for item in with_ott 
                    if item.get("streaming", {}).get("platform_found")
                ]
                print(f"⚠️ No subscriptions, returning all {len(final_recommendations)} OTT items")

            latency_ms = (time.time() - _t0) * 1000

            # Collect token data from OllamaService if recorded
            tokens_in, tokens_out = 0, 0
            try:
                tok = getattr(tracker, '_last_tokens', (0, 0))
                tokens_in, tokens_out = tok
            except Exception:
                pass

            # 7. Quality Assurance (Background Task)
            res = {
                "recommendations": final_recommendations[:limit],
                "algorithm": "ai_personalized_v4",
                "personalization_level": self._get_personalization_level(context),
                "user_stats": {
                    "likes": len(context["liked"]),
                    "watches": len(context["watched"]),
                    "watchlist": len(context["watchlisted"]),
                    "top_genres": profile.get("preferred_genres", [])[:3]
                },
                "thinking_process": {
                    "steps": [
                        {"step": "Context Analysis", "status": "completed",
                         "details": f"Analyzed {len(context['liked'])} likes and {len(profile.get('preferred_genres', []))} preferred genres."},
                        {"step": "Candidate Retrieval", "status": "completed",
                         "details": f"Gathered {len(fresh_candidates)} fresh candidates from {len(languages)} languages."},
                        {"step": "Groq AI Reranking", "status": "completed",
                         "details": f"Reranked top 100 candidates. Tokens used: {tokens_in}+{tokens_out}."},
                        {"step": "OTT Filtering", "status": "completed",
                         "details": f"Filtered for {len(subscribed_ids)} subscribed platforms. {len(final_recommendations)} passed."}
                    ],
                    "latency_ms": round(latency_ms),
                    "tokens_used": tokens_in + tokens_out,
                }
            }

            # Record to analytics tracker
            trace_id = tracker.record_trace(
                trace_type="recommendation",
                query=f"personalized:{user_id[:8]}",
                latency_ms=latency_ms,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cache_hit=False,
            )
            print(f"📊 Analytics trace recorded: {trace_id} ({latency_ms:.0f}ms)")

            # Fire and forget evaluation
            # Use query analysis results for the judge context if available
            eval_query = f"Personalized recommendations based on {len(context['liked'])} likes and genres: {profile.get('preferred_genres', [])[:5]}"
            asyncio.create_task(EvaluationService.evaluate_recommendations(user_id, res["recommendations"], context, query=eval_query, trace_id=trace_id))
            
            return res

        except Exception as e:
            latency_ms = (time.time() - _t0) * 1000
            tracker.record_trace(trace_type="recommendation", query="error",
                                 latency_ms=latency_ms, status="error")
            print(f"❌ AI Recommendation Error: {e}")
            import traceback; traceback.print_exc()
            return await self._get_trending_fallback(limit)

    @observe()
    async def _gather_candidates(self, context: Dict) -> List[Dict]:
        """Fetch candidates according to user profile languages and genres, balancing sources."""
        profile = context["profile"]
        genres = profile.get("preferred_genres", ["action", "drama"])[:3]
        languages = profile.get("preferred_languages", ["en"])[:4]
        
        # We'll collect candidates in groups to balance them later
        source_groups = {
            "global_trending": [],
            "language_trending": [],
            "genre_discovery": [],
            "similar": [],
            "vector_discovery": []
        }
        
        tasks = []
        
        # 1. Vector Search (Semantic Discovery based on ALL positive interactions)
        liked = context.get("liked", [])
        watchlisted = context.get("watchlisted", [])
        positive_interactions = liked + watchlisted
        
        if positive_interactions:
            tasks.append(("vector_discovery", self._fetch_semantic_candidates(positive_interactions, profile)))
        
        # 2. Global Trending
        tasks.append(("global_trending", self._fetch_trending()))
        
        # 2. Per Language & Genre Discovery
        for lang in languages:
            tasks.append(("language_trending", self._fetch_trending(lang)))
            for genre in genres:
                tasks.append(("genre_discovery", self._fetch_discover(genre, lang)))
        
        # 3. Similar to Liked
        for item in context.get("liked", [])[:5]:
            tasks.append(("similar", self._fetch_similar(item["content_id"], item["content_type"])))
            
        # Execute all tasks
        api_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        # Sort results into groups
        for (group_name, _), res in zip(tasks, api_results):
            if isinstance(res, list):
                source_groups[group_name].extend(res)
        
        # Deduplicate and balance
        candidates = []
        seen_ids = set()
        
        # Helper to add item if not seen
        def add_item(item):
            if item['id'] not in seen_ids:
                candidates.append(item)
                seen_ids.add(item['id'])
                return True
            return False

        # THE BALANCING ACT:
        # Instead of global popularity sort, we take items from each source group in a round-robin or weighted way.
        # This prevents English Global Trending from drowning out Hindi niche genres.
        
        # Prioritize Language Specific Trending and Genre Discovery
        lang_items = source_groups["language_trending"]
        genre_items = source_groups["genre_discovery"]
        similar_items = source_groups["similar"]
        vector_items = source_groups["vector_discovery"]
        global_items = source_groups["global_trending"]
        
        # 1. First, take some from vector discovery (Highest semantic relevance)
        for item in vector_items[:60]: add_item(item)

        # 2. Then take from language trending (Local relevance)
        for item in lang_items[:40]: add_item(item)
        
        # 3. Then take some from genre discovery
        for item in genre_items[:40]: add_item(item)
        
        # 4. Then take some from similar
        for item in similar_items[:40]: add_item(item)
        
        # 5. Finally, fill with global trending if needed
        for item in global_items[:30]: add_item(item)
        
        # Print stats for debugging
        print(f"📦 Gathered {len(candidates)} candidates following profile: {languages} / {genres}")
        print(f"   Sources: Vector({len(vector_items)}) Lang({len(lang_items)}) Genre({len(genre_items)}) Similar({len(similar_items)}) Global({len(global_items)})")
        
        return candidates

    @observe()
    async def _ai_rerank(self, context: Dict, candidates: List[Dict], limit: int) -> List[Dict]:
        """Use AI to rank candidates according to profile without artificial bias."""
        if not candidates:
            return []

        profile = context["profile"]
        liked_titles = [item["title"] for item in context.get("liked", [])[:10]]
        watched_titles = [item["title"] for item in context.get("watched", [])[:10]]
        watchlisted_titles = [item["title"] for item in context.get("watchlisted", [])[:10]]
        disliked_titles = [item["title"] for item in context.get("disliked", [])[:10]]
        
        candidate_list = ""
        # Reduce rerank pool to 60 for better latency (was 100)
        for i, c in enumerate(candidates[:60]):
            genre_str = ", ".join(c.get("genres", []))
            lang = c.get("original_language", "en")
            title = c.get("title", "Unknown")
            year = c.get("year", "N/A")
            overview = c.get("overview", "")[:80] # Shorter overview for faster processing
            candidate_list += f"[{i}] {title} ({year}) [{lang}] - {genre_str}. {overview}\n"

        prompt = f"""
        You are a premium movie recommendation AI.
        User Profile:
        - Liked: {", ".join(liked_titles) or "None"}
        - Watched: {", ".join(watched_titles) or "None"}
        - Watchlisted: {", ".join(watchlisted_titles) or "None"}
        - Disliked (STRICTLY EXCLUDE): {", ".join(disliked_titles) or "None"}
        - Preferred Genres: {", ".join(profile.get('preferred_genres', []))}
        - Preferred Languages: {", ".join(profile.get('preferred_languages', []))}

        Task: Select {limit} items from the candidates that match this profile.
        Rank them based on thematic similarity to liked items and genre fit.
        Respect the language preferences equally as listed in the profile.
        
        Provide a CRISP recommendation reason for each (MAX 5-6 words).
        If it's similar to a specific movie they liked, use: "Because you liked [Movie Title]".
        Otherwise, use a 2-3 word genre reason (e.g., "Gritty crime thriller").
        Keep it short so it fits in a single line on a small UI card.

        Candidates:
        {candidate_list}

        Respond ONLY with a JSON object:
        {{
            "recommendations": [
                {{"index": 0, "reason": "Reason here"}},
                ...
            ]
        }}
        Example reasons: "Because you liked Inception", "Dark psychological drama", "Because you liked Interstellar".
        """

        print(f"🤖 AI Reranking {len(candidates[:100])} candidates...")
        ai_response = await OllamaService.get_ai_response(prompt, temperature=0.1)
        
        try:
            import json, re
            match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if match:
                data = json.loads(match.group())
                recs = data.get("recommendations", [])
                
                final_list = []
                for r in recs:
                    idx = r.get("index")
                    if isinstance(idx, int) and 0 <= idx < len(candidates):
                        item = dict(candidates[idx])
                        item["recommendation_reason"] = r.get("reason", "Matches your taste profile")
                        final_list.append(item)
                
                if final_list:
                    print(f"✅ AI selected {len(final_list)} items.")
                    return final_list[:limit]
        except Exception as e:
            print(f"⚠️ AI Parsing Error: {e}")
        
        return candidates[:limit]

    @observe()
    async def _fetch_semantic_candidates(self, interactions: List[Dict], profile: Dict) -> List[Dict]:
        """Generate a taste vector from interactions and search the Vector DB."""
        try:
            import numpy as np
            
            # 1. Collect texts for all interactions to build the taste vector
            texts = []
            weights = []
            
            for item in interactions:
                # Weight Liked items more than Watchlisted
                weight = 1.0 if item.get("action") == "liked" else 0.6
                
                title = item.get("title", "")
                overview = item.get("overview", "")
                # Create a concise but descriptive string for the interaction
                text = f"{title}. {overview[:150]}"
                
                texts.append(text)
                weights.append(weight)
            
            if not texts:
                return []
                
            # 2. Generate embeddings for history
            print(f"🧠 Vectorizing {len(texts)} history items for taste profile...")
            embeddings = self.embedding_service.generate_batch_embeddings(texts)
            
            # 3. Calculate Weighted Average (The "Taste Vector")
            avg_vector = np.average(embeddings, axis=0, weights=weights)
            taste_vector = avg_vector.tolist()
            
            # 4. Search Vector DB
            # Get preferred languages for filtering
            pref_langs = profile.get("preferred_languages", ["en", "hi"])
            
            print(f"🔍 Searching Vector DB for semantic matches...")
            # We fetch 100 candidates to ensure variety
            results = await self.vector_service.semantic_search(
                query_embedding=taste_vector,
                limit=100,
                content_type="both",
                language="any" # Let re-ranking handle language weighting
            )
            
            mapped = []
            for item in results:
                mapped.append({
                    "id": item['tmdb_id'],
                    "title": item['title'],
                    "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}" if item.get('poster_path') else None,
                    "rating": item['rating'],
                    "year": item.get('release_date', '')[:4] if item.get('release_date') else '',
                    "overview": item.get('overview', ''),
                    "content_type": item['content_type'],
                    "original_language": item['language'],
                    "source": "vector"
                })
            
            return mapped

        except Exception as e:
            print(f"⚠️ Vector discovery error: {e}")
            return []

    # --- Helper Fetchers ---

    async def _fetch_trending(self, language: Optional[str] = None, page: int = 1) -> List[Dict]:
        try:
            params = {"api_key": TMDB_API_KEY, "page": page}
            if language:
                # Use discover to get latest popular items for this specific language
                from config.constants import get_date_range
                df, dt = get_date_range("6months")
                
                movie_task = TMDBService.fetch_movies(language, "all", df, dt, page=page)
                tv_task = TMDBService.fetch_tv_shows(language, genre="all", date_from=df, date_to=dt, page=page)
                
                res = await asyncio.gather(movie_task, tv_task)
                return list(res[0]) + list(res[1])
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{TMDB_API_URL}/trending/all/week"
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    return self._map_tmdb_results(results)
        except Exception as e:
            print(f"⚠️ Fetch Trending Error: {e}")
        return []

    async def _fetch_discover(self, genre: str, language: str, page: int = 1) -> List[Dict]:
        try:
            from config.constants import get_date_range
            date_from, date_to = get_date_range("all")
            
            movie_task = TMDBService.fetch_movies(language, genre, date_from, date_to, page=page)
            tv_task = TMDBService.fetch_tv_shows(language, genre, date_from, date_to, page=page)
            
            movies, tvs = await asyncio.gather(movie_task, tv_task)
            return list(movies) + list(tvs)
        except Exception as e:
            print(f"⚠️ Fetch Discover Error: {e}")
        return []

    async def _fetch_similar(self, content_id: int, content_type: str) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{TMDB_API_URL}/{content_type}/{content_id}/similar"
                resp = await client.get(url, params={"api_key": TMDB_API_KEY})
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    return self._map_tmdb_results(results, content_type)
        except: pass
        return []

    def _map_tmdb_results(self, items: List[Dict], ctype: Optional[str] = None) -> List[Dict]:
        mapped = []
        
        # Reverse map for display/AI context
        from config.constants import MOVIE_GENRE_MAP, TV_GENRE_MAP
        movie_rev = {v: k for k, v in MOVIE_GENRE_MAP.items()}
        tv_rev = {v: k for k, v in TV_GENRE_MAP.items()}
        
        for item in items:
            media_type = ctype or item.get("media_type")
            if media_type not in ["movie", "tv"]: continue
            
            # Map genre IDs to names
            gids = item.get("genre_ids", [])
            rev_map = movie_rev if media_type == "movie" else tv_rev
            genre_names = [rev_map[gid].capitalize() for gid in gids if gid in rev_map]
            
            mapped.append({
                "id": item["id"],
                "title": item.get("title") or item.get("name"),
                "content_type": media_type,
                "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}" if item.get("poster_path") else None,
                "rating": item.get("vote_average", 0),
                "year": (item.get("release_date") or item.get("first_air_date", ""))[:4],
                "overview": item.get("overview", ""),
                "original_language": item.get("original_language", ""),
                "popularity": item.get("popularity", 0),
                "genres": genre_names
            })
        return mapped

    async def _get_trending_fallback(self, limit: int) -> Dict:
        items = await self._fetch_trending()
        return {
            "recommendations": items[:limit],
            "algorithm": "trending_fallback",
            "personalization_level": "none",
            "message": "Interact with more content to get better recommendations!"
        }

    def _get_personalization_level(self, context: Dict) -> str:
        count = context.get("total_interactions", 0)
        if count > 20: return "high"
        if count > 5: return "medium"
        return "low"
