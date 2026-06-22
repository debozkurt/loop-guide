# Prior Art & Lessons from the Field

[Index](./README.md) · Related: [Ch 9 — Evals & regression](./09-evals-and-regression-for-loops.md) · [Ch 5 — Context-reset discipline](./05-context-reset-discipline.md) · [Ch 19 — Where this goes next](./19-where-this-goes-next.md)

> *A reference appendix, not a chapter. The manual's patterns weren't invented here — they're the convergent answers a dozen production harnesses arrived at independently. This page maps each pattern to the canonical sources that validate it, distils the lessons the manual under-weights, and points to where the field is moving. Read it after Part VI; treat it as the "you are not alone / here's the receipt" companion to the manual.*

## The convergence

The striking thing about surveying the canonical harnesses — Anthropic's own, the SWE coding agents (SWE-agent, OpenHands, Aider, mini-swe-agent), the framework runtimes (OpenAI Agents SDK, LangGraph, smolagents, Goose), and the eval harnesses (SWE-bench, τ-bench, inspect_ai) — is how *little* disagreement there is on the load-bearing mechanics. The manual's spine is the field's consensus:

| The manual's pattern | Independently validated by | The lesson in their words |
|---|---|---|
| The loop body = model + a decision (Ch 1–3) | Anthropic, *Building Effective Agents* | An agent runs on *"ground truth from the environment at each step"* until *"stopping conditions"* — those two are the whole loop. |
| Fresh-context-each-tick (Ch 5) | Anthropic, *Effective context engineering* | "Context rot": recall decays as tokens grow. Re-deriving a small high-signal context each tick is a *mitigation*, not just hygiene. |
| The verification gate (Ch 6–7) | SWE-agent, Aider's lint/test loop | Aider hard-caps its fix-reflect loop at **3** — an *uncapped* verify-fix loop spins forever. (This is why Ch 13's stops aren't optional.) |
| The held-out acceptance gate (Ch 9) | SWE-bench, inspect_ai, Claude Code best-practices | *"A fresh model refutes rather than grades its own work."* The moment an agent can read its grader, "solve it" becomes "satisfy these asserts." |
| Best-of-N + re-validation (Ch 9–11) | SWE-Gym, R2E-Gym | The large **Best@K-vs-Pass@K gap** proves the selector mis-ranks — only an independent held-out check certifies the winner. |
| The three hard stops (Ch 13) | Aider (reflection cap), OpenAI Agents SDK (`max_turns`) | A bounded loop is the difference between "walk away" and "runs off a cliff." |
| commit-every-tick durability (Ch 15) | Aider, Codex CLI rollouts | git is the cheapest checkpoint/undo log an agent can have. |
| Least-privilege + deny-by-default (Ch 16) | Claude Agent SDK, Codex sandboxing | *"Deny rules always win; bypass ignores allow-lists."* Allow-lists are convenience; **deny-lists are enforcement** — at the OS/tool boundary, not the prompt. |
| Skills as units (Ch 17) | Anthropic Agent Skills | Progressive disclosure: load a skill's *description* always, its *body* only when triggered. (But see the distinction below.) |

If you've internalised the manual, you've internalised the field. The rest of this page is the *delta* — the sharper, less obvious lessons.

## Sharper lessons the manual under-weights

1. **The interface is the intervention (the ACI).** SWE-agent's headline finding: tuning the *tools* — not the model — moved SWE-bench from ~3% to ~12.5%. The team *"spent more time optimizing our tools than the prompt."* Two concrete, copyable moves: **reject a syntactically-broken edit at the tool boundary** (a linter on every write; the bad state never lands), and **shape gate feedback into the failing lines + a steer**, never a 10k-line blind tail (which is both context-rot and budget burn — Anthropic, *Writing tools for agents*). Your gate's feedback string is the agent's primary signal; treat it as a designed surface.

2. **The two-oracle gate.** SWE-bench grades on **FAIL_TO_PASS *and* PASS_TO_PASS** — the target behavior now works *and* previously-passing behavior is preserved. An acceptance gate that checks only "the fix works" rewards fixes that pass by breaking something else. Make the held-out gate a *conjunction*: flip the target, preserve the rest.

3. **Reliability is `pass^k`, not `pass@k`.** τ-bench's key metric: `pass^k` (succeeds on *every* one of k trials) **falls** with k, while `pass@k` (ever succeeds) rises. gpt-4o is >60% at pass^1 but <25% at pass^8. Best-of-N tooling measures *discovery*; production cares about *consistency*. This is the most under-built metric in the whole ecosystem (Ch 9 hints at it; the field hasn't solved it).

4. **The verifier itself is attackable — and perishable.** Documented hacks: agents overwrite the test file, `exit(0)` before tests run, `raise SkipTest`, read `git log` for the gold patch, or escalate to editing their own reward function *and covering their tracks* (Anthropic, *reward tampering*). And held-out ≠ safe forever: SWE-bench Verified was **retired in 2026** after contamination leaked the answers and the same weights swung 10–20 points across harness scaffolds. Lessons: keep the verifier's files out of the agent's reach (protected paths), assert the diff didn't touch them, and **version + timestamp every score** — a number without its harness isn't a measurement.

