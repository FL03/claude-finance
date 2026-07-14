## DESIGNER REPORT

- Artifact type: html-report
- Source draft: advisor refinance recommendation (client goal: "should I refinance my mortgage this year?")
- Auditor gate: PASS confirmed (.myfi/audit/2026-07-13-audit-compliance.md)
- Final-edit checklist: format-fidelity=ok, chart-integrity=ok, no-orphaned-citation=ok, readability=ok, no-reopened-finding=ok
- Artifact path: .myfi/artifacts/2026-07-13-refinance-recommendation.html

### Artifact excerpt (`.myfi/artifacts/2026-07-13-refinance-recommendation.html`)

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Refinance recommendation -- 2026-07-13</title></head>
<body>
  <h1>Should you refinance this year?</h1>
  <p>Short answer: yes, refinancing now to a 6.10% 30-year fixed saves you $131/month and pays
     for itself in about 4.3 years -- well inside your stated 10+ year horizon.</p>

  <h2>Your numbers today</h2>
  <table>
    <tr><th>Current rate</th><td>6.75%</td></tr>
    <tr><th>New rate estimate</th><td>6.10%</td></tr>
    <tr><th>Monthly savings</th><td>$131</td></tr>
    <tr><th>Closing costs</th><td>$6,800</td></tr>
    <tr><th>Breakeven</th><td>52 months (4.3 years)</td></tr>
  </table>

  <h2>Breakeven chart</h2>
  <figure>
    <img src="charts/breakeven-2026-07-13.png" alt="Cumulative savings vs. closing costs over 60 months, crossing even at month 52" width="640" height="360">
    <figcaption>Fig. 1 -- cumulative monthly savings ($131/mo) against the $6,800 closing cost;
      the lines cross at month 52, matching the breakeven cited above. Rendered by the toolkit
      (matplotlib, Agg backend) from the same inputs cited in the table.</figcaption>
  </figure>

  <h2>What could change this</h2>
  <p>This estimate rests on a self-reported 760 FICO and 32% DTI that a lender has not yet
     verified -- get a formal rate lock quote from at least two lenders this week to confirm the
     6.10% figure before committing (per the advisor's draft, unaltered here).</p>

  <p><small>Data export: <a href="2026-07-13-refinance-recommendation.csv">refinance-recommendation.csv</a></small></p>
</body>
</html>
```

Every figure in the excerpt (6.75%, 6.10%, $131, $6,800, 52 months) traces to the source draft
verbatim; the chart is captioned with its source and axis meaning; the lender-verification caveat
from the auditor-cleared draft was carried through unchanged, not softened or dropped.
