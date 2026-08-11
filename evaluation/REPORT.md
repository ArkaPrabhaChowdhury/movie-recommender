# OTT Scout offline evaluation

Frozen dataset: `evaluation/dataset.json` expanded into 36 deterministic cases (3 scenario templates x 12 test conditions, K=3). Conditions cover regional languages, subscriptions, dislikes, like-not-like queries, missing metadata, provider failures, duplicates, hallucinated availability, and cold/warm cache labels.

| Strategy | P@3 | R@3 | NDCG@3 | Diversity | Coverage | Language | Subscription | Metadata error | Latency ms | Tokens | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| keyword | 0.787 | 0.898 | 0.883 | 0.778 | 0.556 | 0.889 | 0.833 | 0.083 | 0.009 | 0 | $0.000000 |
| dense | 0.787 | 0.898 | 0.883 | 0.778 | 0.556 | 0.889 | 0.833 | 0.083 | 0.012 | 0 | $0.000000 |
| hybrid | 0.806 | 0.917 | 0.926 | 0.778 | 0.611 | 0.889 | 0.861 | 0.083 | 0.009 | 0 | $0.000000 |
| rerank | 0.768 | 0.870 | 0.891 | 0.898 | 0.667 | 0.759 | 1.000 | 0.083 | 0.014 | 780 | $0.000460 |
| cache | 0.768 | 0.870 | 0.891 | 0.898 | 0.667 | 0.759 | 1.000 | 0.083 | 0.019 | 0 | $0.000000 |

## Interpretation

This is an offline ranking benchmark, not proof of live TMDB, provider, database, email, or LLM behavior. `rerank` and `cache` use deterministic stand-ins for the network/LLM stages; production metrics must come from `system_analytics` and provider logs.
