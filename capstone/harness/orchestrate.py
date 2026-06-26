#!/usr/bin/env python3
"""
orchestrate.py — the worktree-orchestration variant (Ch 10, Ch 11, Ch 16).

Takes loop.py from ONE loop to MANY: a supervisor that dispatches a list of tasks
to a bounded pool of WORKER LOOPS, each isolated in its own git worktree, and
collects which terminal each worker hit.

This is the supervisor/worker topology from Ch 10 made runnable:
  - each worker is a full self-governed loop (loop.run_loop) — a ralph at the
    bottom (Ch 4), with its own verification gate and three hard stops (Ch 7, 13)
  - each worker gets its OWN git worktree so parallel workers can't collide and
    each worker's blast radius is isolated (Ch 10, Ch 16)
  - a fleet-level budget DECLARES the intended total ceiling (Ch 13, Ch 14); in
    this deterministic dispatcher it is logged but not yet enforced across workers
    (each worker enforces only its own per-worker budget) — enforcing a hard fleet
    cap means a shared, locked spend tally that cancels in-flight workers (exercise)
  - the supervisor records each worker's stop-reason — done vs. a safety halt
    that needs a human (Ch 9, Ch 13)

HONEST SCOPE: the supervisor here is a DETERMINISTIC dispatcher, not an LLM. Gas
Town's "Mayor" is itself an agent making dispatch decisions (Ch 11); that's a
strictly more powerful — and more expensive, higher-blast-radius — design. Start
deterministic; upgrade the supervisor to an agent only once the worker loop is
trustworthy (the maturity ladder, Ch 18). Don't run a fleet of un-verified loops.

    python3 orchestrate.py --dry-run --tasks "fix lint" "add tests" "update docs"
"""
from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import pathlib
import shutil
import tempfile
from typing import Optional

import loop  # the worker loop lives in loop.py — reuse it, don't reinvent it


@dataclasses.dataclass
class FleetConfig:
    tasks: list[str]
    max_workers: int = 3            # concurrency cap — flat beats deep (Ch 12)
    fleet_budget_usd: float = 50.0  # declared total ceiling — logged, not yet enforced across workers (Ch 13, 14)
    per_worker: loop.Config = dataclasses.field(default_factory=loop.Config)
    base_repo: pathlib.Path = pathlib.Path(".")
    dry_run: bool = False


def make_worktree(base_repo: pathlib.Path, task_id: int, dry_run: bool) -> pathlib.Path:
    """Isolation primitive (Ch 10, Ch 16). Real mode: a git worktree on its own
    branch. Dry-run: a throwaway temp dir, so the demo runs with no git setup."""
    if dry_run or not loop.is_git_repo(base_repo):
        path = pathlib.Path(tempfile.mkdtemp(prefix=f"loop-worker-{task_id}-"))
        loop.log("INFO", "supervisor", "created isolated scratch dir (dry-run)",
                 worker=task_id, path=path.name)
        return path
    branch = f"loop/worker-{task_id}"
    path = base_repo / ".worktrees" / f"worker-{task_id}"
    loop.run(["git", "worktree", "add", "-b", branch, str(path), "HEAD"], base_repo)
    loop.log("INFO", "supervisor", "created worktree", worker=task_id, branch=branch)
    return path


def cleanup_worktree(base_repo: pathlib.Path, path: pathlib.Path, dry_run: bool) -> None:
    if dry_run or not loop.is_git_repo(base_repo):
        shutil.rmtree(path, ignore_errors=True)
        return
    loop.run(["git", "worktree", "remove", "--force", str(path)], base_repo)


def run_worker(task_id: int, task: str, fc: FleetConfig) -> tuple[int, str, loop.StopReason]:
    """One worker = one isolated self-governed loop running one task."""
    wt = make_worktree(fc.base_repo, task_id, fc.dry_run)
    try:
        # Thread this worker's task into its loop: run_agent injects it into the
        # prompt and the gate sees it as $LOOP_TASK, so the worker is scoped to its
        # own module (fix only this, test only this) — real fan-out, not 3× the same
        # work on three branches (Ch 12: fan out INDEPENDENT slices).
        cfg = dataclasses.replace(fc.per_worker, repo_dir=wt, task=task, dry_run=fc.dry_run)
        loop.log("INFO", "supervisor", "dispatching task", worker=task_id, task=f'"{task[:40]}"')
        reason = loop.run_loop(cfg)
        return task_id, task, reason
    finally:
        cleanup_worktree(fc.base_repo, wt, fc.dry_run)


def run_fleet(fc: FleetConfig) -> dict[str, int]:
    """The supervisor loop: dispatch tasks to a bounded worker pool, collect
    stop-reasons, report. (Deterministic dispatch — see module docstring.)"""
    loop.log("INFO", "supervisor", "fleet starting",
             tasks=len(fc.tasks), max_workers=fc.max_workers, fleet_budget_usd=fc.fleet_budget_usd)

    results: list[tuple[int, str, loop.StopReason]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=fc.max_workers) as pool:
        futures = {
            pool.submit(run_worker, i, task, fc): i
            for i, task in enumerate(fc.tasks, start=1)
        }
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    # Tally the terminals — the fleet's observability (Ch 11 patrols watch this).
    tally: dict[str, int] = {}
    for task_id, task, reason in sorted(results):
        tally[reason.value] = tally.get(reason.value, 0) + 1
        level = "INFO" if reason is loop.StopReason.DONE else "WARN"
        loop.log(level, "supervisor", "worker finished", worker=task_id, reason=reason.value)

    done = tally.get(loop.StopReason.DONE.value, 0)
    loop.log("INFO", "supervisor", "fleet complete",
             done=done, total=len(fc.tasks), needs_human=len(fc.tasks) - done, tally=tally)
    return tally


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Worktree-orchestration variant (supervisor + worker loops).")
    p.add_argument("--tasks", nargs="+", required=True, help="one task per worker")
    p.add_argument("--max-workers", type=int, default=3, help="concurrency cap (Ch 12)")
    p.add_argument("--fleet-budget", type=float, default=50.0, dest="fleet_budget_usd")
    p.add_argument("--per-worker-budget", type=float, default=10.0, help="budget per worker (Ch 13)")
    p.add_argument("--max-iter", type=int, default=20, help="per-worker iteration cap")
    p.add_argument("--model", help="agent model id for every worker (overrides the Config default)")
    p.add_argument("--subscription", action=argparse.BooleanOptionalAction, default=True,
                   help="bill every worker to your Claude Code subscription instead of the API "
                        "(strips ANTHROPIC_API_KEY from the agent subprocess); --no-subscription "
                        "forces API billing. Default ON (Ch 14).")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    per_worker = loop.Config(
        max_iter=args.max_iter,
        budget_usd=args.per_worker_budget,
        subscription=args.subscription,
        dry_run=args.dry_run,
    )
    if args.model:
        per_worker.model = args.model
    fc = FleetConfig(
        tasks=args.tasks,
        max_workers=args.max_workers,
        fleet_budget_usd=args.fleet_budget_usd,
        per_worker=per_worker,
        dry_run=args.dry_run,
    )
    tally = run_fleet(fc)
    # Non-zero exit if any worker needed a human (didn't reach DONE).
    return 0 if tally.get(loop.StopReason.DONE.value, 0) == len(fc.tasks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
