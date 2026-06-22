# Capstone — The Self-Governed Loop

[← Back to Chapter 21](../21-the-ci-deployment-tier.md) · [Index](../README.md)

> *The finished state of the artifact the manual built. Every chapter's "Implement it" delta, assembled into one runnable harness you can `python3 loop.py` right now, fork against your own repo, and hand to a team.*

## What this is

This is not a new project — it is `loop.py`/`orchestrate.py` from the manual, completed. Each chapter added one delta (see the build-up table in the [manual README](../README.md)); the capstone is where those deltas live assembled, runnable, and dry-run-tested. It ships in three layers:

```
capstone/
├── harness/        Layer 1 — runnable code
│   ├── loop.py         the self-governed loop: verification gate + three hard stops
│   │                   + git-durable state + stop-reason logging   (the assembled artifact)
│   ├── loop.sh         the bash "ralph" form, for the lineage (Ch 4)
│   ├── orchestrate.py  the supervisor + isolated-worker variant   (Ch 10–12)
│   ├── PROMPT.md        the fixed anchor prompt                    (Ch 4–5)
│   ├── verify.sh        an example verification gate               (Ch 7)
│   └── config.json      the pre-flight Config: stops · gate · agent command  (Ch 13–18)
├── lab/            Layer 2 — do it on your own repo
│   └── lab-guide.md     dry-run → real run → your repo → orchestrate
└── teaching-kit/   Layer 3 — teach it to a team
    └── facilitator-guide.md   a 90-minute workshop: run-of-show, exercises, cheat-sheet
```

The harness is the thing; the lab teaches you to wield it on real code; the teaching kit lets you stand it up for a team.

## The three layers, and who each is for

**Layer 1 — the harness** (`harness/`). A runnable reference loop in dependency-free Python (stdlib only), so it runs anywhere and reads as the manual's code made whole. It ships with a **`--dry-run` mode** that uses a stub agent, so you can watch the full control flow — halting, no-progress detection, stop-reason logging — **without installing Claude Code or spending a cent.** Then flip to real mode and it drives `claude -p`. *For: anyone who learns by reading and running code. Start here.*

**Layer 2 — the lab** (`lab/`). A step-by-step path from `python3 loop.py --dry-run` to a real loop on *your* repository, climbing the same rungs the manual does: one bounded loop ([Ch 13](../13-making-loops-halt.md)), a verification gate ([Ch 7](../07-the-feedback-imperative.md)), durability ([Ch 15](../15-durability-and-crash-recovery.md)), orchestration ([Ch 10](../10-from-one-loop-to-many.md)). Each step has a "you should see…" checkpoint and the common failure. *For: applying it tomorrow to your own project.*

**Layer 3 — the teaching kit** (`teaching-kit/`). A 90-minute workshop: a run-of-show with timings, live-demo scripts, three hands-on exercises (build a gate, make it halt, break it on purpose), and a facilitator cheat-sheet. *For: instructing a group — a talk, a brown-bag, onboarding.*

## How the harness assembles the manual

Each element is the final form of one chapter's delta — read the code beside the chapter to see the build-up complete:

| Harness element | Chapter delta | Concern |
|---|---|---|
| `run_agent()` — fresh subprocess each tick | Ch 3, 5 | fresh-context invariant; the model as a subroutine |
| `verification_gate()` → `GateResult`, feedback into next prompt | Ch 6–7 | closed loop; the external stopping oracle |
| `run_loop()` — the three-stop precedence | Ch 13 | iteration cap, budget ceiling, no-progress, then the gate |
| `state_signature()` + stall counter | Ch 13 | no-progress detection |
| `_parse_cost()` feeding the budget stop | Ch 14 | measured cost, structural ceiling |
| `commit_progress()` each tick | Ch 15 | git-durable, resumable state |
| `StopReason` + `log()` | Ch 9, 13 | which terminal fired — observability |
| `Config` agent command, `branch`, `push` | Ch 16 | least-privilege, branch-only blast radius |
| `make_worktree()` / `run_worker()` / `run_fleet()` | Ch 10–12 | isolation; supervisor over worker loops |

## Quick start (60 seconds, no Claude Code required)

```bash
cd harness/
python3 loop.py --dry-run --max-iter 5        # watch it reach DONE
python3 loop.py --dry-run-stall --max-iter 8  # watch the no-progress HALT
python3 loop.py --dry-run --budget 1.0        # watch the budget-ceiling HALT
```

You'll watch the stub agent run, the gate decide, and the loop halt with a logged stop-reason — the whole control flow, safely, for free. Then read [the lab guide](./lab/lab-guide.md) to point it at real code.

> **Safety note before running it for real:** the harness pushes to a *feature branch only* and never to `main`, holds no production credentials, and enforces a budget ceiling — by design ([Chapter 16](../16-permissions-and-safety.md)). Read `config.json` and confirm the blast radius before flipping off `--dry-run`; the agent command runs unattended on your machine.

---

[← Back to Chapter 21](../21-the-ci-deployment-tier.md) · [Index](../README.md) · [Lab guide →](./lab/lab-guide.md)
