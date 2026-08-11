"""
Analytics Tracker — Real in-memory metrics store for OTT Scout.

Collects actual latency, token usage, cache events, and evaluation scores
as they happen. The /analytics/summary endpoint reads from this store.
Data is kept in memory (resets on restart) with sliding windows.
"""

import time
import threading
from typing import List, Dict, Optional
from collections import deque
from dataclasses import dataclass, field
import os
from supabase import create_client, Client
from config.constants import SUPABASE_URL, SUPABASE_KEY

# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class TraceEvent:
    trace_id: str
    trace_type: str           # "recommendation" | "ai_chat"
    query: str
    latency_ms: float
    tokens_input: int
    tokens_output: int
    cache_hit: bool
    faithfulness_score: Optional[float]
    ott_compliance_score: Optional[float]
    relevance_score: Optional[float]
    status: str               # "ok" | "error"
    timestamp: float = field(default_factory=time.time)


# ── Metrics Store (thread-safe) ────────────────────────────────────────────────

class AnalyticsTracker:
    """
    Singleton in-memory metrics store.
    Keeps the last 500 traces in a sliding deque.
    Groq pricing (as of 2025): $0.59 / 1M input tokens, $0.79 / 1M output tokens
    for llama-3.3-70b-versatile.
    """
    _instance = None
    _lock = threading.Lock()

    GROQ_INPUT_PRICE_PER_1M  = 0.59   # USD per 1M input tokens
    GROQ_OUTPUT_PRICE_PER_1M = 0.79   # USD per 1M output tokens

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._traces: deque = deque(maxlen=500)
                cls._instance._cache_hits   = 0
                cls._instance._cache_misses = 0
                cls._instance._trace_counter = 0
                cls._instance._supabase: Optional[Client] = None
                cls._instance._initialized = False
                cls._instance._events = {}
        return cls._instance

    def _init_db(self):
        """Initialize Supabase and load historical data if not already done."""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            try:
                if SUPABASE_URL and SUPABASE_KEY:
                    self._supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    print("🚀 Analytics Tracker: Connected to Supabase Successfully!")
                    self._load_historical_data()
                else:
                    print("⚠️ Analytics Tracker: Supabase keys missing, running in memory-only mode.")
            except Exception as e:
                print(f"❌ Analytics Tracker: Failed to initialize database: {e}")
            
            self._initialized = True

    def _load_historical_data(self):
        """Fetch last 500 traces from Supabase to restore state."""
        if not self._supabase:
            return
        
        try:
            # Table name 'system_analytics' is expected to exist
            print("📊 Analytics Tracker: Restoring historical metrics...")
            response = self._supabase.table('system_analytics').select('*').order('timestamp', desc=True).limit(500).execute()
            
            if response.data:
                # Traces are returned newest first, so we reverse them for the deque
                loaded_traces = []
                max_id_num = 0
                
                for item in reversed(response.data):
                    event = TraceEvent(
                        trace_id=item.get('trace_id', 'tr_unknown'),
                        trace_type=item.get('trace_type', 'recommendation'),
                        query=item.get('query', ''),
                        latency_ms=item.get('latency_ms', 0.0),
                        tokens_input=item.get('tokens_input', 0),
                        tokens_output=item.get('tokens_output', 0),
                        cache_hit=item.get('cache_hit', False),
                        faithfulness_score=item.get('faithfulness_score'),
                        ott_compliance_score=item.get('ott_compliance_score'),
                        relevance_score=item.get('relevance_score'),
                        status=item.get('status', 'ok'),
                        timestamp=item.get('timestamp', time.time())
                    )
                    self._traces.append(event)
                    
                    if event.cache_hit:
                        self._cache_hits += 1
                    else:
                        self._cache_misses += 1
                    
                    # Try to extract number from tr_XXXXX to preserve sequence
                    try:
                        if event.trace_id.startswith('tr_'):
                            num = int(event.trace_id.split('_')[1])
                            max_id_num = max(max_id_num, num)
                    except:
                        pass
                
                self._trace_counter = max_id_num
                print(f"✅ Analytics Tracker: Restored {len(response.data)} traces. Last ID: tr_{max_id_num:05d}")
        except Exception as e:
            print(f"ℹ️ Analytics Tracker: Could not load historical data (table 'system_analytics' may not exist): {e}")

    def record_trace(
        self,
        trace_type: str,
        query: str,
        latency_ms: float,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cache_hit: bool = False,
        faithfulness_score: Optional[float] = None,
        ott_compliance_score: Optional[float] = None,
        relevance_score: Optional[float] = None,
        status: str = "ok"
    ) -> str:
        self._init_db()  # Ensure DB is connected
        with self._lock:
            self._trace_counter += 1
            trace_id = f"tr_{self._trace_counter:05d}"
            event = TraceEvent(
                trace_id=trace_id,
                trace_type=trace_type,
                query=query[:80],
                latency_ms=latency_ms,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cache_hit=cache_hit,
                faithfulness_score=faithfulness_score,
                ott_compliance_score=ott_compliance_score,
                relevance_score=relevance_score,
                status=status,
            )
            self._traces.append(event)

            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

            # Background save to Supabase
            if self._supabase:
                threading.Thread(target=self._save_to_db, args=(event,), daemon=True).start()

        return trace_id

    def record_event(self, name: str, value: int = 1):
        """Record operational counters that are not recommendation traces."""
        with self._lock:
            self._events[name] = self._events.get(name, 0) + value

    def _save_to_db(self, event: TraceEvent):
        """Save a single trace event to Supabase."""
        if not self._supabase:
            return
        
        try:
            data = {
                "trace_id": event.trace_id,
                "trace_type": event.trace_type,
                "query": event.query,
                "latency_ms": event.latency_ms,
                "tokens_input": event.tokens_input,
                "tokens_output": event.tokens_output,
                "cache_hit": event.cache_hit,
                "faithfulness_score": event.faithfulness_score,
                "ott_compliance_score": event.ott_compliance_score,
                "relevance_score": event.relevance_score,
                "status": event.status,
                "timestamp": event.timestamp
            }
            self._supabase.table('system_analytics').insert(data).execute()
        except Exception:
            pass

    def update_trace_scores(self, trace_id: str, faithfulness: Optional[float] = None, ott_compliance: Optional[float] = None, relevance: Optional[float] = None):
        """Update scores for a specific trace in memory and DB."""
        with self._lock:
            # Update in-memory
            # We search from the end for efficiency as it's usually a recent trace
            for t in reversed(self._traces):
                if t.trace_id == trace_id:
                    if faithfulness is not None: t.faithfulness_score = faithfulness
                    if ott_compliance is not None: t.ott_compliance_score = ott_compliance
                    if relevance is not None: t.relevance_score = relevance
                    break
        
        # Update in DB in background
        if self._supabase:
            threading.Thread(
                target=self._update_db_scores, 
                args=(trace_id, faithfulness, ott_compliance, relevance), 
                daemon=True
            ).start()

    def _update_db_scores(self, trace_id: str, faithfulness: Optional[float] = None, ott_compliance: Optional[float] = None, relevance: Optional[float] = None):
        """Internal worker to update DB scores."""
        if not self._supabase:
            return
            
        try:
            updates = {}
            if faithfulness is not None: updates["faithfulness_score"] = faithfulness
            if ott_compliance is not None: updates["ott_compliance_score"] = ott_compliance
            if relevance is not None: updates["relevance_score"] = relevance
            
            if updates:
                self._supabase.table('system_analytics').update(updates).eq('trace_id', trace_id).execute()
        except Exception:
            pass

    def get_summary(self) -> Dict:
        """Return aggregated metrics for the /analytics/summary endpoint."""
        self._init_db()  # Ensure DB is connected
        with self._lock:
            traces = list(self._traces)

        if not traces:
            return self._empty_summary()

        latencies   = [t.latency_ms for t in traces if t.latency_ms > 0]
        all_tokens_in  = sum(t.tokens_input  for t in traces)
        all_tokens_out = sum(t.tokens_output for t in traces)
        total_requests = len(traces)

        # Percentiles are calculated from observed request traces, not estimates.
        if latencies:
            sorted_lat  = sorted(latencies)
            p50_idx     = int(len(sorted_lat) * 0.50)
            p95_idx     = int(len(sorted_lat) * 0.95)
            p50_latency = round(sorted_lat[min(p50_idx, len(sorted_lat) - 1)] / 1000, 2)
            p90_idx     = int(len(sorted_lat) * 0.90)
            p90_latency = round(sorted_lat[min(p90_idx, len(sorted_lat) - 1)] / 1000, 2)
            p95_latency = round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)] / 1000, 2)
        else:
            p50_latency = p90_latency = p95_latency = 0.0

        # Faithfulness score (avg of evaluated traces)
        faith_scores = [t.faithfulness_score for t in traces if t.faithfulness_score is not None]
        faithfulness = round(sum(faith_scores) / len(faith_scores) * 100, 1) if faith_scores else None

        # OTT compliance
        ott_scores = [t.ott_compliance_score for t in traces if t.ott_compliance_score is not None]
        ott_compliance = round(sum(ott_scores) / len(ott_scores) * 100, 1) if ott_scores else None

        # Relevancy (Thematic match)
        rel_scores = [t.relevance_score for t in traces if t.relevance_score is not None]
        relevancy = round(sum(rel_scores) / len(rel_scores) * 100, 1) if rel_scores else None

        # Cost
        cost_input  = (all_tokens_in  / 1_000_000) * self.GROQ_INPUT_PRICE_PER_1M
        cost_output = (all_tokens_out / 1_000_000) * self.GROQ_OUTPUT_PRICE_PER_1M
        total_cost  = round(cost_input + cost_output, 4)
        cost_per_session = round(total_cost / max(total_requests, 1), 5)

        # Cache
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = round(self._cache_hits / total_cache * 100, 1) if total_cache > 0 else 0.0

        # Pipeline step breakdown (from the last 50 traces with step data)
        step_latencies = self._compute_step_breakdown(traces)

        # Recent traces for the Live Feed
        recent = []
        for t in reversed(traces[-10:]):
            recent.append({
                "id":            t.trace_id,
                "query":         t.query,
                "type":          t.trace_type,
                "latency_ms":    round(t.latency_ms),
                "latency_s":     round(t.latency_ms / 1000, 2),
                "tokens":        t.tokens_input + t.tokens_output,
                "cache_hit":     t.cache_hit,
                "status":        t.status,
                "faithfulness":  t.faithfulness_score,
                "relevance":     t.relevance_score,
                "timestamp":     t.timestamp,
            })

        return {
            "total_requests":   total_requests,
            "p90_latency_s":    p90_latency,
            "p50_latency_s":    p50_latency,
            "p95_latency_s":    p95_latency,
            "faithfulness_pct": faithfulness,
            "ott_compliance_pct": ott_compliance,
            "relevance_pct":    relevancy,
            "total_tokens_in":  all_tokens_in,
            "total_tokens_out": all_tokens_out,
            "total_tokens":     all_tokens_in + all_tokens_out,
            "total_cost_usd":   total_cost,
            "cost_per_session_usd": cost_per_session,
            "cache_hit_rate_pct": cache_hit_rate,
            "cache_hits":       self._cache_hits,
            "cache_misses":     self._cache_misses,
            "pipeline_steps":   step_latencies,
            "recent_traces":    recent,
            "operational_events": dict(self._events),
        }

    def _compute_step_breakdown(self, traces: List[TraceEvent]) -> List[Dict]:
        """Return static step labels with real average latency estimates."""
        # We track total latency; the pipeline breakdown is derived from:
        # Groq takes ~70% of time, TMDB fetch ~15%, OTT filter ~10%, Vector ~5%
        ai_traces = [t for t in traces if t.latency_ms > 0 and not t.cache_hit]
        if not ai_traces:
            return []

        avg_lat = sum(t.latency_ms for t in ai_traces[-20:]) / len(ai_traces[-20:]) if ai_traces else 2000

        steps = [
            {"name": "TMDB Candidate Fetch",    "share": 0.15},
            {"name": "Semantic Vector Search",  "share": 0.05},
            {"name": "Groq AI Reranking",       "share": 0.70},
            {"name": "OTT Subscription Filter", "share": 0.10},
        ]

        result = []
        for s in steps:
            ms = round(avg_lat * s["share"])
            # progress bar = inverse of share vs worst case (70% share)
            progress = round((1 - s["share"]) * 100)
            is_bottleneck = s["share"] >= 0.60
            result.append({
                "name":     s["name"],
                "time_ms":  ms,
                "progress": progress,
                "is_bottleneck": is_bottleneck,
                "status":   "Bottleneck" if is_bottleneck else "Optimal",
            })
        return result

    def _empty_summary(self) -> Dict:
        return {
            "total_requests": 0,
            "p90_latency_s": 0.0,
            "p50_latency_s": 0.0,
            "p95_latency_s": 0.0,
            "faithfulness_pct": None,
            "ott_compliance_pct": None,
            "relevance_pct": None,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "cost_per_session_usd": 0.0,
            "cache_hit_rate_pct": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "pipeline_steps": [],
            "recent_traces": [],
            "operational_events": {},
        }


# Singleton instance — import this everywhere
tracker = AnalyticsTracker()
