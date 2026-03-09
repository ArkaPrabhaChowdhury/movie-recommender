"""
Recommendation Engine — v2
==========================
Four algorithms run in parallel and are merged + scored:

1. Content-Based (TF-IDF)  — finds content whose overview text is similar to
                             what the user has liked.
2. Actor / Director        — fetches content featuring actors / directors the
                             user has shown interest in.
3. Popularity-Personalized — trending within the user's preferred genres &
                             languages.
4. Collaborative Filtering — mirrors what similar users liked (works best with
                             multiple users on the shared JSON store).

New-user fallback fetches the global TMDB "trending this week" list instead of
always returning Hindi drama.

Every recommendation carries a human-readable `recommendation_reason` string
("Because you liked <title>", "Featuring <actor>", etc.).
"""

import math
import re
import asyncio
import httpx
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Tuple

from services.user_preference_service import UserPreferenceService
from routes.discovery import get_content_with_date_filtering
from config.constants import (
    LANGUAGE_MAP, TMDB_API_KEY, TMDB_API_URL, API_CONFIG, IMAGE_CONFIG
)


# ─────────────────────────────────────────────────────────────────────────────
# Tiny TF-IDF implementation (no external libraries needed)
# ─────────────────────────────────────────────────────────────────────────────

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "this", "that", "it", "its",
    "he", "she", "they", "we", "you", "i", "his", "her", "their", "our",
    "their", "him", "them", "us", "who", "what", "which", "when", "where",
    "how", "as", "into", "about", "after", "before", "between", "through",
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def _tf(tokens: List[str]) -> Dict[str, float]:
    total = len(tokens) or 1
    return {w: count / total for w, count in Counter(tokens).items()}


