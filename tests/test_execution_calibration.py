"""``gradvar.execution_calibration`` (draft Deviation 65, PROVISIONAL): the tests a to d, f (pool part) and h of the draft's
Section 8 item 8, on the committed properties files of 10 Nov and 20 / 21 Sep 2026 and the committed placements. No hardware,
no network, no measured value: only calibration files, placements and prediction rows are read."""
import copy
import json
import math
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import gradvar.execution_calibration as ec  # noqa: E402

CAL = ROOT / "data" / "calibrations"
FILES = {"0732": "ibm_phoenix_properties_20261110T082134Z.json.gz", "0907": "ibm_phoenix_properties_20261110T101610Z.json.gz",
         "1135": "ibm_phoenix_properties_2026-11-10T124546Z.json", "1337": "ibm_phoenix_properties_2026-11-10T135646Z.json",
         "sep21_0205": "ibm_phoenix_properties_2026-09-21T022722Z.json", "sep21_0224": "ibm_phoenix_properties_20260921T030827Z.json.gz",
         "sep21_0305": "ibm_phoenix_properties_2026-09-21T033603Z.json", "sep21_0127": "ibm_phoenix_properties_2026-09-21T014956Z.json",
         # the three stamps of 10 Nov that the snapshot workflow never committed, as the properties-history trial returned them
         # (run 42958459321, branch trial-properties-history-run-42958459321); the trial's other three sets equal committed files
         "t1120": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json",
         "t1314": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json",
         "t1634": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json"}
# metrics.timestamps of the committed job.json files (running, finished)
MAIN = ("dbpfnr0qtr0c738ebeng", "2026-11-10T11:12:05.243865Z", "2026-11-10T12:35:07.784468Z")      # replication, main job
PROBES = ("dbpfnrgqtr0c738ebeog", "2026-11-10T11:12:33.691043Z", "2026-11-10T11:21:02.733793Z")    # replication, probes
BLOCKC = ("dbpfom8ou4as73ctjes0", "2026-11-10T12:54:18.417644Z", "2026-11-10T13:31:41.789031Z")    # Block C, main job
DAY2 = ("dao2pqv8gn2s739nabkg", "2026-09-21T00:05:35Z", "2026-09-21T00:12:25Z")
REFERENCE_RATIO = 1.0105            # draft, Section 8 item 8 d: n100 L = 8 unital k = 1, truncated, 11:35:39Z over 09:07:11Z


@pytest.fixture(scope="module")
def S():
    return {k: ec.load_properties_file(CAL / f) for k, f in FILES.items()}


@pytest.fixture(scope="module")
def st():
    return ec.load_settings()


def _pool(S, job, s0, mid, after, **kw):
    return ec.build_pool(job[0], job[1], job[2], S[s0], S[s0], [S[m] for m in mid], S[after] if after else None, kw.pop("walk_complete", True), **kw)


def _entries(props):
    return {ident: e for ident, cls, e in ec._iter_entries(props)}


def _settings_with(tmp_path, in_force=False, **changes):
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    for k, v in changes.items():
        table["settings"][k]["value"] = v
    if in_force:                                                 # what the adopting commit does: every entry ruled on, the switch on
        table["status"] = "in_force"
        for e in table["settings"].values():
            e["provisional"] = False
    p = tmp_path / ("settings_in_force.json" if in_force else "settings.json")
    p.write_text(json.dumps(table), encoding="utf-8")
    return ec.load_settings(p)


def _rung(joblist, name="n100"):
    return json.loads((ROOT / "data" / "joblists" / "paper1" / joblist).read_text(encoding="utf-8"))["placement"]["rungs"][name]


# ---------------------------------------------------------------------------------------------------------------------------
# the settings table
# ---------------------------------------------------------------------------------------------------------------------------

def test_the_table_is_not_in_force_and_holds_the_reviews_choices(st, tmp_path):
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert table["status"] == "not_in_force" and st.in_force is False and st.provisional is True and "NOT IN FORCE" in table["status_note"]
    assert st.values == {"primary_calibration": "per_value_at_or_before_running", "coupler_zone_rule": "both_qubits", "coupler_cone_rule": "either_qubit",
                         "zone_for_points_shallower_than_zone": "zone_applies", "decision_line_abs_ln_ratio": 0.10,
                         "when_execution_calibration_cannot_be_built_from_the_service": "committed_snapshots_else_not_evaluable",
                         "split_point_rule": "execution_weighted_mean", "value_age_bound_hours": None, "bracket_decides_gate2e": False, "bracket_zone_flag": True,
                         "rerun_rule": "once_when_not_evaluable_on_calibration_grounds", "dispatch_window": "package_update_or_next_same_utc_day"}
    # the two readings found in implementation are the only entries no review has ruled on
    assert st.provisional_entries == ("coupler_cone_rule", "zone_for_points_shallower_than_zone")
    assert all("review" in e["basis"] for k, e in table["settings"].items() if k not in st.provisional_entries)
    rec = st.record()
    assert rec["provisional"] is True and rec["in_force"] is False and rec["settings_status"] == "not_in_force" and len(rec["settings_sha256"]) == 64
    assert rec["settings_file"] == "data/settings/execution_calibration_settings.json" and rec["provisional_entries"] == list(st.provisional_entries)
    # the switch cannot be turned on over an entry nobody ruled on
    table["status"] = "in_force"
    (tmp_path / "t.json").write_text(json.dumps(table), encoding="utf-8")
    with pytest.raises(ec.SettingsError, match="provisional"):
        ec.load_settings(tmp_path / "t.json")
    on = _settings_with(tmp_path, in_force=True)
    assert on.in_force is True and on.provisional is False and on.provisional_entries == () and on.values == st.values


def test_a_value_outside_the_table_is_refused_and_no_function_takes_a_choice_as_an_argument(tmp_path):
    import inspect
    with pytest.raises(ec.SettingsError):
        _settings_with(tmp_path, coupler_zone_rule="any")
    with pytest.raises(ec.SettingsError):
        _settings_with(tmp_path, decision_line_abs_ln_ratio=-0.1)
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    del table["settings"]["split_point_rule"]
    (tmp_path / "t.json").write_text(json.dumps(table), encoding="utf-8")
    with pytest.raises(ec.SettingsError):
        ec.load_settings(tmp_path / "t.json")
    for fn in (ec.execution_calibration, ec.bracket_calibration, ec.zone, ec.classify, ec.classify_without_execution_calibration, ec.combine_split_point):
        params = set(inspect.signature(fn).parameters)
        assert "settings" in params and not params & {"rule", "line", "threshold", "primary", "fallback", "coupler_rule", "bracket_flag"}


# ---------------------------------------------------------------------------------------------------------------------------
# a. E and B on the committed 10 Nov sets
# ---------------------------------------------------------------------------------------------------------------------------

def test_a_execution_calibration_of_the_replication_job_takes_each_value_by_its_date(S, st):
    pool = _pool(S, MAIN, "0907", ["1135"], "1337")
    assert pool.status == "complete" and pool.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z", "2026-11-10T13:37:31Z"]
    E = ec.execution_calibration(pool, st)
    e, s0907, s1135, s1337 = (_entries(x) for x in (E["properties"], S["0907"], S["1135"], S["1337"]))
    t_r = ec.parse_utc(MAIN[1])
    # the readout measured at 11:05:20Z, seven minutes before running, although it was first published at 11:35:39Z
    readout = [v for k, v in e.items() if k[0] == "qubits" and k[2] == "readout_error"]
    assert len(readout) == 120 and {ec.iso(ec.parse_utc(v["date"])) for v in readout} == {"2026-11-10T11:05:20Z"}
    assert all(e[k] == s1135[k] for k in e if k[0] == "qubits" and k[2] == "readout_error")
    assert E["sources"]["readout_error"] == {"2026-11-10T11:35:39Z": 120}
    assert E["ages_at_running"]["readout_error"]["age_h_max"] == pytest.approx(0.1126, abs=1e-4)
    # the initialisation errors of the 09:07:11Z set: those of the 11:35:39Z set were measured at 11:19 to 11:20Z, after running
    init = [k for k in e if k[0] == "qubits" and k[2] == "init_error"]
    assert len(init) == 116 and all(e[k] == s0907[k] for k in init) and E["sources"]["init_error"] == {"2026-11-10T09:07:11Z": 116}
    later = [k for k in init if ec.parse_utc(s1135[k]["date"]) > t_r]
    assert len(later) == 66 and sum(1 for k in init if s1135[k]["value"] != e[k]["value"]) == 57
    # every value is the latest entry dated at or before running among the three sets, and none is dated after it
    for k, v in e.items():
        dated = [x[k] for x in (s0907, s1135, s1337) if k in x and ec.parse_utc(x[k]["date"]) <= t_r]
        assert ec.parse_utc(v["date"]) == max(ec.parse_utc(d["date"]) for d in dated) and ec.parse_utc(v["date"]) <= t_r
    assert all(c.get("n_dated_after_running", 0) == 0 for c in E["ages_at_running"].values())
    assert E["cases"] == dict(entries_of_s0_dated_after_running={}, ties=[], values_not_in_s0=[])       # none of the four cases of C65-1 arises here
    # test 8a as corrected (C65-2): the static-ZZ entries carry their set's stamp as date, so E takes those of the 09:07:11Z set,
    # and 210 of the 218 differ from those of the 11:35:39Z set
    zz = [k for k in e if k[0] == "general" and k[1].startswith("zz_")]
    assert len(zz) == 218 and all(e[k] == s0907[k] for k in zz) and sum(1 for k in zz if s1135[k]["value"] != e[k]["value"]) == 210
    assert E["sources"]["general:zz"] == {"2026-11-10T09:07:11Z": 218}
    # a composite: neither published set, labelled, with the hash of the settings table
    assert E["value_sha256"] not in {ec.value_sha256(x) for x in S.values()}
    assert E["properties"]["_execution_calibration"]["pool_updates"] == pool.updates() and E["provisional"] is True and E["rule"] == "per_value_at_or_before_running"
    assert E["settings_sha256"] == st.sha256
    # the probes job (running 28 s later) has the same E: one set of rows for the two jobs
    assert ec.execution_calibration(_pool(S, PROBES, "0907", [], "1135"), st)["value_sha256"] == E["value_sha256"]
    # C65-2's count on the placement: of the 82 placed n100 qubits 81 carry an initialisation error, and for 53 of them the later value is dated after running
    placed = set(_rung("replication_01_16384.json")["qubits"])
    assert len(placed) == 82 and sum(1 for k in init if k[1] in placed) == 81 and sum(1 for k in later if k[1] in placed) == 53


def test_a_execution_calibration_of_block_c_equals_the_1135_set_and_the_bracket_equals_the_1337_set(S, st):
    pool = _pool(S, BLOCKC, "1135", [], "1337")
    E, B = ec.execution_calibration(pool, st), ec.bracket_calibration(pool, st)
    assert E["sha256"] == ec.sha256_canonical(S["1135"]) and _entries(E["properties"]) == _entries(S["1135"])      # value for value, date for date
    assert B["sha256"] == ec.sha256_canonical(S["1337"]) and B["kind"] == "bracket"
    assert B["ages_at_running"]["readout_error"]["n_dated_after_running"] == 120          # measured at 13:37:29 to 13:37:31Z: in B, never in E
    assert E["ages_at_running"]["readout_error"]["n_dated_after_running"] == 0
    main = _pool(S, MAIN, "0907", ["1135"], "1337")
    assert ec.bracket_calibration(main, st)["sha256"] == ec.sha256_canonical(S["1337"])
    assert ec.execution_calibration(main, st)["value_sha256"] != E["value_sha256"]        # the two lists of 10 Nov do not share their rows


def test_a_the_other_primary_rules_of_the_table_are_the_published_sets(S, tmp_path):
    pool = _pool(S, MAIN, "0907", ["1135"], "1337")
    at_running = ec.execution_calibration(pool, _settings_with(tmp_path, primary_calibration="set_in_force_at_running"))
    assert at_running["sha256"] == ec.sha256_canonical(S["0907"]) and at_running["rule"] == "set_in_force_at_running"
    after = ec.execution_calibration(pool, _settings_with(tmp_path, primary_calibration="first_set_after_finished"))
    assert after["sha256"] == ec.sha256_canonical(S["1337"])


def test_the_calibration_csv_is_the_snapshot_workflows(S, st, tmp_path):
    committed = (CAL / "ibm_phoenix_2026-11-10T101610Z.csv").read_text(encoding="utf-8")
    assert ec.calibration_csv_text(S["0907"]).strip().splitlines() == committed.strip().splitlines()
    E = ec.execution_calibration(_pool(S, BLOCKC, "1135", [], "1337"), st)
    w = ec.write_calibration(E, tmp_path)
    assert Path(w["csv"]).name == f"ibm_phoenix_2026-11-10T125418Z_execution_{E['value_sha256'][:12]}.csv"
    assert Path(w["properties"]).name == f"ibm_phoenix_properties_2026-11-10T125418Z_execution_{E['value_sha256'][:12]}.json"
    assert ec.sha256_canonical(json.loads(Path(w["properties"]).read_text(encoding="utf-8"))) == E["sha256"]
    assert Path(w["csv"]).read_text(encoding="utf-8") == ec.calibration_csv_text(S["1135"])


def test_a_the_four_cases_of_c65_1(S, st):
    # case 1 is in the test above: the stamp-dated ZZ entries are those of S0.
    # case 2: a job that starts running inside the lag of its own S0. The 11:35:39Z set holds entries dated up to 11:38:31Z; a job
    # running from 11:35:50Z has no earlier entry of those values in its pool, and takes the entries of S0
    t_r = "2026-11-10T11:35:50Z"
    E = ec.execution_calibration(ec.build_pool("lag", t_r, "2026-11-10T11:50:00Z", S["1135"], S["1135"], [], S["1337"], True), st)
    n_after = sum(1 for _, _, e in ec._iter_entries(S["1135"]) if ec.parse_utc(e["date"]) > ec.parse_utc(t_r))
    assert n_after > 0 and sum(E["cases"]["entries_of_s0_dated_after_running"].values()) == n_after
    assert sum(c.get("n_dated_after_running", 0) for c in E["ages_at_running"].values()) == n_after
    assert E["value_sha256"] == ec.value_sha256(S["1135"]) and E["properties"]["_execution_calibration"]["cases"]["entries_of_s0_dated_after_running"] == n_after
    # case 3: one date, two values: the later set's entry, and the tie is recorded
    later = copy.deepcopy(S["1337"])
    old = next(e for e in S["0907"]["qubits"][0] if e["name"] == "T1")
    new = next(e for e in later["qubits"][0] if e["name"] == "T1")
    new.update(date=old["date"], value=old["value"] * 1.5)
    E = ec.execution_calibration(ec.build_pool("tie", MAIN[1], MAIN[2], S["0907"], S["0907"], [], later, True), st)
    assert E["cases"]["ties"] == [dict(value="qubits/0/T1", date=ec.iso(ec.parse_utc(old["date"])), sets=["2026-11-10T09:07:11Z", "2026-11-10T13:37:31Z"],
                                       values=[old["value"], old["value"] * 1.5])]
    assert next(e for e in E["properties"]["qubits"][0] if e["name"] == "T1")["value"] == old["value"] * 1.5
    # case 4: Q47 carries no initialisation error in the 10 Nov sets; a value S0 does not carry is missing in E and recorded
    assert all("init_error" not in {e["name"] for e in S[k]["qubits"][47]} for k in ("0907", "1135", "1337"))
    later = copy.deepcopy(S["1337"])
    later["qubits"][47].append(dict(date="2026-11-10 08:00:00+00:00", name="init_error", unit="", value=9e-3))
    E = ec.execution_calibration(ec.build_pool("missing", MAIN[1], MAIN[2], S["0907"], S["0907"], [], later, True), st)
    assert E["cases"]["values_not_in_s0"] == [dict(value="qubits/47/init_error", first_in="2026-11-10T13:37:31Z")]
    assert "init_error" not in {e["name"] for e in E["properties"]["qubits"][47]}


def test_a_the_trial_sets_fold_into_three_updates_and_leave_e_unchanged(S, st):
    """The six stamps the service returned for 10 Nov (trial run 42958459321) are three sets of values. A re-stamp is not an
    update: it does not close a pool, and E and B are what they are without it."""
    v = {k: ec.value_sha256(S[k]) for k in ("0907", "t1120", "1135", "t1314", "1337", "t1634")}
    assert v["t1120"] == v["1135"] == v["t1314"] and v["1337"] == v["t1634"] and len({v["0907"], v["1135"], v["1337"]}) == 3
    main = ec.build_pool(MAIN[0], MAIN[1], MAIN[2], S["0907"], S["0907"], [S["t1120"], S["1135"]], [S["t1314"], S["1337"], S["t1634"]], True)
    assert main.status == "complete" and main.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:20:04Z", "2026-11-10T13:37:31Z"]
    assert main.restamps == ((), ("2026-11-10T11:35:39Z", "2026-11-10T13:14:38Z"), ("2026-11-10T16:34:05Z",))
    E = ec.execution_calibration(main, st)
    assert E["value_sha256"] == ec.execution_calibration(_pool(S, MAIN, "0907", ["1135"], "1337"), st)["value_sha256"]     # as from the committed files
    assert E["sources"]["readout_error"] == {"2026-11-10T11:20:04Z": 120}        # measured 11:05:20Z, first published 11:20:04Z, not 11:35:39Z
    # C65-2 on the trial sets: the new ZZ values are first carried by the 11:20:04Z set and stamped 11:20:04Z, still after running
    zz1120 = {k: e for k, e in _entries(S["t1120"]).items() if k[0] == "general" and k[1].startswith("zz_")}
    assert {ec.iso(ec.parse_utc(e["date"])) for e in zz1120.values()} == {"2026-11-10T11:20:04Z"} and ec.parse_utc(MAIN[1]) < ec.parse_utc("2026-11-10T11:20:04Z")
    s0907 = _entries(S["0907"])
    assert E["sources"]["general:zz"] == {"2026-11-10T09:07:11Z": 218} and sum(1 for k, e in zz1120.items() if e["value"] != s0907[k]["value"]) == 210
    assert ec.bracket_calibration(main, st)["value_sha256"] == v["1337"]
    # the probes job finished 58.7 s after the 11:20:04Z update was published: the update falls inside its window, and the first
    # update at or after its finished time is the 13:37:31Z one, not the 11:35:39Z re-stamp
    assert (ec.parse_utc(PROBES[2]) - ec.parse_utc("2026-11-10T11:20:04Z")).total_seconds() == pytest.approx(58.73, abs=0.01)
    probes = ec.build_pool(PROBES[0], PROBES[1], PROBES[2], S["0907"], S["0907"], [S["t1120"]], [S["1135"], S["t1314"], S["1337"], S["t1634"]], True)
    assert probes.updates() == main.updates() and ec.bracket_calibration(probes, st)["value_sha256"] == v["1337"]
    assert ec.execution_calibration(probes, st)["value_sha256"] == E["value_sha256"]
    # Block C: the set in force at running is the 11:35:39Z stamp of the 11:20:04Z values; 13:14:38Z repeats them
    blockc = ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], S["1135"], S["1135"], [S["t1314"]], [S["1337"], S["t1634"]], True)
    assert blockc.updates() == ["2026-11-10T11:35:39Z", "2026-11-10T13:37:31Z"] and blockc.restamps == (("2026-11-10T13:14:38Z",), ("2026-11-10T16:34:05Z",))
    assert ec.execution_calibration(blockc, st)["value_sha256"] == v["t1120"]
    # its two other jobs finished at 13:10:40Z and 13:08:16Z: the next stamp, 13:14:38Z, is a re-stamp and leaves the pool pending
    c2 = ("dbpfon8qtr0c738ebgj0", "2026-11-10T12:54:22.817673Z", "2026-11-10T13:10:40.143310Z")
    assert ec.build_pool(c2[0], c2[1], c2[2], S["1135"], S["1135"], [], [S["t1314"]], True).status == "pending"
    done = ec.build_pool(c2[0], c2[1], c2[2], S["1135"], S["1135"], [], [S["t1314"], S["1337"]], True)
    assert done.status == "complete" and done.updates()[-1] == "2026-11-10T13:37:31Z"
    # the set recorded as in force at running must be the last one stamped before it
    with pytest.raises(ec.PoolError, match="at or before running"):
        ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], S["t1120"], S["t1120"], [S["1135"]], [S["1337"]], True)


