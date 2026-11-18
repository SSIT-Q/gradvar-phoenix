"""Gate 2 (e) as of draft Deviation 67 (the row of Section 5.3 (d) of the independent review, option (iii)), behind the
adoption switch of the settings table. Test 8e of draft Deviation 65 as corrected by C65-7, and the 10 Nov 2026 properties
sets: the pause condition of row 67 is not met (no element over a cut on the observable edge or in its L = 2 cone), and the
excursions of Q31 and Q98 are listed as handled per job. Stand-in bundles: the committed job.json of each job (what was sent,
and its times) and the properties sets the service returned for it in the trial of 11 Nov; no result is read."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gradvar.execution_calibration as ec  # noqa: E402
from gradvar.analysis import gates  # noqa: E402
from gradvar.analysis.loader import RunData, read_bundle  # noqa: E402

CAL = ROOT / "data" / "calibrations"
SETS = {"0907": "ibm_phoenix_properties_20261110T101610Z.json.gz", "1135": "ibm_phoenix_properties_2026-11-10T124546Z.json",
        "1337": "ibm_phoenix_properties_2026-11-10T135646Z.json",
        "t1120": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json",
        "t1314": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json",
        "t1634": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json"}
SNAPSHOT = str(CAL / "ibm_phoenix_2026-11-10T101610Z.csv")          # the planning snapshot of the 10 Nov package (the 09:07:11Z values)
POOLS = {"dbpfnr0qtr0c738ebeng": ("0907", ["t1120", "1135"], ["t1314", "1337", "t1634"]),      # replication, main job
         "dbpfnrgqtr0c738ebeog": ("0907", ["t1120"], ["1135", "t1314", "1337", "t1634"]),      # replication, null-control probes
         "dbpfom8ou4as73ctjes0": ("1135", ["t1314"], ["1337", "t1634"]),                       # Block C, main job
         "dbpfon8qtr0c738ebgj0": ("1135", [], ["t1314", "1337", "t1634"])}
EMPTY_RESET = pd.DataFrame(columns=["qubit", "p1", "prep", "reset_kind", "probe_id"])


@pytest.fixture(scope="module")
def S():
    return {k: ec.load_properties_file(CAL / f) for k, f in SETS.items()}


@pytest.fixture(scope="module")
def on(tmp_path_factory):
    """The table as the adopting commit leaves it: every entry ruled on, the switch on."""
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    table["status"] = "in_force"
    table["in_force_from_utc"] = "2026-11-10T00:00:00Z"
    for e in table["settings"].values():
        e["provisional"] = False
        e.setdefault("registered", e["value"])
    p = tmp_path_factory.mktemp("settings") / "in_force.json"
    p.write_text(json.dumps(table), encoding="utf-8")
    return ec.load_settings(p)


def bundle(root: Path, job_id: str, S, change=None, pool=True) -> Path:
    """The committed job.json of a 10 Nov job and its pool files; ``change(sets)`` edits copies of the sets first."""
    d = root / "runs" / "2026-11-10" / job_id
    d.mkdir(parents=True)
    shutil.copy(ROOT / "data" / "runs" / "2026-11-10" / job_id / "job.json", d / "job.json")
    if pool:
        s0, mid, after = POOLS[job_id]
        sets = {k: copy.deepcopy(S[k]) for k in [s0] + mid + after}
        if change:
            change(sets)
        (d / "properties_at_running.json").write_text(json.dumps(dict(job_properties=sets[s0], backend_properties=sets[s0])), encoding="utf-8")
        (d / "properties_between.json").write_text(json.dumps(dict(complete=True, note=None, sets=[dict(properties=sets[k]) for k in mid])), encoding="utf-8")
        (d / "properties_after_finished.json").write_text(json.dumps(dict(sets=[dict(properties=sets[k]) for k in after])), encoding="utf-8")
    return d


def run_of(root: Path, reset: pd.DataFrame = EMPTY_RESET) -> RunData:
    bundles = {p.name: read_bundle(p) for p in sorted((root / "runs").glob("*/*")) if p.is_dir()}
    return RunData(rows=pd.DataFrame(columns=["patch_qubits", "L"]), bundles=bundles, reset_error=reset, csv_paths=[], run_dir=root)


def _entry(props, q, name):
    return next(e for e in props["qubits"][q] if e["name"] == name)


def test_the_switch_while_the_table_is_not_in_force_the_registered_evaluator_runs(S, tmp_path, monkeypatch):
    assert ec.load_settings().in_force is False
    bundle(tmp_path, "dbpfnr0qtr0c738ebeng", S)
    run = run_of(tmp_path)
    calls = []
    monkeypatch.setattr(gates, "_gate2_e_registered", lambda *a: calls.append("registered") or dict(result="registered"))
    monkeypatch.setattr(gates, "_gate2_e_row67", lambda *a: calls.append("row67") or dict(result="row67"))
    assert gates.gate2_e(run, SNAPSHOT)["result"] == "registered" and calls == ["registered"]          # the committed table: v0.18.0 stays what main evaluates


def test_row_67_on_the_10_nov_sets_no_pause_and_the_excursions_of_q31_and_q98_are_listed(S, on, tmp_path):
    """The pause condition of row 67 is not met on 10 Nov: nothing over a cut on the observable edge (75, 85) or in its L = 2 cone,
    on E or on B, for either list. Q31 and Q98 (readout, published 11:20:04Z, measured 11:05:20Z) are over the cut elsewhere on
    the placed rung and are handed to the per-job rule of Deviation 65; the clause as Deviations 49 and 52 write it was met."""
    for jid in ("dbpfnr0qtr0c738ebeng", "dbpfnrgqtr0c738ebeog"):
        bundle(tmp_path / "replication", jid, S)
    v = gates.gate2_e(run_of(tmp_path / "replication"), SNAPSHOT, None, settings=on)
    assert v["result"] == "pass" and v["pausing"] == [] and v["deviation"] == "67 (draft)" and v["settings"]["in_force"] is True
    assert sorted((x["qubit"], x["reasons"], x["zone"]) for x in v["handled_per_job"]) == [(31, ["readout"], "outside_zone"), (98, ["readout"], "outside_zone")]
    main = v["jobs"]["dbpfnr0qtr0c738ebeng"]
    assert main["pool_case"] == "service" and main["pool_updates"] == ["2026-11-10T09:07:11Z", "2026-11-10T11:20:04Z", "2026-11-10T13:37:31Z"]
    assert main["rungs"] == [dict(n=82, edge="75_85", depths=[8])] and v["jobs"]["dbpfnrgqtr0c738ebeog"]["rungs"] == []      # the L = 0 probes place no rung
    c49 = main["clause_49"][0]
    assert [x["qubit"] for x in c49["above_cut"]] == [31, 98] and c49["met"] is True and v["logged"]["clause_49_met_jobs"] == ["dbpfnr0qtr0c738ebeng"]
    assert v["bracket_zone"] == [] and v["bracket_decides"] is False and "handled per job by Deviation 65 (no pause): Q31 (readout), Q98 (readout)" in v["note"]
    for jid in ("dbpfom8ou4as73ctjes0", "dbpfon8qtr0c738ebgj0"):
        bundle(tmp_path / "blockc", jid, S)
    v = gates.gate2_e(run_of(tmp_path / "blockc"), SNAPSHOT, None, settings=on)
    assert v["result"] == "pass" and v["pausing"] == []
    assert sorted({(x["qubit"], x["reasons"][0]) for x in v["handled_per_job"]}) == [(25, "init"), (31, "readout"), (98, "readout"), (100, "init")]
    assert all(x["zone"] == "outside_zone" for x in v["handled_per_job"])


def test_8e_row_67_pauses_on_an_element_of_the_zone_and_only_there(S, on, tmp_path):
    jid = "dbpfnr0qtr0c738ebeng"
    rung = gates._job_rungs(json.loads((ROOT / "data" / "runs" / "2026-11-10" / jid / "job.json").read_text(encoding="utf-8")))[0]
    from gradvar.circuits import light_cone
    patch, edge = ec.placement_patch(rung)
    c2 = sorted(set(light_cone(patch, 2, edge)) - set(edge))
    inside = next((a, b) for a, b in patch.edges() if a in c2 and b in c2)
    half = next((a, b) for a, b in patch.edges() if (a in c2) != (b in c2) and a not in edge and b not in edge)

    def readout(q, value):                                         # in every set of the pool, so that E carries it whatever the dates
        return lambda sets: [_entry(s, q, "readout_error").update(value=value) for s in sets.values()]

    def cz(pair, value):
        def change(sets):
            for s in sets.values():
                for g2 in s["gates"]:                              # both directions of the coupler, as the calibration lists them
                    if g2["gate"] == "cz" and sorted(g2["qubits"]) == sorted(pair):
                        next(e for e in g2["parameters"] if e["name"] == "gate_error").update(value=value)
        return change
    cases = [("edge", readout(75, 4e-2), "fail", ("qubit", 75), "observable_edge"),
             ("cone2", readout(c2[0], 4e-2), "fail", ("qubit", c2[0]), "l2_cone"),
             ("coupler_in", cz(inside, 1e-2), "fail", ("coupler",) + tuple(sorted(inside)), "l2_cone"),
             ("coupler_half", cz(half, 1e-2), "pass", None, None)]                       # one qubit in the zone: both must be (the table, row 67 (i))
    for name, change, want, ident, zone in cases:
        bundle(tmp_path / name, jid, S, change=change)
        v = gates.gate2_e(run_of(tmp_path / name), SNAPSHOT, None, settings=on)
        assert v["result"] == want, (name, v["note"])
        if ident:
            assert [(ec._identity(x), x["zone"]) for x in v["pausing"]] == [(ident, zone)]
        else:
            assert v["pausing"] == [] and ("coupler",) + tuple(sorted(half)) in {ec._identity(x) for x in v["handled_per_job"]}
    # a readout value published after the job started running is not on E: it does not pause (it is in the pool, dated after running)
    def late(sets):
        _entry(sets["t1120"], 75, "readout_error").update(value=4e-2, date="2026-11-10 11:15:00+00:00")
        _entry(sets["1135"], 75, "readout_error").update(value=4e-2, date="2026-11-10 11:15:00+00:00")
        _entry(sets["t1314"], 75, "readout_error").update(value=4e-2, date="2026-11-10 11:15:00+00:00")
    bundle(tmp_path / "late", jid, S, change=late)
    v = gates.gate2_e(run_of(tmp_path / "late"), SNAPSHOT, None, settings=on)
    assert v["result"] == "pass"
    # CI-6 (cases 56, 57 of the code review): the element is over the cut on the update published inside the job's window and normal
    # again at the closing update. It is not on E and not on B; the verdict names it all the same, with the stamp of that update
    assert [(x["qubit"], x["zone"], x["also_on_E"], x["stamp"], x["is_bracket"], x["restamps"]) for x in v["bracket_zone"]] == \
        [(75, "observable_edge", False, "2026-11-10T11:20:04Z", False, ["2026-11-10T11:35:39Z", "2026-11-10T13:14:38Z"])]
    assert "Q75 (readout) [observable_edge, job dbpfnr0qtr0c738ebeng] on 2026-11-10T11:20:04Z in the zone and not on E" in v["note"]


def test_8e_the_bracket_is_reported_and_an_in_force_table_cannot_make_it_decide(S, on, tmp_path):
    jid = "dbpfnr0qtr0c738ebeng"

    def on_b(sets):                                               # Q75 over the readout cut in the first update after finished only
        for k in ("1337", "t1634"):
            _entry(sets[k], 75, "readout_error").update(value=4e-2)
    bundle(tmp_path / "b", jid, S, change=on_b)
    run = run_of(tmp_path / "b")
    v = gates.gate2_e(run, SNAPSHOT, None, settings=on)
    assert v["result"] == "pass" and [(x["qubit"], x["zone"], x["also_on_E"]) for x in v["bracket_zone"]] == [(75, "observable_edge", False)]
    assert [(x["stamp"], x["is_bracket"], x["restamps"]) for x in v["bracket_zone"]] == [("2026-11-10T13:37:31Z", True, ["2026-11-10T16:34:05Z"])]   # case 58: on the closing update only
    assert "Q75 (readout) [observable_edge, job dbpfnr0qtr0c738ebeng] on 2026-11-10T13:37:31Z in the zone and not on E" in v["note"]
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    table["status"] = "in_force"
    table["in_force_from_utc"] = "2026-11-10T00:00:00Z"
    table["settings"]["bracket_decides_gate2e"]["value"] = True
    for e in table["settings"].values():
        e["provisional"] = False
        e.setdefault("registered", e["value"])
    (tmp_path / "t.json").write_text(json.dumps(table), encoding="utf-8")
    # CI-1: the registered value is false (review 8.5 item 5: E decides, B is reported), so this table does not load in force
    with pytest.raises(ec.SettingsError, match="bracket_decides_gate2e = True"):
        ec.load_settings(tmp_path / "t.json")


def test_8e_the_reset_error_unfolded_at_or_above_the_kill_line_pauses_and_the_ratios_are_only_logged(S, on, tmp_path):
    bundle(tmp_path, "dbpfnr0qtr0c738ebeng", S)

    def reset(p1_by_qubit, refs=True):
        rows = []
        for q, p1 in p1_by_qubit.items():
            rows.append(dict(qubit=q, p1=p1, prep="1", reset_kind="reset", probe_id="reset_error_prep1"))
            if refs:
                rows += [dict(qubit=q, p1=0.004, prep="0", reset_kind="none", probe_id="readout_ref_prep0"),
                         dict(qubit=q, p1=0.984, prep="1", reset_kind="none", probe_id="readout_ref_prep1")]
        return pd.DataFrame(rows)
    low = gates.gate2_e(run_of(tmp_path, reset({10: 0.0064, 11: 0.0089})), SNAPSHOT, {10: 0.002, 11: 0.008}, settings=on)
    assert low["result"] == "pass" and low["reset_error"][10] == pytest.approx((0.0064 - 0.004) / 0.98) and low["reset_error_at_or_above"] == []
    # raw P(1) of qubit 10 is 3.2 times its reference: logged, no pause (row 67 (ii))
    assert [d["qubit"] for d in low["logged"]["reset_drift_above"]] == [10] and "above 1.5x" in low["note"]
    at = gates.gate2_e(run_of(tmp_path, reset({10: 0.004 + 0.98 * 2e-2, 11: 0.006})), SNAPSHOT, None, settings=on)       # unfolded value exactly on the line
    assert at["result"] == "fail" and at["reset_error_at_or_above"] == [10] and at["reset_error"][10] == pytest.approx(2e-2)
    # raw P(1) above 2e-2 whose unfolded value is below it does not pause: the line is read on the unfolded value
    below = gates.gate2_e(run_of(tmp_path, reset({10: 0.0225})), SNAPSHOT, None, settings=on)
    assert below["reset_error_raw"][10] > gates.RESET_ERROR_KILL and below["reset_error"][10] < gates.RESET_ERROR_KILL and below["result"] == "pass"
    # probes that cannot be unfolded: not evaluable, never passed
    v = gates.gate2_e(run_of(tmp_path, reset({10: 0.004}, refs=False)), SNAPSHOT, None, settings=on)
    assert v["result"] == "not-evaluable" and v["reset_not_unfolded"] == [10] and "cannot be unfolded" in v["note"]


def test_8e_a_job_without_an_execution_time_calibration_makes_the_gate_not_evaluable_and_legacy_bundles_use_the_snapshots(S, on, tmp_path):
    # a bundle written before the two-phase retrieval has no pool files: E is built from the committed snapshots, and the verdict says so
    bundle(tmp_path / "legacy", "dbpfnr0qtr0c738ebeng", S, pool=False)
    v = gates.gate2_e(run_of(tmp_path / "legacy"), SNAPSHOT, None, settings=on)
    assert v["result"] == "pass" and v["jobs"]["dbpfnr0qtr0c738ebeng"]["pool_case"] == "committed_snapshots" and "from the committed snapshots" in v["note"]
    assert sorted(x["qubit"] for x in v["handled_per_job"]) == [31, 98]
    # no pool and no committed set after the job: not evaluable; with a pause established by another job the gate still fails
    d = bundle(tmp_path / "none", "dbpfnr0qtr0c738ebeng", S, pool=False)
    job = json.loads((d / "job.json").read_text(encoding="utf-8"))
    job["metrics"]["timestamps"].update(running="2031-01-01T00:00:00Z", finished="2031-01-01T00:10:00Z")
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    v = gates.gate2_e(run_of(tmp_path / "none"), SNAPSHOT, None, settings=on)
    assert v["result"] == "not-evaluable" and list(v["jobs_without_execution_calibration"]) == ["dbpfnr0qtr0c738ebeng"]
    bundle(tmp_path / "none", "dbpfom8ou4as73ctjes0", S, change=lambda sets: [_entry(s, 85, "readout_error").update(value=5e-2) for s in sets.values()])
    assert gates.gate2_e(run_of(tmp_path / "none"), SNAPSHOT, None, settings=on)["result"] == "fail"


# ------------------------------------------------------------------------------------------------ correction CI-12 (code review part 2)

ROW67_PARTS_I_II_SHA256 = "b11074ce37db7e8b2d9c2b76924280cb759d2d904a74a0e37228d18d77056091"      # of parts (i) and (ii) of the row in the draft, branch dev67-gate2e-scope at 0e6e4b6


def test_ci12_the_text_of_the_evaluator_is_the_row(S, on, tmp_path):
    """``ROW67_TEXT`` is parts (i) and (ii) of row 67, word for word (the hash is that of the text in the draft); once the row is
    in the pre-registration the text must be found there."""
    import hashlib
    assert hashlib.sha256(gates.ROW67_TEXT.encode("utf-8")).hexdigest() == ROW67_PARTS_I_II_SHA256
    assert gates.ROW67_TEXT.startswith("(i) What pauses. From this Deviation on, Gate 2 (e) pauses the campaign when, on the execution-time calibration E(J)")
    assert gates.ROW67_TEXT.endswith("are computed and logged per qubit for every job and no longer pause.") and len(gates.ROW67_TEXT.split()) == 174
    assert "(a coupler counts when both its qubits are in it)" in gates.ROW67_TEXT and "(iii)" not in gates.ROW67_TEXT
    prereg = (ROOT / "docs" / "artifacts" / "paper1_preregistration.md").read_text(encoding="utf-8")
    if "| 67. Gate 2 (e) after Deviation 65" in prereg:                # after adoption: the registered row holds the evaluator's text
        assert gates.ROW67_TEXT in prereg
    bundle(tmp_path, "dbpfnr0qtr0c738ebeng", S)
    v = gates.gate2_e(run_of(tmp_path), SNAPSHOT, None, settings=on)
    assert v["text"] == gates.ROW67_TEXT and v["id"] == "gate2_e"


def test_ci12_the_two_ratios_are_logged_per_qubit_for_every_job(S, on, tmp_path):
    """Row 67 (ii): "computed and logged per qubit for every job". The readout ratio (E over the planning snapshot) of every cone
    qubit of the main job and of every SPAM-only qubit of the probes job (Deviation 52), not only of those above 1.5x; the reset
    ratio of every probed qubit, with or without a reference value."""
    for jid in ("dbpfnr0qtr0c738ebeng", "dbpfnrgqtr0c738ebeog"):
        bundle(tmp_path, jid, S)
    reset = pd.DataFrame([dict(qubit=q, p1=p1, prep=prep, reset_kind=kind, probe_id=pid) for q in (10, 11, 75)
                          for p1, prep, kind, pid in ((0.0064, "1", "reset", "reset_error_prep1"), (0.004, "0", "none", "readout_ref_prep0"), (0.984, "1", "none", "readout_ref_prep1"))])
    v = gates.gate2_e(run_of(tmp_path, reset), SNAPSHOT, {10: 0.002, 75: 0.0064}, settings=on)
    main, probes = v["jobs"]["dbpfnr0qtr0c738ebeng"], v["jobs"]["dbpfnrgqtr0c738ebeog"]
    cone = main["clause_49"][0]["n_cone_qubits"]
    assert {x["role"] for x in main["readout_ratios"]} == {"cone"} and len(main["readout_ratios"]) == cone > 60
    assert sum(1 for x in main["readout_ratios"] if x["above"]) >= 2 and all(x["ratio"] == pytest.approx(x["readout"] / x["snapshot"]) for x in main["readout_ratios"])
    by = {x["qubit"]: x for x in main["readout_ratios"]}
    assert by[31]["above"] and by[98]["above"] and by[31]["readout"] > 3e-2                                # the two qubits of 10 Nov, and every other cone qubit beside them
    assert probes["rungs"] == [] and {x["role"] for x in probes["readout_ratios"]} == {"spam_only"} and len(probes["readout_ratios"]) == 82
    assert v["logged"]["readout_ratios"].keys() == {"dbpfnr0qtr0c738ebeng", "dbpfnrgqtr0c738ebeog"} and "82 SPAM-only entries" in v["note"]
    rr = {x["qubit"]: x for x in v["logged"]["reset_ratios"]}
    assert sorted(rr) == [10, 11, 75] and rr[10]["ratio"] == pytest.approx(3.2) and rr[10]["above"] is True and rr[75]["ratio"] == pytest.approx(1.0) and rr[75]["above"] is False
    assert rr[11]["reference"] is None and rr[11]["ratio"] is None and rr[11]["unfolded"] == pytest.approx((0.0064 - 0.004) / 0.98)      # no reference: logged all the same
    # per job: the probed qubits among its own cone and SPAM-only qubits (10 and 11 are not placed on this rung)
    assert [x["qubit"] for x in probes["reset_ratios"]] == [x["qubit"] for x in main["reset_ratios"]] == [75] and v["result"] == "pass"


def test_ci12_a_run_with_dial_points_and_no_reset_probe_is_not_evaluable(S, on, tmp_path):
    """The reset-error half of the pause clause cannot pass silently: dial points without a reset probe make the gate not evaluable."""
    d = bundle(tmp_path, "dbpfnr0qtr0c738ebeng", S)
    job = json.loads((d / "job.json").read_text(encoding="utf-8"))
    first = job["points"][0]
    job["points"].append(dict(kind="reset_dial", reset_kind="reset", p=0.25, n=first["n"], L=8, k_1based=8, qubits=first["patch_qubits"], edge=first["edge"],
                              patch=first["patch"], origin=first["origin"], holes=first["holes"], broken_edges=first["broken_edges"]))
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    v = gates.gate2_e(run_of(tmp_path), SNAPSHOT, None, settings=on)
    assert v["result"] == "not-evaluable" and v["dial_points_without_reset_probe"] is True and "dial points and no reset probe" in v["note"]
    probes = pd.DataFrame([dict(qubit=10, p1=0.0064, prep="1", reset_kind="reset", probe_id="reset_error_prep1"),
                           dict(qubit=10, p1=0.004, prep="0", reset_kind="none", probe_id="readout_ref_prep0"), dict(qubit=10, p1=0.984, prep="1", reset_kind="none", probe_id="readout_ref_prep1")])
    v = gates.gate2_e(run_of(tmp_path, probes), SNAPSHOT, None, settings=on)
    assert v["result"] == "pass" and v["dial_points_without_reset_probe"] is False
    # a reference at p = 0 is not a dial point: the run of 10 Nov (no dial point) passes without a reset probe, as before
    job["points"][-1]["p"] = 0.0
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    assert gates.gate2_e(run_of(tmp_path), SNAPSHOT, None, settings=on)["result"] == "pass"
    # a pause that is established stays a pause
    job["points"][-1]["p"] = 0.25
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    shutil.rmtree(tmp_path / "runs")
    bundle(tmp_path, "dbpfnr0qtr0c738ebeng", S, change=lambda sets: [_entry(s, 75, "readout_error").update(value=4e-2) for s in sets.values()])
    d2 = tmp_path / "runs" / "2026-11-10" / "dbpfnr0qtr0c738ebeng"
    (d2 / "job.json").write_text(json.dumps(job), encoding="utf-8")
    assert gates.gate2_e(run_of(tmp_path), SNAPSHOT, None, settings=on)["result"] == "fail"


def test_the_single_qubit_transient_rule_of_deviation_49_and_the_cut_itself():
    snap = {q: 0.010 for q in range(6)}
    cut = 3e-2
    one = gates.clause_49({0: 0.016, 1: 0.012, 2: 0.010, 5: 0.5}, snap, [0, 1, 2, 3], cut)        # qubit 5 is not a cone qubit; qubit 3 has no value
    assert one["single_qubit_transient"] is True and one["met"] is False and [r["qubit"] for r in one["above_ratio"]] == [0] and one["n_cone_qubits"] == 3
    two = gates.clause_49({0: 0.016, 1: 0.0151, 2: 0.010}, snap, [0, 1, 2], cut)
    assert two["met"] is True and two["single_qubit_transient"] is False and len(two["above_ratio"]) == 2
    edge = gates.clause_49({0: 0.015, 1: 0.010}, snap, [0, 1], cut)                                # exactly 1.5x is not above
    assert edge["met"] is False and edge["above_ratio"] == [] and edge["ratio_max"] == pytest.approx(1.5)
    over = gates.clause_49({0: 0.031, 1: 0.010}, snap, [0, 1], cut)                                # the cut itself: one qubit above it pauses, whatever its ratio
    assert over["met"] is True and [x["qubit"] for x in over["above_cut"]] == [0] and over["above_ratio"] == [] and over["single_qubit_transient"] is False
    at_cut = gates.clause_49({0: 0.030, 1: 0.010}, {0: 0.029, 1: 0.010}, [0, 1], cut)             # at the cut, not above it
    assert at_cut["met"] is False and at_cut["above_cut"] == []
