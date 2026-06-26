# Lab — A Self-Governed Loop, End to End

[← Capstone overview](../README.md) · [Index](../../README.md)

> *One guided path that exercises the whole course on a throwaway repo, then points the same harness at your own code, then fans it out across workers. Each step has a checkpoint (what you should see) and a trap (the common failure), and names the concept it demonstrates. Do them in order — each climbs one rung of the maturity ladder ([Chapter 18](../../18-anti-patterns-and-decision-framework.md)).*

## What you'll need

- **Python 3.10+** (the harness is stdlib-only — nothing to install). `pytest` for the worked example (`pip install pytest`).
- For the real runs (Step 2 onward): **Claude Code** installed and authenticated (`claude` on your PATH). Step 1 needs neither.
- A throwaway dir for Steps 1–2 and Step 4, and your own repo for Step 3.

Set a shorthand for the harness path:

```bash
HARNESS=/path/to/capstone/harness   # adjust to where you forked it
```

---

## Step 1 — Watch the control flow (no install, no spend)

**Demonstrates:** the three hard stops + stop-reason observability ([Ch 13](../../13-making-loops-halt.md)).

```bash
python3 "$HARNESS/loop.py" --dry-run --repo-dir "$(mktemp -d)" --max-iter 5         # reaches DONE
python3 "$HARNESS/loop.py" --dry-run-stall --repo-dir "$(mktemp -d)" --max-iter 8   # no-progress HALT
python3 "$HARNESS/loop.py" --dry-run --repo-dir "$(mktemp -d)" --budget 1.0         # budget HALT
```

**Checkpoint** — the last line of each run is `HALT reason=done` (exit 0), `HALT reason=no_progress`, and `HALT reason=budget_ceiling` respectively. Every log line is `<time> LEVEL [loops][component] message key=value` — one event per line, greppable: `grep reason=` reconstructs any run.

**Trap** — re-running in the *same* `--repo-dir` resumes the dry-run scratch state and "finishes" early. That's the harness correctly resuming durable state ([Ch 15](../../15-durability-and-crash-recovery.md)) — pass a fresh `--repo-dir $(mktemp -d)` to start clean.

Now open `loop.py` and find `run_loop` (the precedence of stops), `state_signature` (no-progress), `verification_gate` (the stopping oracle), `commit_progress` (durability). The code is the lesson.

---

## Step 2 — The end-to-end worked example (the whole course, runnable)

**Demonstrates, in one run:** anchor files ([Ch 4–5](../../04-the-ralph-technique.md)) · a skill the loop calls ([Ch 17](../../17-its-not-loops-its-skills.md)) · the verification gate + feedback ([Ch 7](../../07-the-feedback-imperative.md)) · the three stops ([Ch 13](../../13-making-loops-halt.md)) · git-durable commits ([Ch 15](../../15-durability-and-crash-recovery.md)) · the anti-gaming guard ([Ch 9](../../09-evals-and-regression-for-loops.md)).

Build a small repo with a deliberately broken feature, a real test gate, the anchor files, and a skill — everything the course covers, in one place:

```bash
LAB=$(mktemp -d); cd "$LAB"; git init -q

# the broken feature + a test that pins the real goal (the gate, Ch 7)
cat > pricing.py <<'EOF'
def total(items, tax_rate):
    return sum(items)            # BUG: ignores tax
EOF
cat > test_pricing.py <<'EOF'
from pricing import total
def test_total_applies_tax():
    assert total([100, 50], 0.10) == 165.0   # 150 + 10% tax
EOF

# the verification gate = the real test suite (Ch 7: external, deterministic, end-to-end)
cat > verify.sh <<'EOF'
#!/usr/bin/env bash
# anti-gaming guard (Ch 9): reject a "pass" achieved by editing the tests
if git rev-parse HEAD~1 >/dev/null 2>&1 && git diff --name-only HEAD~1 HEAD | grep -qE '(^|/)test_[^/]*\.py$'; then
  echo "REJECTED: last commit modified tests"; exit 1
fi
python3 -m pytest -q
EOF
chmod +x verify.sh

# anchor files (Ch 4–5): fixed prompt + house rules
cat > PROMPT.md <<'EOF'
Fix the bug in pricing.py so the test suite passes. Follow the skill below.
Do ONE thing, run the gate, and stop. Do not edit tests.
EOF
cat > CLAUDE.md <<'EOF'
# House rules
- Build/test: `./verify.sh`
- Never edit files matching `test_*` (Ch 9 anti-gaming)
EOF

# a skill the loop calls (Ch 17): the reusable capability, in the standard format
mkdir -p .claude/skills/fix-bug
cat > .claude/skills/fix-bug/SKILL.md <<'EOF'
---
name: fix-bug
allowed-tools: Bash(python3 *), Bash(git *)
---
# How we fix a failing test here
- Read the failing assertion; it defines the real goal, not your guess.
- Make the minimal change to pricing logic; never weaken or delete the test.
- Run `./verify.sh`; iterate until it exits 0.
EOF

# .gitignore (Ch 15): the loop commits with `git add -A` every tick. Without this it
# would also commit pytest's bytecode (__pycache__/test_*.pyc) — and the gate's
# anti-gaming guard would then match that compiled-test filename and falsely REJECT
# on the 2nd+ tick. Every loop repo needs a .gitignore so `git add -A` stays clean.
cat > .gitignore <<'EOF'
__pycache__/
.pytest_cache/
*.pyc
EOF

git add -A && git commit -qm "broken feature + gate + anchors + skill"
```