# ---------------------------------------------------------------------------------------------------------------------------
# b. unchanged values published again
# ---------------------------------------------------------------------------------------------------------------------------

def test_b_a_republication_of_unchanged_values_gives_the_same_hash_of_e(S, st):
    a, b = S["sep21_0224"], S["sep21_0305"]                      # stamps 21 Sep 02:24:15Z and 03:05:59Z: every value equal
    assert a["last_update_date"] != b["last_update_date"] and ec.sha256_canonical(a) != ec.sha256_canonical(b)
    assert ec.value_sha256(a) == ec.value_sha256(b)
    later = changed_after(b)
    e1 = ec.execution_calibration(ec.build_pool("j1", "2026-09-21T02:30:00Z", "2026-09-21T02:40:00Z", a, a, [], [b, later], True), st)
    e2 = ec.execution_calibration(ec.build_pool("j2", "2026-09-21T03:10:00Z", "2026-09-21T03:20:00Z", b, b, [], later, True), st)
    assert e1["value_sha256"] == e2["value_sha256"] == ec.value_sha256(a) and e1["sha256"] != e2["sha256"]
    # the re-stamp is not an update: it does not close the pool of the first job, and the pool says what it folded
    pending = ec.build_pool("j1", "2026-09-21T02:30:00Z", "2026-09-21T02:40:00Z", a, a, [], b, True)
    assert pending.status == "pending" and "repeat the values in force before" in " ".join(pending.notes)
    full = ec.build_pool("j1", "2026-09-21T02:30:00Z", "2026-09-21T02:40:00Z", a, a, [], [b, later], True)
    assert full.updates() == ["2026-09-21T02:24:15Z", "2026-09-21T04:00:00Z"] and full.restamps == (("2026-09-21T03:05:59Z",), ())