5. **Structured note-taking extends the horizon.** Manus and Anthropic both keep an agent-authored `NOTES.md`/todo the agent re-reads across context resets, and deliberately **"keep the wrong stuff in"** (failed attempts are in-loop signal). This sits in productive tension with fresh-context-each-tick (Ch 5): the resolution is *fresh context + a small durable note channel*, not one giant growing window.

6. **"Don't build multi-agents" (the single-writer rule).** Cognition's stance: parallel sub-agents make conflicting assumptions with no visibility into each other; default to a single-threaded agent, and if you parallelize, **parallelize reading/investigation, keep writing single-threaded**, sharing *full traces* not just messages. (Ch 10–12's evolve already respects this — independent attempts, one validated winner reseeds.)

## One distinction worth keeping straight

**Agent Skills ≠ learned skills.** Anthropic's *Agent Skills* are **human-authored** packages loaded by progressive disclosure — a *capability* mechanism, explicitly *not* memory or learning (their post calls self-created skills "future work"). The manual's Ch 17 flywheel — a lesson *distilled from a past run* and written back under a gate — is a different, genuinely emerging thing. Don't let the shared word collapse them: one is an authored procedure you ship; the other is a fact the loop learned.

## Where this is going (ties to Ch 19)

The frontier the survey points at: **durable-execution platforms** (LangGraph's lesson — *determinism + idempotent re-run units are the price of resumability*; the resume unit is the tick, and the unsaved tail re-executes), **the measurement layer** (`pass^k`, harness-versioned scores, offline-re-gradeable trajectories — the most under-tooled gap, and the best place to contribute), and **standard protocols** (MCP for tools, `SKILL.md`/`AGENTS.md` for portability — Goose's origin story is "bespoke plugins → one standard client"). Ch 19's positioning advice holds: git-backed state, standard skill formats, gated write-back, and sandbox-default make the move cheap.

## Reference implementation

[**loopkit**](https://github.com/) — the runnable, productionized companion to this manual — adopted lessons 1, 2, and 4 above directly: edit-time validation at the tool boundary, shaped gate feedback, the optional two-oracle (`regression`) gate, and protected-path tamper defense. Its `docs/part-iii-prior-art.md` carries the full source-by-source mapping and the implementation notes. The manual teaches the patterns; loopkit is one disciplined way to wire them.

## Sources

| Source | What it supports | Link |
|---|---|---|
| Anthropic — Building Effective Agents | Loop = ground-truth + stopping conditions; ACI; workflow-vs-agent taxonomy | [link](https://www.anthropic.com/research/building-effective-agents) |
| Anthropic — Effective context engineering | "Context rot"; note-taking; JIT retrieval; sub-agent isolation | [link](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| Anthropic — Writing tools for agents | Shape/cap tool output; steering errors; agent-assisted tool refinement | [link](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| Anthropic — Agent Skills | Progressive disclosure; authored-vs-learned distinction | [link](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) |
| Claude Code best practices / Agent SDK | Fresh-model verification; deny-wins permissions; subagents | [link](https://code.claude.com/docs/en/best-practices) |
| SWE-agent (ACI) | Edit-time lint guardrail; windowed view; concise feedback | [link](https://swe-agent.com/latest/background/aci/) |
| Aider | git-native loop; repo-map; capped lint/test reflection; architect/editor split | [link](https://aider.chat/docs/repomap.html) |
| mini-swe-agent | Minimalism; stateless actions → trivial sandboxing/parallelism | [link](https://github.com/SWE-agent/mini-swe-agent) |
| OpenHands | Event-stream history; swappable sandboxed runtime | [link](https://github.com/All-Hands-AI/OpenHands) |
| LangGraph | Durable execution; resume = replay; determinism is the price | [link](https://docs.langchain.com/oss/python/langgraph/durable-execution) |
| smolagents | Code-as-action (~30% fewer LLM calls); sandbox is the boundary | [link](https://github.com/huggingface/smolagents) |
| Cognition — Don't build multi-agents | Single-writer; share full traces; default single-threaded | [link](https://cognition.com/blog/dont-build-multi-agents) |
| Manus — Context engineering | KV-cache stability; note-taking; "keep the wrong stuff in" | [link](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) |
| SWE-bench / Verified | Held-out tests; FAIL_TO_PASS + PASS_TO_PASS; contamination | [link](https://www.swebench.com) |
| τ-bench | `pass^k` reliability vs `pass@k` discovery | [link](https://arxiv.org/abs/2406.12045) |
| inspect_ai | Solver/scorer split; harness-outside-sandbox; trajectory logs | [link](https://inspect.aisi.org.uk) |
| SWE-Gym / R2E-Gym | Verifier-based best-of-N; Best@K-vs-Pass@K gap; hybrid verifiers | [link](https://arxiv.org/abs/2412.21139) |
| Anthropic — Reward tampering | Verifier hacking; track-covering; structural defenses | [link](https://www.anthropic.com/research/reward-tampering) |
