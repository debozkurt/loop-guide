# Graduating to loopkit

[Index](./README.md) · Builds on: [the capstone](./capstone/README.md) · [Prior art & field lessons](./prior-art.md)

> *This manual teaches the patterns against a minimal, stdlib-only harness you can read end to end. **[loopkit](https://github.com/debozkurt/loop-kit)** is those same patterns built out as a product. This page is the bridge: which manual concept becomes which loopkit part, when to make the move, and where both still have open work. Read it after the [capstone](./capstone/README.md) — once you've run the ideas, this is how you run them on real repositories.*

## Two separate artifacts

The [capstone harness](./capstone/harness/) and loopkit are deliberately **not** the same codebase, and the separation is intentional:

- **The capstone** is the manual's code made whole — minimal, dependency-free, every line legible. It exists so you can *read and run the ideas*. You extend it by editing one `loop.py`.
- **loopkit** is the full implementation — a 2×2 adapter matrix with exact per-model cost, an in-process and a Kubernetes fleet, credential hardening against prompt injection, a keyless-executor sandbox, and the three deployment tiers of [Chapter 21](./21-the-ci-deployment-tier.md). It exists so you can *run the ideas on real repositories, unattended*.

They share a common core — the loop body, the two-tier gate, the three hard stops, git-backed durability, skills-as-units — so moving from one to the other means recognising familiar parts rather than relearning them. The capstone stays dependency-free on purpose, while loopkit carries the operational weight so the manual doesn't have to.

## When to graduate

| Stay in the manual + capstone when… | Reach for loopkit when… |
|---|---|
| you're learning the patterns or prototyping | you're running loops on a real repo, unattended, repeatedly |
| one repo, one loop, driven by hand | you need a **fleet** — many concurrent runs, or `evolve` (best-of-N + held-out re-validation) |
| you want to read and edit every line | you need **measured cost** with a per-model price table and a budget stop that bites |
| a shell env and a laptop are enough | you need the **CI or cloud tiers** — forge-triggered, credential-hardened, isolated |
| the gate is a command you wrote | you want the **held-out two-oracle gate**, a gate-stability preflight, and `pass^k` reliability numbers |

The rule mirrors [Chapter 21](./21-the-ci-deployment-tier.md)'s tier ladder: start at the top and descend only when a real need pushes you. Most work never leaves the capstone, and loopkit is where the heavier work goes when it must.

## The map — concept → capstone → loopkit

Each row is one manual concept, the capstone artifact that embodies it, and the loopkit part that hardens it. The last column is what loopkit adds *beyond* the readable version.

| Manual concept | Capstone artifact | loopkit part | What loopkit adds |
|---|---|---|---|
| Fresh context ([Ch 5](./05-context-reset-discipline.md)) | `build_prompt` + anchor files | `prompt.py` | ordered anchors, prompt-cache discipline, the bounded note channel as a design target |
| The completion gate ([Ch 6](./06-goal-and-loop-productized.md)) | `goal_met` / `gate_cmd` | `gate.py` (`ShellGate`) | swappable adapters; exit-code gate with shaped, not blind, feedback |
| The feedback imperative ([Ch 7](./07-the-feedback-imperative.md)) | `verification_gate` | `gate.py` + `executor.shape_failure_output` | failing lines + a steer, budget-bounded, instead of a 10k-line tail |
| Continuous review ([Ch 8](./08-continuous-review.md)) | `review_commit` | `extensions/review.py` (`ShellReviewHook`) | a pluggable per-commit reviewer seam (any command / model) |
| Evals + the held-out gate ([Ch 9](./09-evals-and-regression-for-loops.md)) | `evals.py` + held-out gate | `config.gate.acceptance` + `gate.regression`; `safety.gate_stability` (`run --check-gate`) | the **two-oracle** gate (target works *and* nothing regressed) + a determinism preflight that refuses to start on a flaky gate |
| Orchestration ([Ch 10–12](./10-from-one-loop-to-many.md)) | `orchestrate.py` | `extensions/orchestrate.py` | an in-process fleet **and** a Kubernetes fleet; `evolve` = fan-out + held-out re-validation of the winner |
| The three hard stops ([Ch 13](./13-making-loops-halt.md)) | `StopReason` + `state_signature` | `stops.py` | the same three, with the budget stop fed by *exact* cost |
| Economics ([Ch 14](./14-the-economics-of-loops.md)) | `roi_ok` + measured cost | `pricing.py` + `extensions/measure.py` | a per-model price table; `pass^k` reliability + `cost_per_accepted` (`loopkit measure`) |
| Durability ([Ch 15](./15-durability-and-crash-recovery.md)) | `commit_progress` | `durability.py` | hardened git flags (hooks off, injected-config overridden), resumable remote-only branches |
| Permissions & safety ([Ch 16](./16-permissions-and-safety.md)) | pre-tool-use hook + `Config` | `safety.py` + `executor.py` + `secrets.py` | the blast-radius envelope, a **keyless-executor sidecar** (a kernel boundary, not a timed shred), credential hygiene vs prompt injection |
| Skills flywheel ([Ch 17](./17-its-not-loops-its-skills.md)) | `SKILL.md` + `write_back` | `extensions/skills.py` (`GitSkillRegistry`, `ShellDistiller`) | a git-repo flywheel durable across *machines*, gated by the held-out acceptance gate, content-sanitized against poisoning |
| Triggers ([Ch 20](./20-triggers-as-infrastructure.md)) | `trigger.py` | `extensions/triggers.py` (`WebhookApp`, `parse_review_event`) | GitHub-HMAC + GitLab-token providers, Redis dedupe for replicas, issue-author binding, **revise runs** |
| The CI tier ([Ch 21](./21-the-ci-deployment-tier.md)) | `--from-event` / `--open-pr` | `loopkit run --from-event/--open-pr`, `init --ci` | all three tiers; the cloud fleet (`extensions/cloudrun.py`) with per-run namespaces |

Run any of these labs to watch a row live: `loopkit demo 20` (triggers, with the revise beat), `loopkit demo 21` (the CI tier), `loopkit demo 22` (agent isolation), `loopkit demo 23` (the skills repo across pods), `loopkit demo 24` (reliability / `pass^k`).

## The frontier both share

A few lessons the manual now teaches as foundational are ones loopkit is *still building*. These are the open problems where a graduating engineer can contribute:

- **Oracle synthesis** ([Ch 9](./09-evals-and-regression-for-loops.md)) — the biggest real-use friction is hand-authoring a fail-first held-out oracle per task. The fix is an independent proposer that drafts the check and a harness that verifies it fails first. loopkit tracks this as its top adoption lever.
- **The bounded note channel** ([Ch 5](./05-context-reset-discipline.md)) — fresh-context is right, but the agent re-explores the codebase every tick. A size-capped, agent-curated working note repays that without reintroducing rot. loopkit tracks it as a "persistent scratchpad" with a hard-bound caveat.
- **Semantic stops + `NEEDS_HUMAN`** ([Ch 13](./13-making-loops-halt.md)) — the three counters catch mechanical stalls, not semantic thrash or genuine ambiguity. A content-level thrash signal and an early human-escalation terminal are the direction, not a solved problem, in either repo.

loopkit's own read on these — ranked, with the prior-art receipts — lives in its `docs/part-iii-prior-art.md` ("Lessons to adopt next").

## Sources

| Source | What it anchors | Link |
|---|---|---|
| The [capstone](./capstone/README.md) | the readable, stdlib form of every row's left column | [local](./capstone/README.md) |
| **loopkit** — modules, CLI, `demo 20`–`24` | the production form of every row's right column | [github.com/debozkurt/loop-kit](https://github.com/debozkurt/loop-kit) |
| loopkit `docs/part-iii-ecosystem.md` | the three tiers + the per-primitive map, from the product side | [part-iii-ecosystem.md](https://github.com/debozkurt/loop-kit/blob/main/docs/part-iii-ecosystem.md) |
