# Glossary — Agentic Loops

Every term used in this curriculum, one or two sentences each. Ordered roughly foundational → advanced. When a term has a precise meaning *in this guide* that differs from loose industry usage, the difference is noted.

[← Back to index](./README.md)

---

### Loop (agentic loop)
A small program you write that prompts a coding agent for you, reads what it produced, decides whether it's done, and prompts it again if not. The defining property: a **model**, not a hardcoded branch, decides the next action each tick. "Cron plus a decision-maker in the body."

### Loop body
The decision-making step inside one iteration — the model invocation that looks at current state and chooses what to do. The thing cron never had.

### Loop author / loop engineer
You, when you've stopped typing prompts into the agent and started writing the program that prompts it — the altitude shift from prompting each step to authoring the loop ("stop being the thing in the loop").

### Tick / iteration
One pass through the loop: prompt the agent → it acts → read the result → decide whether to continue. Loops are bounded by a **maximum iteration count** to prevent runaways.

### ReAct (Reasoning + Acting)
The 2022 paper (Yao et al.) that formalized the inner loop: the model produces a reasoning trace, takes an action (tool call), observes the result, and repeats. Every modern agent framework wraps this loop. See [Chapter 3](./03-the-inner-loop-formally.md).

### Inner loop vs outer loop
The **inner loop** is ReAct inside a single agent turn (invoke → tool calls → observe → repeat until the model stops asking for tools). The **outer loop** is what this curriculum is about: the program wrapped *around* the whole agent, re-invoking it across many fresh sessions, on a schedule, with durable state.

### Termination
How a loop decides to stop. In the inner loop, the model stops emitting tool calls. In the outer loop, a **stopping oracle** (a validator, a test gate, a completion condition) decides — *not* the agent declaring itself done.

### Recursion limit / iteration cap
A hard maximum on inner-loop steps (`max_iterations`, `recursion_limit`) or outer-loop ticks. The first and most universal of the **three hard stops**. Without it, a confused model loops forever.

### AutoGPT
The March 2023 viral autonomous agent that gave a model a goal and let it prompt itself. Famous for "spinning forever doing nothing" — a termination-criteria failure. Its lasting contribution was a *catalogue of failure modes*, not a technique. See [Chapter 2](./02-the-lineage.md).

### ralph (the ralph loop / Ralph Wiggum technique)
A July 2025 technique: a bash one-liner that pipes the *same fixed prompt file* into a coding agent over and over, e.g. `while :; do cat PROMPT.md | claude-code ; done`. Each iteration gets a fresh context window; durable progress lives in files, not conversation history. See [Chapter 4](./04-the-ralph-technique.md).

### Anchor files
The fixed set of files (`PROMPT.md`, `AGENTS.md`/`CLAUDE.md`, `specs/*`, a plan file) that a ralph loop reloads deterministically every iteration. The loop's memory lives here, on disk, not in the context window.

### Context reset / fresh context
Discarding the conversation history each iteration and rebuilding context from the anchor files. The core ralph discipline: a small, fresh, correct context beats a large, accumulating, degrading one. See [Chapter 5](./05-context-reset-discipline.md).

### Context rot
The degradation of a long-running conversation: early instructions get forgotten, compaction corrupts constraints, irrelevant tokens crowd out relevant ones. Context reset is the antidote.

### `/goal`
Claude Code's "run until done" command (v2.1.154): set a completion condition and Claude keeps working across turns until it's met. The productized ralph loop with a **completion gate**. See [Chapter 6](./06-goal-and-loop-productized.md).

### `/loop`
Claude Code's recurring-run command: schedule a prompt or slash-command to run unattended on an interval (cron under the hood) or self-paced. Canonical example: `/loop babysit all my PRs. Auto-fix build issues...`. See [Chapter 6](./06-goal-and-loop-productized.md).

### Completion gate / stopping oracle
The thing that decides a loop is *actually done* — a validator model, a passing test suite, a satisfied completion condition. Distinct from the agent's own claim of doneness, which is unreliable.

### Validator model
A separate (often smaller, cheaper) model whose only job is to judge whether the loop's exit condition is met. Reported as the mechanism behind `/goal`; also the LLM-as-judge stopping signal. Itself fallible — see **judge fallibility**.

### Open loop vs closed loop
Borrowed from control theory. An **open loop** writes code and never checks the result — "a machine for generating confident mistakes." A **closed loop** feeds the result (test output, compiler errors, a review) back in and corrects. The feedback edge is what makes a loop trustworthy. See [Chapter 7](./07-the-feedback-imperative.md).

### Self-verification
The loop running build / test / lint / typecheck on *its own output* each iteration and using the result as feedback. Widely cited as the single highest-leverage practice — one practitioner estimate puts it at a 2–3× quality lift (an estimate, not a benchmark).

### Intrinsic self-correction
A model re-reading and "fixing" its own reasoning with **no external signal**. The DeepMind finding (Huang et al., 2024): this does not reliably improve correctness and can degrade it. The reason verification must be grounded in something outside the model — tests, a compiler, a different model.

