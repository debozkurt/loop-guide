#!/usr/bin/env python3
"""
loop.py — The Self-Governed Loop (capstone reference harness)

A runnable reference implementation of the patterns taught in the `loops/`
curriculum. It wraps a coding agent (Claude Code's `claude -p`, by default) in an
*outer loop* that:

  - re-invokes the agent with a FRESH context each tick          (Ch 5)
  - runs an external VERIFICATION GATE and feeds failures back   (Ch 7)
  - enforces the THREE HARD STOPS: iteration cap, budget          (Ch 13)
    ceiling, and no-progress detection
  - commits progress every iteration for DURABLE, resumable state (Ch 15)
  - logs WHICH terminal fired (done vs. each halt reason)         (Ch 9, 13)
  - stays inside a bounded BLAST RADIUS (branch-only, capped)     (Ch 16)

It is deliberately dependency-free (Python stdlib only) so it runs anywhere and
reads as teaching material. Run it with `--dry-run` to watch the full control
flow against a stub agent, with no Claude Code install and no spend.

    python3 loop.py --dry-run --max-iter 5            # watch it reach DONE
    python3 loop.py --dry-run-stall --max-iter 5      # watch no-progress HALT
    python3 loop.py --dry-run --budget 1.0            # watch the budget ceiling

See ./README in the capstone for the full mapping to curriculum chapters.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import enum
import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Optional

APP_TAG = "loops"  # root app tag — one grep isolates this harness in any log stream


# --------------------------------------------------------------------------- #
# Logging — one event per line, machine-filterable, with root + component tags.
# Shape: <ISO time> LEVEL [loops][component] message key=value ...
# (Never log payload content — ids, counts, lengths, reasons only.)
# --------------------------------------------------------------------------- #
def log(level: str, component: str, message: str, **fields: object) -> None:
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    kv = " ".join(f"{k}={v}" for k, v in fields.items())
    line = f"{ts} {level:<5} [{APP_TAG}][{component}] {message}"
    if kv:
        line += f" {kv}"
    print(line, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Stop reasons — the four terminals. THREE ways to halt safely, ONE to succeed.
# Recording which one fired is what makes the loop observable (Ch 13).
# --------------------------------------------------------------------------- #
class StopReason(str, enum.Enum):
    DONE = "done"                       # success: completion condition met
    ITERATION_CAP = "iteration_cap"     # safety: hit MAX iterations
    BUDGET_CEILING = "budget_ceiling"   # safety: hit the dollar ceiling
    NO_PROGRESS = "no_progress"         # safety: state stopped advancing


@dataclasses.dataclass
class Config:
    """The loop's contract. Every field maps to a pre-flight checklist line (Ch 18)."""
    repo_dir: pathlib.Path = pathlib.Path(".")
    prompt_file: pathlib.Path = pathlib.Path("PROMPT.md")
    # The agent command. {prompt_file} and {model} are substituted; the prompt
    # (plus any gate feedback) is also piped to stdin. Least-privilege by default:
    # acceptEdits, not --dangerously-skip-permissions (Ch 16).
    agent_cmd: str = (
        "claude -p --output-format stream-json "
        "--permission-mode acceptEdits --model {model}"
    )
    model: str = "claude-fable-5"
    # Billing/auth (Ch 14). When True, run_agent strips ANTHROPIC_API_KEY from the
    # agent subprocess so `claude` uses your Claude Code SUBSCRIPTION login (plan
    # rate-limited) instead of per-token API billing — the API key takes precedence
    # whenever it is present in the env, so removing it is what lets the plan win.
    subscription: bool = False
    gate_cmd: str = "./verify.sh"       # the external stopping oracle (Ch 7) — exit 0 == done
    # Per-run work assignment (Ch 10–12). When a supervisor fans out, each worker
    # carries its OWN slice here. run_agent injects it into the prompt and the gate
    # sees it as $LOOP_TASK — that pairing is what scopes a worker to ONE module
    # (fix only this AND test only this). None for a plain single loop, where the
    # prompt and gate already cover the whole goal.
    task: Optional[str] = None
    # --- the three hard stops (Ch 13) ---
    max_iter: int = 50                  # stop 1: iteration cap
    budget_usd: float = 20.0            # stop 2: budget ceiling
    no_progress_n: int = 3              # stop 3: halt after N unchanged-state iterations
    # --- durability (Ch 15) ---
    commit: bool = True                 # commit progress each iteration
    push: bool = False                  # push to the feature branch (Level-3 durability)
    branch: str = "loop/work"           # branch-only blast radius (Ch 16) — never main
    # --- dry-run knobs ---
    dry_run: bool = False
    dry_run_stall: bool = False         # stub stops making progress, to exercise no-progress halt
    _dry_target: int = 3                # dry-run "completion" after this many real changes
    _dry_cost: float = 0.50             # fake $/iteration in dry-run, to exercise the budget stop


