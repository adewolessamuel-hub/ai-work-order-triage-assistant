#!/usr/bin/env python3
"""AI Work Order Triage Assistant.

Classifies a facilities work order request as P1 / P2 / P3 using the Claude API.

Single request:
    python src/triage.py "Burning smell from the living room outlet" --property "Brookside Village"

Batch (CSV with a request_text column; optional property, location, trade, requester_role):
    python src/triage.py --csv data/work_orders.csv --out results/my_run.csv

Requires ANTHROPIC_API_KEY in the environment. Set TRIAGE_MODEL to change the model.
"""
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "prompts" / "triage_prompt_v4.md"
DEFAULT_MODEL = os.environ.get("TRIAGE_MODEL", "claude-sonnet-5-5")
VALID_PRIORITIES = {"P1", "P2", "P3"}

OUTPUT_INSTRUCTION = """
Respond with ONE JSON object and nothing else, using exactly these keys:
{"ai_priority": "P1|P2|P3", "rationale": "<one sentence>", "missing_info": "<one question or none>", "needs_human_review": true|false}
"""

OUT_FIELDS = ["request_id", "ai_priority", "rationale", "missing_info",
              "needs_human_review", "requires_human_confirmation"]


def load_system_prompt(path=PROMPT_PATH):
    return Path(path).read_text(encoding="utf-8") + "\n" + OUTPUT_INSTRUCTION


def build_user_message(request_text, property_name=None, location=None,
                       trade=None, requester_role=None):
    lines = []
    if property_name:
        lines.append(f"Property: {property_name}")
    if location:
        lines.append(f"Location: {location}")
    if trade:
        lines.append(f"Trade: {trade}")
    if requester_role:
        lines.append(f"Requester: {requester_role}")
    lines.append(f"Request: {request_text}")
    return "\n".join(lines)


def parse_response(text):
    """Extract and validate the JSON object from a model reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in model reply")
    data = json.loads(match.group(0))
    priority = str(data.get("ai_priority", "")).strip().upper()
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"invalid priority: {priority!r}")
    review = data.get("needs_human_review", False)
    if isinstance(review, str):
        review = review.strip().lower() == "true"
    return {
        "ai_priority": priority,
        "rationale": str(data.get("rationale", "")).strip(),
        "missing_info": str(data.get("missing_info", "none")).strip() or "none",
        "needs_human_review": bool(review),
    }


def with_confirmation_flag(result):
    """Safety rule: every P3 and every uncertain call is confirmed by a person."""
    result["requires_human_confirmation"] = (
        result["ai_priority"] == "P3" or result["needs_human_review"]
    )
    return result


def error_result(message):
    """Fail safe: if the model reply cannot be used, a person must look at it."""
    return {
        "ai_priority": "ERROR",
        "rationale": message,
        "missing_info": "none",
        "needs_human_review": True,
        "requires_human_confirmation": True,
    }


def reply_text(reply):
    """Join the text blocks of a reply, skipping thinking or other non-text blocks."""
    parts = [b.text for b in reply.content if isinstance(getattr(b, "text", None), str)]
    if not parts:
        raise ValueError("model reply contained no text block")
    return "".join(parts)


def triage(client, request_text, system_prompt, model=DEFAULT_MODEL, **context):
    user_message = build_user_message(
        request_text,
        context.get("property_name"), context.get("location"),
        context.get("trade"), context.get("requester_role"),
    )
    try:
        reply = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return with_confirmation_flag(parse_response(reply_text(reply)))
    except Exception as exc:  # network, parsing, validation
        return error_result(f"{type(exc).__name__}: {exc}")


def run_batch(client, csv_in, csv_out, system_prompt, model=DEFAULT_MODEL):
    with open(csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            result = triage(
                client, row["request_text"], system_prompt, model,
                property_name=row.get("property"), location=row.get("location"),
                trade=row.get("trade"), requester_role=row.get("requester_role"),
            )
            result["request_id"] = row.get("request_id") or f"ROW-{i:03d}"
            writer.writerow({k: result[k] for k in OUT_FIELDS})
    return len(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description="AI work order triage assistant")
    p.add_argument("request", nargs="?", help="work order request text")
    p.add_argument("--property"); p.add_argument("--location")
    p.add_argument("--trade"); p.add_argument("--role", dest="requester_role")
    p.add_argument("--csv", help="batch mode: input CSV")
    p.add_argument("--out", default="results/triage_run.csv", help="batch mode: output CSV")
    p.add_argument("--prompt", default=str(PROMPT_PATH), help="path to a prompt file")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = p.parse_args(argv)
    if not args.request and not args.csv:
        p.error("give a request text or --csv")

    import anthropic  # imported late so tests do not need the SDK
    client = anthropic.Anthropic()
    system_prompt = load_system_prompt(args.prompt)

    if args.csv:
        n = run_batch(client, args.csv, args.out, system_prompt, args.model)
        print(f"Triaged {n} requests -> {args.out}")
        return 0

    result = triage(client, args.request, system_prompt, args.model,
                    property_name=args.property, location=args.location,
                    trade=args.trade, requester_role=args.requester_role)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Priority:   {result['ai_priority']}")
        print(f"Reason:     {result['rationale']}")
        print(f"Ask:        {result['missing_info']}")
        print(f"Human check needed before dispatch: "
              f"{'YES' if result['requires_human_confirmation'] else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