### Continuous review
Reviewing every commit a loop produces, in the background, and feeding findings back while the context that produced them is still fresh. The roborev pattern. See [Chapter 8](./08-continuous-review.md).

### roborev
A 2026 tool (Kenn Software, `kenn-io`) that hooks post-commit, reviews each diff in a background worker pool, persists findings, and loops fix → re-review until clean. The canonical continuous-review instantiation. *(Authorship is sometimes misattributed in social posts; primary materials credit the org.)*

### Gaming the verifier
A closed-loop failure mode where the loop learns to satisfy the gate without satisfying the intent — e.g., deleting the failing test instead of fixing the bug. Why the gate must be hard to cheat and the intent must be checked too. The *adversarial* form of proxy optimization; its honest counterpart is **overfitting the gate**.

### Overfitting the gate
The honest twin of gaming the verifier: a loop iterating against a *fixed* gate fits *those exact checks* — passing them without reaching the goal — with no test-tampering and no bad intent. The *regressional* form of Goodhart's law (optimize a proxy, select its noise) versus the *adversarial* form that is gaming. Caught by a held-out gate. See [Chapter 9](./09-evals-and-regression-for-loops.md).

### Iteration gate vs acceptance gate (held-out gate)
Two tiers of verification. The **iteration gate** is the fast, in-sample check the loop optimizes against every tick; the **acceptance gate** is a held-out check — a reserved test set, an integration suite, a fresh reviewer, acceptance criteria the loop can't read — run once on the candidate, which it never optimized against. The held-out gate is what tells you the green was real, not just fit. See [Chapter 9](./09-evals-and-regression-for-loops.md).

### Selection inflation (best-of-N)
Keeping the best of N attempts against a noisy gate inflates the winner's apparent quality — the maximum of N noisy scores is optimistically biased, and the bias grows with N. With a near-oracle gate the gain is mostly real; with a noisy one, past a turnover point you select flukes. Re-validate the selected winner on a held-out gate it never competed against. See [Chapter 9](./09-evals-and-regression-for-loops.md), [Chapter 12](./12-dynamic-workflows-and-fan-out.md).

### pass^k
The probability that *all* k runs pass (reliability), as opposed to pass@k (any of k succeed). A single green can be flaky luck; for anything nondeterministic, score pass^k — consistency is the signal, one green is a sample of size one. See [Chapter 9](./09-evals-and-regression-for-loops.md).

### Trajectory eval
An evaluation that scores *how* the loop reached its answer (which tools, which steps, did it converge) — not just the final output. Catches loops that "pass" for the wrong reasons. See [Chapter 9](./09-evals-and-regression-for-loops.md).

### Golden task
A known-good task with a known-good outcome, replayed against the loop to detect regressions. The loop's unit test.

### Convergence
Whether a loop actually finishes the task and stops, versus oscillating, stalling, or declaring false victory. An emerging, under-standardized area of loop evaluation.

### Orchestration loop / supervisor loop
A loop whose *job is to dispatch and monitor other loops* — assigning work to worker loops, watching their progress, restarting or reassigning the stuck ones. The "continuous orchestration loop that oversees other threads" — the genuinely new 2026 layer. See [Chapter 10](./10-from-one-loop-to-many.md).

### Worker loop
A loop doing the actual coding work (write, test, commit) under the direction of an orchestration loop. In Gas Town, a "polecat."

### Gas Town
An open-source orchestration system (Jan 2026): ~20–30 Claude Code instances coordinated by a **Mayor** agent, with **patrol** agents running continuous supervisory loops and state stored in **git** (via Beads) so work survives a crash. See [Chapter 11](./11-gastown-and-the-mayor-pattern.md).

### Mayor
In Gas Town, the top-level coordinator — itself a full Claude Code instance with workspace context — that you task and that spawns/dispatches worker agents. The human operates "one layer removed."

### Patrol agent
In Gas Town, a supervisory agent running a continuous scheduled loop (on a heartbeat) that monitors worker loops and nudges, hands off, or escalates the stuck ones. The literal "loop watching loops."

### Beads
A git-backed issue ledger (SQLite for queries → JSONL → committed to git; "git IS the database"). The durability substrate that lets a crashed agent's successor resume the in-progress work. See [Chapter 11](./11-gastown-and-the-mayor-pattern.md) and [Chapter 15](./15-durability-and-crash-recovery.md).

### Dynamic workflow
Claude Code's feature (v2.1.154) for asking Claude to *create a workflow* that orchestrates work across "tens to hundreds of agents." The productized fan-out. See [Chapter 12](./12-dynamic-workflows-and-fan-out.md).

### Fan-out
Spawning many subagents to work in parallel on independent slices of a task, then collecting results. Bounded by a concurrency cap; the wall-clock win is real when the slices are genuinely independent.

### Evolutionary loop / population search
A loop topology that is fan-out plus selection plus cross-pollination: generate a population of candidates, score each against an objective, keep the top-k, reseed those winners into the next generation's prompts, and repeat. How program-search systems (FunSearch, AlphaEvolve) discover non-obvious solutions; the third topology alongside single-artifact refinement and independent fan-out, and the one most exposed to **selection inflation**. See [Chapter 12](./12-dynamic-workflows-and-fan-out.md).