def changed_after(props):
    """A later update: the set re-stamped 04:00:00Z with one readout value changed."""
    later = copy.deepcopy(props)
    later["last_update_date"] = "2026-09-21 04:00:00+00:00"
    e = next(x for x in later["qubits"][0] if x["name"] == "readout_error")
    e.update(value=e["value"] * 2 + 1e-3, date="2026-09-21 03:59:00+00:00")
    return later


def S_after_of(props):
    later = copy.deepcopy(props)
    later["last_update_date"] = "2026-09-21 04:00:00+00:00"
    return later


def test_b_the_pair_the_draft_names_differs_in_values_no_prediction_reads(S):
    """The draft names 21 Sep 02:05Z and 02:24Z. Those two sets are not equal value for value: the four measurement-discriminator
    threshold classes differ (119 values each) and nothing else, so their calibration CSVs are equal and their value hashes are not."""
    a, b = S["sep21_0205"], S["sep21_0224"]
    eb = _entries(b)
    differing = {}
    for ident, cls, e in ec._iter_entries(a):
        if e["value"] != eb[ident]["value"]:
            differing[cls] = differing.get(cls, 0) + 1
    assert differing == {"threshold:measure": 119, "threshold:measure_2": 119, "threshold:measure_reset": 119, "threshold:measure_reset_2": 119}
    assert ec.value_sha256(a) != ec.value_sha256(b)
    assert ec.calibration_csv_text(a) == ec.calibration_csv_text(b)


