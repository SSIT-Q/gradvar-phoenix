"""Both-idle time per coupler and layer for the static ZZ model (Deviation 34).

python scripts/zz_layer_timing.py            # writes data/predictions/zz_layer_timing.json

Schedules (ASAP, per-qubit chains, barriers align every qubit) (i) the transpiled ISA circuits of the list 02 dry run
(4x5 patch: grid L = 2 and L = 8, the reset-dial and delay-matched probes at L = 8) and (ii) the transpiled cone circuits
of every ladder patch at L = 8, with the ibm_phoenix target durations of the placements snapshot (per-edge cz gate_length,
sx 40 ns, rz 0, per-qubit reset, delay as instructed). For each coupler (a, b) of the patch and each layer (segment
between barriers) the ZZ-active time is the layer time during which neither end is inside a 1q gate and the pair is not
inside its own CZ; time inside a CZ on a neighbouring pair counts as active for this pair (the neighbour's CZ does not
cancel the a-b coupling). The dial slot (reset / delay(400 ns)) is reported separately: it is active only when both ends
idle (mask-conditional), so it stays the conditional idle term of the dial model.
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from qiskit import qpy, transpile

from gradvar import noise
from gradvar.circuits import hea_observable, hea_on_qubits, light_cone
from gradvar.pauliprop import cone_couplers

ROOT = Path(__file__).resolve().parents[1]
PLACEMENTS = ROOT / "data" / "predictions" / "ladder_placements.json"
OUT = ROOT / "data" / "predictions" / "zz_layer_timing.json"
SX_NS, RZ_NS = 40.0, 0.0


def durations_from_properties(props: dict):
    cz, reset = {}, {}
    for g in props["gates"]:
        for p in g["parameters"]:
            if p["name"] == "gate_length":
                if g["gate"] == "cz":
                    cz[tuple(g["qubits"])] = float(p["value"])
                elif g["gate"] == "reset":
                    reset[int(g["qubits"][0])] = float(p["value"])
    return cz, reset


def schedule(circ, phys, cz_dur, reset_dur):
    """ASAP schedule. ``phys(qubit_index) -> physical qubit``. Returns (intervals, layer_bounds): intervals = list of
    (start_ns, end_ns, kind, physical qubits); layer_bounds = [(start, end)] between barriers (a layer ends at the barrier
    time = max finish of every qubit, the last one at the last gate)."""
    free = defaultdict(float)
    intervals, bounds = [], []
    t_layer0 = 0.0
    for inst in circ.data:
        name = inst.operation.name
        qs = [phys(circ.find_bit(q).index) for q in inst.qubits]
        if name == "barrier":
            t = max(free.values()) if free else 0.0
            for q in list(free):
                free[q] = t
            bounds.append((t_layer0, t))
            t_layer0 = t
            continue
        if name == "cz":
            d = cz_dur.get((qs[0], qs[1]), cz_dur.get((qs[1], qs[0])))
        elif name == "sx" or name == "x":
            d = SX_NS
        elif name == "rz":
            d = RZ_NS
        elif name == "reset":
            d = reset_dur.get(qs[0], 400.0)
        elif name == "delay":
            d = float(inst.operation.duration) * ({"ns": 1.0, "us": 1e3, "dt": 4.0, "s": 1e9}[inst.operation.unit])
        elif name == "measure":
            d = 1940.0
        else:
            raise RuntimeError(name)
        start = max(free[q] for q in qs)
        for q in qs:
            free[q] = start + d
        if d > 0:
            intervals.append((start, start + d, name, tuple(qs)))
    t_end = max(free.values())
    bounds.append((t_layer0, t_end))
    return intervals, bounds


def coupler_active_time(intervals, bounds, couplers):
    """Per layer, per coupler: both-idle time (layer length minus 1q-gate time on a or b minus the pair's own CZ), and
    separately the dial-slot time (reset / delay on a or b) which is excluded from the static term."""
    out = []
    for (t0, t1) in bounds:
        rec = {}
        for (a, b) in couplers:
            busy = []      # intervals during which the static ZZ of (a, b) is not accrued
            slot = []
            for (s, e, kind, qs) in intervals:
                s_, e_ = max(s, t0), min(e, t1)
                if e_ <= s_:
                    continue
                if kind in ("sx", "x", "rz") and (a in qs or b in qs):
                    busy.append((s_, e_))
                elif kind == "cz" and set(qs) == {a, b}:
                    busy.append((s_, e_))
                elif kind in ("reset", "delay") and (a in qs or b in qs):
                    slot.append((s_, e_))
            def measure(iv):
                iv = sorted(iv)
                tot, cur = 0.0, None
                for s, e in iv:
                    if cur is None or s > cur[1]:
                        if cur:
                            tot += cur[1] - cur[0]
                        cur = [s, e]
                    else:
                        cur[1] = max(cur[1], e)
                if cur:
                    tot += cur[1] - cur[0]
                return tot
            m_busy, m_slot = measure(busy), measure(slot)
            rec[f"{a}_{b}"] = dict(layer_ns=t1 - t0, busy_1q_or_own_cz_ns=m_busy, dial_slot_ns=m_slot, static_zz_ns=(t1 - t0) - m_busy - m_slot)
        out.append(rec)
    return out


def summarize(layers):
    vals = np.array([[v["static_zz_ns"] for v in lay.values()] for lay in layers])
    return dict(n_layers=len(layers), layer_ns=[float(next(iter(l.values()))["layer_ns"]) for l in layers],
                static_zz_ns_median=float(np.median(vals)), static_zz_ns_min=float(vals.min()), static_zz_ns_max=float(vals.max()),
                static_zz_ns_per_coupler_layer_mean={k: float(np.mean([l[k]["static_zz_ns"] for l in layers])) for k in layers[0]},
                dial_slot_ns_median=float(np.median([[v["dial_slot_ns"] for v in l.values()] for l in layers])))


def main():
    pl = json.loads(PLACEMENTS.read_text())
    props = noise.load_properties(ROOT / "data" / "calibrations" / pl["properties"])
    cz_dur, reset_dur = durations_from_properties(props)
    out = dict(properties=pl["properties"], durations_ns=dict(sx=SX_NS, rz=RZ_NS, cz_median=float(np.median(list(cz_dur.values()))),
               cz_values=sorted(set(cz_dur.values())), reset_median=float(np.median(list(reset_dur.values()))), delay_dial=400.0),
               rule=("ASAP schedule with the target durations; per layer (barrier to barrier) and coupler (a, b): static ZZ time = layer length "
                     "- time a or b is inside a 1q gate (sx 40 ns; rz 0) - time inside the pair's own CZ; time inside a CZ on a "
                     "neighbouring pair counts as ZZ-active; the dial slot (reset / delay 400 ns) is excluded from the static term and "
                     "kept as the mask-conditional idle term"),
               dry_run={}, ladder={})
    # (i) dry-run ISA circuits
    scratch = Path("/tmp/claude-0/-workspace/7097aca5-2811-5a07-966b-147d13c851bc/scratchpad/dryrun_out/02/runs/2026-09-19")
    for d, label in (("dryrun-20260919T185443Z-L0", "grid"), ("dryrun-20260919T185443Z-L1-probes-s64", "dial")):
        path = scratch / d / "circuits.qpy"
        if not path.exists():
            continue
        with open(path, "rb") as f:
            cs = qpy.load(f)
        meta = json.loads((scratch / d / "circuits.json").read_text())
        seen = set()
        for c, mt in zip(cs, meta):
            key = (mt["L"], mt.get("probe_id"))
            if key in seen:
                continue
            seen.add(key)
            qs = sorted({c.find_bit(q).index for inst in c.data for q in inst.qubits if inst.operation.name != "barrier"})
            patch_q = pl["patches"]["4x5"]["qubits"]
            assert set(qs) <= set(patch_q), (qs, patch_q)
            couplers = [tuple(e) for e in pl["patches"]["4x5"]["edges"]]
            intervals, bounds = schedule(c, lambda i: i, cz_dur, reset_dur)
            layers = coupler_active_time(intervals, bounds, couplers)
            out["dry_run"][f"4x5 L={mt['L']} {mt.get('probe_id') or label}"] = dict(circuit=c.name, ops=dict(c.count_ops()), **summarize(layers))
    # (ii) ladder patches, cone circuits at L = 8
    for spec, pt in pl["patches"].items():
        from gradvar.lattice import Patch
        r, cc = (int(x) for x in spec.split("x"))
        patch = Patch(qubits=tuple(pt["qubits"]), n_rows=r, n_cols=cc, origin=tuple(pt["origin"]), holes=tuple(pt["holes"]),
                      broken_edges=tuple(tuple(e) for e in pt["broken_edges"]))
        _, edge = hea_observable(patch)
        cone = light_cone(patch, 8, edge)
        qc = hea_on_qubits(patch, 8, cone)
        qc = qc.assign_parameters(np.zeros(qc.num_parameters))
        isa = transpile(qc, basis_gates=["rz", "sx", "cz"], optimization_level=0)
        couplers = cone_couplers(patch, cone)
        intervals, bounds = schedule(isa, lambda i: cone[i], cz_dur, reset_dur)
        layers = coupler_active_time(intervals, bounds, couplers)
        sm = summarize(layers)
        out["ladder"][spec] = dict(n=patch.n, cone=len(cone), n_couplers=len(couplers), ops=dict(isa.count_ops()), **sm)
        print(spec, "layers", sm["n_layers"], "layer ns", sorted(set(sm["layer_ns"])), "static ZZ ns median", sm["static_zz_ns_median"],
              "min/max", sm["static_zz_ns_min"], sm["static_zz_ns_max"], flush=True)
    for k, v in out["dry_run"].items():
        print(k, "layers", v["n_layers"], "layer ns", sorted(set(v["layer_ns"])), "static ZZ ns median", v["static_zz_ns_median"],
              "min/max", v["static_zz_ns_min"], v["static_zz_ns_max"], "dial slot ns", v["dial_slot_ns_median"])
    med = [v["static_zz_ns_median"] for v in out["ladder"].values()]
    out["tau_grid_ns_median_over_ladder"] = float(np.median(med))
    out["tau_dial_conditional_ns"] = 400.0
    out["note"] = ("tau_grid is the static, unconditional ZZ time per layer for every coupler of the cone (per-coupler values in "
                   "static_zz_ns_per_coupler_layer_mean; used by gate1_pauliprop.py --zz layer); tau_dial = 400 ns is the additional "
                   "mask-conditional idle term of the dial layer (both ends idle). Deviation 24's 0.71 us per layer is the budget formula's "
                   "circuit-length coefficient, not the ZZ-active time.")
    OUT.write_text(json.dumps(out, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