### Scheduling-replaces-kickoff
The shift from a human starting each run to the loop running on **infrastructure time** — a cron tick, a GitHub event, an HTTP trigger — instead of on your attention. See [Chapter 12](./12-dynamic-workflows-and-fan-out.md).

### The three hard stops
The trio every serious 2026 loop converges on: **(1) maximum iteration count**, **(2) no-progress detection**, **(3) a token-or-dollar budget ceiling**. Most of your job as a loop author is making the loop *halt*. See [Chapter 13](./13-making-loops-halt.md).

### No-progress detection
Detecting that the loop's state isn't advancing — the same error, an empty/unchanged diff, or the same failing test N times in a row — and halting. The least-standardized of the three hard stops; mostly heuristic.

### Budget ceiling
A token or dollar cap that halts the loop regardless of progress. The guardrail against "billing surprises orders of magnitude over budget." See [Chapter 14](./14-the-economics-of-loops.md).

### The cost shift
The observation that once the model writes code for almost nothing, the expensive resource becomes **loop management** — running, supervising, retrying the loop — not token generation. "The costliest thing in AI coding is no longer writing code, it's managing the agent loop." See [Chapter 14](./14-the-economics-of-loops.md).

### Auto mode
Claude Code's safer-than-skip-permissions mode (Mar 2026): instead of disabling all approval checks, it delegates routine approvals to model classifiers with tiered allowlisting, so only high-risk actions hit the full gate. Enables permissionless autonomous runs. See [Chapter 16](./16-permissions-and-safety.md).

### Blast radius
The maximum damage a loop can do if it goes wrong — files it can write, commands it can run, branches it can push, money it can spend. Loop safety is largely blast-radius containment. See [Chapter 16](./16-permissions-and-safety.md).

### Sandboxing
OS-level isolation (filesystem, network, process) that bounds what a loop can touch regardless of what the model decides. Distinct from auto mode's classifier-gating; the two compose.

### Headless mode
Running the agent non-interactively (`claude -p`) so it can be driven by a script or loop with no human at the keyboard. The primitive that cloud Routines and bash loops wrap.

### Routines (Claude Code on the web)
Anthropic-managed cloud execution of Claude Code that runs unattended on a schedule, GitHub event, or HTTP trigger — the "close your laptop" product. Distinct from **Remote Control**, which runs the session on *your* machine.

### Skill (as the unit inside the loop)
A reusable, named, tested unit of capability the loop calls — in Claude Code, a `SKILL.md`. The guiding doctrine: "if you do something more than once, turn it into a skill." Loops that call sharp named skills **compound**; loops that re-derive everything every cold session **burn money**. See [Chapter 17](./17-its-not-loops-its-skills.md).

### Compound engineering
A 2026 framing: each unit of engineering work should make subsequent units *easier*, by codifying learnings into reusable agent instructions/skills. The lineage behind "it's not loops, it's skills."

### Flywheel vs treadmill
A loop that writes its learnings back into the skills it calls gets cheaper and better over time (flywheel). A loop that re-derives everything from a cold start every iteration runs in place forever (treadmill). The structural difference is whether there's a write-back edge into the skill.

### Fable 5 / Mythos 5
Anthropic's June 9 2026 models, built for long-horizon agentic work: 1M-token context, up to 128k output, self-verification at highest effort. Fable 5 is the public model with safety classifiers; Mythos 5 is the same capability without them, for approved organizations only. The model capability that flipped loops from "burns money chasing its tail" to "trustworthy overnight." See [Chapter 17](./17-its-not-loops-its-skills.md).

### Maturity ladder
A three-stage progression: (1) write code by hand with autocomplete → (2) run several agent sessions in parallel and prompt each → (3) stop prompting; write the loops that prompt the agents. Placing yourself on the ladder tells you what to automate next. See [Chapter 18](./18-anti-patterns-and-decision-framework.md).

### Task horizon
The length of task an agent can complete autonomously. Measured horizons have been doubling roughly every four months — the precondition that made overnight loops viable, and still moving, so loops you can't trust today are worth re-testing on a cadence. See [Chapter 19](./19-where-this-goes-next.md).

### Durable execution
Checkpoint/resume as a managed platform primitive — the hosted alternative to the loop's hand-rolled commit-every-tick, git-as-database durability. Trades vendor-neutral transparency for managed resilience. See [Chapter 15](./15-durability-and-crash-recovery.md), [Chapter 19](./19-where-this-goes-next.md).

### Self-improving loop
A loop that automates the write-back edge — distilling its own trajectories into reusable skills. Works only when each new skill is validation-gated; ungated, self-generated skills tend to regress. The flywheel automated, behind the gate. See [Chapter 17](./17-its-not-loops-its-skills.md), [Chapter 19](./19-where-this-goes-next.md).

---

[← Back to index](./README.md)
