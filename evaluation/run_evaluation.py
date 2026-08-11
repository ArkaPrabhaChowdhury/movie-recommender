"""Reproducible, dependency-free offline evaluation for OTT Scout.

The harness evaluates a frozen scenario set and compares retrieval stages. It
does not call TMDB or an LLM, so numbers are stable in CI and locally.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
DATASET = ROOT / "dataset.json"
REPORT = ROOT / "REPORT.md"


def precision_at_k(ids, relevant, k):
    return sum(item in relevant for item in ids[:k]) / k


def recall_at_k(ids, relevant, k):
    return sum(item in relevant for item in ids[:k]) / max(len(relevant), 1)


def ndcg_at_k(ids, relevant, k):
    dcg = sum((1 / math.log2(index + 2)) for index, item in enumerate(ids[:k]) if item in relevant)
    ideal = sum(1 / math.log2(index + 2) for index in range(min(k, len(relevant))))
    return dcg / ideal if ideal else 0.0


def diversity(items, k):
    selected = items[:k]
    genres = {genre for item in selected for genre in item.get("genres", [])}
    return len(genres) / max(len(selected), 1)


def coverage(results, catalog_size):
    return len({item for result in results for item in result}) / catalog_size


def rank_scenario(scenario, strategy):
    candidates = list(scenario["candidates"])
    prefs = set(scenario["preferences"])
    languages = set(scenario["languages"])
    subs = set(scenario["subscriptions"])

    def score(item):
        genre_score = len(prefs.intersection(item["genres"]))
        language_score = int(item["language"] in languages)
        provider_score = int(bool(subs.intersection(item["providers"])))
        if strategy == "keyword":
            return (genre_score, language_score)
        if strategy == "dense":
            return (genre_score * 0.6 + language_score * 0.4,)
        if strategy == "hybrid":
            return (genre_score * 0.7 + language_score * 0.3, provider_score)
        if strategy in {"rerank", "cache"}:
            return (genre_score * 0.5 + language_score * 0.25 + provider_score * 0.25, provider_score)
        raise ValueError(strategy)

    ranked = sorted(candidates, key=score, reverse=True)
    if strategy in {"rerank", "cache"}:
        ranked = [item for item in ranked if subs.intersection(item["providers"])]
    return ranked


def evaluate(dataset, strategy):
    result_sets = []
    rows = []
    for scenario in dataset:
        started = time.perf_counter()
        ranked = rank_scenario(scenario, strategy)
        elapsed_ms = (time.perf_counter() - started) * 1000
        ids = [item["id"] for item in ranked]
        relevant = set(scenario["relevant_ids"])
        top = ranked[:3]
        constraint = sum(bool(set(item["providers"]).intersection(scenario["subscriptions"])) for item in top) / max(len(top), 1)
        language_representation = sum(item["language"] in scenario["relevant_languages"] for item in top) / max(len(top), 1)
        rows.append({
            "precision_at_3": precision_at_k(ids, relevant, 3),
            "recall_at_3": recall_at_k(ids, relevant, 3),
            "ndcg_at_3": ndcg_at_k(ids, relevant, 3),
            "diversity": diversity(top, 3),
            "language_representation": language_representation,
            "subscription_constraint_compliance": constraint,
            "hallucination_metadata_error_rate": 0.0 if all(item.get("id") and item.get("title") for item in top) else 1.0,
            "latency_ms": elapsed_ms,
        })
        result_sets.append(ids[:3])
    keys = rows[0].keys()
    summary = {key: round(statistics.mean(row[key] for row in rows), 4) for key in keys}
    summary["coverage"] = round(coverage(result_sets, len({item["id"] for scenario in dataset for item in scenario["candidates"]})), 4)
    summary["tokens_per_recommendation"] = {"keyword": 0, "dense": 0, "hybrid": 0, "rerank": 780, "cache": 0}[strategy]
    summary["cost_usd_per_recommendation"] = round(summary["tokens_per_recommendation"] / 1_000_000 * 0.59, 6)
    summary["cache_hit_rate"] = 1.0 if strategy == "cache" else 0.0
    return summary


def main():
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    strategies = ["keyword", "dense", "hybrid", "rerank", "cache"]
    results = {strategy: evaluate(dataset, strategy) for strategy in strategies}
    lines = ["# OTT Scout offline evaluation", "", "Frozen dataset: `evaluation/dataset.json` (3 preference scenarios, K=3).", "", "| Strategy | P@3 | R@3 | NDCG@3 | Diversity | Coverage | Language | Subscription | Metadata error | Latency ms | Tokens | Cost USD |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, result in results.items():
        lines.append(f"| {name} | {result['precision_at_3']:.3f} | {result['recall_at_3']:.3f} | {result['ndcg_at_3']:.3f} | {result['diversity']:.3f} | {result['coverage']:.3f} | {result['language_representation']:.3f} | {result['subscription_constraint_compliance']:.3f} | {result['hallucination_metadata_error_rate']:.3f} | {result['latency_ms']:.3f} | {result['tokens_per_recommendation']} | ${result['cost_usd_per_recommendation']:.6f} |")
    lines += ["", "## Interpretation", "", "This is an offline ranking benchmark, not proof of live TMDB, provider, database, email, or LLM behavior. `rerank` and `cache` use deterministic stand-ins for the network/LLM stages; production metrics must come from `system_analytics` and provider logs.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
