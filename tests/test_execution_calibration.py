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
         "sep21_0305": "ibm_phoenix_properties_2026-09-21T033603Z.json", "sep21_0127": "ibm_phoenix_properties_2026-09-21T014956Z.json"}
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


def _settings_with(tmp_path, **changes):
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    for k, v in changes.items():
        table["settings"][k]["value"] = v
    p = tmp_path / "settings.json"
    p.write_text(json.dumps(table), encoding="utf-8")
    return ec.load_settings(p)


def _rung(joblist, name="n100"):
    return json.loads((ROOT / "data" / "joblists" / "paper1" / joblist).read_text(encoding="utf-8"))["placement"]["rungs"][name]


# ---------------------------------------------------------------------------------------------------------------------------
# the settings table
# ---------------------------------------------------------------------------------------------------------------------------

def test_the_table_is_provisional_and_holds_the_drafts_recommendations(st):
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert table["status"] == "provisional" and st.provisional is True and "PROVISIONAL" in table["status_note"]
    assert all(e["provisional"] is True for e in table["settings"].values())
    assert st.values == {"primary_calibration": "per_value_at_or_before_running", "general_entries_rule": "by_date", "coupler_zone_rule": "both_qubits",
                         "coupler_cone_rule": "either_qubit", "zone_for_points_shallower_than_zone": "zone_applies", "decision_line_abs_ln_ratio": 0.10,
                         "fallback_when_execution_calibration_cannot_be_built": "dispatch_row_with_flag", "split_point_rule": "execution_weighted_mean",
                         "value_age_bound_hours": None, "bracket_decides_gate2e": False, "dispatch_window": "package_update_or_next_same_utc_day"}
    rec = st.record()
    assert rec["provisional"] is True and rec["settings_status"] == "provisional" and len(rec["settings_sha256"]) == 64
    assert rec["settings_file"] == "data/settings/execution_calibration_settings.json"


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
        assert "settings" in params and not params & {"rule", "line", "threshold", "primary", "fallback", "coupler_rule"}


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
    # found in implementation: the general entries (ZZ, J) carry their set's publication time as date, so they come from the 09:07:11Z set,
    # and 210 of the 218 ZZ values differ from those of the 11:35:39Z set
    zz = [k for k in e if k[0] == "general" and k[1].startswith("zz_")]
    assert len(zz) == 218 and all(e[k] == s0907[k] for k in zz) and sum(1 for k in zz if s1135[k]["value"] != e[k]["value"]) == 210
    assert E["sources"]["general:zz"] == {"2026-11-10T09:07:11Z": 218}
    # a composite: neither published set, labelled, with the hash of the settings table
    assert E["value_sha256"] not in {ec.value_sha256(x) for x in S.values()}
    assert E["properties"]["_execution_calibration"]["pool_updates"] == pool.updates() and E["provisional"] is True and E["rule"] == "per_value_at_or_before_running"
    assert E["settings_sha256"] == st.sha256
    # the probes job (running 28 s later) has the same E: one set of rows for the two jobs
    assert ec.execution_calibration(_pool(S, PROBES, "0907", [], "1135"), st)["value_sha256"] == E["value_sha256"]


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
    same = ec.execution_calibration(pool, _settings_with(tmp_path, general_entries_rule="from_set_in_force_at_running"))
    assert same["value_sha256"] == ec.execution_calibration(pool, ec.load_settings())["value_sha256"]     # the two readings coincide on the record


def test_the_calibration_csv_is_the_snapshot_workflows(S, st, tmp_path):
    committed = (CAL / "ibm_phoenix_2026-11-10T101610Z.csv").read_text(encoding="utf-8")
    assert ec.calibration_csv_text(S["0907"]).strip().splitlines() == committed.strip().splitlines()
    E = ec.execution_calibration(_pool(S, BLOCKC, "1135", [], "1337"), st)
    w = ec.write_calibration(E, tmp_path)
    assert Path(w["csv"]).name == f"ibm_phoenix_2026-11-10T125418Z_execution_{E['value_sha256'][:12]}.csv"
    assert Path(w["properties"]).name == f"ibm_phoenix_properties_2026-11-10T125418Z_execution_{E['value_sha256'][:12]}.json"
    assert ec.sha256_canonical(json.loads(Path(w["properties"]).read_text(encoding="utf-8"))) == E["sha256"]
    assert Path(w["csv"]).read_text(encoding="utf-8") == ec.calibration_csv_text(S["1135"])


# ---------------------------------------------------------------------------------------------------------------------------
# b. unchanged values published again
# ---------------------------------------------------------------------------------------------------------------------------

def test_b_a_republication_of_unchanged_values_gives_the_same_hash_of_e(S, st):
    a, b = S["sep21_0224"], S["sep21_0305"]                      # IBM updates 21 Sep 02:24:15Z and 03:05:59Z: every value equal
    assert a["last_update_date"] != b["last_update_date"] and ec.sha256_canonical(a) != ec.sha256_canonical(b)
    assert ec.value_sha256(a) == ec.value_sha256(b)
    e1 = ec.execution_calibration(ec.build_pool("j1", "2026-09-21T02:30:00Z", "2026-09-21T02:40:00Z", a, a, [], b, True), st)
    e2 = ec.execution_calibration(ec.build_pool("j2", "2026-09-21T03:10:00Z", "2026-09-21T03:20:00Z", b, b, [], S_after_of(b), True), st)
    assert e1["value_sha256"] == e2["value_sha256"] == ec.value_sha256(a) and e1["sha256"] != e2["sha256"]


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
    assert c["reading"] == ec.NOT_EVALUABLE and c["pi_decision_required"] is False and "exploratory" in c["reason"]
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
    c = ec.classify_without_execution_calibration("pending: no set published after finished", st)
    assert c["reading"] == ec.READ_WITH_FLAG and c["row"] == "dispatch" and c["flag"] is True


def test_f_a_gap_in_the_walk_back_stops(S):
    with pytest.raises(ec.PoolError, match="gap"):
        _pool(S, MAIN, "0907", ["1135"], "1337", walk_complete=False, walk_note="asked for 11:35:38Z and got 13:37:31Z")
    with pytest.raises(ec.PoolError, match="not the first"):                         # a set dated after finished among the intermediate ones
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


def _write_bundle(d, job, s0, mid, after, S, complete=True, drop=None, job_props=None):
    d.mkdir(parents=True, exist_ok=True)
    files = {"job.json": dict(job_id=job[0], metrics=dict(timestamps=dict(created="2026-11-10T11:13:29.583977Z", running=job[1], finished=job[2]))),
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
    assert inside["reading"] == ec.READ_WITH_FLAG and inside["flag"] is True and inside["pi_decision_required"] is False and inside["ln_ratio"] == pytest.approx(0.09)
    for ratio in (math.exp(0.11), math.exp(-0.11)):
        over = ec.classify(rung, 8, els, ratio, 1.0, st)
        assert over["reading"] == ec.NOT_EVALUABLE and over["pi_decision_required"] is True and over["flag"] is True and "0.1" in over["reason"]
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
    fb = ec.classify_without_execution_calibration("stopped", _settings_with(tmp_path, fallback_when_execution_calibration_cannot_be_built="not_evaluable"))
    assert fb["reading"] == ec.NOT_EVALUABLE and fb["flag"] is False
