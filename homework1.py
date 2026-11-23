"""Homework 1: GPU Media Worker — 10 assets in one run, timed, with cost per asset.

Stdlib only. Run it RIGHT AFTER you click Create on the Sana Endpoint:

    python3 homework1.py

It asks for the Endpoint URL and token (token via getpass, never printed) unless
ENDPOINT_URL / ENDPOINT_TOKEN are set in the environment or in a local .env file.

What it does (one startup, one model load, ten generations):
  1. Polls GET /v1/models until the model answers -> time from Create to ready.
  2. Asks how long Create -> RUNNING took in the console, to split startup vs load.
  3. Generates 10 images (one prompt per storybook page), timing each call.
  4. Writes runs/<timestamp>/page-XX.png, metrics.json and a cost summary.
Then STOP the Endpoint in the console.

Re-compute costs later from a saved run (no GPU needed):
    python3 homework1.py --recost runs/<timestamp>/metrics.json --price 0.75
"""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import math
import os
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- your idea --
# Edit IDEA and PAGES to make it yours. Keep it free of real people, brands and
# known characters. Same CHARACTER text + same SEED on every page helps keep
# the character recognisable (it won't be perfect — see lesson 02).
IDEA = "A 10-page children's bedtime storybook about Pip, a small otter lighthouse keeper"
CHARACTER = (
    "Pip, a small round sea otter with chestnut-brown fur, a cream belly, "
    "a yellow knitted beanie and a tiny blue scarf"
)
STYLE = "soft watercolor children's book illustration, warm gentle light, simple shapes, no text"
PAGES = [
    "Pip waking up in a cosy bed at the top of a red-and-white lighthouse at sunrise",
    "Pip polishing the giant glass lamp of the lighthouse with a cloth",
    "Pip waving to a small fishing boat from the rocky shore",
    "Pip collecting shiny shells on a sandy beach with seagulls nearby",
    "Pip sharing a picnic of fish sandwiches with a friendly puffin",
    "Pip watching dark storm clouds roll in over a choppy sea",
    "Pip climbing the spiral lighthouse stairs holding a lantern during the storm",
    "Pip lighting the great lamp, its beam cutting through rain and waves",
    "the little fishing boat arriving safely in the harbour guided by the beam, Pip cheering",
    "Pip asleep under the stars on the lighthouse balcony, calm sea, crescent moon",
]
SEED = 7

# ---------------------------------------------------------- run settings -----
MODEL = "Efficient-Large-Model/Sana_1600M_1024px_diffusers"
SIZE = "512x512"
STEPS = 20
GUIDANCE = 4.5
GPU = "L40S"
# $/hour your run paid. Default: preemptible L40S 1gpu-8vcpu-32gb, eu-north1,
# as read by the course on 2026-11-16. CHECK https://nebius.com/prices on the
# day you run and pass --price if it differs.
DEFAULT_PRICE_PER_HOUR = 0.75
PROJECT_N = 1000


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _ctx() -> ssl.SSLContext:
    try:
        import certifi  # optional, avoids macOS python cert issues

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def call(base: str, token: str, path: str, body: dict | None = None, timeout: int = 300) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method="POST" if body is not None else "GET",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        return json.loads(r.read())


def wait_ready(base: str, token: str, limit_s: int = 1800) -> float:
    t0 = time.perf_counter()
    last = ""
    while True:
        elapsed = time.perf_counter() - t0
        try:
            call(base, token, "/v1/models", timeout=10)
            print(f"\n  ready after {elapsed:.1f} s")
            return elapsed
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit(f"\nHTTP {e.code}: token rejected. Check the token and re-run.")
            last = f"HTTP {e.code}"
        except Exception as e:  # connection refused, DNS not yet, timeouts...
            last = type(e).__name__
        if elapsed > limit_s:
            sys.exit(f"\nNot ready after {limit_s} s ({last}). Check the Endpoint logs, then STOP it.")
        print(f"\r  waiting {elapsed:6.0f} s  ({last})        ", end="", flush=True)
        time.sleep(2)


def cost_summary(m: dict, price_per_hour: float, n: int = PROJECT_N) -> dict:
    per_s = price_per_hour / 3600
    lat = list(m["latency_s"].values())
    median = statistics.median(lat)
    fixed_s = m["startup_s"] + m["load_s"]
    F = fixed_s * per_s
    c = median * per_s
    return {
        "price_per_hour_usd": price_per_hour,
        "fixed_time_s": round(fixed_s, 1),
        "median_generation_s": round(median, 3),
        "fixed_cost_F_usd": round(F, 4),
        "cost_per_asset_c_usd": round(c, 6),
        "cost_per_asset_at_N": {
            str(k): round(F / k + c, 6) for k in (1, 10, n)
        },
        "actual_run_cost_usd_10_assets": round((fixed_s + sum(lat)) * per_s, 4),
    }


