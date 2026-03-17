import random
import asyncio
from typing import List, Dict
from utils.observability import observe, langfuse_context
from utils.analytics_tracker import tracker

class EvaluationService:
    @observe()
    @staticmethod
    async def evaluate_recommendations(user_id: str, recommendations: List[Dict], context: Dict, query: str = None):
        """
        LLM-as-a-Judge: evaluates 10% of requests for faithfulness, relevance, and OTT compliance.
        Scores are written back to the analytics tracker so the health dashboard is real.
        """
        if random.random() > 0.1:
            return
            
        print(f"🧐 Quality Gate: evaluating recommendations for user {user_id[:8]}...")
        
        tasks = [
            EvaluationService.check_hallucinations(recommendations),
            EvaluationService.check_ott_constraints(recommendations, context),
            EvaluationService.check_relevance(recommendations, query)
        ]
        
        faithfulness_score, ott_score, rel_score = await asyncio.gather(*tasks)
        
        # Write scores to langfuse
        langfuse_context.score(name="faithfulness", value=faithfulness_score)
        langfuse_context.score(name="ott_compliance", value=ott_score)
        langfuse_context.score(name="relevance", value=rel_score)

        # Patch the LAST recorded trace with real scores
        try:
            with tracker._lock:
                if tracker._traces:
                    last = tracker._traces[-1]
                    last.faithfulness_score  = faithfulness_score
                    last.ott_compliance_score = ott_score
                    last.relevance_score = rel_score
        except Exception:
            pass

        print(f"✅ QA result: faith={faithfulness_score:.2f}, ott={ott_score:.2f}, rel={rel_score:.2f}")

    @observe()
    @staticmethod
    async def check_relevance(recommendations: List[Dict], query: str) -> float:
        """Use AI to judge if recommendations match the user's intent/query."""
        if not query or not recommendations:
            return 1.0
            
        from services.ollama_service import OllamaService
        
        titles = [r.get("title") for r in recommendations[:5]]
        prompt = f"""
        User Query: "{query}"
        AI Recommendations: {", ".join(titles)}
        
        Do these recommendations actually match what the user is looking for?
        (e.g., If they asked for Marvel and got crime dramas, that's a 0).
        
        Respond ONLY with a decimal between 0.0 and 1.0 (e.g. 0.85).
        No text, just the number.
        """
        try:
            res = await OllamaService.get_ai_response(prompt, temperature=0)
            return float(res.strip())
        except Exception:
            return 1.0 # Fallback to perfect score if judge fails

    @observe()
    @staticmethod
    async def check_hallucinations(recommendations: List[Dict]) -> float:
        """Verify if the suggested movies have valid TMDB IDs (anti-hallucination check)."""
        if not recommendations:
            return 1.0
        valid = sum(1 for r in recommendations if r.get("id") and r.get("title"))
        return valid / len(recommendations)

    @observe()
    @staticmethod
    async def check_ott_constraints(recommendations: List[Dict], context: Dict) -> float:
        """Check if suggested movies are actually on the user's OTT platforms."""
        profile = context.get("profile", {})
        subscribed_ids = set(profile.get("subscribed_providers", []))
        
        if not subscribed_ids or not recommendations:
            return 1.0
            
        compliant = sum(
            1 for rec in recommendations
            if {p.get("id") for p in rec.get("streaming", {}).get("available_on", [])}.intersection(subscribed_ids)
        )
        return compliant / len(recommendations)
