"""The workflow files of the two retrieval phases and of the one re-run (review corrections CI2-2 (a), (d) and CI2-9 of the
code review of 11 Nov 2026, part 4). The files are read as text; nothing is executed."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MAIN_ONLY = "github.ref == 'refs/heads/main'"
OFF_MAIN = "github.ref != 'refs/heads/main'"


def _steps(name):
    """The steps of the one job of a workflow file, in order: ``{name, if, text}`` (comment lines and trailing comments dropped)."""
    text = (WORKFLOWS / name).read_text(encoding="utf-8")
    body = text.split("\n    steps:\n", 1)[1]
    out = []
    for chunk in re.split(r"\n(?=      - )", "\n" + body):
        if not chunk.strip():
            continue
        code = "\n".join(l for l in chunk.splitlines() if not l.strip().startswith("#"))
        m = re.search(r"^      - (?:name|uses): (.*)$", code, re.M)
        cond = re.search(r"^        if: (.*)$", code, re.M)
        out.append(dict(name=m.group(1).strip().strip('"') if m else "", cond=cond.group(1) if cond else "", text=code))
    return out


def test_ci2_9_the_steps_that_hold_secrets_or_commit_run_on_main_only():
    for name in ("retrieve_jobs.yml", "rerun_jobs.yml", "redraw_execution.yml"):
        steps = _steps(name)
        guarded = [s for s in steps if "secrets." in s["text"] or re.search(r"\bgit (push|commit)\b", s["text"])]
        assert guarded, name
        for s in guarded:
            assert MAIN_ONLY in s["cond"], (name, s["name"])
        first = min(i for i, s in enumerate(steps) if s in guarded)
        refusals = [i for i, s in enumerate(steps) if OFF_MAIN in s["cond"] and "exit 1" in s["text"]]
        assert refusals and refusals[0] == 0 and refusals[0] < first, name               # a run on another ref is red, not silently empty
        assert "secrets." not in steps[0]["text"]
    # the re-draw holds no secret at all; the plan step of the re-run holds none and may run anywhere
    assert "secrets." not in (WORKFLOWS / "redraw_execution.yml").read_text(encoding="utf-8")
    rerun = {s["name"].split(":")[0]: s for s in _steps("rerun_jobs.yml")}
    assert "secrets." not in rerun["Step plan"]["text"] and MAIN_ONLY not in rerun["Step plan"]["cond"]
    assert "inputs.step != 'plan'" in _steps("rerun_jobs.yml")[0]["cond"]
    # the dispatch honours only a decision whose commit is an ancestor of origin/main
    dispatch = rerun["Step dispatch"]["text"]
    assert dispatch.index("git fetch origin main") < dispatch.index('--rerun "$IDS_FILE" --yes-submit --decision-on origin/main')
    for s in _steps("rerun_jobs.yml"):
        if "--yes-submit" in s["text"]:
            assert "--decision-on origin/main" in s["text"]


def test_ci2_2_the_retrieval_workflow_draws_no_row_and_the_redraw_commits_only_after_it_succeeded():
    text = (WORKFLOWS / "retrieve_jobs.yml").read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
    steps = _steps("retrieve_jobs.yml")
    assert not any("redraw_execution.py" in s["text"] or "data/predictions" in s["text"] for s in steps)     # no row is drawn or committed here
    assert "redraw_workers" not in code and "execution_rows_commit for phase results" not in code           # and no commit for phase results is printed
    assert '--metadata-only --phase-status-file "$STATUS_FILE"' in code
    commit = next(s for s in steps if "git push" in s["text"])
    assert "always()" in commit["cond"] and 'git add data/jobs/ data/calibrations/ data/runs/\n' in commit["text"]
    assert all(word in commit["text"] for word in ("first phase: complete", "first phase: pending", "no row is drawn and no result can be retrieved"))
    # the re-draw: its own workflow, started by hand, from a first-phase commit that is on main, only when every pool is closed
    redraw = (WORKFLOWS / "redraw_execution.yml").read_text(encoding="utf-8")
    on = redraw.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "workflow_dispatch:" in on and not re.search(r"^\s*(schedule|push|pull_request|workflow_run)\s*:", on, re.M)
    rs = _steps("redraw_execution.yml")
    order = [next(i for i, s in enumerate(rs) if word in s["text"]) for word in
             ('git merge-base --is-ancestor "$FIRST_PHASE_COMMIT" HEAD', 'python -m gradvar.hardware --first-phase-status "$IDS_FILE"',
              'python scripts/redraw_execution.py --ids "$IDS_FILE" --workers "$WORKERS"', "git push")]
    assert order == sorted(order) and len(set(order)) == 4
    for i in order[:3]:
        assert rs[i]["cond"] == ""                                                    # none of them runs after a failure of the step before
    commit = rs[order[3]]
    assert "success()" in commit["cond"] and "always()" not in commit["cond"]
    lines = [l.strip() for l in commit["text"].splitlines()]
    assert lines.index("git push") < next(i for i, l in enumerate(lines) if "execution_rows_commit for phase results" in l) < lines.index("fi")
    assert lines.index("else") < lines.index("git push")                                # the commit is printed only in the branch that committed
    added = re.search(r"for d in (.*); do", commit["text"]).group(1).split()
    assert added == ["data/predictions/execution", "data/predictions/execution_exploratory", "data/calibrations/execution", "data/calibrations/execution_exploratory"]
    assert "git add data/runs" not in commit["text"] and "git add data/jobs" not in commit["text"]


def test_the_inputs_of_the_workflows_reach_the_shell_through_the_environment_only():
    for name in ("retrieve_jobs.yml", "rerun_jobs.yml", "redraw_execution.yml"):
        for s in _steps(name):
            run = s["text"].split("\n        run:", 1)[1] if "\n        run:" in s["text"] else ""
            assert "${{" not in run, (name, s["name"])
