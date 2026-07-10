# Chapter 14 — The Economics of Loops

[← Previous](./13-making-loops-halt.md) · [Index](./README.md) · [Next: Durability & crash recovery →](./15-durability-and-crash-recovery.md)

> *When the model writes code for almost nothing, the expensive resource becomes the loop running it. The dominant cost is how many times the loop runs, so the three hard stops double as your main cost control.*

## Concept

Loop economics start from a cost shift. When a single code generation cost real money, you optimized the prompt. Now that generation is cheap, and the expensive resource is the loop around it: running it, supervising it, retrying it, and letting it run too long.[<sup>1</sup>](#sources) Cost is dominated by one term:

```
cost ≈ iterations × cost_per_iteration
```

`iterations` is the large, open-ended term, which is why the three hard stops (Chapter 13) are also the main cost control: an iteration cap, no-progress detection, and a budget ceiling all bound it. Three things make the curve worse. Context rot raises cost per tick over time while lowering quality, since an accumulating-context loop pays more for worse output (Chapter 5). Orchestration multiplies the whole thing — a fleet runs on the order of 10× a single session (Chapter 11). And a runaway loop has no natural ceiling at all.

The canonical failure: an engineering org exhausted its annual AI budget in four months. The fix was a hard per-person, per-tool monthly cap — the budget-ceiling stop, imposed by administration because the loops never enforced it themselves.[<sup>2</sup>](#sources)

`cost_per_iteration` is the second lever, and running one fixed model for the whole loop leaves it unused. You rarely need the strongest model on every tick or every seam, and two moves cut the bill. **Difficulty-adaptive escalation:** start on a cheap, fast model and switch to a stronger one only when the loop stalls. The no-progress signal from Chapter 13 is the trigger, so it costs nothing extra to detect. **Per-seam routing:** reserve the strong model for the code edit, and send the mechanical seams — reviewing a diff, distilling a note, running the completion check — to a cheap one. Running a frontier model through your own reviewer and distiller pays premium rates for clerical work. Both moves need measurement: escalation only pays when the cheap model clears enough tasks that the occasional switch beats always running strong.

## How it works

A loop pays off in some conditions and loses in others:

- **Worth it** for repeated, well-specified, verifiable work under tight guardrails — an overnight grind on a clear backlog, a large mechanical migration, continuous PR babysitting. Supervision overhead amortizes across many tasks, and the guardrails cap the downside.
- **Not worth it** for a one-shot, fuzzy, hard-to-verify task. A single ambiguous task is cheaper to drive interactively, with your judgment in the inner loop, than to wrap in a loop that thrashes against an unclear target.

The dividing line is repetition and verifiability. Include your own time in the math: a loop that produces more output than you can review hasn't saved the time it appears to.

## Implement it

Two pieces: measure real cost instead of guessing, and enforce the ceiling in code. The `loop.py` delta wires the measured cost into the budget stop from Chapter 13, plus a back-of-envelope you run *before* the loop:

```python
# loop.py delta — measure real cost per tick; the budget stop (Ch 13) consumes it.
import json

def run_agent_tick(cfg, feedback) -> float:
    """Run one tick; return its MEASURED cost so the budget ceiling is real, not a guess.
    (In the capstone this is assembled into run_agent() returning an AgentResult with .cost_usd.)"""
    prompt = build_prompt(cfg.repo, feedback)
    out = subprocess.run(["claude", "-p", "--output-format", "stream-json",
                          "--permission-mode", "acceptEdits", "--model", cfg.model],
                         cwd=cfg.repo, input=prompt, capture_output=True, text=True).stdout
    cost = 0.0
    for line in out.splitlines():
        try: obj = json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(obj, dict) and "total_cost_usd" in obj:
            cost = float(obj["total_cost_usd"])   # last cumulative value wins
    return cost

def roi_ok(cfg, value_of_outcome: float, your_review_hours: float, hourly: float) -> bool:
    """Run BEFORE the loop. If MAX × measured cost/tick + review time > the outcome's value, don't."""
    worst_case = cfg.max_iter * cfg.avg_cost_per_tick + your_review_hours * hourly
    return value_of_outcome > worst_case
```

`roi_ok` takes a minute and catches upside-down loops before they run. If `MAX × cost/tick` already exceeds what the outcome is worth, the loop loses money however well it runs. Measure `avg_cost_per_tick` on a few real runs; loops vary by more than 10× across tasks.

`roi_ok` is the estimate you run before; **cost per accepted change** is the number you track after — total spend divided by the changes that cleared your held-out gate. Tokens spent and tasks attempted both look productive, so measure against accepted changes instead. Spend $40 across ten runs, have two clear the gate, and each shipped change cost $20 — the other eight runs were the review work the loop was meant to remove. Track it per goal: a low acceptance rate means the loop is generating queue rather than throughput, and the fix is a better gate or a narrower task, not more runs. Report it as undefined when nothing was accepted, so pure waste doesn't hide behind a `0`. The [reference implementation](./README.md#reference-implementation) computes it on every reliability report (`ReliabilityReport.cost_per_accepted`, from `loopkit measure`), alongside the `pass^k` curve (Ch 9).

## Builds on

Chapter 13 left `run_agent_tick` returning a cost figure abstractly; this chapter measures it for real and feeds the budget-ceiling stop. The budget ceiling becomes a cost control as well as a safety one, and `roi_ok` is the check you run before starting the loop at all.

## Pitfalls

1. **Optimizing tokens while ignoring iterations.** Cost is iterations × cost/iteration, and iterations is the open-ended term. Cap it.
2. **No per-user / per-fleet ceiling.** Costs look fine per-call and catastrophic in aggregate. Enforce ceilings administratively *and* in the loop.
3. **Skipping the ROI back-of-envelope.** `MAX × cost/tick` against the outcome's value takes a minute and catches upside-down loops before they run.
4. **Forgetting your review time is a cost.** A loop that outputs more than you can verify hasn't saved the time it appears to.
5. **Measuring by tokens or attempts instead of accepted changes.** Tokens spent and tasks attempted look productive; cost per accepted change is the figure that ties spend to what shipped. A loop with a low acceptance rate is paying to generate review queue.
6. **One model for every tick and every seam.** Treat `cost_per_iteration` as a lever. Start cheap and escalate on no-progress, and route the mechanical seams (review, distillation, the gate) to a cheaper model than the code edit — after checking the routing actually pays.

## Takeaway

Cost shifted from writing code to running the loop, and the dominant term is how many times it runs, so the three hard stops are also the cost control. Context rot worsens the curve, orchestration multiplies it (~10× for a fleet), and the canonical failure is a blown annual budget capped after the fact. `cost_per_iteration` is a second lever: cheaper models on the mechanical seams, escalation only on a stall. A loop pays off for repeated, verifiable work under guardrails and loses on fuzzy one-offs, and the ROI math has to include your review time.

## Sources

| # | Source | Supports | Link |
|---|--------|----------|------|
| 1 | Cost-shift practitioner accounts (2026) | "the costliest thing is no longer writing code, it's managing the agent loop" | reported across 2026 discourse |
| 2 | Reporting on an org's AI-spend cap (Jun 2026) | annual budget exhausted in ~4 months; a $1,500/person/tool/month cap imposed. *(Verified figure; many adjacent viral numbers in this space are inflated in retelling — design against measured mechanics.)* | [techcrunch.com](https://techcrunch.com/2026/06/02/uber-caps-employee-ai-spending-after-blowing-through-budget-in-four-months/) |
| 3 | Hype-cycle survey (2026) | agentic AI at peak expectations; ~17% of orgs actually deploying — intent runs ahead of deployment | [gartner.com](https://www.gartner.com/en/articles/hype-cycle-for-agentic-ai) |
