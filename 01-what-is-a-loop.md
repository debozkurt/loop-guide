# Chapter 1 — What Is a Loop?

[Index](./README.md) · [Next: The five-year lineage →](./02-the-lineage.md)

> *A loop is a small program that prompts a coding agent for you, reads what it produced, decides whether it's done, and prompts it again. You stop typing prompts; you author the program that types them.*

## Concept

A **loop** is a control program wrapped around a coding agent. Each tick it: invokes the agent, reads the result, decides whether the goal is met, and — if not — invokes it again with what it learned. The operator stops being the entity inside the loop typing prompts and becomes the **author** of the loop. The model becomes a subroutine the program calls.

The one-sentence definition to carry through the whole manual:

> **A loop is cron plus a decision-maker in the body.**

A cron job runs a fixed script on a timer. A loop runs a *model* that inspects the current state, **decides** the next action, performs it, **checks** whether it worked, and **decides** whether to continue. The scheduling layer is genuinely just cron — that part was invented in 1975. What cron never had is the decision in the middle:

| On each tick… | Cron job | Agentic loop |
|---|---|---|
| What runs | a fixed script, then exits | a **model** invocation |
| The next action is… | hardcoded in the script | **decided by the model** from current state |
| After acting | nothing — idle until the next tick | the model/loop **checks whether it worked** |
| Continue? | only on the fixed schedule | the loop **decides** whether to keep going |

The engineering of loops is everything you wrap around that decision so it produces value instead of running off a cliff. That wrapping — verification, halting, durability, isolation, orchestration — is the rest of this manual.

## How it works

There are three levels of automation, and naming your current level tells you what to build next:[<sup>1</sup>](#sources)

1. **Hand-code** with autocomplete — you write the code.
2. **Prompt an agent** — you describe each step; the agent writes the code; you drive every turn.
3. **Author a loop** — you write the program that prompts the agent; it drives the turns. You set the *intent* and the *stopping behavior* once; the model makes the per-tick decisions.

This manual is about getting fluent at level 3. The skill is not prompting better — it's designing the control flow around a model call so the model can run unattended without going wrong. Note that level-3 does not remove the engineer: someone still decides *what* to build, defines "done," and writes the loop. The work moves up an altitude; it does not disappear.[<sup>1</sup>](#sources)

## Implement it

The simplest thing that is a loop (and not a cron job) is a handful of lines. This is the seed of the artifact you build across the whole manual — by Chapter 18 it becomes the capstone's `loop.py`:

```python
# loop.py — v0.1 (conceptual). The decision in the body is what makes this a loop.
done = False
while not done:
    state  = read_state()          # what does the world look like right now?
    action = agent.decide(state)   # THE DECISION — a model, not a hardcoded branch
    apply(action)                  # do it
    done   = goal_met(state)       # check — and decide whether to continue
```

Three lines carry the whole idea: `agent.decide` is the decision cron never had; `goal_met` is the stopping logic that keeps it from running forever; `read_state` is what keeps each tick grounded in reality instead of the model's memory. Every later chapter hardens exactly one of these three — the decision (Parts I–II), the check (Part III), and the surrounding safety, durability, and scale (Parts IV–VI).

## Builds on

Nothing — this is the seed. Hold the three-line skeleton in your head; the rest of the manual is the production-grade version of it, added one concern at a time.

## Pitfalls

1. **Confusing "I scheduled a prompt" with "I wrote a loop."** Scheduling a fixed prompt is a cron job. It becomes a loop only when a model decides the next action *and* something checks the result and decides whether to continue.
2. **Omitting the "decide whether it's done" line.** A loop with no stopping logic is a money fire, not a loop. The most common production failure is the loop that never halts (Chapter 13).
3. **Taking viral productivity numbers literally.** Reported figures in this space are routinely inflated in retelling; design against verified mechanics, not headlines. Where this manual cites a number, it flags whether it's measured or anecdotal.

## Takeaway

A loop is cron plus a decision-maker in the body: a program that calls the agent, checks the result, and decides whether to continue. Your job is to author that program — set the intent and the stopping behavior — and let the model make the per-tick decisions. Everything that follows hardens the three-line skeleton above.

## Sources

| # | Source | Supports | Link |
|---|--------|----------|------|
| 1 | Conference talk by the creator of Claude Code, WorkOS / Acquired Unplugged (Jun 2026) | the three levels of automation ("my job is to write loops"); engineers move up an altitude, not out | reported across Jun 2026 coverage |
| 2 | Cherny, verified contribution figures, via S. Willison (Dec 27 2025) | the level-3 operator is real (259 PRs, every line agent-written); viral retellings ("deleted his IDE," "100% of contributions") overstate the softer original | [simonwillison.net](https://simonwillison.net/2025/Dec/27/boris-cherny/) |
| 3 | `/loop` launch post (Mar 7 2026) | the scheduling layer is literally cron | [threads.com](https://www.threads.com/@boris_cherny/post/DVk4eGHFaRn/) |