# ---------------------------------------------------------------------------------------------------------------------------
# c. zones
# ---------------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def nov10(S, st, tmp_path_factory):
    """The 10 Nov n100 placement with the over-cut elements of its two execution-time calibrations."""
    d = tmp_path_factory.mktemp("nov10")
    rung = _rung("replication_01_16384.json")
    out = dict(rung=rung)
    for name, pool in (("main", _pool(S, MAIN, "0907", ["1135"], "1337")), ("blockc", _pool(S, BLOCKC, "1135", [], "1337"))):
        w = ec.write_calibration(ec.execution_calibration(pool, st), d / name)
        out[name] = ec.over_cut_elements(rung, w["csv"], w["properties"])
        w = ec.write_calibration(ec.bracket_calibration(pool, st), d / (name + "_bracket"))
        out[name + "_bracket"] = ec.over_cut_elements(rung, w["csv"], w["properties"])
    return out


def test_c_over_cut_elements_of_the_10_nov_placement_at_execution(nov10):
    name = {k: [(ec._name(e)) for e in nov10[k]] for k in ("main", "blockc")}
    # the replication jobs: the two readout errors measured at 11:05:20Z; the initialisation errors over the cut were measured after running
    assert name["main"] == ["Q31 (readout)", "Q98 (readout)"]
    assert name["blockc"] == ["Q25 (init)", "Q31 (readout)", "Q98 (readout)", "Q100 (init)"]
    q98 = [e for e in nov10["blockc"] if e["qubit"] == 98][0]
    assert q98["readout"] == pytest.approx(6.40e-2, rel=2e-2)


