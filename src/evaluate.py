#!/usr/bin/env python3
"""Compare AI priorities with the manual priorities and print a summary.

    python src/evaluate.py
    python src/evaluate.py --ai results/ai_triage_results_v1.csv --write results/comparison.csv
"""
import argparse
import collections
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEVEL = {"P1": 1, "P2": 2, "P3": 3}


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def agreement(manual, ai):
    hits = sum(manual[i] == ai[i]["ai_priority"] for i in ai)
    return hits, len(ai)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manual", default=str(ROOT / "data" / "manual_priorities.csv"))
    p.add_argument("--ai", default=str(ROOT / "results" / "ai_triage_results_v2.csv"))
    p.add_argument("--dataset", default=str(ROOT / "data" / "work_orders.csv"))
    p.add_argument("--write", help="write a side-by-side comparison CSV")
    args = p.parse_args()

    manual_rows = read(args.manual)
    orig = {r["request_id"]: r["manual_original"] for r in manual_rows}
    rev = {r["request_id"]: r["manual_revised"] for r in manual_rows}
    ai = {r["request_id"]: r for r in read(args.ai)}
    data = {r["request_id"]: r for r in read(args.dataset)}

    for name, manual in (("original", orig), ("revised", rev)):
        hits, n = agreement(manual, ai)
        print(f"Agreement with manual_{name}: {hits}/{n} = {hits / n:.0%}")
        c = collections.Counter(manual.values())
        print(f"  manual {name}: P1={c['P1']} P2={c['P2']} P3={c['P3']}")
    c = collections.Counter(r["ai_priority"] for r in ai.values())
    print(f"  AI: P1={c['P1']} P2={c['P2']} P3={c['P3']}")

    print("\nConfusion (rows = manual_revised, cols = AI):")
    cm = collections.Counter((rev[i], ai[i]["ai_priority"]) for i in ai)
    print("        P1  P2  P3")
    for m in ("P1", "P2", "P3"):
        print(f"  {m}   " + "  ".join(f"{cm[(m, a)]:>2}" for a in ("P1", "P2", "P3")))

    higher = sum(LEVEL[ai[i]["ai_priority"]] > LEVEL[rev[i]] for i in ai)
    lower = sum(LEVEL[ai[i]["ai_priority"]] < LEVEL[rev[i]] for i in ai)
    print(f"\nAI rated higher than manual_revised on {higher}, lower on {lower}")

    print("\nAgreement by trade (manual_revised):")
    by = collections.defaultdict(lambda: [0, 0])
    for i in ai:
        t = data[i]["trade"]
        by[t][1] += 1
        by[t][0] += rev[i] == ai[i]["ai_priority"]
    for t, (h, n) in sorted(by.items()):
        print(f"  {t:<28} {h}/{n}")

    safety = [i for i in ai if LEVEL[ai[i]["ai_priority"]] < LEVEL[rev[i]]]
    print(f"\nRequests where the AI rated BELOW manual_revised ({len(safety)}):")
    for i in safety:
        print(f"  {i} manual={rev[i]} ai={ai[i]['ai_priority']}  {data[i]['request_text'][:80]}")

    if args.write:
        with open(args.write, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["request_id", "property", "trade", "request_text", "manual_original",
                        "manual_revised", "ai_priority", "match_original", "match_revised",
                        "ai_rationale", "ai_missing_info", "ai_needs_human_review"])
            for i in ai:
                a = ai[i]
                w.writerow([i, data[i]["property"], data[i]["trade"], data[i]["request_text"],
                            orig[i], rev[i], a["ai_priority"], orig[i] == a["ai_priority"],
                            rev[i] == a["ai_priority"], a["rationale"], a["missing_info"],
                            a["needs_human_review"]])
        print(f"\nWrote {args.write}")


if __name__ == "__main__":
    main()