# --------------------------------------------------------------------------- #
# Subprocess + git helpers
# --------------------------------------------------------------------------- #
def run(cmd: list[str] | str, cwd: pathlib.Path, stdin: Optional[str] = None,
        env: Optional[dict] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), shell=isinstance(cmd, str),
        input=stdin, capture_output=True, text=True, env=env,
    )


def is_git_repo(repo: pathlib.Path) -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], repo).returncode == 0


def state_signature(cfg: Config) -> str:
    """A fingerprint of the working-tree state. If it doesn't change across an
    iteration, the loop made NO PROGRESS (Ch 13). Prefer the git diff; fall back
    to hashing the dry-run scratch file so the harness runs in a non-repo dir."""
    if is_git_repo(cfg.repo_dir):
        diff = run(["git", "diff", "HEAD"], cfg.repo_dir).stdout
        return hashlib.sha256(diff.encode()).hexdigest()
    scratch = cfg.repo_dir / ".loop-state"
    data = scratch.read_bytes() if scratch.exists() else b""
    return hashlib.sha256(data).hexdigest()


def commit_progress(cfg: Config, iteration: int) -> None:
    """Durable checkpoint: one commit per iteration so a crash costs at most one
    iteration of work, and a restarted process can resume from git alone (Ch 15)."""
    if not cfg.commit:
        return
    if not is_git_repo(cfg.repo_dir):
        log("WARN", "git", "not a git repo — skipping commit (durability disabled)")
        return
    run(["git", "add", "-A"], cfg.repo_dir)
    if not run(["git", "diff", "--cached", "--quiet"], cfg.repo_dir).returncode:
        return  # nothing staged — no change to commit
    run(["git", "commit", "-m", f"loop: iteration {iteration}"], cfg.repo_dir)
    if cfg.push:
        # Branch-only push — bounded blast radius (Ch 16). Never pushes to main.
        run(["git", "push", "-u", "origin", cfg.branch], cfg.repo_dir)
    log("INFO", "git", "committed iteration", iteration=iteration, pushed=cfg.push)


# --------------------------------------------------------------------------- #
# The agent invocation (one tick of the OUTER loop — Ch 3). Fresh context each
# call; the model is a subroutine we hand a prompt and read a result from.
# --------------------------------------------------------------------------- #
@dataclasses.dataclass
class AgentResult:
    cost_usd: float
    ok: bool


