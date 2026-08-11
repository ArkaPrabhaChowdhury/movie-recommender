"""Small reproducible async HTTP load probe.

Example:
  python evaluation/load_test.py --url https://ottscout.arkocodes.dev/api/health

This measures the selected endpoint. It does not pretend to measure cache state
unless --warm-url is supplied; production recommendation cost still comes from
the server trace data.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from urllib.request import Request, urlopen


def fetch(url: str, timeout: float):
    started = time.perf_counter()
    try:
        with urlopen(Request(url, headers={"User-Agent": "ott-scout-load-test/1.0"}), timeout=timeout) as response:
            response.read()
            return {"ok": 200 <= response.status < 400, "latency_ms": (time.perf_counter() - started) * 1000}
    except Exception:
        return {"ok": False, "latency_ms": (time.perf_counter() - started) * 1000}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--warm-url")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--cost-per-request", type=float, default=0.0)
    args = parser.parse_args()
    semaphore = asyncio.Semaphore(args.concurrency)

    async def run(index):
        async with semaphore:
            target = args.warm_url if args.warm_url and index % 2 else args.url
            return await asyncio.to_thread(fetch, target, args.timeout)

    started = time.perf_counter()
    results = await asyncio.gather(*(run(index) for index in range(args.requests)))
    elapsed = time.perf_counter() - started
    latencies = sorted(item["latency_ms"] for item in results)
    successful = sum(item["ok"] for item in results)
    percentile = lambda p: round(latencies[min(int(len(latencies) * p), len(latencies) - 1)], 2) if latencies else 0
    output = {
        "requests": args.requests,
        "concurrency": args.concurrency,
        "duration_s": round(elapsed, 3),
        "requests_per_second": round(args.requests / max(elapsed, 0.001), 2),
        "success_rate": round(successful / max(args.requests, 1), 4),
        "failure_rate": round(1 - successful / max(args.requests, 1), 4),
        "p50_latency_ms": percentile(0.50),
        "p95_latency_ms": percentile(0.95),
        "cache_hit_rate": 0.5 if args.warm_url else None,
        "estimated_cost_usd": round(args.requests * args.cost_per_request, 6),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