def test_c_zones_on_the_10_nov_placement(nov10, st):
    rung = nov10["rung"]
    z = {(e["qubit"], L): ec.zone(rung, L, e, st) for e in nov10["blockc"] for L in (1, 2, 4, 8, 12)}
    for q in (25, 98):
        assert z[(q, 8)] == ec.ZONE_CONE and z[(q, 12)] == ec.ZONE_CONE and z[(q, 1)] == ec.ZONE_OUTSIDE and z[(q, 2)] == ec.ZONE_OUTSIDE
    assert z[(25, 4)] == ec.ZONE_CONE and z[(98, 4)] == ec.ZONE_CONE and z[(31, 4)] == ec.ZONE_OUTSIDE and z[(100, 4)] == ec.ZONE_OUTSIDE
    assert z[(31, 8)] == ec.ZONE_CONE and z[(100, 8)] == ec.ZONE_CONE
    assert rung["edge"] == "75_85"
    # a synthetic readout over the cut on Q75, an observable qubit: not evaluable, whatever the rows say
    synthetic = dict(kind="qubit", qubit=75, reasons=["readout"], readout=4e-2)
    assert ec.zone(rung, 8, synthetic, st) == ec.ZONE_EDGE
    c = ec.classify(rung, 8, [synthetic], 1.0, 1.0, st)
    assert c["reading"] == ec.NOT_EVALUABLE and c["grounds"] == [ec.GROUND_ZONE] and c["flag"] is False
    # the edge coupler itself, and a qubit of the L = 2 cone off the edge
    assert ec.zone(rung, 8, dict(kind="coupler", coupler=[85, 75], reasons=["CZ"]), st) == ec.ZONE_EDGE
    from gradvar.circuits import light_cone
    patch, edge = ec.placement_patch(rung)
    c2 = sorted(set(light_cone(patch, 2, edge)) - set(edge))
    assert c2 == sorted(set(rung["cone_L2_qubits"]) - {75, 85})
    assert all(ec.zone(rung, L, dict(kind="qubit", qubit=q, reasons=["init"]), st) == ec.ZONE_L2 for q in c2 for L in (1, 2, 8))


def test_c_a_point_shallower_than_the_zone_follows_the_table(nov10, st, tmp_path):
    rung = nov10["rung"]
    q = sorted(set(rung["cone_L2_qubits"]) - {75, 85})[0]
    el = dict(kind="qubit", qubit=q, reasons=["readout"])
    assert ec.zone(rung, 1, el, st) == ec.ZONE_L2                                            # provisional: the table read from the top
    own = _settings_with(tmp_path, zone_for_points_shallower_than_zone="own_cone_only")
    assert ec.zone(rung, 1, el, own) == ec.ZONE_OUTSIDE and ec.zone(rung, 2, el, own) == ec.ZONE_L2


def test_c_day_2_coupler_95_105_under_the_two_coupler_rules(S, st, tmp_path):
    rung = _rung("grid_n100_16384.json")
    assert rung["n"] == 85 and rung["edge"] == "75_85"
    s1844 = json.loads((ROOT / "data" / "runs" / "2026-09-20" / DAY2[0] / "properties.json").read_text(encoding="utf-8"))     # the properties at creation, 18:44:14Z
    pool = ec.build_pool(DAY2[0], DAY2[1], DAY2[2], s1844, s1844, [], S["sep21_0127"], True)
    E = ec.execution_calibration(pool, st)
    assert E["sources"]["readout_error"] == {"2026-09-21T01:27:50Z": 120}                    # measured 20 Sep 21:10:09Z, before the job ran
    w = ec.write_calibration(E, tmp_path / "E2")
    els = ec.over_cut_elements(rung, w["csv"], w["properties"])
    assert sorted(ec._name(e) for e in els) == sorted(["Q105 (readout)", "coupler 104-105 (CZ)", "coupler 118-119 (CZ)", "coupler 105-106 (CZ)",
                                                       "coupler 41-51 (CZ)", "coupler 105-115 (CZ)", "coupler 95-105 (CZ)"])
    c95 = [e for e in els if e["kind"] == "coupler" and set(e["coupler"]) == {95, 105}][0]
    from gradvar.circuits import light_cone
    patch, edge = ec.placement_patch(rung)
    c2 = set(light_cone(patch, 2, edge))
    assert 95 in c2 and 105 not in c2
    assert ec.zone(rung, 8, c95, st) == ec.ZONE_CONE                                         # both-qubits rule: elsewhere in the cone
    either = _settings_with(tmp_path, coupler_zone_rule="either_qubit")
    assert ec.zone(rung, 8, c95, either) == ec.ZONE_L2
    assert ec.classify(rung, 8, els, 0.957, 1.0, st)["reading"] == ec.READ_WITH_FLAG
    assert ec.classify(rung, 8, els, 0.957, 1.0, either)["reading"] == ec.NOT_EVALUABLE


def test_c_a_coupler_with_one_qubit_in_the_points_cone(nov10, st, tmp_path):
    from gradvar.circuits import light_cone
    rung = nov10["rung"]
    patch, edge = ec.placement_patch(rung)
    c4 = set(light_cone(patch, 4, edge))
    a, b = next((a, b) for a, b in patch.edges() if (a in c4) != (b in c4))
    el = dict(kind="coupler", coupler=[a, b], reasons=["CZ"])
    assert ec.zone(rung, 4, el, st) == ec.ZONE_CONE                                          # provisional: either qubit, the reading that drops no flag
    assert ec.zone(rung, 4, el, _settings_with(tmp_path, coupler_cone_rule="both_qubits")) == ec.ZONE_OUTSIDE


