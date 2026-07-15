# services/eval -- the myfi eval harness

Scores a **latent agent output** (an advisor recommendation, a plan, a trade
thesis, a skill's own orientation, …) against a rubric, using the
local-Claude-Code judge in [`../llm`](../llm/README.md). This is the
behavioral half of `CLAUDE.md`'s "every feature ships with a test suite AND
an eval suite, in the same commit" rule -- the plugin's latent instructions get
a real judge, not just gate-tested storage.

Stdlib-only (no `poetry` env required) -- runs with any Python 3 on `PATH`.

## The split, applied to the plugin itself

The plugin preaches a latent/deterministic split. The harness lives it:

| Part | Owner | Where |
|------|-------|-------|
| Per-dimension 1..scale scores + rationale | the model (latent) | the judge call |
| Rubric, judge-prompt build, weighted overall, threshold verdict, exit code | code (deterministic) | `eval.py` |

Same scores in ⇒ same verdict out. The only non-reproducible step is the
model's judgement, and that is exactly the part a rubric + threshold is meant
to bound.

## Use

```bash
# score text directly
echo "redirect $650/mo into savings until 6mo runway, then raise 401k to 6% for the match" \
  | python3 services/eval/eval.py run --kind=advisory -

# score a file, machine-readable verdict
python3 services/eval/eval.py run --kind=advisory --input-file=evals/golden_good.txt --json

python3 services/eval/eval.py rubrics        # list rubric kinds
python3 services/eval/eval.py show advisory  # print a rubric
```

The root wrapper `bin/myfi-eval` is a thin `exec python3 .../eval.py "$@"`.

Exit codes: `0` pass · `1` fail (below threshold) · `2` usage · `4` judge/parse
error. `--json` prints **only** the verdict object -- the contract a future
`myctx`-backed caller records into the registry (Wave 3).

## Rubrics

One file per subject kind in [`rubrics/`](rubrics/), shape:

```json
{
  "kind": "advisory",
  "subject": "what is being judged, in one sentence",
  "scale": 5,
  "threshold": 65,
  "dimensions": [
    { "key": "actionable-recs", "weight": 2, "desc": "…" }
  ],
  "guidance": "what to reward / penalize"
}
```

Overall score = `round(100 * Σ(score·weight) / (scale · Σweight))`, rounded
half-up. Adding a new subject is one JSON file -- no code change.
`test_eval_rubrics.py` enforces the shape so a malformed rubric fails loudly
instead of scoring garbage.

Three baseline rubric kinds ship with this unit -- the flock's scoring
substrate that later waves extend beside (file-disjoint), never edit:

- `advisory` -- a financial advisory recommendation/report (`@advisor`'s
  assembled output).
- `plan` -- a financial plan from the `/myfi:plan` pipeline.
- `trade` -- a trade idea/thesis from `@quant`/`@trader` (analysis only, never
  a live order).

## Two lanes (per the project's test/eval discipline)

- **Gate lane** -- `python3 -m unittest discover -s services/eval/tests`.
  Deterministic, free, <2s. The judge is mocked (`MYFI_LLM_MOCK`), so the
  eval→llm boundary, the score math, the threshold verdict, and every error
  path are tested for real while the model's response is a canned string.
- **Live lane** -- real judge, spends LLM calls:
  ```bash
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=advisory --input-file=evals/golden_good.txt
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=advisory --input-file=evals/golden_bad.txt
  ```
  `MYFI_EVAL_LIVE=1` also strips any inherited `MYFI_LLM_MOCK`/`MYFI_LLM_MOCK_TEXT`
  before shelling to `llm.py` -- a stray mock from a parent shell must not make
  the live lane a lie. `golden_good.txt` must score above the `advisory`
  rubric's threshold; `golden_bad.txt` must score below it. Run before ship
  and nightly, not on every commit.

## Reachability

This service is pure + stateless: it reads a rubric + an input and returns a
verdict, and does not touch a DB. `myfi_toolkit.myctx` (Wave 3) is the
project-side glue that will resolve subjects and record verdicts into the
per-project registry -- this service stays a clean function so it is trivially
testable with a mocked judge.
