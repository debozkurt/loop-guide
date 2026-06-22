<!--
  PROMPT.md — the FIXED anchor prompt (Ch 4, Ch 5).

  This file is piped to the agent verbatim every iteration. It does NOT change
  between iterations — that is the whole point of ralph-style discipline. The
  loop's *memory* lives on disk (IMPLEMENTATION_PLAN.md, git history, specs/),
  NOT in this prompt and NOT in a growing conversation.

  Tune this deliberately and infrequently. If you find yourself hand-editing it
  every iteration, you've become the thing in the loop again (Ch 1).
-->

# Your task this iteration

You are one iteration of an autonomous coding loop. You have a **fresh context** —
everything you need to know is on disk, not in your memory. Do exactly one unit of
work, verify it, record it, and stop. The loop will invoke you again with a fresh
context for the next unit.

## Orient (read these first — they are your only memory)

1. Read `IMPLEMENTATION_PLAN.md` — what is done, what is next, known issues.
2. Read `specs/` (if present) — the source of truth for *what* to build and what
   "done" looks like. The spec, not your guess, defines the target.
3. Read `AGENTS.md` / `CLAUDE.md` — house rules, build/test commands, hard
   constraints. Honor them exactly.
4. If a `## Verification feedback from the previous attempt` section was appended
   below, the last attempt **failed its gate** — that feedback is your error
   signal. Fix the cause it names before doing anything else.

## Do ONE thing

- Pick the single most important next task from `IMPLEMENTATION_PLAN.md`.
- Do only that. Resist doing "just one more thing" — large changes per iteration
  reintroduce the long-context problems this loop exists to avoid (Ch 5).

## Verify your own work end to end (Ch 7)

- Run the build, the tests, the typechecker, the linter — whatever proves the
  change actually works, not just that it compiles. Reaching the *real* goal, not
  a proxy, is the difference between progress and a confident mistake.
- If your change does not pass, fix it now, in this iteration, while the context
  that produced it is fresh.

## Record progress (Ch 15)

- Update `IMPLEMENTATION_PLAN.md`: mark the task done, note anything the next
  iteration needs, and **prune** resolved notes so the plan file stays small and
  current (durable state rots too if you only append).
- Do not delete, weaken, or skip tests to make the gate pass. That defeats the
  gate's purpose and the loop will catch it (Ch 9).

## Stop

- When your one task is done and verified, stop. The loop handles committing,
  the next iteration, and halting. Your job is one verified unit of work.
