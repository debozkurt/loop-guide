# Agentic Loops — An Engineering Manual for Self-Governed Coding

> *Last verified: June 2026. This is a fast-moving topic; product names, slash commands, and prices are snapshots, not gospel. The **patterns** underneath — the loop body, the verification gate, the three hard stops, durability, skills-as-units — are what stabilize. Where a number is unverified or inflated in retelling, the relevant chapter flags it.*

This manual teaches you to **design loops that drive coding agents**: a control program that invokes the agent, reads what it produced, decides whether the goal is met, and — if not — invokes it again. You stop typing prompts and start authoring the program that types them. The model becomes a subroutine; your job becomes the control flow around it.

It is **Claude Code first**, with **OpenAI Codex parity** flagged throughout for people who run both. The concepts are harness-agnostic; the implementations use `loop.sh`/`loop.py`, `/goal`, `/loop`, worktrees, and hooks.

## The one-sentence thesis

**A loop is cron plus a decision-maker in the body.** A cron job runs a fixed script; a loop runs a *model* that inspects state, decides the next action, performs it, checks whether it worked, and decides whether to continue. Everything in this manual is the engineering you wrap around that decision so it produces value instead of running off a cliff.

## How this manual is built

Two things make it a manual rather than a survey:

**A fixed chapter template.** Every chapter is structured the same way, so you can navigate by section:

- **Concept** — what the thing is, as an engineering fact.
- **How it works** — the mechanism, with a diagram where it helps.
- **Implement it** — runnable code/config that adds this chapter's concern to the evolving artifact.
- **Builds on** — how this extends the previous chapters.
- **Pitfalls** — the failure modes, numbered.
- **Takeaway** — one paragraph.
- **Sources** — a compact table (source · what it supports · link). Names and citations live here, not in the body.

**One evolving artifact.** The manual builds a single loop harness incrementally. Each chapter's "Implement it" adds one delta to the same `loop.py`/`orchestrate.py`, and the [capstone](./capstone/README.md) is its finished, runnable state:

| Chapter | Delta added to the artifact |
|---|---|
| 1–3 | the outer-loop skeleton (`run_loop`, `run_agent`, a stopping-oracle placeholder) |
| 4–5 | the ralph form (`loop.sh`), fresh-context priming (`build_prompt`), anchor files |
| 6–7 | the completion gate → a real `verification_gate` that feeds failures back (closed loop) |
| 8–9 | continuous review (`review_commit`); the eval runner (`evals.py`) + a held-out acceptance gate and a best-of-N selection check |
| 10–12 | `orchestrate.py` (supervisor + isolated workers), a patrol, fan-out, evolutionary fan-out (`evolve`: select + reseed), triggers |
| 13–14 | the three hard stops (`StopReason`, `state_signature`, budget) + measured cost |
| 15–16 | `commit_progress` (durable, resumable) + least-privilege config and a pre-tool-use hook |
| 17 | a `SKILL.md` the loop calls, with a `write_back` flywheel edge |
| 18 | the pre-flight `Config` — the whole manual as one object — assembled in the capstone |
| 19 | positioning choices — git-backed state, standard skill formats, gated write-back (portability for the horizon) |
| 20–21 | a verified webhook front-end (`trigger.py`) + `--from-event`/`--open-pr` and a CI workflow — **the loop deployed into the forge ecosystem** |

Read a chapter's code next to the [capstone harness](./capstone/harness/) to see the delta in its final, assembled context.

## How to read it

