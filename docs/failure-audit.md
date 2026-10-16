# Failure audit (Day 2.1)

Run on 2026-10-15 against the local backend (commit after 1.6). Each dependency was broken on purpose and the response recorded.

| # | Failure | Trigger | Target | Observed (HTTP · weather · attractions · time) | What the recommendation said |
|---|---|---|---|---|---|
| 0 | Attractions regex never matches | any city | attractions `ok` with items | ❌ 200 · ok · `unavailable` for every city | Lists attractions from general knowledge; doesn't always say the data was missing |
| 1 | Unknown city | `Xyzzyqqplorf` | 422, no model call | ✅ 422 · 0.9 s | — |
| 2 | Dates beyond forecast | `2026-12-20` | 200 · weather `unavailable` | ❌ 200 · `error` ("The weather service failed.") · unavailable · 5.2 s | Says weather is unavailable; presents attractions as if sourced |
| 3 | Dates in the past | `2025-06-01` | 422 "start date is in the past" | ❌ 200 · `error` · unavailable · 3.7 s (wasted model call) | Admits data is missing, then plans a trip in the past |
| 4 | Weather API unreachable | forecast host → `.invalid` | 200 · weather `error` after retries | ⚠️ 200 · `error` · unavailable · 4.7 s; status correct, no retry | Admits weather and attractions are missing |
| 5 | Wikipedia unreachable | Wikipedia host → `.invalid` | 200 · attractions `error` after retries | ⚠️ 200 · ok · `error` · 5.6 s; status correct, no retry | Uses the real weather numbers; admits attractions are missing |
| 6 | Invalid Gemini key | `GOOGLE_API_KEY=invalid` | 502, fast, no retries | ✅ 502 · 1.2 s | — |
| 7 | Ambiguous city | `Springfield` | both tools describe the same place | ❌ 200 · ok for the geocoder's top match (not named) · Wikipedia used the disambiguation page · 4.8 s | Generic advice for "Springfield"; says attractions weren't available |
| 8 | Burst of requests | 10 in parallel | no 429 errors reach the user | ❌ 3/10 succeeded; 7 × 502 after ~37 s | — |

## Findings

- **No retries anywhere.** The tools catch every exception and return error data, so nothing upstream ever sees a failure to retry (rows 4–5).
- **"Error" covers expected gaps.** Dates beyond the forecast window show as a service failure (row 2).
- **Invalid input reaches the model.** Past dates cost a full agent run (row 3).
- **The tools can disagree about the place.** Geocoding and Wikipedia resolve "Springfield" independently, and the response never names which city it used (row 7).
- **Burst failures are likely Gemini rate limiting** (unconfirmed): two fast successes, then the client retried with backoff for ~37 s before giving up (row 8). This probably also explains the 23 s outlier in the 1.6 baseline.
- **Inconsistent grounding.** The model sometimes presents general knowledge as sourced data (rows 0, 2).

## Fix plan

| Gap | Fix | When |
|---|---|---|
| Rows 4–5: no retries | Tools raise; retry middleware for timeouts, 429s and 5xx; error middleware outside it | 2.2–2.3 |
| Row 2: wrong status | Check the forecast window before calling → `unavailable` | 2.4 |
| Row 3: past dates | Reject in `TravelRequest` → 422 | 2.4 |
| Row 7: ambiguous city | Return the resolved place (name, region, country) and use it for the Wikipedia lookup and the prompt | 2.4 |
| Row 0: attractions | Replace the regex extraction | Day 2, needs its own slot |
| Grounding | Prompt rule: say when a tool returned no data; label general knowledge | Day 2 |
| Row 8: rate limits | Per-IP rate limit; return 503 "busy, try again" instead of 502 | Day 6 |