def _cosine_similarity(tf_a: Dict[str, float], tf_b: Dict[str, float]) -> float:
    common = set(tf_a) & set(tf_b)
    if not common:
        return 0.0
    dot = sum(tf_a[w] * tf_b[w] for w in common)
    mag_a = math.sqrt(sum(v ** 2 for v in tf_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in tf_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _text_similarity(text_a: str, text_b: str) -> float:
    """Return cosine similarity [0, 1] between two overview strings."""
    return _cosine_similarity(_tf(_tokenize(text_a)), _tf(_tokenize(text_b)))


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationEngine:
    def __init__(self):
        self.user_service = UserPreferenceService()

    # ── public entry point ───────────────────────────────────────────────────

    async def get_personalized_recommendations(
        self, user_id: str, limit: int = 15
    ) -> Dict:
        try:
            context = await self.user_service.get_recommendation_context(user_id)

            if not context["has_preferences"]:
                return await self._get_trending_fallback(limit)

            recommendations = await self._run_algorithms(context, limit)

            return {
                "recommendations": recommendations,
                "algorithm": "hybrid_v2",
                "personalization_level": self._personalization_level(context),
                "user_stats": {
                    "total_interactions": context["total_interactions"],
                    "total_liked": context["profile"].get("total_liked", 0),
                    "top_genres": context["profile"].get("preferred_genres", [])[:3],
                    "top_actors": context["profile"].get("liked_actors", [])[:3],
                },
            }

        except Exception as e:
            print(f"❌ Recommendation engine error: {e}")
            import traceback; traceback.print_exc()
            return await self._get_trending_fallback(limit)

    # ── algorithm orchestrator ───────────────────────────────────────────────

    async def _run_algorithms(self, context: Dict, limit: int) -> List[Dict]:
        per_algo = max(limit // 4, 5)

        results = await asyncio.gather(
            self._content_based_tfidf(context, per_algo * 2),   # extra budget — best signal
            self._actor_director_based(context, per_algo),
            self._popularity_personalized(context, per_algo),
            self._collaborative_filtering(context, per_algo),
            return_exceptions=True,
        )

        all_recs: List[Dict] = []
        for algo_result in results:
            if isinstance(algo_result, Exception):
                print(f"⚠️ Algorithm error (skipped): {algo_result}")
                continue
            all_recs.extend(algo_result)

        # Deduplicate keeping first occurrence (highest-confidence algorithm first)
        seen: set = set()
        unique: List[Dict] = []
        for rec in all_recs:
            key = f"{rec.get('content_type', '')}_{rec.get('id', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(rec)

        # Score and sort
        for rec in unique:
            rec["personalization_score"] = self._score(rec, context)

        unique.sort(key=lambda x: x["personalization_score"], reverse=True)
        return unique[:limit]

    # ── Algorithm 1: Content-based TF-IDF ───────────────────────────────────

    async def _content_based_tfidf(self, context: Dict, limit: int) -> List[Dict]:
        """
        Build TF vectors from the overviews the user has liked.
        Fetch candidate pools by preferred genre × language, then rank by
        cosine similarity to the merged liked-overview corpus.
        """
        try:
            recent_liked = context.get("recent_liked", [])
            if not recent_liked:
                return []

            # Build a "taste profile" TF vector from liked overviews
            liked_texts = " ".join(
                item.get("overview", "") for item in recent_liked if item.get("overview")
            )
            if not liked_texts.strip():
                return []

            taste_tf = _tf(_tokenize(liked_texts))
            liked_ids = {item["content_id"] for item in recent_liked}

            preferred_genres = context["profile"].get("preferred_genres", [])[:3]
            preferred_languages = context["profile"].get("preferred_languages", [])[:2]

            if not preferred_genres or not preferred_languages:
                return []

            # Fetch candidate content pools in parallel
            tasks = []
            combos = []
            for genre in preferred_genres:
                for lang in preferred_languages:
                    lang_code = LANGUAGE_MAP.get(lang, "en")
                    tasks.append(
                        get_content_with_date_filtering(lang_code, "both", genre, "2years")
                    )
                    combos.append((genre, lang))

            pools = await asyncio.gather(*tasks, return_exceptions=True)

            scored: List[Tuple[float, Dict]] = []
            for (genre, lang), pool in zip(combos, pools):
                if isinstance(pool, Exception):
                    continue
                for item in pool:
                    if item.get("id") in liked_ids:
                        continue
                    overview = item.get("overview", "")
                    sim = _text_similarity(liked_texts, overview) if overview else 0.0
                    if sim > 0.05:  # minimum relevance threshold
                        # Pick the most similar liked item for the reason string
                        best_reason_title = self._best_reason_title(
                            overview, recent_liked
                        )
                        item = dict(item)  # copy before mutation
                        item["recommendation_reason"] = (
                            f"Because you liked \"{best_reason_title}\""
                            if best_reason_title
                            else f"Matches your taste in {genre}"
                        )
                        item["_sim_score"] = sim
                        scored.append((sim, item))

            scored.sort(key=lambda t: t[0], reverse=True)
            return [item for _, item in scored[:limit]]

        except Exception as e:
            print(f"❌ TF-IDF content-based error: {e}")
            return []

    def _best_reason_title(self, candidate_overview: str, liked: List[Dict]) -> str:
        """Return the title of the liked item most similar to the candidate."""
        best_sim, best_title = 0.0, ""
        for item in liked:
            sim = _text_similarity(candidate_overview, item.get("overview", ""))
            if sim > best_sim:
                best_sim = sim
                best_title = item.get("title", "")
        return best_title

    # ── Algorithm 2: Actor / Director based ─────────────────────────────────

    async def _actor_director_based(self, context: Dict, limit: int) -> List[Dict]:
        """
        Use the stored actors/directors from liked interactions to search TMDB
        for other content featuring those people.
        """
        try:
            liked_actors = context["profile"].get("liked_actors", [])[:5]
            liked_directors = context["profile"].get("liked_directors", [])[:3]
            people = liked_actors + liked_directors

            if not people:
                return []

            liked_ids = {item["content_id"] for item in context.get("recent_liked", [])}
            results: List[Dict] = []

            async with httpx.AsyncClient(timeout=API_CONFIG["TIMEOUT"]) as client:
                # Search TMDB for each person and get their work
                person_tasks = [
                    self._fetch_person_credits(client, name) for name in people[:6]
                ]
                person_credits = await asyncio.gather(*person_tasks, return_exceptions=True)

                for person_name, credits in zip(people, person_credits):
                    if isinstance(credits, Exception) or not credits:
                        continue
                    is_actor = person_name in liked_actors
                    role = "starring" if is_actor else "directed by"

                    for item in credits:
                        if item.get("id") in liked_ids:
                            continue
                        item = dict(item)
                        item["recommendation_reason"] = (
                            f"{role.capitalize()} {person_name}"
                        )
                        results.append(item)

            # Deduplicate within this algorithm
            seen: set = set()
            unique: List[Dict] = []
            for r in results:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    unique.append(r)

            # Prefer higher-rated content
            unique.sort(key=lambda x: x.get("rating", 0), reverse=True)
            return unique[:limit]

        except Exception as e:
            print(f"❌ Actor/director-based error: {e}")
            return []

    async def _fetch_person_credits(
        self, client: httpx.AsyncClient, person_name: str
    ) -> List[Dict]:
        """Search for a person in TMDB and return their top-rated movie/TV credits."""
        try:
            resp = await client.get(
                f"{TMDB_API_URL}/search/person",
                params={"api_key": TMDB_API_KEY, "query": person_name},
            )
            if resp.status_code != 200:
                return []

            people = resp.json().get("results", [])
            if not people:
                return []

            person_id = people[0]["id"]

            # Fetch combined credits
            credits_resp = await client.get(
                f"{TMDB_API_URL}/person/{person_id}/combined_credits",
                params={"api_key": TMDB_API_KEY},
            )
            if credits_resp.status_code != 200:
                return []

            raw_credits = credits_resp.json()
            items: List[Dict] = []

            for credit in raw_credits.get("cast", []) + raw_credits.get("crew", []):
                media_type = credit.get("media_type", "")
                if media_type not in ("movie", "tv"):
                    continue
                if credit.get("vote_average", 0) < 6.0:
                    continue
                if not credit.get("poster_path"):
                    continue

                title = credit.get("title") or credit.get("name", "")
                items.append(
                    {
                        "id": credit["id"],
                        "title": title,
                        "content_type": media_type,
                        "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{credit['poster_path']}",
                        "rating": credit.get("vote_average", 0),
                        "year": (credit.get("release_date") or credit.get("first_air_date", ""))[:4],
                        "overview": credit.get("overview", ""),
                        "original_language": credit.get("original_language", ""),
                        "genre_ids": credit.get("genre_ids", []),
                        "release_date": credit.get("release_date") or credit.get("first_air_date", ""),
                    }
                )

            # Sort by rating and return top results
            items.sort(key=lambda x: x["rating"], reverse=True)
            return items[:8]

        except Exception as e:
            print(f"⚠️ Person credit fetch error for '{person_name}': {e}")
            return []

    # ── Algorithm 3: Popularity-personalized ────────────────────────────────

    async def _popularity_personalized(self, context: Dict, limit: int) -> List[Dict]:
        """
        Fetch recently popular content per preferred genre × language combo,
        annotated with a clear reason.
        """
        try:
            preferred_genres = context["profile"].get("preferred_genres", [])[:2]
            preferred_languages = context["profile"].get("preferred_languages", [])[:2]

            if not preferred_genres or not preferred_languages:
                return []

            liked_ids = {item["content_id"] for item in context.get("recent_liked", [])}

            tasks = []
            combos = []
            for genre in preferred_genres:
                for lang in preferred_languages:
                    lang_code = LANGUAGE_MAP.get(lang, "en")
                    tasks.append(
                        get_content_with_date_filtering(lang_code, "both", genre, "6months")
                    )
                    combos.append((genre, lang))

            pools = await asyncio.gather(*tasks, return_exceptions=True)

            results: List[Dict] = []
            for (genre, lang), pool in zip(combos, pools):
                if isinstance(pool, Exception):
                    continue
                for item in pool:
                    if item.get("id") in liked_ids:
                        continue
                    item = dict(item)
                    item["recommendation_reason"] = (
                        f"Popular {genre} content in {lang.capitalize()}"
                    )
                    results.append(item)

            results.sort(
                key=lambda x: x.get("rating", 0) * math.log1p(x.get("vote_count", 1)),
                reverse=True,
            )
            return results[:limit]

        except Exception as e:
            print(f"❌ Popularity-personalized error: {e}")
            return []

    # ── Algorithm 4: Collaborative filtering ────────────────────────────────

    async def _collaborative_filtering(self, context: Dict, limit: int) -> List[Dict]:
        """
        Find other users with overlapping tastes (Jaccard on genres + languages)
        and surface content they liked that the current user hasn't seen.
        """
        try:
            user_genres = set(context["profile"].get("preferred_genres", []))
            user_languages = set(context["profile"].get("preferred_languages", []))
            current_user_id = context["profile"].get("user_id")
            liked_ids = {item["content_id"] for item in context.get("recent_liked", [])}

            preferences_data = self.user_service._load_data(
                self.user_service.preferences_file
            )
            profiles_data = self.user_service._load_data(
                self.user_service.profiles_file
            )

            similar_users: List[Tuple[str, float]] = []
            for uid, profile in profiles_data.items():
                if uid == current_user_id:
                    continue
                other_genres = set(profile.get("preferred_genres", []))
                other_langs = set(profile.get("preferred_languages", []))

                g_sim = len(user_genres & other_genres) / max(len(user_genres | other_genres), 1)
                l_sim = len(user_languages & other_langs) / max(len(user_languages | other_langs), 1)
                sim = (g_sim * 0.7 + l_sim * 0.3)

                if sim > 0.3:
                    similar_users.append((uid, sim))

            similar_users.sort(key=lambda t: t[1], reverse=True)

            results: List[Dict] = []
            for uid, sim in similar_users[:5]:
                for interaction in preferences_data.get(uid, []):
                    if interaction["action"] != "liked":
                        continue
                    if interaction["content_id"] in liked_ids:
                        continue
                    results.append(
                        {
                            "id": interaction["content_id"],
                            "content_type": interaction["content_type"],
                            "title": interaction["title"],
                            "genres": interaction.get("genres", []),
                            "language": interaction.get("language", ""),
                            "recommendation_reason": "Liked by users with similar taste",
                            "_collab_score": sim,
                        }
                    )

            results.sort(key=lambda x: x.get("_collab_score", 0), reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"❌ Collaborative filtering error: {e}")
            return []

    # ── Scoring ──────────────────────────────────────────────────────────────

    def _score(self, content: Dict, context: Dict) -> float:
        score = content.get("rating", 0)  # TMDB base score out of 10

        # Genre match bonus (2 pts each)
        content_genres = [g.lower() for g in content.get("genres", [])]
        preferred_genres = [g.lower() for g in context["profile"].get("preferred_genres", [])]
        score += len(set(content_genres) & set(preferred_genres)) * 2.0

        # Language match bonus
        content_lang = content.get("original_language", content.get("language", "")).lower()
        preferred_languages = [
            l.lower() for l in context["profile"].get("preferred_languages", [])
        ]
        if content_lang in preferred_languages:
            score += 1.5

        # Recency bonus (< 1 year old)
        release = content.get("release_date", "")
        if release:
            try:
                days_old = (datetime.now() - datetime.strptime(release[:10], "%Y-%m-%d")).days
                if days_old < 365:
                    score += 0.5
            except ValueError:
                pass

        # Text-similarity bonus already embedded in _sim_score
        score += content.get("_sim_score", 0) * 3.0

        # Collaborative score bonus
        score += content.get("_collab_score", 0) * 2.0

        return round(score, 3)

    def _personalization_level(self, context: Dict) -> str:
        interactions = context["total_interactions"]
        liked = context["profile"].get("total_liked", 0)
        if interactions >= 20 and liked >= 10:
            return "high"
        elif interactions >= 5 and liked >= 3:
            return "medium"
        return "low"

    # ── New-user fallback : global trending ─────────────────────────────────

    async def _get_trending_fallback(self, limit: int) -> Dict:
        """
        For brand-new users fetch TMDB's global weekly trending list rather
        than a hard-coded Hindi drama query.
        """
        try:
            async with httpx.AsyncClient(timeout=API_CONFIG["TIMEOUT"]) as client:
                resp = await client.get(
                    f"{TMDB_API_URL}/trending/all/week",
                    params={"api_key": TMDB_API_KEY},
                )

            items: List[Dict] = []
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    media_type = item.get("media_type", "")
                    if media_type not in ("movie", "tv"):
                        continue
                    if not item.get("poster_path"):
                        continue

                    title = item.get("title") or item.get("name", "")
                    items.append(
                        {
                            "id": item["id"],
                            "title": title,
                            "content_type": media_type,
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}",
                            "rating": item.get("vote_average", 0),
                            "year": (item.get("release_date") or item.get("first_air_date", ""))[:4],
                            "overview": item.get("overview", ""),
                            "original_language": item.get("original_language", ""),
                            "genre_ids": item.get("genre_ids", []),
                            "release_date": item.get("release_date") or item.get("first_air_date", ""),
                            "recommendation_reason": "Trending worldwide this week",
                        }
                    )

            if not items:
                # Hard fallback if TMDB trending fails
                items = await get_content_with_date_filtering(None, "both", "all", "6months")
                for it in items:
                    it["recommendation_reason"] = "Popular right now"

            return {
                "recommendations": items[:limit],
                "algorithm": "trending_fallback",
                "personalization_level": "none",
                "message": "Start liking content to get personalised recommendations!",
            }

        except Exception as e:
            print(f"❌ Trending fallback error: {e}")
            return {
                "recommendations": [],
                "algorithm": "error",
                "personalization_level": "none",
            }
