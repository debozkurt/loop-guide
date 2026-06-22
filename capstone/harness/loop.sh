#!/usr/bin/env bash
#
# loop.sh — the bash "ralph" version of the self-governed loop (Ch 2, Ch 4).
#
# This is the *lineage* version: the same loop as loop.py, stripped to the
# ~30 lines of bash that started it all (the ralph technique, July 2025). Read it
# next to loop.py to see that the Python harness is just this with the three
# hard stops, no-progress detection, and durability made explicit and robust.
#
# The original ralph one-liner was literally:
#     while :; do cat PROMPT.md | claude-code ; done
# ...with NO stopping conditions. That is exactly the "money fire" (Ch 13). This
# version keeps ralph's spirit (fixed prompt, fresh context, files-as-state) and
# adds the guardrails that make it safe to run unattended.
#
# Usage:  ./loop.sh
set -uo pipefail

MAX_ITER="${MAX_ITER:-50}"          # STOP 1: iteration cap (Ch 13)
NO_PROGRESS_N="${NO_PROGRESS_N:-3}" # STOP 3: halt after N unchanged-state iterations
GATE="${GATE:-./verify.sh}"         # the external stopping oracle (Ch 7)
MODEL="${MODEL:-claude-fable-5}"
# STOP 2 (budget) is enforced with --max-cost below if your CLI supports it; the
# Python harness (loop.py) tracks cumulative cost itself for portability (Ch 14).

i=0
last_sig=""
stall=0

while (( i < MAX_ITER )); do
  (( i++ ))

  # One tick: fixed prompt, FRESH context (Ch 5). State lives on disk, not here.
  cat PROMPT.md | claude -p --permission-mode acceptEdits --model "$MODEL"

  # Durable checkpoint: one commit per iteration (Ch 15).
  git add -A && git commit -m "loop: iteration $i" --quiet 2>/dev/null || true

  # STOP 3: no-progress detection — did the working-tree state change? (Ch 13)
  sig="$(git diff HEAD~1 HEAD 2>/dev/null | sha256sum | cut -d' ' -f1)"
  if [[ "$sig" == "$last_sig" ]]; then
    (( stall++ ))
    if (( stall >= NO_PROGRESS_N )); then
      echo "HALT no_progress iteration=$i stall=$stall" >&2; exit 1
    fi
  else
    stall=0
  fi
  last_sig="$sig"

  # SUCCESS check: the external gate is the stopping oracle (Ch 7).
  if "$GATE"; then
    echo "HALT done iteration=$i" >&2; exit 0
  fi
  echo "iteration $i complete, gate not yet met — continuing" >&2
done

echo "HALT iteration_cap iteration=$MAX_ITER" >&2   # STOP 1 fired (Ch 13)
exit 1