- **Newcomers:** top to bottom. Chapters 1–7 take you from "what is a loop" to a closed, verifying loop.
- **Intermediate** (you've run a loop overnight): start at Chapter 7 (Verification) — the line between a trustworthy loop and a confident-mistake machine.
- **Experienced** (you orchestrate already): Part IV (orchestration), Part V (halting, economics, durability, safety), and Part VIII (deploying the loop into the forge ecosystem).
- **Everyone** ends at the [capstone](./capstone/README.md): a runnable harness, a lab to point it at your own repo, and a teaching kit for a team.

This manual complements two existing curricula and does not duplicate them: [`agents/`](../agents/README.md) (building an agent — the *inner* loop) and [`claude-code/`](../claude-code/README.md) (Claude Code mechanics). This one is the *outer* loop wrapped around the whole agent, running unattended. Use the [glossary](./glossary.md) for terms.

---

## Index

### Part I — Foundations

1. [What is a loop?](./01-what-is-a-loop.md) — cron + a decision-maker; the loop skeleton
2. [The lineage: five loop designs](./02-the-lineage.md) — each design fixes the last's failure; topology as a second axis
3. [Inner loop vs outer loop](./03-the-inner-loop-formally.md) — the model as a subroutine; the stopping oracle

### Part II — The Single-Agent Loop

4. [The ralph technique](./04-the-ralph-technique.md) — fixed prompt, fresh context, state on disk (`loop.sh`)
5. [Context-reset discipline](./05-context-reset-discipline.md) — why fresh, small context beats a growing one
6. [The completion gate (`/goal`, `/loop`)](./06-goal-and-loop-productized.md) — the stopping oracle, productized; Codex parity

### Part III — Verification & Feedback

7. [The feedback imperative](./07-the-feedback-imperative.md) — closed loop; external verification; `verification_gate`
8. [Continuous review](./08-continuous-review.md) — review every commit; feed findings back while context is fresh
9. [Evals & regression for loops](./09-evals-and-regression-for-loops.md) — trajectory, convergence, gaming vs overfitting the gate, the held-out acceptance gate, selection inflation

### Part IV — Orchestration

10. [From one loop to many](./10-from-one-loop-to-many.md) — supervisor over isolated worker loops (`orchestrate.py`)
11. [Patterns from a real fleet (Gas Town)](./11-gastown-and-the-mayor-pattern.md) — four patterns + the reality check
12. [Fan-out, dynamic workflows & triggers](./12-dynamic-workflows-and-fan-out.md) — three fan-out topologies (incl. evolutionary); infrastructure time vs attention time

### Part V — Production

13. [Making loops halt](./13-making-loops-halt.md) — the three hard stops: iteration cap, no-progress, budget
14. [The economics of loops](./14-the-economics-of-loops.md) — the cost shift; measure cost; ROI before you run
15. [Durability & crash recovery](./15-durability-and-crash-recovery.md) — commit every tick; resume from git
16. [Permissions & safety](./16-permissions-and-safety.md) — blast radius, least privilege, pre-tool-use hooks

### Part VI — Compounding & Practice

17. [It's not loops, it's skills](./17-its-not-loops-its-skills.md) — flywheel vs treadmill; the write-back edge
18. [Anti-patterns & the decision framework](./18-anti-patterns-and-decision-framework.md) — maturity ladder; the pre-flight config

### Part VII — Horizon

19. [Where this goes next](./19-where-this-goes-next.md) — shipped / emerging / speculative; positioning so the future is a cheap adoption, not a rewrite

### Part VIII — Deployment & the Ecosystem

20. [Triggers as infrastructure](./20-triggers-as-infrastructure.md) — a forge webhook as a public trigger; HMAC-verify fail-closed; dedupe on issue identity
21. [The CI deployment tier](./21-the-ci-deployment-tier.md) — run the finished loop as a CI job; the three deployment tiers; use the platform's primitives first

### Capstone & Reference

- [The Self-Governed Loop](./capstone/README.md) — runnable harness + lab guide + teaching kit
- **[loopkit](#reference-implementation)** — the production-grade reference implementation of this manual; Chapters 20–21 cite its runnable labs
- [Prior Art & Lessons from the Field](./prior-art.md) — the canonical harnesses (Anthropic, SWE-agent, Aider, LangGraph, SWE-bench, τ-bench…) mapped to the manual's patterns: what validates them, the sharper lessons (ACI, the two-oracle gate, `pass^k`, verifier hacking), and where the field is heading
- [Glossary](./glossary.md)

<a id="reference-implementation"></a>
**Reference implementation — loopkit.** Where the [capstone](./capstone/README.md) is *the manual's code made whole* — minimal, stdlib-only, readable end to end — **loopkit** (`~/Documents/loopkit`) is the same patterns built out as a **product**: the 2×2 adapter matrix with measured cost, a cloud control plane, credential hardening against prompt injection, and the three deployment tiers of Chapter 21. The capstone is for *reading and running the ideas*; loopkit is for *seeing them at production scale*. It mirrors this manual chapter-for-chapter and ships runnable `demo`/`learn` labs — Chapters 20–21 point at `loopkit demo 20` (triggers) and `loopkit demo 21` (the CI tier). Keep them separate on purpose: the manual stays dependency-free; the product carries the operational weight.

---

## Claude Code ↔ OpenAI Codex cheat sheet

| Capability | Claude Code (Jun 2026) | OpenAI Codex (2026) |
|---|---|---|
| Run-until-done, **enforced gate** | `/goal` — completion condition, loops until met | *no equivalent* — `AGENTS.md` "Done when" is advisory + `/review` |
| Recurring runs (cron) | `/loop` (cron under the hood) | Automations |
| Multi-agent orchestration | dynamic workflows ("tens to hundreds of agents") | subagents; parallel tasks |
| Permissionless autonomy | auto mode (classifier-gated) | sandbox-first execution |
| Cloud / close-your-laptop | Routines / web | Codex cloud tasks |
| Conventions file | `CLAUDE.md` | `AGENTS.md` |
| Reusable skill | Skills (`SKILL.md`) | `AGENTS.md` + prompt files |

The biggest divergence: **`/goal`'s enforced completion gate has no Codex equivalent** — port the stopping oracle by hand. Details in Chapters 6 and 12; current syntax always via `/help`.

---

## Primary sources

The manual was built with multi-agent research and adversarial verification of the viral quantitative claims; full per-chapter citations live in each chapter's Sources table. The load-bearing primaries:

| Area | Source | Link |
|---|---|---|
| The ReAct loop | Yao et al., *ReAct* (2022 / ICLR 2023) | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |
| Why feedback must be external | *LLMs Cannot Self-Correct Reasoning Yet* (ICLR 2024) | [arxiv.org/abs/2310.01798](https://arxiv.org/abs/2310.01798) |
| The ralph technique | ralph writeup + reference impl (2025) | [ghuntley.com/ralph](https://ghuntley.com/ralph/) |
| Productized loops | Claude Code CHANGELOG (`/goal`, `/loop`, dynamic workflows) | [github.com/anthropics/claude-code](https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/CHANGELOG.md) |
| Orchestration | "Gas Town" + the independent hands-on account | [github.com/gastownhall/gastown](https://github.com/gastownhall/gastown) · [dolthub.com](https://www.dolthub.com/blog/2026-01-15-a-day-in-gas-town/) |
| Durability | "Beads" git-backed ledger (2025) | [steve-yegge.medium.com](https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a) |
| Auto mode safety | "How we built Claude Code auto mode" (2026) | [anthropic.com/engineering](https://www.anthropic.com/engineering/claude-code-auto-mode) |
| Compounding / skills | "Compound Engineering" (2026) | [every.to](https://every.to/guides/compound-engineering) |
| Long-horizon model | Claude Fable 5 / Mythos 5 (Jun 2026) | [anthropic.com/news](https://www.anthropic.com/news/claude-fable-5-mythos-5) |
| Reality check | AI-spend cap reporting; agentic-AI hype-cycle survey (2026) | [techcrunch.com](https://techcrunch.com/2026/06/02/uber-caps-employee-ai-spending-after-blowing-through-budget-in-four-months/) · [gartner.com](https://www.gartner.com/en/articles/hype-cycle-for-agentic-ai) |

**Verification notes carried in the chapters:** several widely-repeated figures are inflated in retelling — a "$297 programming language" (a conflation of two separate facts), "deleted his IDE / 100% of contributions" (an embellishment of a softer original), and "4% of GitHub commits" (a credible analyst *estimate*, not a measured figure). The manual cites the primary and designs against verified mechanics. The framework matters less than the discipline; pick the harness that fits your stack.
