"""Deviation 63 (draft), Part A3: the two new truncation pairs as their own pinned job list, generated from the day-3 list.

    python scripts/make_truncation_pairs.py data/joblists/paper1/day3_dial_refs.json
        [--out data/joblists/paper1/dial_truncation_pairs.json] [--allow-dial-excluded] [--check]

The pairs run as a separate list (``dial_truncation_pairs.json``), not inside ``day3_dial_refs.json``, so that day 3 does not wait on
Deviation 63's reviews or the PI's countersignature. The list is built from the day-3 list it follows:

- **Placement.** The day-3 list's ``placement`` block is copied unchanged, with its ``pin_snapshot`` (Deviation 58): the runner builds the
  pairs on the same snapshot and rung origins as day 3, so the pairs share day 3's n60 rung (qubits, holes, broken couplers, edge). A
  day-3 list without ``pin_snapshot`` is refused.
- **Geometry and estimator** are the booked p = 0.5 pair's (``trunc_full_p0.5_L8`` / ``trunc_l2_p0.5_L8``, Section 3b 'Truncation
  arm'): the n60 rung, L = 8, k = L, 100 draws, 256 masks x 64 shots (16,384 per circuit), resilience 0, the full circuit and the circuit
  with its first L - 2 layers deleted (``truncate_to`` = 2, all qubits from |0>), which share theta and the masks of the kept layers
  because they share one seed (``gradvar.hardware.build_probes``: theta of draw d from seed + d, mask m from the lottery stream
  (seed + 1 + m, MASK_STREAM), the truncated circuit taking the last 2 layers' masks).
- **Pairs.** (a) the reset dial at p = 0.25 (``trunc_full_p0.25_L8``, ``trunc_l2_p0.25_L8``); (b) the unital dephasing dial at p = 0.5
  (``trunc_full_dephase_p0.5_L8``, ``trunc_l2_dephase_p0.5_L8``: control (b)'s dial, virtual Z with probability p/2 = 0.25 per qubit per
  layer (``mask_p``) and the matched 400 ns delay). The probe ids follow the loader's ``trunc_full_*`` / ``trunc_l<l>_*`` rule
  (Deviation 60), so the rows map to kind 'truncation' with their own point ids ('truncation reset p0.25 ...', 'truncation dephase
  p0.5 ...'); H7 reads only the reset p = 0.5 rows.
- **Seeds.** A fresh seed block: role ``trunc_pairs`` (index 16, after the generator's 0-15) on the n60 rung at L = 8, seed
  ``PAIRS_SEED`` = 23891001 (the ``make_paper1_joblists.seed_for`` formula), one seed for the four probes as the day-3 dial points share
  one seed across p and the dephasing control (Section 3b 'Pooling'). The θ draws are therefore new: nothing is paired with day 3's
  p = 0.5 pair (seed 23291001), and Deviation 63's comparisons across the two lists are two-sample. The block is checked against every
  committed list under ``data/joblists/`` (and the day-3 list given): [seed, seed + max(M, masks + 1)) must not overlap.
- **Qubit 79.** Section 3b excludes qubit 79 (native reset 2140 ns) from the dial patches. A day-3 placement whose n60 rung contains an
  excluded qubit is refused (the pinned 23 Sep 16:35Z list does; Deviation 62 re-packages it), unless ``--allow-dial-excluded`` is
  given for a dry check, in which case the list's notes say so and it must not be armed.
- **Budget** by ``gradvar.hardware.estimate_budget`` (model v3, the runner's packing), ``dry_run`` true and the placeholder
  ``preflight_review``: nothing is submitted by this script.
- **Booking (Deviation 63, M4).** The pairs are booked at adoption, funded inside the Section 3b dial line, PI countersignature on
  return. Because a placement passes the live cuts only on the calibration it was built on, this list is generated with the day-3 list
  in the same-day cycle and dispatched in the same IBM properties window, right after day 3, on day 3's placement; it is never
  re-placed. Before dispatch, in that cycle: the pairs' comparators drawn on this placement (``scripts/predict_h7_truncation.py
  --joblist <this list>``), ``scripts/check_comparators.py`` exiting 0, and its own pre-flight review (pre-flight 10). The pairs run
  whatever day 3 shows, except for the pre-stated technical stops: the Section 3b kill rule, Paper 2's H4 refuted before dispatch, and a
  list that cannot be dispatched in that properties window (including a live-check failure without an admissible Deviation 26
  override). After a stop the pairs are reported as not run.

Only this file is written; ``scripts/make_paper1_joblists.py`` and the committed lists are not touched (the re-package track owns them).
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar.hardware import estimate_budget, load_joblist            # noqa: E402

PLACEHOLDER = "TBD: pre-flight review permalink"
DEFAULT_OUT = ROOT / "data" / "joblists" / "paper1" / "dial_truncation_pairs.json"
LIST_NAME = "paper1_dial_truncation_pairs"
BOOKED = ("trunc_full_p0.5_L8", "trunc_l2_p0.5_L8")          # the booked H7 pair (Section 3b 'Truncation arm')
# make_paper1_joblists.seed_for("n60", <role 16>, 8, 0): SEED_BASE 20261001 + 1e6 x rung index 2 + 1e5 x role 16 + 1e4 x depth index 3
SEED_BASE, RUNG_INDEX_N60, ROLE_TRUNC_PAIRS, DEPTH_INDEX_L8 = 20261001, 2, 16, 3
PAIRS_SEED = SEED_BASE + 1_000_000 * RUNG_INDEX_N60 + 100_000 * ROLE_TRUNC_PAIRS + 10_000 * DEPTH_INDEX_L8
try:                                   # Deviation 62's dial exclusion, where the branch carries it; Section 3b's qubit 79 otherwise
    from gradvar.noise import DIAL_EXCLUDE as _DIAL_EXCLUDE        # noqa: E402
    DIAL_EXCLUDED = tuple(int(q) for q in _DIAL_EXCLUDE)
except ImportError:
    DIAL_EXCLUDED = (79,)
DEVIATION = "Deviation 63 (draft, not adopted)"


def _seed_span(entry: dict) -> tuple[int, int]:
    """[seed, seed + max(M, masks + 1)) of a point or probe: its theta seeds and its mask seeds (``mask_lottery``: seed + 1 + m)."""
    s = int(entry["seed"])
    return s, s + max(int(entry.get("M", 1) or 1), int(entry.get("masks", 0) or 0) + 1)


def seed_clashes(probes: list, lists_dir: Path, extra: dict | None = None) -> list:
    """Every committed list entry (points and probes) under ``lists_dir``, and ``extra``, whose seed span overlaps a new probe's."""
    spans = sorted({_seed_span(p) for p in probes})
    out = []
    sources = [(f, None) for f in sorted(lists_dir.rglob("*.json"))] + ([("given day-3 list", extra)] if extra else [])
    for f, jl in sources:
        if jl is None:
            try:
                jl = json.loads(Path(f).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
        if not isinstance(jl, dict):
            continue
        for kind in ("points", "probes"):
            for e in jl.get(kind, []) or []:
                if not isinstance(e, dict) or "seed" not in e:
                    continue
                a, b = _seed_span(e)
                for lo, hi in spans:
                    if a < hi and lo < b:
                        out.append(dict(file=str(Path(f).name) if jl is not extra else f, entry=e.get("id", kind), seed=int(e["seed"]), span=[a, b]))
    return out


def _probe(pid: str, template: dict, p: float, reset_kind: str, purpose: str, truncate_to: int | None, mask_p: float | None) -> dict:
    """One probe in the committed lists' key order (``make_paper1_joblists.dial_probe``), geometry and estimator from the booked pair."""
    pr = dict(id=pid, kind="reset_dial", reset_kind=reset_kind, n=template["n"], patch=template["patch"], edge=template["edge"],
              L=template["L"], k=template["k"], p=p, masks=template["masks"], M=template["M"], shots=template["shots"],
              resilience=template["resilience"], seed=PAIRS_SEED, purpose=purpose)
    if mask_p is not None:
        pr["mask_p"] = mask_p
    pr["unshifted"] = True
    if truncate_to is not None:
        pr["truncate_to"] = int(truncate_to)
    return pr


def build(day3: dict, day3_name: str, allow_dial_excluded: bool = False, lists_dir: Path | None = None) -> dict:
    """The Deviation 63 pairs' list for the day-3 list ``day3`` (read from ``day3_name``)."""
    pl = day3.get("placement") or {}
    if not pl.get("pin_snapshot"):
        raise SystemExit(f"{day3_name}: the placement block has no pin_snapshot; the pairs must be pinned to day 3's snapshot (Deviation 58)")
    probes = {p.get("id"): p for p in day3.get("probes", []) or []}
    missing = [pid for pid in BOOKED if pid not in probes]
    if missing:
        raise SystemExit(f"{day3_name}: not a day-3 list: the booked truncation pair {missing} is missing")
    full, cut = probes[BOOKED[0]], probes[BOOKED[1]]
    keys = ("n", "patch", "edge", "L", "k", "p", "masks", "M", "shots", "resilience", "seed", "reset_kind")
    if any(full.get(k) != cut.get(k) for k in keys) or not full.get("unshifted") or not cut.get("unshifted") or int(cut.get("truncate_to", 0)) != 2:
        raise SystemExit(f"{day3_name}: the booked pair is not a full / l = 2 pair on one point and seed")
    rung_name, rung = next(((name, r) for name, r in (pl.get("rungs") or {}).items()
                            if r.get("patch") == full["patch"] and int(r.get("n", -1)) == int(full["n"])), (None, None))
    if rung is None or rung.get("edge") != full["edge"]:
        raise SystemExit(f"{day3_name}: no rung of the placement block carries the booked pair's patch {full['patch']}, n = {full['n']}, edge {full['edge']}")
    excluded = sorted(set(int(q) for q in rung.get("qubits", [])) & set(DIAL_EXCLUDED))
    if excluded and not allow_dial_excluded:
        raise SystemExit(f"{day3_name}: the {rung_name} rung contains {excluded}, which Section 3b excludes from dial patches (qubit 79: 2140 ns reset); "
                         "generate the pairs from the re-packaged day-3 list (Deviation 62), or pass --allow-dial-excluded for a dry check only")
    tmpl = dict(full)
    A = ("Deviation 63 (draft) A3(a), truncation pair at p = 0.25: {what}; the reset dial p = 0.25 on day 3's n60 rung, L = 8, 100 draws, 256 masks x 64 shots, "
         "resilience 0; RMS over draws of C_mix - C_mix[L-2, L] (Deviation 60 statistic, shot and residual pattern terms subtracted) against its "
         "pre-drawn comparator and above day 3's p = 0.5 RMS(2) (two-sample bootstrap over draws, one-sided 95 percent); own seed block, no draw shared with day 3")
    B = ("Deviation 63 (draft) A3(b), truncation pair on the unital dephasing dial at p = 0.5: {what}; control (b)'s dial (virtual Z with probability "
         "p/2 = 0.25 per qubit per layer, mask_p, then the matched 400 ns delay; t = 0), day 3's n60 rung, L = 8, 100 draws, 256 masks x 64 shots, "
         "resilience 0; RMS(2) against its pre-drawn comparator and above day 3's reset p = 0.5 RMS(2) by the pre-drawn margin (two-sample)")
    new = [
        _probe("trunc_full_p0.25_L8", tmpl, 0.25, "reset", A.format(what="the full L = 8 circuit at theta (unshifted, C_mix)"), None, None),
        _probe("trunc_l2_p0.25_L8", tmpl, 0.25, "reset", A.format(what="the circuit with its first L - 2 = 6 layers deleted, all qubits started in |0>, "
                                                               "the last 2 layers' theta and masks of the full circuit"), 2, None),
        _probe("trunc_full_dephase_p0.5_L8", tmpl, 0.5, "dephase", B.format(what="the full L = 8 circuit at theta (unshifted, C_mix)"), None, 0.25),
        _probe("trunc_l2_dephase_p0.5_L8", tmpl, 0.5, "dephase", B.format(what="the circuit with its first 6 layers deleted, all qubits from |0>, the last "
                                                                  "2 layers' theta and Z masks of the full circuit"), 2, 0.25),
    ]
    clashes = seed_clashes(new, lists_dir or (ROOT / "data" / "joblists"), extra=day3)
    if clashes:
        raise SystemExit(f"seed block {PAIRS_SEED} overlaps committed entries: {clashes[:5]}")
    camp = day3.get("campaign") or {}
    campaign = dict(pre_registration=camp.get("pre_registration"), deviation=DEVIATION, ledger_line="dial:dev63_pairs",
                    budget_model_version=camp.get("budget_model_version"), max_experiments=camp.get("max_experiments"),
                    max_job_param_mb=camp.get("max_job_param_mb"), packing=copy.deepcopy(camp.get("packing")),
                    day="Deviation 63 A3 truncation pairs: booked; generated with the day-3 list in the same-day cycle, dispatched right after day 3 in the same IBM properties window (same placement)",
                    placement_source=day3_name, placement_source_list=day3.get("name"), seed_block=dict(role="trunc_pairs", role_index=ROLE_TRUNC_PAIRS,
                    seed=PAIRS_SEED, span=[PAIRS_SEED, PAIRS_SEED + 257], disjoint_from="every committed list under data/joblists/ and the day-3 list"),
                    dial_excluded_in_rung=excluded)
    jl = dict(name=LIST_NAME, backend=day3.get("backend", "ibm_phoenix"), instance=day3.get("instance", "flex"), dry_run=True,
              rep_delay_probe=bool(day3.get("rep_delay_probe", True)), preflight_review=PLACEHOLDER, notes="",
              layout_check="enforce", placement=copy.deepcopy(pl), campaign=campaign, points=[], probes=new)
    jl["budget"] = estimate_budget(jl)
    b = jl["budget"]
    warn = (f" DRY CHECK ONLY: the {rung_name} rung of this placement contains qubit(s) {excluded}, which Section 3b excludes from dial patches; "
            "this list must not be armed (generate it from the Deviation 62 day-3 list).") if excluded else ""
    jl["notes"] = (
        f"{DEVIATION}, Part A3: two truncation pairs, (a) the reset dial at p = 0.25 and (b) the unital dephasing dial at p = 0.5, each the full L = 8 "
        f"circuit and the circuit cut to its last l = 2 layers (all qubits from |0>), on day 3's n60 rung ({rung['patch']}, n = {rung['n']}, origin "
        f"{tuple(rung['origin'])}, edge {rung['edge']}), 100 draws, 256 masks x 64 shots (16384 executions per circuit), resilience 0: the booked p = 0.5 "
        f"pair's geometry and estimator (Section 3b 'Truncation arm'), with shared theta and shared masks on the kept layers. Placement block copied "
        f"unchanged from {day3_name} ({day3.get('name')}; snapshot {pl.get('snapshot')}, stamp {pl.get('stamp')}, pinned, Deviation 58), so the pairs run "
        f"on day 3's placement. Fresh seed block {PAIRS_SEED} (role trunc_pairs; one seed for the four probes; disjoint from every committed list): no "
        "draw is shared with day 3, and the comparisons with day 3's p = 0.5 pair are two-sample. Section 3b's 'Not run' list names 'p = 0.25 "
        "truncation'; Deviation 63 adds it, and the dephasing pair, before any day-3 datum is read, with its reasons. Booked at adoption (Deviation "
        "63, M4), funded inside the Section 3b dial line, PI countersignature on return. Generated with the day-3 list in the same-day cycle and "
        "dispatched in the same IBM properties window, right after day 3, on day 3's placement; never re-placed. Before dispatch: the pairs' "
        "comparators drawn on this placement (python scripts/predict_h7_truncation.py --joblist <this list>), scripts/check_comparators.py "
        "exiting 0, and this list's own pre-flight review (pre-flight 10). The pairs run whatever day 3 shows, except for the pre-stated "
        "technical stops: the Section 3b kill rule, Paper 2's H4 refuted before dispatch, and a list that cannot be dispatched in that "
        "properties window (a live-check failure without an admissible Deviation 26 override included); after a stop they are reported as "
        "not run. Generated by scripts/make_truncation_pairs.py from the day-3 list; not produced by "
        "scripts/make_paper1_joblists.py. Budget model v"
        f"{b['model_version']} (runner packing): {b['jobs']} jobs, {b['pubs']} pubs, {b['circuits']} parameter sets, {b['executions']} executions, "
        f"{b['minutes_at_1us']} min at the booked 1 us rep_delay ({b['minutes_at_250us']} min at 250 us). Nothing is submitted while dry_run is true "
        "and the pre-flight review permalink is the placeholder." + warn)
    return jl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("day3", help="the day-3 list whose placement the pairs follow (data/joblists/paper1/day3_dial_refs.json)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--allow-dial-excluded", action="store_true", help="dry check on a placement whose n60 rung holds a Section 3b dial-excluded qubit")
    ap.add_argument("--check", action="store_true", help="compare with the file at --out instead of writing (exit 1 on a difference)")
    a = ap.parse_args(argv)
    src = Path(a.day3)
    day3 = json.loads(src.read_text(encoding="utf-8"))
    rel = src.resolve().relative_to(ROOT).as_posix() if src.resolve().is_relative_to(ROOT) else str(src)
    jl = build(day3, rel, allow_dial_excluded=a.allow_dial_excluded)
    out = Path(a.out)
    if a.check:
        same = out.exists() and json.loads(out.read_text(encoding="utf-8")) == jl
        print("matches the generator" if same else f"differs: {out}")
        return 0 if same else 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(jl, indent=1) + "\n", encoding="utf-8")
    load_joblist(str(out))                                   # schema check
    b = jl["budget"]
    print(f"{out.name}: {len(jl['probes'])} probes, {b['jobs']} jobs, {b['pubs']} pubs, {b['circuits']} parameter sets, {b['executions']} exec, "
          f"{b['minutes_at_1us']} min at 1 us / {b['minutes_at_250us']} min at 250 us; seed {PAIRS_SEED}; placement {jl['placement']['stamp']}"
          + (f"; dial-excluded qubits in the rung: {jl['campaign']['dial_excluded_in_rung']} (dry check only)" if jl["campaign"]["dial_excluded_in_rung"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
