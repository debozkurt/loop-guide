# Chapter 5 — Context-Reset Discipline

[← Previous](./04-the-ralph-technique.md) · [Index](./README.md) · [Next: /goal and /loop →](./06-goal-and-loop-productized.md)

> *Why a fresh, small context beats a large, growing one — and how to design the anchor files that become the loop's real memory. This is the mechanism the durability and cost chapters depend on.*

## Concept

The central, counterintuitive rule of loop engineering:

> **A small, fresh, correct context beats a large, accumulating, degrading one.**

The naive instinct — "keep the whole conversation so the agent remembers everything" — is wrong for any loop that runs more than a handful of ticks. A growing conversation **rots**, and the failure is silent: it produces confident wrong output instead of raising an error. The fix is to discard the conversation each tick and rebuild context deterministically from files on disk.

## How it works

Long context degrades four ways, none patchable because they are properties of the system:

1. **Attention dilutes.** A transformer attends across the whole window; more tokens means the relevant constraint competes with thousands of tokens of stale output. Facts in the middle of a long context are recalled less reliably.
2. **Early instructions fade.** The constraint set on tick 1 is one whisper among forty ticks of the model's own later output, which it treats as established fact — including mistakes it "corrected" that still sit in the history.
3. **Compaction corrupts.** When the window overflows, the runtime summarizes older turns. Summarization is lossy and routinely drops the load-bearing constraint while keeping the chatty preamble.
4. **Failed trajectories poison.** Ticks spent on a wrong approach stay in context; the model re-reads its own dead end and is measurably likelier to repeat it.

The **fresh-context invariant** eliminates all four:

> **The context the model sees on tick N is a function only of the files on disk — not of ticks 1…N−1.**

This buys three properties an accumulating loop cannot have: **reproducibility** (tick 500 is primed exactly like tick 5), **bounded context size** (flat cost and quality over a long run instead of a degrading curve — load-bearing for economics, Chapter 14), and **self-healing** (a mistake on tick 12 doesn't haunt tick 13, which never sees tick 12's context — only its committed result on disk).

The cost is **re-priming** each tick. Prompt caching largely absorbs it: the anchor files are *identical* across ticks, which is the best case for prefix caching, so re-reading them is served cheaply.[<sup>1</sup>](#sources) Order anchor files stable-prefix-first (rarely-changing files before the volatile plan file) to maximize the cache hit.

Re-priming has two costs. The token cost — re-reading the anchors — is the one caching absorbs. The one it *doesn't* is **rediscovery**: the agent re-derives its understanding of the codebase every tick, including which files matter, what it already tried, and which approach was a dead end. On a large repo that is minutes of wasted work per tick, and it scales with repo size rather than cache state. The fresh-context invariant is what *causes* it: tick N cannot see tick N−1's reasoning, only its committed result on disk.

The resolution avoids reopening the transcript, which would reintroduce all four rot mechanisms. Instead it is a **bounded, agent-curated note channel**: a small file the agent writes and re-reads across ticks holding only durable working state — files found, the current hypothesis, what failed and *why* — rendered like any other anchor. This keeps fresh-context's purity (the note is a designed, size-capped surface rather than an accumulating conversation) while giving the loop the one thing pure fresh-context throws away: intra-run memory. It is the plan file's discipline applied one level down: the plan file is the *human-facing* durable state, the note channel is the *agent-facing* one. The sharp edge is the bound — uncapped, the note becomes the growing history it was meant to replace, so cap its size and prune it every tick, exactly as you prune the plan.

## Implement it

The implementation is `run_agent` building a fresh prompt from anchor files every tick, plus the anchor-file roles separated by change-frequency so intent stays stable while state churns. The `loop.py` delta:

```python
# loop.py delta — fresh-context priming. Each tick rebuilds context from disk; nothing carries over.
import pathlib

ANCHORS = ["PROMPT.md", "AGENTS.md", "specs/", "IMPLEMENTATION_PLAN.md"]  # stable-prefix-first

def build_prompt(repo: str, feedback: str | None = None) -> str:
    base = pathlib.Path(repo, "PROMPT.md").read_text()       # the FIXED instruction
    if feedback:                                             # last tick's gate failure (Ch 7)
        base += f"\n\n## Verification feedback\n{feedback}\n"
    return base   # the agent reads AGENTS.md / specs / plan from disk itself, by instruction

def run_agent(prompt: str, repo: str) -> None:
    subprocess.run(["claude", "-p", "--permission-mode", "acceptEdits"],
                   cwd=repo, input=prompt, text=True)        # FRESH process = fresh context
```

Each anchor file has a role and a change-frequency, kept in separate files so each can be reasoned about independently:

| File | Role | Changes |
|---|---|---|
| `PROMPT.md` | fixed instruction: read plan, do one task, verify, update plan, stop | rarely |
| `AGENTS.md` / `CLAUDE.md` | conventions, build/test commands, hard constraints | occasionally |
| `specs/` | durable **intent** — what to build, what "done" means | on requirement change |
| `IMPLEMENTATION_PLAN.md` | mutable **state** — done / next / known issues | every tick |

Two disciplines keep this healthy: **separate intent (`specs/`) from state (plan file)** so progress updates can't corrupt the spec, and **prune the plan file** each tick (mark done, delete resolved notes) so even the durable state doesn't rot by append-only growth.

## Builds on

Chapter 4's `cat PROMPT.md | claude -p` becomes a structured `build_prompt` + fresh `run_agent`, and the anchor-file layout from Chapter 4 gets a change-frequency discipline. The feedback parameter is the hook Chapter 7 fills with the verification gate's output.

## Pitfalls

1. **"Just keep the history, it's easier."** It is — for about twenty ticks. Then it rots silently. Default to fresh context for long loops.
2. **One giant anchor file.** You then can't keep intent stable while state churns, and you wreck the cache hit. Separate by change-frequency.
3. **Append-only plan files.** Durable state rots too if you only add to it. Instruct the loop to prune.
4. **Assuming the model handles a cold start for free.** Fresh context means no conversational ramp — the model must orient from the anchor files alone every tick. Write them to make that easy.
5. **Paying the rediscovery cost every tick.** Fresh context is right, but re-deriving the whole codebase each tick is wasted motion caching can't absorb. Give the loop a *bounded* note channel for intra-run working state — and bound it hard, or it rots back into the history you removed.

## Takeaway

Long conversations rot — attention dilutes, early instructions fade, compaction corrupts, failed trajectories poison. The fresh-context invariant (tick N's context depends only on files on disk) trades a cache-cheap re-priming cost for reproducibility, flat cost/quality over long runs, and self-healing. Its one real recurring cost is *rediscovery* — the agent re-derives the codebase each tick — which a bounded, agent-curated note channel repays without reintroducing rot. The anchor files are the loop's real memory, and designing them — intent separate from state, stable-prefix-first, plus a size-capped note channel for what the loop learns within a run — is where the design effort goes.

## Sources

| # | Source | Supports | Link |
|---|--------|----------|------|
| 1 | Anthropic, *Effective Context Engineering for AI Agents* | context rot mechanisms; filesystem as durable memory; prompt-cache discipline | [anthropic.com/engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 2 | "Ruthless context resets" / RPI production accounts (2026) | fresh-context discipline at scale; research→plan→implement phases on disk | [linearb.io](https://linearb.io/blog/dex-horthy-humanlayer-rpi-methodology-ralph-loop) |
| 3 | Companion curricula, `agents/09`, `claude-code/06` | context & cache engineering in depth | [local](../agents/09-context-and-cache-engineering.md) |
