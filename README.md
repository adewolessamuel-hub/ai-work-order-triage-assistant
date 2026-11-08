# AI Work Order Triage Assistant

An AI assistant that reads a facilities work order request and assigns a priority, a
one-line reason, the one question a dispatcher should ask next, and a flag for whether a
person should confirm the call before anyone is dispatched.

It was built and evaluated from a facility manager's point of view: the priority scale is
defined by **response time**, and the evaluation asks a practical question — *where can AI
help a service desk, and where must human judgement stay in the loop?*

> **Status: prototype.** Evaluated on 100 fictional requests scored by one human rater.
> It is a decision-support tool, not a replacement for a dispatcher. See [Limitations](#limitations).

## Priority scale

| Level | Meaning | Response |
|---|---|---|
| **P1** | Routine | Handle within 24 hours |
| **P2** | Urgent | Handle within 12 hours |
| **P3** | Emergency, life-threatening | Respond immediately |

P3 is the **highest** priority. The full prompt is in [`prompts/triage_prompt_v2.md`](prompts/triage_prompt_v4.md).

## What it returns

```
$ python src/triage.py "Burning smell from the living room outlet" --property "Brookside Village"
Priority:   P3
Reason:     Warm, discoloured outlet with a burning smell is an active fire hazard.
Ask:        none
Human check needed before dispatch: YES
```

(Illustrative output.) Each result has `ai_priority`, `rationale`, `missing_info`,
`needs_human_review` and `requires_human_confirmation`.

### Built-in safety rule

`requires_human_confirmation` is true for **every P3** and for **every request the model is
unsure about**. If the model's reply cannot be parsed, the result is `ERROR` and a person
must look at it — the tool never silently guesses.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key        # your own key; never commit it

python src/triage.py "Toilet runs all night" --property "Maple Hollow Estate" --trade Plumbing
python src/triage.py --csv data/work_orders.csv --out results/triage_run.csv
python src/evaluate.py                    # compare AI vs manual priorities
python -m unittest discover -s tests      # unit tests (no API key needed)
```

The model defaults to `claude-sonnet-5-5`; override with `TRIAGE_MODEL`.

## Evaluation

**Dataset:** 100 fictional requests — 10 trades × two residential estates and one office
(Maple Hollow Estate, Brookside Village, Lakeshore Corporate Centre). Requests are written in
realistic, sometimes vague language, with a mix of true emergencies, calm reports of serious
problems, and urgent-sounding trivia.

**Method:** the author scored all 100 requests by hand first, then compared them with the AI's
scores. Details and caveats are in [`METHODOLOGY.md`](METHODOLOGY.md).

| | Agreement with AI |
|---|---|
| Manual priorities as first scored (AI pass was blind) | **65 / 100** |
| Manual priorities after review of the AI's safety flags | **70 / 100** |

| Totals | P1 | P2 | P3 |
|---|---|---|---|
| Manual, first pass | 58 | 39 | 3 |
| Manual, revised | 56 | 36 | 8 |
| AI | 66 | 29 | 5 |

### Reproducible API run

The numbers above came from a chat session. To make the result reproducible, the 100 original requests were also run through `src/triage.py` against the Claude API (prompt v4, default model `claude-sonnet-5-5`, one request at a time).

| API run, 100 original requests | Result |
|---|---|
| Agreement with the author's original scores | **60 / 100** |
| Agreement with the author's revised scores | **65 / 100** |
| AI totals (P1 / P2 / P3) | 57 / 26 / 17 (author, revised: 56 / 36 / 8) |
| Time for 100 requests | about 7 minutes, timed by hand (roughly 4 seconds each) |
| Failed rows | 0 |

- **No emergency was under-called:** all 8 of the author's revised P3 requests were rated P3.
- **Every case where the AI rated lower was P2 to P1** (15 of them), mostly everyday nuisances such as mice, a blank thermostat or a pothole.
- **Fire & Life Safety agreement was 3 of 10** because prompt v4 rates every fire-safety item P3, while seven of the author's earlier fire scores were made before that policy existed.
- This run is not directly comparable to the 70% chat figure: it uses the newer prompt and is a separate pass. A v2 run through the API (`--prompt prompts/triage_prompt_v2.md`) gives a like-for-like check.

### Time

Measured by the author on the 100 requests: **20 minutes to score them by hand, and 15
minutes to review the AI's table.** Reviewing every row cost about three-quarters as long as
scoring from scratch, so the saving is small unless the AI's unflagged calls can be trusted.
They cannot yet: checking only the 22 requests the tool flags for confirmation would have
caught just 5 of the 30 disagreements with the revised manual scores.

### Testing a fix: writing the site's policy into the prompt

The biggest gap was fire-safety equipment (Fire & Life Safety agreement 4 of 10). Two versions of a rule were tested.

**v3, a cautious rule** (faulty alarm or missing extinguisher is at least P2). It helped on the data it was written from (fire items 4 to 7 of 10) and barely helped on 30 unseen requests (1 to 2 of 9). The author had scored 8 of those 9 items P3, so the rule was weaker than the author's actual policy.

**v4, the author's stated policy** ("fire safety should be P3"; `prompts/triage_prompt_v4.md`, rule 6). It was tested on 30 fresh requests written after the rule. The AI's answers under v2 and v4 were recorded before the author scored the requests, and the author scored without seeing them.

| 30 fresh requests | v2 prompt | v4 prompt |
|---|---|---|
| Fire-safety items (10) | 1 of 10 | **9 of 10** |
| All other items (20) | 13 of 20 | 13 of 20 |
| All items | 14 of 30 (47%) | **22 of 30 (73%)** |

Takeaways:

- **Once the policy was written down, the AI followed it** (fire items 1 to 9 of 10) without changing its answers elsewhere. The prompt is where a site's policy lives; edit rule 6 for your own site.
- **The one fire-safety miss** was a sprinkler pipe dripping onto a car, which the author scored P2: leak damage, not loss of fire protection. The rule's scope needs that line drawn.
- **The remaining misses show the next policy gaps.** The author scored P3 for a whole building with no water, an office at 29 degrees with staff struggling, and a resident locked inside. The AI said P2. A rule for loss of essential services and anyone trapped would be the next test, again on fresh requests.
- **Caveats:** I wrote the fresh requests knowing the rule, so the fire items are fairly clear-cut. Seven of the author's earlier fire-safety scores on the original 100 (made before the policy was stated) conflict with it and were left as scored. Each further tuning round needs a new fresh set.

## Findings

1. **The AI caught five fire and safety hazards that a fast human pass under-rated.** A
   sparking outlet, a burning-smell outlet, water pouring into a light fixture, a carbon
   monoxide alarm and a gas smell were all rated P3 by the AI. The human first scored them
   P1 or P2 and revised them after seeing the AI's reasoning. A second pair of eyes on
   safety-critical requests has real value.
2. **The AI under-weights compliance gaps and vulnerable occupants.** Where the human scored
   fire-safety equipment higher — a removed smoke alarm, an expired extinguisher, a missing
   extinguisher, a locked-out parent with a baby — the AI rated it lower. Fire & Life Safety
   had the lowest agreement of any trade (4 of 10).
3. **The AI is less cautious on everyday nuisances.** It rated pests, grounds issues and
   comfort complaints P1 where the human chose P2. Whether that is "right" depends on how
   an organisation weighs tenant impact and complaint risk — a policy choice, not a fact.
4. **Design implication:** use the AI as a first-pass sorter and a safety second opinion, keep
   a person on every P3 and every uncertain call, and let the organisation set its own
   thresholds for the middle band.

## Limitations

- **One human rater.** A disagreement does not prove the AI is wrong; there is no ground truth.
- **Fictional data**, written by the author with help from an AI model. Real requests are
  messier and arrive with photos, history and context the AI does not see here.
- **The first AI passes were run in a Claude chat session, not by `src/triage.py`.** A reproducible API run is reported separately above. Its numbers differ because it uses the newer prompt (v4) and is a separate pass.
- **The second AI pass was not blind** (the author had seen the manual scores), and the manual
  scores were revised after seeing the AI's. Both are recorded openly; original scores are kept.
- Not safety-certified. Do not use as the only control for fire, gas or electrical emergencies.

## Repository layout

```
src/triage.py          the assistant (single request and CSV batch)
src/evaluate.py        agreement, confusion matrix, per-trade results
prompts/               prompt v1 (blind pass), v2 (response-time definitions), v3 (cautious fire rule), v4 (fire safety = P3, default)
data/work_orders.csv   the 100 fictional requests
data/manual_priorities.csv   manual scores: original and revised
data/holdout*_*.csv    two sets of 30 unseen requests and the author's scores for them
results/               AI results (v1, v2), hold-out results, and the side-by-side comparisons
scripts/generate_dataset.py  regenerates the dataset (seeded)
tests/                 unit tests with a fake API client
METHODOLOGY.md         how the evaluation was run, and its caveats
```

## License

MIT — see [LICENSE](LICENSE).
