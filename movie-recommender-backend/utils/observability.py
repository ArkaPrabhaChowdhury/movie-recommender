"""
Observability helper — Langfuse tracing with graceful fallback.

langfuse 2.57.4 has langfuse.decorators.
If the keys are not set, tracing is a no-op so the app still runs.
"""

import os
import functools

_langfuse_enabled = False

try:
    from langfuse.decorators import observe as _lf_observe, langfuse_context as _lf_ctx  # type: ignore
    _pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    _sk = os.getenv("LANGFUSE_SECRET_KEY", "")
    # Only enable if real keys are present (not the placeholder strings)
    if _pk and _sk and not _pk.startswith("pk-lf-...") and not _sk.startswith("sk-lf-..."):
        _langfuse_enabled = True
        print("✅ Langfuse tracing ENABLED — traces visible at https://cloud.langfuse.com")
    else:
        print("ℹ️  Langfuse installed but keys not configured — add LANGFUSE_PUBLIC_KEY/SECRET_KEY to .env to activate")
except ImportError:
    print("ℹ️  langfuse not installed — pip install langfuse==2.57.4 to enable tracing")


# ── Public symbols ──────────────────────────────────────────────────────────

# ── Token & Analytics System Explanation ───────────────────────────────────
# The app tracks actual token usage to calculate costs in real-time.
# 1. INPUT TOKENS: The length of the prompt + metadata sent to Groq. 
#    ($0.59 per 1M tokens for Llama-3.3-70b)
# 2. OUTPUT TOKENS: The length of the AI response generated.
#    ($0.79 per 1M tokens for Llama-3.3-70b)
# 3. ANALYTICS TRACKER: Captures these metrics in-memory and provides a 
#    summary via the /analytics/summary endpoint for the Health Dashboard.
# ────────────────────────────────────────────────────────────────────────────

if _langfuse_enabled:
    observe = _lf_observe
    
    # Wrap context in a safe proxy to ensure .score exists even on older SDKs
    class _LangfuseProxy:
        def __getattr__(self, name):
            # Try to get it from the real langfuse_context
            val = getattr(_lf_ctx, name, None)
            if val: return val
            
            # If missing (like .score), return a no-op to prevent app crashes
            def noop(*args, **kwargs): pass
            return noop

    langfuse_context = _LangfuseProxy()
else:
    def observe(func=None, *, name=None, **kwargs):  # type: ignore
        if func is not None:
            return func
        def decorator(fn):
            return fn
        return decorator

    class _NoopContext:
        def update_current_observation(self, **kw): pass
        def update_current_trace(self, **kw): pass
        def score(self, **kw): pass

    langfuse_context = _NoopContext()


__all__ = ["observe", "langfuse_context"]
