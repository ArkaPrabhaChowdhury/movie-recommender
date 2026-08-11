# OTT Scout offline evaluation

Frozen dataset: `evaluation/dataset.json` (3 preference scenarios, K=3).

| Strategy | P@3 | R@3 | NDCG@3 | Diversity | Coverage | Language | Subscription | Metadata error | Latency ms | Tokens | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| keyword | 0.778 | 0.889 | 0.875 | 0.889 | 0.600 | 0.889 | 0.889 | 0.000 | 0.015 | 0 | $0.000000 |
| dense | 0.778 | 0.889 | 0.875 | 0.889 | 0.600 | 0.889 | 0.889 | 0.000 | 0.011 | 0 | $0.000000 |
| hybrid | 0.778 | 0.889 | 0.901 | 0.889 | 0.600 | 0.889 | 0.889 | 0.000 | 0.009 | 0 | $0.000000 |
| rerank | 0.778 | 0.889 | 0.901 | 1.000 | 0.600 | 0.778 | 1.000 | 0.000 | 0.010 | 780 | $0.000460 |
| cache | 0.778 | 0.889 | 0.901 | 1.000 | 0.600 | 0.778 | 1.000 | 0.000 | 0.009 | 0 | $0.000000 |

## Interpretation

This is an offline ranking benchmark, not proof of live TMDB, provider, database, email, or LLM behavior. `rerank` and `cache` use deterministic stand-ins for the network/LLM stages; production metrics must come from `system_analytics` and provider logs.