def test_over_cut_elements_refuses_a_csv_without_a_stamp(nov10, tmp_path):
    p = tmp_path / "calibration.csv"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="coherence floor"):
        ec.over_cut_elements(nov10["rung"], p, p)


# ---------------------------------------------------------------------------------------------------------------------------
# d. regression against the draft's number (draws one row: slow)
# ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.slow
def test_d_the_n100_l8_row_on_block_cs_execution_calibration_over_the_package_row(S, st, tmp_path):
    import redraw_gate1b as rd
    package = json.loads((ROOT / "data" / "predictions" / "main_grid_redraw_2026-11-10T1016.json").read_text(encoding="utf-8"))
    base = [r for r in package["main_grid"]["rows"] if r["rung"] == "n100" and r["L"] == 8 and r["model"] == "unital"][0]
    assert base["pp_converged"] is True and base["var_k1_pp"] == pytest.approx(4.166525557338754e-4, rel=1e-12)
    rung = package["runday_placement"]["rungs"]["n100"]
    assert rung["qubits"] == _rung("replication_01_16384.json")["qubits"]
    w = ec.write_calibration(ec.execution_calibration(_pool(S, BLOCKC, "1135", [], "1337"), st), tmp_path)
    s = package["settings"]
    row = rd._run_main_grid_job(dict(csv=w["csv"], props=w["properties"], stamp="2026-11-10T125418Z", placement_label="execution-time calibration", cone_sha="",
                                     rung_name="n100", rung=rung, spec=rung["patch"], L=8, model="unital", time_limit_s=s["time_limit_s"], n_cap=s["n_cap"],
                                     n_samples=2000))          # the truncated value does not depend on the number of sampled paths
    assert row["pp_converged"] is True
    assert row["var_k1_pp"] / base["var_k1_pp"] == pytest.approx(REFERENCE_RATIO, abs=1e-3)


# ---------------------------------------------------------------------------------------------------------------------------
# f. an incomplete pool is pending or stops (pool part)
# ---------------------------------------------------------------------------------------------------------------------------

def test_f_no_set_after_finished_is_pending_and_gives_no_calibration(S, st):
    pool = _pool(S, BLOCKC, "1135", [], None)
    assert pool.status == "pending" and pool.s_after is None
    for fn in (ec.execution_calibration, ec.bracket_calibration):
        with pytest.raises(ec.PoolPending):
            fn(pool, st)
    c = ec.classify_without_execution_calibration("pending: no set published after finished", st)                   # C65-4: never the dispatch-time row
    assert c["reading"] == ec.NOT_EVALUABLE and c["grounds"] == [ec.GROUND_NO_E] and "not the registered reading" in c["row"]


def test_f_a_gap_in_the_walk_back_stops(S):
    with pytest.raises(ec.PoolError, match="gap"):
        _pool(S, MAIN, "0907", ["1135"], "1337", walk_complete=False, walk_note="asked for 11:35:38Z and got 13:37:31Z")
    with pytest.raises(ec.PoolError, match="does not lie between"):                  # a set stamped after finished among the intermediate ones
        ec.build_pool(PROBES[0], PROBES[1], PROBES[2], S["0907"], S["0907"], [S["1135"]], S["1337"], True)
    with pytest.raises(ec.PoolError, match="does not lie between"):
        ec.build_pool(MAIN[0], MAIN[1], MAIN[2], S["0907"], S["0907"], [S["0732"]], S["1337"], True)


def test_f_two_records_of_the_set_at_running_that_disagree_stop(S):
    with pytest.raises(ec.PoolError, match="disagree"):
        ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], S["0907"], S["1135"], [], S["1337"], True)      # job.properties() gave the set at creation
    changed = copy.deepcopy(S["1135"])
    changed["qubits"][5][2]["value"] *= 1.01
    with pytest.raises(ec.PoolError, match="disagree"):
        ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], changed, S["1135"], [], S["1337"], True)
    for a, b in ((None, S["1135"]), (S["1135"], None)):
        with pytest.raises(ec.PoolError, match="needs both records"):
            ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], a, b, [], S["1337"], True)


def test_f_sets_on_the_wrong_side_of_the_job_stop(S):
    with pytest.raises(ec.PoolError, match="after running"):
        ec.build_pool(MAIN[0], MAIN[1], MAIN[2], S["1135"], S["1135"], [], S["1337"], True)             # published 11:35:39Z, the job ran from 11:12:05Z
    with pytest.raises(ec.PoolError, match="before finished"):
        ec.build_pool(BLOCKC[0], BLOCKC[1], BLOCKC[2], S["0907"], S["0907"], [], S["1135"], True)       # 11:35:39Z is not after 13:31:41Z