def run_agent(cfg: Config, feedback: Optional[str]) -> AgentResult:
    prompt = cfg.prompt_file.read_text() if cfg.prompt_file.exists() else "Make progress on the task."
    if cfg.task:
        # Fan-out (Ch 10–12): this worker's assigned slice. Making it explicit in the
        # prompt — "do ONLY this" — is what keeps a worker on one module instead of
        # fixing the whole suite. Pairs with the $LOOP_TASK-scoped gate below.
        prompt += f"\n\n## Your assigned task — do ONLY this, leave every other module untouched\n{cfg.task}\n"
    if feedback:
        # Closed loop: last iteration's gate FAILURE becomes this iteration's input (Ch 7).
        prompt += f"\n\n## Verification feedback from the previous attempt\n{feedback}\n"

    if cfg.dry_run or cfg.dry_run_stall:
        return _dry_run_agent(cfg)

    cmd = cfg.agent_cmd.format(prompt_file=cfg.prompt_file, model=cfg.model)
    # Billing (Ch 14): with --subscription, strip ANTHROPIC_API_KEY from the agent's
    # env so `claude` falls back to your subscription login. The key would otherwise
    # take precedence and bill the API per token (apiKeySource=ANTHROPIC_API_KEY).
    agent_env = None
    if cfg.subscription:
        agent_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    proc = run(cmd, cfg.repo_dir, stdin=prompt, env=agent_env)
    cost = _parse_cost(proc.stdout)
    if proc.returncode != 0:
        # The agent exited non-zero — it almost certainly did NO work this tick
        # (bad/unavailable model, auth failure, CLI error). Surface it LOUDLY: a
        # silent failure here masquerades as a no-progress stall, because a broken
        # agent makes no file changes (Ch 13). Payload-safe: lengths/rc only, no
        # content — check the model id and auth, then re-run with --model.
        log("WARN", "agent", "agent exited non-zero — likely did no work this tick (check model/auth)",
            rc=proc.returncode, cost_usd=round(cost, 4),
            stdout_len=len(proc.stdout), stderr_len=len(proc.stderr))
    else:
        log("INFO", "agent", "agent tick complete", rc=proc.returncode, cost_usd=round(cost, 4))
    return AgentResult(cost_usd=cost, ok=proc.returncode == 0)


def _parse_cost(stream_json_stdout: str) -> float:
    """Read the real $ cost from `claude -p --output-format stream-json` output.
    Measuring actual cost (not guessing) is what makes the budget stop and the
    ROI math real (Ch 14)."""
    cost = 0.0
    for line in stream_json_stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "total_cost_usd" in obj:
            cost = float(obj["total_cost_usd"])  # last one wins (cumulative)
    return cost


def _dry_run_agent(cfg: Config) -> AgentResult:
    """A stub agent for `--dry-run`. Writes an incrementing counter to a scratch
    file (a 'change'). In --dry-run-stall mode it stops advancing after 2 ticks,
    so you can watch no-progress detection fire."""
    scratch = cfg.repo_dir / ".loop-state"
    n = int(scratch.read_text()) if scratch.exists() else 0
    if not (cfg.dry_run_stall and n >= 2):
        n += 1
        scratch.write_text(str(n))
    log("INFO", "agent", "stub agent tick (dry-run)", counter=n, stalled=cfg.dry_run_stall)
    return AgentResult(cost_usd=cfg._dry_cost, ok=True)


# --------------------------------------------------------------------------- #
# The verification gate — the EXTERNAL stopping oracle (Ch 7). A model is a poor
# judge of its own work, so 'done' is a command that exits 0, not an opinion.
# --------------------------------------------------------------------------- #
@dataclasses.dataclass
class GateResult:
    passed: bool
    feedback: Optional[str]


def verification_gate(cfg: Config) -> GateResult:
    if cfg.dry_run or cfg.dry_run_stall:
        scratch = cfg.repo_dir / ".loop-state"
        n = int(scratch.read_text()) if scratch.exists() else 0
        passed = n >= cfg._dry_target
        fb = None if passed else f"counter is {n}, needs {cfg._dry_target}"
        log("INFO", "gate", "gate check (dry-run)", passed=passed, counter=n)
        return GateResult(passed=passed, feedback=fb)

    # The worker's task rides to the gate as $LOOP_TASK so a fleet gate can scope
    # itself to one module (e.g. `pytest test_$LOOP_TASK.py`). Unset for a plain
    # loop, where the gate runs the whole suite.
    gate_env = {**os.environ, "LOOP_TASK": cfg.task} if cfg.task else None
    proc = run(cfg.gate_cmd, cfg.repo_dir, env=gate_env)
    passed = proc.returncode == 0
    # On failure, hand the gate's output back as the next prompt's feedback.
    feedback = None if passed else (proc.stdout + proc.stderr)[-2000:]
    log("INFO", "gate", "gate check", passed=passed, rc=proc.returncode)
    return GateResult(passed=passed, feedback=feedback)


