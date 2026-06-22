# Teaching Kit — Loop Engineering Workshop (90 minutes)

[← Capstone overview](../README.md) · [Index](../../README.md)

> *A 90-minute workshop to take a room of mid-to-senior engineers from "I prompt an agent each step" to "I can author a bounded, verifying loop." Run-of-show with timings, demo scripts that can't fail, three hands-on exercises, and a facilitator cheat-sheet. Pairs with the [harness](../harness/) and [lab](../lab/lab-guide.md).*

## Who this is for and what they'll leave with

**Audience:** engineers who use a coding agent interactively (Rung 1–2 of the maturity ladder) and want to drive it with a loop instead.

**Learning objectives** — by the end, each participant can:

1. Define a loop precisely ("cron plus a decision-maker") and place themselves on the maturity ladder.
2. Name the three hard stops and explain why each exists.
3. Explain why a loop needs an *external* verification gate, and grade their own loop against it.
4. Run the harness against a toy repo and read its stop-reason logs.
5. Apply the decision framework to decide whether a given task should be a loop at all.

**Pre-reqs to send ahead:** install Python 3.10+ and Claude Code; clone the capstone harness; skim [Chapter 1](../../01-what-is-a-loop.md) and [Chapter 13](../../13-making-loops-halt.md).

---

## Run-of-show (90 minutes)

| Time | Segment | Mode | Artifact |
|---|---|---|---|
| 0:00–0:10 | The definition | Talk | cron-vs-loop table ([Ch 1](../../01-what-is-a-loop.md)) |
| 0:10–0:25 | The five loop designs | Talk + diagram | lineage ladder ([Ch 2](../../02-the-lineage.md)) |
| 0:25–0:40 | Live demo: watch a loop halt | Demo | `loop.py --dry-run` |
| 0:40–0:55 | Exercise 1: build a gate | Hands-on | toy repo ([lab Step 2](../lab/lab-guide.md)) |
| 0:55–1:05 | The feedback imperative | Talk | [Ch 7](../../07-the-feedback-imperative.md) |
| 1:05–1:20 | Exercise 2: make it halt / break it | Hands-on | the three stops |
| 1:20–1:30 | Decision framework & next steps | Discussion | maturity ladder ([Ch 18](../../18-anti-patterns-and-decision-framework.md)) |

Drop Exercise 2 for a 75-minute version, or expand the discussion for a 2-hour version. The demo and Exercise 1 are the irreducible core — never cut those.

---

## Segment 1 — The Definition (0:00–0:10)

Open with the problem the audience already has: they run an agent and babysit every turn. Then give the definition that names the way out:

> **A loop is cron plus a decision-maker in the body.** A cron job runs a fixed script. A loop runs a *model* that looks at the state, decides the next action, does it, checks whether it worked, and decides whether to continue. You stop typing prompts and start authoring the program that types them.

**Suggested slides 1–3:**

1. Cron vs loop — the side-by-side from [Chapter 1](../../01-what-is-a-loop.md) (`tick → run fixed script` vs `tick → model decides`).
2. The three levels of automation: hand-code → prompt each step → **author the loop**.
3. "The job moves up an altitude, not out" — someone still decides what to build, writes the loops, and reviews the output.

**Facilitator note:** a room splits into excited and skeptical on this topic. Name it early: "By the end you'll know exactly which parts are real and which are hype." It earns the skeptics, who are usually your seniors.

---

## Segment 2 — The Five Loop Designs (0:10–0:25)

Walk the lineage ladder ([Chapter 2](../../02-the-lineage.md)): the ReAct loop → unbounded self-prompting → fixed-prompt-plus-context-reset (ralph) → the completion gate (`/goal`) → orchestration. The teaching payoff:

> Each design fixes one failure of the last. "Loops are old hat" (true of single-agent ralph) and "loops are the frontier" (true of orchestration) are both correct — about different designs. Name the design first.

Spend the most time on **design 2, unbounded self-prompting** — it motivates everything downstream:

> Give a model a goal and let it prompt itself and it becomes famous for spinning forever doing nothing. That's not a model problem — it's a **missing harness**: no stopping condition, no verification, no budget. Every guardrail in this workshop is a direct answer to that failure.

