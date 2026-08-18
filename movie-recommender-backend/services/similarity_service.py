"""Deterministic ranking for title-to-title recommendations."""

import re
from typing import Dict, Iterable, List


STOPWORDS = {
    "about", "after", "against", "also", "and", "are", "around", "been", "before",
    "being", "between", "from", "have", "into", "that", "their", "there", "these",
    "they", "this", "through", "when", "where", "which", "with", "while", "will",
    "you", "your", "the", "for", "its", "who", "what", "then", "than", "them",
}
# The production function may fall back to lexical overview matching when the
# embedding provider is unavailable, so keep this gate conservative but usable.
MIN_STORY_SIMILARITY = 0.05
MIN_GENRE_FIT = 0.25
MIN_CONTENT_FIT = 0.22


def _genre_ids(item: Dict) -> set:
    genres = item.get("genre_ids") or item.get("genres") or []
    return {genre.get("id") if isinstance(genre, dict) else genre for genre in genres if (genre.get("id") if isinstance(genre, dict) else genre) is not None}


def _story_tokens(item: Dict) -> set:
    words = re.findall(r"[a-z0-9]+", (item.get("overview") or "").lower())
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def story_similarity(source: Dict, candidate: Dict) -> float:
    """Measure shared story vocabulary without using cast or crew metadata."""
    if candidate.get("_story_similarity") is not None:
        return float(candidate["_story_similarity"])
    source_tokens = _story_tokens(source)
    candidate_tokens = _story_tokens(candidate)
    if not source_tokens or not candidate_tokens:
        return 0.0
    return (2 * len(source_tokens & candidate_tokens)) / (len(source_tokens) + len(candidate_tokens))


def similarity_score(source: Dict, candidate: Dict) -> float:
    """Score a candidate: story first, genre second, trending third."""
    genre_fit = len(_genre_ids(source) & _genre_ids(candidate)) / max(len(_genre_ids(source)), 1)
    story_fit = story_similarity(source, candidate)
    content_fit = story_fit * 0.65 + genre_fit * 0.35
    trend_fit = 1.0 if candidate.get("is_trending") else 0.0
    return content_fit * 0.85 + trend_fit * 0.15


def rank_similar_content(source: Dict, candidates: Iterable[Dict], limit: int = 12) -> List[Dict]:
    """Remove invalid/duplicate candidates and return the strongest matches first."""
    source_key = (source.get("content_type"), source.get("id"))
    unique = {}
    for candidate in candidates:
        key = (candidate.get("content_type"), candidate.get("id"))
        if not key[1] or key == source_key or key in unique or not candidate.get("poster"):
            continue
        if candidate.get("streaming") and not candidate["streaming"].get("platform_found"):
            continue
        genre_fit = len(_genre_ids(source) & _genre_ids(candidate)) / max(len(_genre_ids(source)), 1)
        story_fit = story_similarity(source, candidate)
        content_fit = story_fit * 0.65 + genre_fit * 0.35
        if story_fit < MIN_STORY_SIMILARITY or genre_fit < MIN_GENRE_FIT or content_fit < MIN_CONTENT_FIT:
            continue
        unique[key] = candidate
    ranked = sorted(unique.values(), key=lambda item: (similarity_score(source, item), float(item.get("popularity", 0) or 0)), reverse=True)[:limit]
    return [{key: value for key, value in item.items() if key != "_story_similarity"} for item in ranked]