def print_summary(m: dict, s: dict) -> None:
    lat = m["latency_s"]
    print("\nPer-asset times (s):")
    for k, v in lat.items():
        print(f"  {k}: {v:.2f}")
    print(
        f"""
Startup (Create -> RUNNING): {m['startup_s']:.1f} s
Model load (RUNNING -> ready): {m['load_s']:.1f} s
Fixed time per run:           {s['fixed_time_s']} s
Median generation per asset:  {s['median_generation_s']} s      <- Question 6
Price used:                   ${s['price_per_hour_usd']}/h ({m.get('gpu')})
Fixed cost per run  F = ${s['fixed_cost_F_usd']}
Cost per asset      c = ${s['cost_per_asset_c_usd']}
Projected cost/asset at N=1:    ${s['cost_per_asset_at_N']['1']}
Projected cost/asset at N=10:   ${s['cost_per_asset_at_N']['10']}
Projected cost/asset at N={PROJECT_N}: ${s['cost_per_asset_at_N'][str(PROJECT_N)]}   <- Question 7
"""
    )


def ask_seconds(prompt: str) -> float:
    while True:
        ans = input(prompt).strip().lower().rstrip("s").strip()
        if not ans:
            return 0.0
        try:
            return float(ans)
        except ValueError:
            print("   Please type a number of seconds, e.g. 48.5")


def run(price: float, startup_arg: float | None = None, load_arg: float | None = None) -> None:
    load_dotenv()
    base = os.environ.get("ENDPOINT_URL") or input("Endpoint URL (https://...): ").strip()
    token = os.environ.get("ENDPOINT_TOKEN") or getpass.getpass("Endpoint token (hidden): ").strip()

    out = Path("runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    print("1) Waiting for the model to answer (start this right after clicking Create)...")
    create_to_ready = wait_ready(base, token)

    if startup_arg is not None and load_arg is not None:
        # Endpoint was already up: times read from the Endpoint's console logs.
        startup_s, load_s = startup_arg, load_arg
    else:
        startup_s = ask_seconds(
            "\n2) In the console, how many seconds from Create until status RUNNING?\n"
            "   (Endpoint page / events; blank = count it all as model load): "
        )
        load_s = max(create_to_ready - startup_s, 0.0)

    print(f"\n3) Generating {len(PAGES)} assets...")
    latency: dict[str, float] = {}
    for i, page in enumerate(PAGES, 1):
        prompt = f"{CHARACTER}. {page}. {STYLE}"
        body = {
            "model": MODEL, "prompt": prompt, "size": SIZE, "n": 1,
            "response_format": "b64_json", "num_inference_steps": STEPS,
            "guidance_scale": GUIDANCE, "negative_prompt": "", "seed": SEED,
        }
        t = time.perf_counter()
        payload = call(base, token, "/v1/images/generations", body)
        dt = time.perf_counter() - t
        png = base64.b64decode(payload["data"][0]["b64_json"])
        name = f"page-{i:02d}"
        (out / f"{name}.png").write_bytes(png)
        latency[name] = round(dt, 3)
        print(f"  {name}: {dt:.2f} s")

    metrics = {
        "idea": IDEA, "model": MODEL, "modality": "image", "how": "Endpoint", "gpu": GPU,
        "size": SIZE, "steps": STEPS, "guidance_scale": GUIDANCE, "seed": SEED,
        "started_utc": started, "startup_s": round(startup_s, 1), "load_s": round(load_s, 1),
        "create_to_ready_s": round(create_to_ready, 1), "latency_s": latency,
        "prompts": {f"page-{i:02d}": f"{CHARACTER}. {p}. {STYLE}" for i, p in enumerate(PAGES, 1)},
    }
    summary = cost_summary(metrics, price)
    metrics["cost"] = summary
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print_summary(metrics, summary)
    print(f"Saved to {out}/\n\n>>> NOW STOP (or delete) THE ENDPOINT IN THE NEBIUS CONSOLE <<<")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--price", type=float, default=DEFAULT_PRICE_PER_HOUR, help="USD per GPU-hour your run paid")
    ap.add_argument("--startup-s", type=float, help="Create -> container start, from the Endpoint logs")
    ap.add_argument("--load-s", type=float, help="container start -> model ready, from the Endpoint logs")
    ap.add_argument("--recost", type=Path, help="recompute costs from an existing metrics.json")
    a = ap.parse_args()
    if a.recost:
        m = json.loads(a.recost.read_text())
        s = cost_summary(m, a.price)
        m["cost"] = s
        a.recost.write_text(json.dumps(m, indent=2))
        print_summary(m, s)
    else:
        run(a.price, a.startup_s, a.load_s)


if __name__ == "__main__":
    main()