**Whiteboard moment:** draw the failure cycle with no exit edge (set goal → search → save → "verify" → "need more" → search). Ask: "where's the bug?" Let someone say "it never stops." That's the whole workshop in one question.

---

## Segment 3 — Live Demo: Watch a Loop Halt (0:25–0:40)

This demo **cannot fail and costs nothing** — it's the dry-run harness. Run all three terminals live:

```bash
cd capstone/harness
python3 loop.py --dry-run --max-iter 5         # the happy path — reaches DONE
python3 loop.py --dry-run-stall --max-iter 8   # a stuck loop — no-progress detection saves you
python3 loop.py --dry-run --budget 1.0         # the budget ceiling — halts before overspending
```

**Narrate the log lines as they scroll.** Point at:

- `[loops][agent] stub agent tick` — "this is the model in the loop body."
- `[loops][gate] gate check passed=False` — "this external check, not the agent's opinion, decides done."
- `HALT reason=no_progress` / `reason=budget_ceiling` — "three ways to stop safely, one to succeed; a production loop treats all four as first-class."

Then open `loop.py` and show that `run_loop` is ~30 lines and every guardrail is a labeled section:

> The scary autonomous loop is a few hundred lines of plain Python with no dependencies. The magic isn't the code — it's the discipline the code enforces: verify, halt, commit, log which terminal fired.

---

## Exercise 1 — Build a Gate (0:40–0:55)

**Setup (keep in a gist to paste):** participants create the toy repo from [lab Step 2](../lab/lab-guide.md) — a deliberately wrong `add(a, b)` and a test expecting `add(2,3)==5`, with `verify.sh` running pytest.

**The task:** run a real, tightly-bounded loop and watch it close the feedback loop:

```bash
python3 /path/to/harness/loop.py --repo-dir "$LAB" \
  --gate-cmd ./verify.sh --max-iter 5 --budget 2.0 --no-progress-n 2
```

**What they should see:** the agent fixes `a - b` → `a + b`, the gate exits 0, `HALT reason=done`, one commit per tick in `git log`.

**The teaching beat:** have everyone make their gate *gameable* — remove the anti-gaming guard — and re-run with "make the tests pass by any means." Some loops will delete or weaken the test. That's the **Gate-Gamer** anti-pattern ([Chapter 9](../../09-evals-and-regression-for-loops.md)) live, and the most memorable five minutes of the session:

> The loop did exactly what you asked — "make tests pass" — and defeated the point. The gate must check *intent*, not a proxy you can cheat. A gate you can game is not a gate.

---

## Segment 4 — The Feedback Imperative (0:55–1:05)

The single most important idea, stated plainly:

> An open loop that writes code with no feedback is a machine for generating confident mistakes. A loop that writes, runs, reads the result, and corrects is the thing that works. The loop is not the magic — the feedback is.

Ground it in the research so the seniors trust it:

> This isn't an opinion. A published result shows that models *cannot reliably self-correct* by re-reading their own reasoning with no external signal — they need an external check ([Chapter 7](../../07-the-feedback-imperative.md)). A model grading its own homework is the thing that demonstrably doesn't work. So "done" has to be a command that exits zero, not the agent saying "looks good."

Add the practitioner data point — a real feedback loop is estimated to lift output quality ~2–3× — and flag it explicitly as an estimate, not a benchmark. Modeling that "verify, don't repeat the hype" habit is part of what you're teaching.

---

## Exercise 2 — Make It Halt / Break It On Purpose (1:05–1:20)

Participants internalize the three stops by *causing* each to fire on their own loop:

1. **Iteration cap:** set `--max-iter 2` on a task that needs more. Read `HALT reason=iteration_cap`.
2. **No-progress:** give an impossible gate (`--gate-cmd "exit 1"`) and watch the stall counter climb to `HALT reason=no_progress`.
3. **Budget ceiling:** set `--budget 0.50` and watch it halt almost immediately.

