# Methodology

## 1. Dataset

`data/work_orders.csv` holds 100 fictional work order requests: 10 per trade across Plumbing,
HVAC, Electrical, Carpentry, Painting & Drywall, Roofing & Envelope, Landscaping & Grounds,
Pest Control, Fire & Life Safety, and Locksmith & Access Control. They are spread over three
fictional properties — two residential estates and one office — with timestamps across
October 2026, a requester role and an intake channel.

Requests were written to resemble real reports: some are clearly urgent, some are calm
descriptions of serious problems (a gas smell, a CO alarm that "stopped on its own"), some
sound urgent but are cosmetic, and some lack information a dispatcher would need.
`scripts/generate_dataset.py` regenerates the file exactly (seeded).

## 2. Priority scale

Two versions of the scale were used, both set by the author:

- **v1** (`prompts/triage_prompt_v1.md`): P1 routine, P2 urgent, P3 emergency / life-saving.
- **v2** (`prompts/triage_prompt_v2.md`): P1 handled within 24 hours, P2 within 12 hours,
  P3 immediately and life-threatening.

## 3. Manual scoring

The author scored all 100 requests by hand using the v1 scale, before seeing any AI output
(`manual_original`). A one-line reasoning column was offered but not filled in, so there is no
written reasoning for individual calls.

## 4. AI scoring

| Pass | Prompt | Blind to manual scores? |
|---|---|---|
| `ai_triage_results_v1.csv` | v1 | **Yes** — completed before the manual scores were opened |
| `ai_triage_results_v2.csv` | v2 | **No** — the manual scores had been seen. v2 was applied to the request text, and four ratings changed (all P2 → P1) |

Both of these AI passes were produced by Claude applying the prompt to each request in a chat
session, not by calling `src/triage.py`. Section 9 reports a reproducible API run.

## 5. Revision of the manual scores

After seeing the comparison, the author reviewed five requests the AI had rated P3 and agreed
they were life-threatening: WO-006 (sparking garage outlet), WO-015 (burning-smell outlet),
WO-070 (water into a light fixture), WO-074 (CO alarm) and WO-078 (gas smell). They are
recorded in `manual_revised`. `manual_original` is unchanged, and both columns are reported.

**Why report both:** revising after seeing the AI's answers makes agreement look better than
the blind result. The honest blind figure is 65 / 100; the 70 / 100 figure reflects human
review informed by the AI. That difference *is* the finding — the AI works as a safety second
opinion.

## 6. Metrics

`src/evaluate.py` reports exact-match agreement, a confusion matrix, whether the AI rated
higher or lower than the human, agreement by trade, and the list of requests where the AI
rated below the human.

## 7. Timing

The author timed the manual work: 20 minutes to score 100 requests and 15 minutes to review
the AI's table. The AI's own generation time was not measured for the first pass.

## 8. Testing a fix on unseen requests

After the comparison, one rule was added to the prompt to address the weakest area (fire-safety
equipment). Prompt v3 = v2 plus that rule. It was evaluated twice:

- **In-sample:** re-labelling the 10 Fire & Life Safety requests from the original 100, which
  the rule was written from. This is optimistic by construction.
- **Hold-out:** 30 new requests (`data/holdout_requests.csv`), nine about fire-safety equipment.
  The AI labels under v2 and v3 were recorded before the author scored the requests, and the
  author scored them without seeing any AI output. Result: v2 matched 19/30 and v3 matched
  20/30. The two prompts differ on only 3 of the 30 requests, so the test is small.

Any further prompt change tuned on these 30 requests would no longer be a fair test.

**Second hold-out (v4).** The author then stated a policy: fire safety should be P3. Prompt v4 encodes it. A second set of 30 requests (`data/holdout2_requests.csv`, 10 on fire safety) was written after the rule, with AI labels under v2 and v4 recorded before scoring and the author scoring blind. Result: v2 14/30, v4 22/30; fire-safety items 1/10 to 9/10; the other 20 items 13/20 under both. Caveats: the author of the requests (an AI model) knew the rule, so the fire-safety requests are mostly clear-cut; and seven earlier fire-safety scores on the original 100 predate the policy and conflict with it. They were not changed.

## 9. API rerun

The 100 original requests were run through `src/triage.py` with prompt v4 and the default model (`claude-sonnet-5-5`), sequentially. Run time was about 7 minutes, timed by hand with a clock (the script's own `%time%` echo in Command Prompt was not usable). No rows failed (the AI's P1, P2 and P3 counts sum to 100). Agreement was 60/100 with the original manual scores and 65/100 with the revised ones. All 8 revised-P3 requests were rated P3. The 15 cases where the AI rated lower were all P2 to P1. This run differs from the earlier chat runs in prompt (v4 against v2) and in being a separate pass, so a v2 API run is the like-for-like comparison.

## 10. Caveats

- One rater, so no inter-rater reliability and no ground truth.
- Fictional requests; no photos, building history or tenant history.
- Exact-match agreement treats P1 vs P3 and P1 vs P2 as equally wrong; the confusion matrix
  shows the direction of errors.
- The v2 pass and the revised scores were not blind (section 4 and 5).
- Results from one model and one prompt; other models or prompts may differ.
