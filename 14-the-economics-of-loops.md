# Chapter 14 — The Economics of Loops

[← Previous](./13-making-loops-halt.md) · [Index](./README.md) · [Next: Durability & crash recovery →](./15-durability-and-crash-recovery.md)

> *Once the model writes code for almost nothing, the expensive resource becomes the loop running it. The dominant cost variable is how many times the loop runs — which makes the three hard stops an economic control, not just a safety one.*

## Concept

The central economic fact of loop engineering is a **cost shift**: when a single code generation costs real money you optimized the prompt; now that generation is cheap, the expensive resource is the *loop* — running it, supervising it, retrying it, and especially letting it run too long.[<sup>1</sup>](#sources) The cost is no longer per-token; it is:

```
cost ≈ iterations × cost_per_iteration
```

and `iterations` is the large, open-ended term. This is exactly why the three hard stops (Chapter 13) are an economic control: capping iterations, detecting no-progress, and enforcing a budget ceiling are how you bound the dominant variable. Three forces make this sharper: **rot** worsens the curve over time (an accumulating-context loop pays *more* per tick for *worse* output — Chapter 5), **orchestration** multiplies everything (a fleet runs on the order of 10× a single session — Chapter 11), and a runaway loop has *no* natural ceiling.

The canonical real-world failure: an engineering org's annual AI budget was exhausted in four months, and the fix was a hard per-person, per-tool monthly cap — the budget-ceiling stop, imposed administratively because it wasn't enforced in the loops.[<sup>2</sup>](#sources)

## How it works

A loop pays off under a clear condition and loses under its opposite:

- **Worth it** for a *repeated, well-specified, verifiable* workflow under tight guardrails — overnight grind on a clear backlog, large mechanical migrations, continuous PR babysitting. The supervision overhead amortizes across many tasks; the guardrails cap the downside.
- **Not worth it** for a *one-shot, fuzzy, hard-to-verify* task. A single ambiguous task is cheaper to drive interactively, where your judgment is in the inner loop, than to wrap in a loop that thrashes against an unclear target.

The dividing line is repetition and verifiability. And the ROI must include *your* time: a loop that produces more output than you can review hasn't saved the time it appears to.

## Implement it

Two pieces: measure real cost (don't guess), and enforce the ceiling structurally. The `loop.py` delta wires the measured cost into the budget stop from Chapter 13, plus a back-of-envelope you run *before* the loop:

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

`roi_ok` takes a minute and catches upside-down loops before they run: if `MAX × cost/tick` already exceeds what the outcome is worth, the loop is a money fire no matter how clever. Measure `avg_cost_per_tick` on a few real runs; loops vary 10×+ by task.

`roi_ok` is the *before* estimate; the *after* metric is **cost per accepted change** — total spend divided by the changes that actually cleared your held-out gate. Not tokens spent, not tasks attempted, not loops scheduled; all three flatter you. It's the honest unit cost of a *trustworthy* result: spend $40 across ten runs and have two clear the gate, and each shipped change cost $20 — the other eight runs were review work the loop was supposed to *remove*, not savings. Track it per goal; a low acceptance rate means the loop is generating queue, not throughput, and the fix is a better gate or a narrower task, not more runs. Report it as **undefined, not zero**, when nothing was accepted — spend with no accepted change is pure waste, and a `0` would hide that. The [reference implementation](./README.md#reference-implementation) computes it on every reliability report (`ReliabilityReport.cost_per_accepted`, from `loopkit measure`), the cost twin of the `pass^k` curve (Ch 9).

## Builds on

Chapter 13 left `run_agent_tick` returning a cost figure abstractly; this chapter measures it for real and feeds the budget-ceiling stop. The budget ceiling is now an *economic* control, not just a safety one, and `roi_ok` is the gate you run before even starting the loop.

## Pitfalls

1. **Optimizing tokens while ignoring iterations.** Cost is iterations × cost/iteration, and iterations is the big, open-ended term. Cap it.
2. **No per-user / per-fleet ceiling.** Costs look fine per-call and catastrophic in aggregate. Enforce ceilings administratively *and* in the loop.
3. **Skipping the ROI back-of-envelope.** `MAX × cost/tick` vs the outcome's value takes a minute and catches upside-down loops before they run.
4. **Forgetting your review time is a cost.** A loop that outputs more than you can verify hasn't saved the time it appears to.
5. **Measuring cost by tokens or attempts, not accepted changes.** Tokens spent and tasks attempted always look productive; cost per *accepted* change is the only figure that ties spend to what shipped. A loop with a low acceptance rate is paying to generate review queue.

## Takeaway

The cost shifted from writing code to managing the loop: the dominant variable is how many times the loop runs, which makes the three hard stops an economic control. Rot worsens the curve, orchestration multiplies it (~10× for a fleet), and the canonical failure is an org's blown annual budget, fixed with a hard ceiling. A loop pays off for repeated, well-specified, verifiable work under tight guardrails and loses for fuzzy one-offs — and the ROI math must include your review time.

## Sources

| # | Source | Supports | Link |
|---|--------|----------|------|
| 1 | Cost-shift practitioner accounts (2026) | "the costliest thing is no longer writing code, it's managing the agent loop" | reported across 2026 discourse |
| 2 | Reporting on an org's AI-spend cap (Jun 2026) | annual budget exhausted in ~4 months; a $1,500/person/tool/month cap imposed. *(Verified figure; many adjacent viral numbers in this space are inflated in retelling — design against measured mechanics.)* | [techcrunch.com](https://techcrunch.com/2026/06/02/uber-caps-employee-ai-spending-after-blowing-through-budget-in-four-months/) |
| 3 | Hype-cycle survey (2026) | agentic AI at peak expectations; ~17% of orgs actually deploying — intent runs ahead of deployment | [gartner.com](https://www.gartner.com/en/articles/hype-cycle-for-agentic-ai) |