# --------------------------------------------------------------------------- #
# The loop. Precedence: cheap safety stops first, then work, then success check.
# --------------------------------------------------------------------------- #
def run_loop(cfg: Config) -> StopReason:
    log("INFO", "loop", "starting loop",
        max_iter=cfg.max_iter, budget_usd=cfg.budget_usd, no_progress_n=cfg.no_progress_n,
        dry_run=(cfg.dry_run or cfg.dry_run_stall))

    spent = 0.0
    stall = 0
    last_sig = state_signature(cfg)
    feedback: Optional[str] = None

    for i in range(1, cfg.max_iter + 1):
        # --- STOP 1: iteration cap is enforced by the loop bound itself. ---
        # --- STOP 2: budget ceiling, checked BEFORE spending more (Ch 13). ---
        if spent >= cfg.budget_usd:
            return _halt(StopReason.BUDGET_CEILING, i, spent=round(spent, 2))

        # --- do the work: one agent tick ---
        result = run_agent(cfg, feedback)
        spent += result.cost_usd

        # --- STOP 3: no-progress detection — did the working-tree state change? ---
        sig = state_signature(cfg)
        if sig == last_sig:
            stall += 1
            log("DEBUG", "loop", "no state change this iteration", iteration=i, stall=stall)
            if stall >= cfg.no_progress_n:
                return _halt(StopReason.NO_PROGRESS, i, stall=stall, spent=round(spent, 2))
        else:
            stall = 0  # progress resets the stall counter
        last_sig = sig

        commit_progress(cfg, i)

        # --- SUCCESS check: the external gate is the stopping oracle (Ch 7). ---
        gate = verification_gate(cfg)
        if gate.passed:
            return _halt(StopReason.DONE, i, spent=round(spent, 2))
        feedback = gate.feedback  # closed loop: failure feeds the next tick

        log("INFO", "loop", "iteration complete, continuing",
            iteration=i, spent_usd=round(spent, 2), stall=stall)

    return _halt(StopReason.ITERATION_CAP, cfg.max_iter, spent=round(spent, 2))


def _halt(reason: StopReason, iteration: int, **fields: object) -> StopReason:
    level = "INFO" if reason is StopReason.DONE else "WARN"
    log(level, "loop", "HALT", reason=reason.value, iteration=iteration, **fields)
    return reason


# --------------------------------------------------------------------------- #
# CLI — config.json provides defaults; flags override (Ch 5: stable anchor +
# small overrides). Every knob is a pre-flight checklist line (Ch 18).
# --------------------------------------------------------------------------- #
def load_config(path: pathlib.Path) -> Config:
    cfg = Config()
    if path.exists():
        data = json.loads(path.read_text())
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, pathlib.Path(v) if isinstance(getattr(cfg, k), pathlib.Path) else v)
    return cfg


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="The Self-Governed Loop (capstone harness).")
    p.add_argument("--config", type=pathlib.Path, default=pathlib.Path("config.json"))
    p.add_argument("--repo-dir", type=pathlib.Path)
    p.add_argument("--max-iter", type=int, help="STOP 1: iteration cap")
    p.add_argument("--budget", type=float, dest="budget_usd", help="STOP 2: dollar ceiling")
    p.add_argument("--no-progress-n", type=int, help="STOP 3: halt after N unchanged iterations")
    p.add_argument("--gate-cmd", help="the external verification gate command")
    p.add_argument("--model", help="agent model id")
    p.add_argument("--push", action="store_true", help="push commits to the feature branch (Ch 15)")
    p.add_argument("--subscription", action="store_true",
                   help="bill the agent to your Claude Code subscription, not the API: "
                        "strips ANTHROPIC_API_KEY from the agent subprocess (Ch 14)")
    p.add_argument("--dry-run", action="store_true", help="stub agent that reaches DONE — no spend")
    p.add_argument("--dry-run-stall", action="store_true", help="stub agent that stalls — exercises no-progress HALT")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    for field in ("repo_dir", "max_iter", "budget_usd", "no_progress_n", "gate_cmd", "model",
                  "push", "subscription", "dry_run", "dry_run_stall"):
        val = getattr(args, field, None)
        if val:
            setattr(cfg, field, val)

    reason = run_loop(cfg)
    # Exit code carries the verdict: 0 == DONE, non-zero == a safety halt that
    # likely needs a human. A supervisor (orchestrate.py) reads this.
    return 0 if reason is StopReason.DONE else 1


if __name__ == "__main__":
    raise SystemExit(main())
