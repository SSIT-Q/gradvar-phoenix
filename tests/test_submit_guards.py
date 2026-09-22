"""Submission guards of ``gradvar.hardware`` added 22 Sep 2026 (handover Section 9): the pre-flight record may be the GitHub
permalink of the committed pre-flight document, pinned to its commit, and a list that already has an ids file is never submitted
whole a second time (run 35694886452 dispatched ``day2_main_grid.json``, submitted on 20 Sep, without ``only_job_tag``)."""
import json
from pathlib import Path

import pytest

import gradvar.hardware as hw

ROOT = Path(__file__).resolve().parents[1]
SHA = "0123456789abcdef0123456789abcdef01234567"
GOOD = f"https://github.com/SSIT-Q/gradvar-phoenix/blob/{SHA}/docs/preflight/06_paper1_day3_dial_2026-09-22.md"
SLACK = "https://ssitcrew.slack.com/archives/C0C29EYR0GZ/p1789964716690299?thread_ts=1789669318.385169&cid=C0C29EYR0GZ"


@pytest.mark.parametrize("record, ok", [
    (GOOD, True),
    (GOOD + "#4-kill-rules", True),
    (SLACK, True),
    ("TBD: pre-flight review permalink", False),
    ("", False),
    (GOOD.replace(SHA, "main"), False),                                        # a branch URL moves with the branch
    (GOOD.replace(SHA, SHA[:7]), False),                                       # a short hash is not a pinned record
    (GOOD.replace("docs/preflight/", "docs/"), False),                         # only a pre-flight document is a record
    (GOOD.replace("SSIT-Q/gradvar-phoenix", "someone/gradvar-phoenix"), False),
    (GOOD.replace("https://", "http://"), False),
    (GOOD.replace("/blob/", "/tree/"), False),
    (GOOD + " and more", False),
])
def test_preflight_record_forms(record, ok):
    assert hw.joblist_submittable({"preflight_review": record}) is ok


class Reached(Exception):
    """Raised by a stub to show that run_joblist went past the guard."""


def _stop(*args, **kwargs):
    raise Reached


def _armed_copy(tmp_path):
    jl = json.loads((ROOT / "data" / "joblists" / "paper1" / "replication_01.json").read_text())
    jl.update(dry_run=False, preflight_review=GOOD)
    path = tmp_path / "replication_01.json"
    path.write_text(json.dumps(jl))
    return path, jl


def _ids_file(runs: Path, name: str) -> Path:
    (runs / "2026-09-22").mkdir(parents=True, exist_ok=True)
    p = runs / "2026-09-22" / f"{name}_job_ids.json"
    p.write_text("{}")
    return p


def test_whole_list_with_an_ids_file_is_refused_before_any_build(tmp_path, monkeypatch):
    path, jl = _armed_copy(tmp_path)
    runs = tmp_path / "runs"
    ids = _ids_file(runs, jl["name"])
    monkeypatch.setattr(hw, "joblist_points", _stop)
    with pytest.raises(SystemExit, match="already submitted") as e:
        hw.run_joblist(str(path), submit=True, run_root=str(runs), log_dir=str(tmp_path / "jobs"))
    assert str(ids) in str(e.value)


def test_first_submission_passes_the_guard(tmp_path, monkeypatch):
    path, _ = _armed_copy(tmp_path)
    monkeypatch.setattr(hw, "joblist_points", _stop)
    with pytest.raises(Reached):
        hw.run_joblist(str(path), submit=True, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"))


def test_resubmission_and_dry_run_are_not_guarded(tmp_path, monkeypatch):
    path, jl = _armed_copy(tmp_path)
    runs = tmp_path / "runs"
    _ids_file(runs, jl["name"])
    monkeypatch.setattr(hw, "resubmission_context", _stop)
    with pytest.raises(Reached):                  # only_job_tag goes on to the resubmission path
        hw.run_joblist(str(path), submit=True, run_root=str(runs), only_tag="L4-c1", log_dir=str(tmp_path / "jobs"))
    monkeypatch.setattr(hw, "joblist_points", _stop)
    with pytest.raises(Reached):                  # a dry run builds as before
        hw.run_joblist(str(path), submit=False, run_root=str(runs), log_dir=str(tmp_path / "jobs"))


def test_resubmit_ids_file_does_not_count_as_a_whole_submission(tmp_path):
    runs = tmp_path / "runs"
    (runs / "2026-09-22").mkdir(parents=True)
    (runs / "2026-09-22" / "paper1_x_resubmit_L2-c5_job_ids.json").write_text("{}")
    assert hw.prior_submissions({"name": "paper1_x"}, "x.json", str(runs)) == []
