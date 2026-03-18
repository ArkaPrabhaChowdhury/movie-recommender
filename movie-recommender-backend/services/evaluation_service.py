import random
import asyncio
from typing import List, Dict
from utils.observability import observe, langfuse_context
from utils.analytics_tracker import tracker

class EvaluationService:
    @observe()
    @staticmethod
    async def evaluate_recommendations(user_id: str, recommendations: List[Dict], context: Dict, query: str = None, trace_id: str = None):
        """
        LLM-as-a-Judge: evaluates 30% of requests for exhaustive quality audit.
        Now includes a 'Mistake Reason' to see exactly why it failed.
        """
        if random.random() > 0.3:
            return
            
        print(f"🧐 Quality Gate: evaluating recommendations for user {user_id[:8]}...")
        
        # Parallel Audit
        tasks = [
            EvaluationService.check_hallucinations(recommendations),
            EvaluationService.check_ott_constraints(recommendations, context),
            EvaluationService.check_relevance(recommendations, query)
        ]
        
        faithfulness_score, ott_score, rel_data = await asyncio.gather(*tasks)
        rel_score, rel_reason = rel_data # Decompose tuple
        
        # 1. Log to Langfuse (with Reasoning)
        langfuse_context.score(name="faithfulness", value=faithfulness_score)
        langfuse_context.score(name="ott_compliance", value=ott_score)
        langfuse_context.score(
            name="relevance", 
            value=rel_score,
            comment=f"Audit Mistakes: {rel_reason}" # Capture the 'WHY'
        )
        
        # 2. Patch the trace for the Dashboard
        if trace_id:
            tracker.update_trace_scores(
                trace_id=trace_id, 
                faithfulness=faithfulness_score, 
                ott_compliance=ott_score, 
                relevance=rel_score
            )
            print(f"✅ QA result recorded for trace {trace_id}: rel={rel_score:.2f}")
        else:
            # Fallback to last trace if no trace_id provided (deprecated)
            try:
                with tracker._lock:
                    if tracker._traces:
                        last = tracker._traces[-1]
                        last.faithfulness_score  = faithfulness_score
                        last.ott_compliance_score = ott_score
                        last.relevance_score = rel_score
            except Exception: pass

    @observe()
    @staticmethod
    async def check_relevance(recommendations: List[Dict], query: str) -> tuple:
        """Use AI to judge if ALL matches are strict. Returns (core, mistakes_json)."""
        if not query or not recommendations:
            return (1.0, "[]")
            
        from services.ollama_service import OllamaService
        
        # FORMAT ITEMS FOR JUDGE
        items_list = []
        for i, r in enumerate(recommendations):
            items_list.append({
                "index": i+1,
                "title": r.get('title'),
                "overview": r.get('overview', '')[:80]
            })
        
        prompt = f"""
        USER INTENT: "{query}"
        PROPOSED LIST: {json.dumps(items_list)}
        
        CRITICAL TASK:
        Find every item that DOES NOT strictly match the intent.
        
        SCORING RULES:
        1. If user asks for a 'DIRECT' person (Nolan) or franchise (DC), ANY non-member is a 0.5 penalty.
        2. More than 2 unrelated items = 0.0 total score.
        
        RESPONSE FORMAT (JSON ONLY):
        {{
            "score": 0.0-1.0,
            "mistakes": ["Item X is not related because..."],
            "reasoning": "Overall audit summary"
        }}
        """
        try:
            res_text = await OllamaService.get_ai_response(prompt, temperature=0)
            # Try to parse JSON from AI
            import re
            match = re.search(r'\{.*\}', res_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return (float(data.get('score', 1.0)), json.dumps(data.get('mistakes', [])))
            return (1.0, "[]")
        except Exception as e:
            print(f"⚠️ Judge failed: {e}")
            return (1.0, "[]")

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