def test_f_the_degraded_pool_from_the_committed_snapshots(S, st, tmp_path):
    """C65-4: the same rule on the files the snapshot workflow committed. The trial sets are not such files and are not read."""
    main = ec.committed_snapshot_pool(MAIN[0], "ibm_phoenix", MAIN[1], MAIN[2])
    assert main.source == ec.SOURCE_SNAPSHOTS and main.status == "complete" and main.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z", "2026-11-10T13:37:31Z"]
    assert {FILES["0907"], FILES["1135"], FILES["1337"]} <= set(main.files) and not any("update_" in f for f in main.files)
    E = ec.execution_calibration(main, st)
    assert E["from_committed_snapshots"] is True and E["pool_source"] == ec.SOURCE_SNAPSHOTS
    assert E["value_sha256"] == ec.execution_calibration(_pool(S, MAIN, "0907", ["1135"], "1337"), st)["value_sha256"]
    # what the degraded pool gets wrong: the snapshots first saw the 11:20:04Z values under the stamp 11:35:39Z, after the probes
    # job had finished (11:21:02Z), so they close its pool; on the service's sets that update falls inside the job's window
    probes = ec.committed_snapshot_pool(PROBES[0], "ibm_phoenix", PROBES[1], PROBES[2])
    assert probes.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z"] and ec.bracket_calibration(probes, st)["value_sha256"] == ec.value_sha256(S["1135"])
    cal = tmp_path / "cal"
    cal.mkdir()
    for k in ("0907", "1135"):
        shutil.copy(CAL / FILES[k], cal / FILES[k])
    shutil.copy(CAL / FILES["t1634"], cal / "ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json")     # not a snapshot file name: ignored
    pending = ec.committed_snapshot_pool(MAIN[0], "ibm_phoenix", MAIN[1], MAIN[2], cal)
    assert pending.status == "pending" and pending.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z"]
    with pytest.raises(ec.PoolError, match="at or before running"):
        ec.committed_snapshot_pool("early", "ibm_phoenix", "2026-11-10T08:00:00Z", "2026-11-10T08:10:00Z", cal)
    with pytest.raises(ec.PoolError, match="at or before running"):
        ec.committed_snapshot_pool(MAIN[0], "ibm_other", MAIN[1], MAIN[2], cal)
    # pool_for_job: the service files first, then the committed snapshots, else not evaluable; the case is recorded
    pool, rec = ec.pool_for_job(_write_bundle(tmp_path / "svc", MAIN, "0907", ["1135"], "1337", S))
    assert rec["case"] == ec.SOURCE_SERVICE and pool.source == ec.SOURCE_SERVICE and rec["service_problem"] is None
    for name, kw in (("nofile", dict(drop="properties_between.json")), ("gap", dict(complete=False)), ("pending", dict())):
        d = _write_bundle(tmp_path / name, MAIN, "0907", ["1135"], None if name == "pending" else "1337", S, **kw)
        pool, rec = ec.pool_for_job(d)
        assert rec["case"] == ec.SOURCE_SNAPSHOTS and pool.source == ec.SOURCE_SNAPSHOTS and pool.status == "complete" and rec["service_problem"]
        assert set(rec["files"]) == set(main.files)
        pool, rec = ec.pool_for_job(d, calibrations_dir=cal)
        assert pool is None and rec["case"] == "not_evaluable" and rec["snapshot_problem"].startswith("pending")
    c = ec.classify_without_execution_calibration(rec["snapshot_problem"], st)
    assert c["reading"] == ec.NOT_EVALUABLE and c["grounds"] == [ec.GROUND_NO_E]


def test_c_the_flags_that_do_not_come_from_e(nov10, st, tmp_path):
    """C65-6: a zone element over a cut on B and not on E flags the point. C65-4: so does an E from the committed snapshots.
    Neither changes a reading other than 'read'."""
    rung = nov10["rung"]
    q75 = dict(kind="qubit", qubit=75, reasons=["readout"], readout=4e-2)
    c = ec.classify(rung, 8, [], None, None, st, bracket_elements=[q75])
    assert c["reading"] == ec.READ_WITH_FLAG and c["flags"] == [ec.FLAG_BRACKET_ZONE] and c["grounds"] == [] and [e["qubit"] for e in c["bracket_zone_elements"]] == [75]
    both = ec.classify(rung, 8, [q75], 1.0, 1.0, st, bracket_elements=[q75])                 # over the cut on E too: the rule on E decides
    assert both["reading"] == ec.NOT_EVALUABLE and both["bracket_zone_elements"] == [] and both["flags"] == []
    assert ec.classify(rung, 8, [], None, None, _settings_with(tmp_path, bracket_zone_flag=False), bracket_elements=[q75])["reading"] == ec.READ
    # the 10 Nov bracket (13:37:31Z): Q25, Q98 and Q100 are over a cut, none of them in the zone, so B raises no flag
    assert [ec._name(e) for e in nov10["blockc_bracket"]] == ["Q25 (init)", "Q98 (readout)", "Q100 (init)"]
    c = ec.classify(rung, 8, nov10["blockc"], 1.0105, 1.0, st, bracket_elements=nov10["blockc_bracket"])
    assert c["reading"] == ec.READ_WITH_FLAG and c["flags"] == [ec.FLAG_CONE] and c["bracket_zone_elements"] == []
    snap = ec.classify(rung, 1, [], None, None, st, from_committed_snapshots=True)
    assert snap["reading"] == ec.READ_WITH_FLAG and snap["flags"] == [ec.FLAG_SNAPSHOTS] and snap["flag"] is True
    snap = ec.classify(rung, 8, nov10["blockc"], 1.0105, 1.0, st, from_committed_snapshots=True)
    assert snap["reading"] == ec.READ_WITH_FLAG and snap["flags"] == [ec.FLAG_CONE, ec.FLAG_SNAPSHOTS]
    assert ec.classify(rung, 8, [q75], 1.0, 1.0, st, from_committed_snapshots=True)["reading"] == ec.NOT_EVALUABLE


def _write_bundle(d, job, s0, mid, after, S, complete=True, drop=None, job_props=None):
    d.mkdir(parents=True, exist_ok=True)
    files = {"job.json": dict(job_id=job[0], backend_name="ibm_phoenix", metrics=dict(timestamps=dict(created="2026-11-10T11:13:29.583977Z", running=job[1], finished=job[2]))),
             "properties_at_running.json": dict(job_properties=S[job_props or s0], backend_properties=S[s0]),
             "properties_between.json": dict(complete=complete, note=None, sets=[dict(properties=S[m]) for m in mid]),
             "properties_after_finished.json": S[after] if after else dict(status="pending"),
             "properties.json": S["0732"]}                                           # the properties at creation: never read
    for name, content in files.items():
        if name != drop:
            (d / name).write_text(json.dumps(content), encoding="utf-8")
    return d