Run a real, tightly-bounded loop against it:

```bash
python3 "$HARNESS/loop.py" \
  --repo-dir "$LAB" --gate-cmd ./verify.sh \
  --max-iter 5 --budget 2.0 --no-progress-n 2
```

> **If the agent appears to do nothing** — each tick logs `WARN … agent exited non-zero … rc=1 cost_usd=0.0` and the loop halts on `no_progress` almost immediately — the agent command failed *before* doing any work, almost always because the **model isn't enabled on your account**. The harness defaults to `claude-fable-5`; pass `--model <a model you can run>` (e.g. `--model claude-haiku-4-5-20251001`) and re-run. A broken agent makes no file changes, so without that WARN it would read as a no-progress stall rather than a failure — which is why the harness logs the non-zero exit loudly.

**Checkpoint** — watch the whole course fire in the logs: the agent reads the anchors and the skill, edits `pricing.py`, the **gate** runs (`[loops][gate] gate check`), a failure feeds back as the next tick's input, and on success you get `HALT reason=done`. Then inspect the durable trail:

```bash
git -C "$LAB" log --oneline      # a commit per tick — durability (Ch 15)
git -C "$LAB" show HEAD          # the fix: sum(items) * (1 + tax_rate)
```

**Trap (run it on purpose)** — change `PROMPT.md` to "make the test pass by any means" and re-run. If the loop tries to edit `test_pricing.py`, the gate's anti-gaming guard ([Ch 9](../../09-evals-and-regression-for-loops.md)) rejects the commit (`REJECTED: last commit modified tests`). That's the **Gate-Gamer** anti-pattern caught live — and why a gate you can game is not a gate.

> This single repo *is* the working example of the whole course. Every concept above is the same one you'll apply to your own repo next — only the gate command and the skill change.

---

## Step 3 — Point it at your own repo

**Demonstrates:** the decision framework + pre-flight config ([Ch 18](../../18-anti-patterns-and-decision-framework.md)) and least-privilege blast radius ([Ch 16](../../16-permissions-and-safety.md)).

**Run the decision framework first** ([Ch 18](../../18-anti-patterns-and-decision-framework.md)): pick a task that is machine-verifiable, repeated, decomposable, and containable. Good first tasks: "make the linter clean," "raise coverage on module X," "migrate these N files to the new API." Bad first tasks: fuzzy "done," or anything touching prod, auth, or migrations.

Then fill the pre-flight config — the same shape as Step 2, with *your* gate and a feature branch:

```bash
python3 "$HARNESS/loop.py" \
  --repo-dir /path/to/your/repo \
  --gate-cmd "npm run typecheck && npm test" \   # your REAL end-to-end gate (Ch 7)
  --model claude-fable-5 \
  --max-iter 30 --budget 10.0 --no-progress-n 3 \  # the three stops (Ch 13); start budget LOW (Ch 14)
  --push                                            # Level-3 durability to a feature branch (Ch 15–16)
```

Add the anchor files to your repo as in Step 2: a `PROMPT.md`, your `CLAUDE.md` house rules, and a `fix-*` skill for the task. Keep the gate fast (typecheck + targeted tests inline; full e2e on a slower cadence).

**Checkpoint** — the loop opens a feature branch, commits per tick, and either reaches `done` or halts on a safety terminal you can read in the log. Review the branch as a PR; **never let it merge to main** ([Ch 16](../../16-permissions-and-safety.md)).

**Traps, most common first:** budget set too high on the first run (start $5–10); a gate that isn't end-to-end ("it builds" ≠ "it works"); no `CLAUDE.md` constraints (the loop touches what it shouldn't); running it fully unattended on the first try (watch the first few — earn the right to walk away).

---

## Step 4 — A thin orchestration run (one loop → a small fleet)

**Demonstrates:** the supervisor over isolated worker loops ([Ch 10](../../10-from-one-loop-to-many.md)) and fan-out independence ([Ch 12](../../12-dynamic-workflows-and-fan-out.md)). Only do this once Step 2–3 are trustworthy — a fleet of unverified loops is the Premature-Fleet anti-pattern ([Ch 18](../../18-anti-patterns-and-decision-framework.md)).

Watch it dry first (no spend) — three independent tasks, three isolated workers:

```bash
python3 "$HARNESS/orchestrate.py" --dry-run \
  --tasks "fix module a" "fix module b" "fix module c" \
  --max-workers 3 --per-worker-budget 2.0 --fleet-budget 5.0 --max-iter 6
```

