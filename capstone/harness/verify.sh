#!/usr/bin/env bash
#
# verify.sh — the VERIFICATION GATE / stopping oracle (Ch 7).
#
# This is the external check that decides whether the loop is DONE. The loop
# treats `exit 0` as "the goal is met, stop" and any non-zero exit as "not done,
# here's the output as feedback, keep going."
#
# THE RULES (why this file matters more than the prompt):
#   1. It must be DETERMINISTIC and EXTERNAL. "Tests pass" beats "the agent thinks
#      it's good" — a model is a poor judge of its own work (Ch 7).
#   2. It must reach the REAL goal, not a proxy. "It compiles" is not "it works."
#      Prefer the failing test that reproduced the bug now passing; the feature
#      actually running; CI actually green (Ch 7).
#   3. It must be HARD TO GAME. A loop under pressure will delete the failing test
#      to make this exit 0. Guard against it (Ch 9) — see the optional check below.
#
# Replace the body with your project's real gate. Keep it fast enough to run every
# iteration (Ch 7: cheap-to-expensive ladder — typecheck + targeted tests inline,
# full e2e on a slower cadence).

set -uo pipefail

echo "[verify] running verification gate..."

# --- Example gate. Swap these for your project's real commands. ---------------
# npm run typecheck   || { echo "[verify] typecheck failed"; exit 1; }
# npm test            || { echo "[verify] tests failed";     exit 1; }
# npm run lint        || { echo "[verify] lint failed";      exit 1; }

# --- Anti-gaming guard (Ch 9): refuse to "pass" if the loop modified the tests.
#     A green suite achieved by editing the tests is not a passing suite.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -qE '(^|/)(tests?|__tests__|spec)/'; then
    echo "[verify] REJECTED: the last commit modified test files — gate cannot be trusted (Ch 9)"
    exit 1
  fi
fi

# Default placeholder gate: succeed only if a sentinel file says the work is done.
# (Real projects delete this and use the commands above.)
if [[ -f .loop-done ]]; then
  echo "[verify] gate PASSED"
  exit 0
fi

echo "[verify] gate not yet satisfied"
exit 1