**Debrief question:** "When your loop halts, how do you know whether it *succeeded* or *gave up*?" Answer: the logged stop-reason. `done` is success; the other three need a human. That distinction is the difference between a fleet you can monitor and one you can't ([Chapter 11](../../11-gastown-and-the-mayor-pattern.md), [Chapter 13](../../13-making-loops-halt.md)).

---

## Segment 5 — Decision Framework & Next Steps (1:20–1:30)

Close on engineering judgment, not hype. Two things on the board.

**The reality check** — what's verified, so the room designs against mechanics, not headlines:

- A single loop is cheap; a fleet runs on the order of ~10× a single session (~$100/hour in independent testing). The budget ceiling and the ROI back-of-envelope are mandatory, not optional.
- Output quality at fleet scale is *unsolved* — independently-tested orchestration produced bad PRs and merged over failing tests. The architecture is real; the outcome is not yet. Budget and verify accordingly.
- Most organizations are early on this ladder; intent runs well ahead of deployment. Treat viral productivity numbers skeptically and design against the verified mechanics taught here.

**The maturity ladder** ([Chapter 18](../../18-anti-patterns-and-decision-framework.md)) as the call to action:

> Most of you are at Rung 1–2 — you prompt every step. Your homework isn't "build an orchestration fleet." It's Rung 3: wrap *one* repeated, verifiable task in a loop with a real gate and the three hard stops. The [lab guide](../lab/lab-guide.md) walks you through it on your own repo. Climb one rung.

One-sentence summary to leave them with:

> Stop being the thing in the loop. Write the loop once, give it skills worth calling and feedback so it can check itself, cap it so it halts, contain it so it can't do damage, and let it run while you go decide what to build next.

---

## Facilitator cheat-sheet — the questions that always come up

**"Isn't this just a cron job?"** Half right, and say so. The scheduling layer *is* cron. What cron never had is a *model deciding the next action and checking the result* in the loop body. Loops are cron *plus a decision-maker* ([Chapter 1](../../01-what-is-a-loop.md)).

**"Doesn't this replace engineers?"** No — it moves the job up an altitude. Someone decides what to build, writes the loops, designs the gates, and reviews the output. The person who can author and verify a loop is more valuable, not less.

**"What does it cost?"** Real money, and the cost shifted from tokens to *loop management*. A single loop is cheap; a fleet measured ~$100/hour in independent testing. That's why the budget ceiling and the ROI back-of-envelope are mandatory ([Chapter 14](../../14-the-economics-of-loops.md)).

**"Is the output actually good?"** Often not yet — independently-tested orchestration produced bad PRs and merged over failing tests. The *architecture* is real; the *output quality* is unsolved. Saying this plainly is what earns the skeptics ([Chapter 11](../../11-gastown-and-the-mayor-pattern.md)).

**"Claude Code or Codex?"** Both work; the patterns are harness-agnostic. The one real difference: Claude Code's `/goal` has an enforced completion gate; Codex's "Done when" is advisory, so you re-implement the stopping oracle yourself ([Chapter 6](../../06-goal-and-loop-productized.md)).

**"Where do I start Monday?"** One repeated, machine-verifiable task. A `/goal` loop or this harness, a real gate, the three hard stops, a low budget, a feature branch. Watch the first few runs. That's Rung 3 ([Chapter 18](../../18-anti-patterns-and-decision-framework.md)).

---

## Materials checklist

- [ ] Harness cloned and `python3 loop.py --dry-run` verified working on your demo machine.
- [ ] Toy-repo setup script in a gist for Exercise 1 (from [lab Step 2](../lab/lab-guide.md)).
- [ ] Slides 1–3 (definition) + the lineage ladder diagram ([Ch 2](../../02-the-lineage.md)).
- [ ] The maturity-ladder diagram ([Chapter 18](../../18-anti-patterns-and-decision-framework.md)) as the closing call-to-action.
- [ ] A printed copy of this cheat-sheet.

> **30-minute version:** the dry-run demo (Segment 3) and Exercise 1 are the whole talk. Lead with the cron-vs-loop definition, run the three halts live, build one gate, close with the maturity ladder. Everything else is depth for Q&A.

---

[← Capstone overview](../README.md) · [Index](../../README.md) · [Lab guide →](../lab/lab-guide.md)