**Checkpoint** — each worker gets its own isolated scratch dir, runs its own self-governed loop concurrently (the logs interleave by `worker=`), and the supervisor reports `fleet complete done=3 total=3 needs_human=0`. Note `--fleet-budget 5.0` declares the intended *total* ceiling and is logged at startup — but in this reference dispatcher it is **not yet enforced** across workers: each worker enforces only its own `--per-worker-budget`, so the true bound is `max-workers × per-worker-budget` (here 3 × $2 = $6). A hard fleet cap needs a shared, locked spend tally that cancels in-flight workers — a deliberate next step ([Ch 13–14](../../13-making-loops-halt.md)). Until then, set per-worker budgets so their sum is the ceiling you can actually afford.

For a **real** thin fleet, build three independent broken modules (each like Step 2's `pricing.py`, in its own file with its own test) in one git repo. Two anchors make the fan-out *partition* the work instead of having every worker redundantly fix everything:

- **The task names the module.** The supervisor passes each worker its own `--tasks` entry; the harness injects it into that worker's prompt (`run_agent`) and exposes it to the gate as `$LOOP_TASK` (`verification_gate`). So `--tasks "pricing" "shipping" "tax"` scopes worker 1 to `pricing`, worker 2 to `shipping`, worker 3 to `tax`.
- **The prompt and the gate are both scoped to it.** The shared `PROMPT.md` says *fix only your assigned module*; the gate runs only that module's test. A whole-suite gate would force every worker to fix all three to go green — defeating the partition.

```bash
# PROMPT.md — explicit single-module scope (this is what keeps a worker on its lane)
cat > PROMPT.md <<'EOF'
You are ONE worker in a fleet. Fix ONLY the module named in your assigned task
below — do not modify any other module, and never edit a test file.
Each *_total ignores its rate; it must return sum(items) * (1 + rate).
Run ./verify.sh until it exits 0, then stop.
EOF

# verify.sh — scope the gate to this worker's module via $LOOP_TASK (fall back to
# the whole suite for a plain single loop, where $LOOP_TASK is unset)
cat > verify.sh <<'EOF'
#!/usr/bin/env bash
if git rev-parse HEAD~1 >/dev/null 2>&1 && git diff --name-only HEAD~1 HEAD | grep -qE '(^|/)test_[^/]*\.py$'; then
  echo "REJECTED: last commit modified tests"; exit 1
fi
if [ -n "${LOOP_TASK:-}" ]; then
  python3 -m pytest -q "test_${LOOP_TASK}.py"   # fleet: only this worker's module
else
  python3 -m pytest -q                          # single loop: the whole suite
fi
EOF
chmod +x verify.sh
```

Add the `CLAUDE.md` and `.gitignore` from Step 2, commit, then drop `--dry-run`:

```bash
python3 "$HARNESS/orchestrate.py" \
  --tasks "pricing" "shipping" "tax" \
  --model claude-fable-5 \
  --max-workers 3 --per-worker-budget 2.0 --fleet-budget 5.0 --max-iter 8
```

Each worker gets its own **git worktree** on its own branch ([Ch 10](../../10-from-one-loop-to-many.md), [Ch 16](../../16-permissions-and-safety.md)) — parallel workers can't collide, and each worker's blast radius is isolated.

**Checkpoint** — `fleet complete done=3 total=3 needs_human=0`, and each branch changed **only its own module**: `git diff --name-only main loop/worker-1` shows `pricing.py` alone, worker-2 shows `shipping.py`, worker-3 shows `tax.py`. That's real fan-out — three independent slices — not 3× the same work. Integrate all three green branches and the full suite passes.

**Trap** — fan out only *independent* tasks ([Ch 12](../../12-dynamic-workflows-and-fan-out.md)). Three workers editing the *same* module produce three conflicting branches and a merge headache, not a 3× speedup. Independence is the precondition for parallelism — and it only holds if the task **and** the gate are scoped per worker, as above; without that, the workers all chase the same whole-suite green and redundantly rewrite everything.

---

## Where to go next

You now have one runnable artifact that demonstrates the whole course, pointed at real code, fanned across workers — Rung 3–4 of the maturity ladder. From here:

- **Make it compound** ([Ch 17](../../17-its-not-loops-its-skills.md)): fold what the loop kept re-deriving back into the `SKILL.md` it calls. Treadmill → flywheel.
- **Add continuous review** ([Ch 8](../../08-continuous-review.md)): a second loop reviewing every commit, feeding findings back. The harness's per-tick commit is the hook point.
- **Build your eval set** ([Ch 9](../../09-evals-and-regression-for-loops.md)): turn your first successful runs into golden tasks, so tuning the prompt later can't silently regress.
- **Run it on infrastructure time** ([Ch 15](../../15-durability-and-crash-recovery.md)): once trustworthy locally, move it to cloud Routines / `/loop` so it runs with your laptop closed.
- **Read the horizon** ([Ch 19](../../19-where-this-goes-next.md)): keep state git-backed and skills in the standard format so the emerging shifts are cheap adoptions, not rewrites.

The [teaching kit](../teaching-kit/facilitator-guide.md) helps you take a team through this same path.

---

[← Capstone overview](../README.md) · [Index](../../README.md) · [Teaching kit →](../teaching-kit/facilitator-guide.md)