def test_f_load_pool_reads_the_bundle_and_never_the_properties_at_creation(S, st, tmp_path):
    pool = ec.load_pool(_write_bundle(tmp_path / "a", MAIN, "0907", ["1135"], "1337", S))
    assert pool.status == "complete" and pool.job_id == MAIN[0] and pool.updates() == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z", "2026-11-10T13:37:31Z"]
    assert "2026-11-10T07:32:03Z" not in pool.updates()
    assert ec.execution_calibration(pool, st)["value_sha256"] == ec.execution_calibration(_pool(S, MAIN, "0907", ["1135"], "1337"), st)["value_sha256"]
    assert ec.load_pool(_write_bundle(tmp_path / "b", BLOCKC, "1135", [], None, S)).status == "pending"
    # the times are taken from the retrieval record when the bundle has one (branch pipeline-day3-2026-11-10), before metrics.timestamps
    d = _write_bundle(tmp_path / "b2", MAIN, "0907", ["1135"], "1337", S)
    job = json.loads((d / "job.json").read_text(encoding="utf-8"))
    job["metrics"]["timestamps"].update(running="2026-11-10T10:00:00Z", finished="2026-11-10T10:05:00Z")
    job["retrieval"] = dict(execution_span=dict(created="2026-11-10T11:11:40.956832Z", running=MAIN[1], finished=MAIN[2], complete=True))
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    assert ec.iso(ec.load_pool(d).t_running) == "2026-11-10T11:12:05.243865Z"
    for i, drop in enumerate(("properties_at_running.json", "properties_between.json", "properties_after_finished.json", "job.json")):
        with pytest.raises(ec.PoolError, match="missing"):
            ec.load_pool(_write_bundle(tmp_path / f"c{i}", MAIN, "0907", ["1135"], "1337", S, drop=drop))
    with pytest.raises(ec.PoolError, match="gap"):
        ec.load_pool(_write_bundle(tmp_path / "d", MAIN, "0907", ["1135"], "1337", S, complete=False))
    with pytest.raises(ec.PoolError, match="disagree"):
        ec.load_pool(_write_bundle(tmp_path / "e", BLOCKC, "1135", [], "1337", S, job_props="0907"))
    # an intermediate set named by file, relative to the repository root
    d = _write_bundle(tmp_path / "f", MAIN, "0907", [], "1337", S)
    (d / "properties_between.json").write_text(json.dumps(dict(complete=True, sets=[dict(file="data/calibrations/" + FILES["1135"])])), encoding="utf-8")
    assert ec.load_pool(d).updates()[1] == "2026-11-10T11:35:39Z"
    (d / "properties_between.json").write_text(json.dumps(dict(complete=True, sets=[dict(file="data/calibrations/absent.json")])), encoding="utf-8")
    with pytest.raises(ec.PoolError, match="missing"):
        ec.load_pool(d)


def test_f_the_module_reads_no_service_no_result_and_no_live_set():
    import ast
    tree = ast.parse((ROOT / "gradvar" / "execution_calibration.py").read_text(encoding="utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
    assert not [m for m in imported if m.startswith(("qiskit_ibm_runtime", "gradvar.hardware", "requests", "urllib"))]
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not attrs & {"result", "properties", "backend", "job"}
    strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "result.json" not in strings and not [s for s in strings if s == "properties.json"]


# ---------------------------------------------------------------------------------------------------------------------------
# h. the 10 percent line and a split point
# ---------------------------------------------------------------------------------------------------------------------------

def test_h_the_decision_line(nov10, st, tmp_path):
    rung, els = nov10["rung"], nov10["blockc"]
    inside = ec.classify(rung, 8, els, math.exp(0.09), 1.0, st)
    assert inside["reading"] == ec.READ_WITH_FLAG and inside["flag"] is True and inside["grounds"] == [] and inside["ln_ratio"] == pytest.approx(0.09)
    assert "pi_decision_required" not in inside                                       # C65-3: above the line the point is not evaluable; nobody decides
    for ratio in (math.exp(0.11), math.exp(-0.11)):
        over = ec.classify(rung, 8, els, ratio, 1.0, st)
        assert over["reading"] == ec.NOT_EVALUABLE and over["grounds"] == [ec.GROUND_LINE] and over["flag"] is True and "0.1" in over["reason"]
        assert "PI" not in over["reason"]
    assert ec.classify(rung, 8, els, math.exp(0.0999), 1.0, st)["reading"] == ec.READ_WITH_FLAG
    assert ec.classify(rung, 8, els, math.exp(0.5), 1.0, _settings_with(tmp_path, decision_line_abs_ln_ratio=None))["reading"] == ec.READ_WITH_FLAG
    assert ec.classify(rung, 8, els, math.exp(0.06), 1.0, _settings_with(tmp_path, decision_line_abs_ln_ratio=0.05))["reading"] == ec.NOT_EVALUABLE
    # the line belongs to flagged points: no element in the cone, no line (an L = 1 point on this placement), however far the rows are apart
    clean = ec.classify(rung, 1, els, math.exp(0.3), 1.0, st)
    assert clean["reading"] == ec.READ and clean["flag"] is False and "4 outside it" in clean["reason"]
    assert ec.classify(rung, 8, [], None, None, st)["reading"] == ec.READ
    with pytest.raises(ValueError, match="decision line"):
        ec.classify(rung, 8, els, None, None, st)                                     # a flagged point without its two rows is not read
    # the 10 Nov shift of this row, +1.05 percent, is far inside the line
    assert ec.classify(rung, 8, els, 1.0105, 1.0, st)["reading"] == ec.READ_WITH_FLAG
    assert inside["provisional"] is True and inside["settings_sha256"] == st.sha256


def test_h_a_point_split_over_two_jobs(st, tmp_path):
    parts = [dict(value=4.0e-4, se=1.0e-5, executions=300), dict(value=4.2e-4, se=2.0e-5, executions=100)]
    out = ec.combine_split_point(parts, st)
    assert out["rule"] == "execution_weighted_mean" and out["weights"] == [0.75, 0.25]
    assert out["value"] == pytest.approx(4.05e-4) and out["se"] == pytest.approx(math.sqrt((300 * 1e-5) ** 2 + (100 * 2e-5) ** 2) / 400)
    sep = ec.combine_split_point(parts, _settings_with(tmp_path, split_point_rule="separate_shares"))
    assert sep["rule"] == "separate_shares" and "value" not in sep and sep["parts"] == parts
    with pytest.raises(ValueError):
        ec.combine_split_point([dict(value=1.0, se=0.0, executions=0)], st)
    # the strictest classification among the jobs (C65-1)
    assert "reading" not in out
    for readings, want in ((("read", "read"), "read"), (("read", "read_with_flag"), "read_with_flag"), (("read_with_flag", "not_evaluable"), "not_evaluable"),
                           (("read", None), None), ((None, "not_evaluable"), "not_evaluable")):
        both = ec.combine_split_point([dict(x, reading=r) for x, r in zip(parts, readings)], st)
        assert both["reading"] == want and both["value"] == pytest.approx(4.05e-4)
        assert ec.combine_split_point([dict(x, reading=r) for x, r in zip(parts, readings)], _settings_with(tmp_path, split_point_rule="separate_shares"))["reading"] == want
