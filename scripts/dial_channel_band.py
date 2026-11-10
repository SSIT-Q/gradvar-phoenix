"""Deviation 64 (draft): the dial comparators over a stated range of the dial channel (analysis script, no registered module changed).

    python scripts/dial_channel_band.py entry --joblist <list> --probe <probe id> --channel '{"kN": 0.025}' --out out/x.json
    python scripts/dial_channel_band.py plan <plan.json> --out-dir out [--workers N]          # every task of a plan, one process each
    python scripts/dial_channel_band.py bootstrap --rms-true 0.06 --resid 2.3e-4 --kurtosis 9 --reps 600 --out out/b.json

What it computes. The Deviation 60 comparators (``scripts/predict_h7_truncation.py`` ``realised_entry``, ``scripts/redraw_gate1b.py``
``realised_dial_row``) model the dial as designed: mask bit 0 = an idle with pure T2 dephasing, Bloch (d, d, 1, 0), d = exp(-400 ns / T2);
mask bit 1 = a perfect reset, Bloch (0, 0, 0, 1). This script draws the same quantities, with the same program builder
(``redraw_gate1b.dial_program``), the same realised masks (``redraw_gate1b.probe_masks``) and the same sampler
(``pauliprop.propagate_realised``), for a dial whose two branches differ from that design:

    kept branch   B0 = (d (1 - k), d (1 - k), 1 - gz, gz),   k = kT + kN on the reset dial, k = kT on the dephasing dial
    reset branch  B1 = (r, r, e1 - e0, 1 - e0 - e1)

kT: error of the T2 model of the 400 ns idle (either sign); kN: extra transverse contraction of an idle qubit while neighbours are reset
(reset dial only: ZZ with a decaying neighbour, drive crosstalk); gz: T1 over the idle (D_zz = 1 - gz and the translation gz towards
|0>); e1 / e0: P(1) after a reset of |1> / |0>; r: the transverse residual a reset leaves (complete positivity allows |r| <= sqrt(e1 (1 - e0))).
The dephasing dial's branches are (+-d (1 - kT), +-d (1 - kT), 1 - gz, gz).

How. The registered modules are not edited. ``dial_channel`` replaces, inside this process only, ``pauliprop.dial_bloch_by_qubit`` (the
mixture map the program carries) and ``pauliprop.dial_branches`` (the two branches the realised sampler, the prefix and the cut means
read) by wrappers that return the branches above and their exact mixture; with the all-zero channel nothing is replaced and the code that
runs is the repository's. Mixture values are taken from the realised sampler's own mixture estimate (``*_mix``, the same paths): the
mixture engines (``propagate_truncated`` / ``propagate_sampled``) read the channel's t_z as the reset probability inside the dial-ZZ
rule and would misread a channel whose t_z differs from the lottery probability.

Monte Carlo error. A task runs ``batches`` independent calls of ``propagate_realised`` (seeds seed0 .. seed0 + batches - 1, ``paths``
each); every channel uses the same seeds, so two channels' batches are paired and the error of a difference or ratio between channels is
taken from the paired batch values (``collect``). Batch 0 with seed 0 starts on the repository's sampler stream.

Floors. ``floors_at_channel``: the Deviation 33 floor mode (``gradvar/analysis/floors.py``) with the channel's branch values in place of
the designed ones, mixture and realised. A derivation for the draft, not a registered floor: it needs the exact 2 x 2 two-copy test
before it is used.

Bootstrap. ``bootstrap`` simulates the registered H7 statistic and interval (``dial_hypotheses.truncation_rms``, unmodified) on synthetic
rows; the generating model is stated in ``synthetic_rows``.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np                                                          # noqa: E402

CAL_DIR = ROOT / "data" / "calibrations"
KEEP = ("cost", "kL", "k1", "msd2", "msd4")


@dataclass(frozen=True)
class Channel:
    kT: float = 0.0
    kN: float = 0.0
    gz: float = 0.0
    e1: float = 0.0
    r: float = 0.0
    e0: float = 0.0

    def nominal(self) -> bool:
        return not any(asdict(self).values())

    def check(self) -> None:
        if self.e1 < 0 or self.e0 < 0 or self.gz < 0 or self.e0 + self.e1 > 1:
            raise ValueError(f"channel outside its domain: {self}")
        if self.r ** 2 > self.e1 * (1.0 - self.e0) + 1e-15:
            raise ValueError(f"reset branch not completely positive: r^2 = {self.r ** 2} > e1 (1 - e0) = {self.e1 * (1 - self.e0)}")


def _tuple(b) -> tuple:
    return (float(b.dx), float(b.dy), float(b.dz), float(b.tz))


@contextlib.contextmanager
def dial_channel(ch: Channel):
    """Inside the block the dial of every program built, and the branches the realised code reads, are those of ``ch`` (module
    docstring). The nominal channel leaves the repository code untouched."""
    from gradvar import pauliprop as pp
    ch.check()
    if ch.nominal():
        yield {}
        return
    orig_map, orig_branches = pp.dial_bloch_by_qubit, pp.dial_branches
    reg: dict = {}

    def bloch_by_qubit(csv_path, qubits, kind, p=0.0, idle_ns=pp.T_RESET_NS):
        nominal = orig_map(csv_path, qubits, kind, p, idle_ns)
        if kind not in ("reset", "dephase"):
            return nominal
        out = {}
        for q, b in nominal.items():
            d = float(b.dx) / (1.0 - float(p))                               # the idle's dephasing factor exp(-400 ns / T2)
            k = ch.kT + (ch.kN if kind == "reset" else 0.0)
            b0 = pp.Bloch(d * (1.0 - k), d * (1.0 - k), 1.0 - ch.gz, ch.gz)
            if kind == "reset":
                b1, w = pp.Bloch(ch.r, ch.r, ch.e1 - ch.e0, 1.0 - ch.e0 - ch.e1), float(p)
            else:
                b1, w = pp.Bloch(-b0.dx, -b0.dy, b0.dz, b0.tz), float(p) / 2.0
            mix = pp.Bloch(*[(1.0 - w) * x0 + w * x1 for x0, x1 in zip(_tuple(b0), _tuple(b1))])
            old = reg.get(_tuple(mix))
            if old is not None and (old[0] != kind or _tuple(old[2]) != _tuple(b0) or _tuple(old[3]) != _tuple(b1)):
                raise RuntimeError("two different branch pairs give one mixture: the wrapper cannot tell them apart")
            reg[_tuple(mix)] = (kind, w, b0, b1)
            out[q] = mix
        return out

    def branches(b, kind, p, mask_p):
        hit = reg.get(_tuple(b))
        if hit is None:
            return orig_branches(b, kind, p, mask_p)
        k0, w, b0, b1 = hit
        if k0 != kind or abs(w - float(mask_p)) > 1e-12:
            raise ValueError(f"dial {kind} with lottery probability {mask_p}: the channel was built for {k0}, {w}")
        return b0, b1

    pp.dial_bloch_by_qubit, pp.dial_branches = bloch_by_qubit, branches
    try:
        yield reg
    finally:
        pp.dial_bloch_by_qubit, pp.dial_branches = orig_map, orig_branches


def _kind(pr: dict) -> str:
    rk = str(pr.get("reset_kind", "reset"))
    return "dephase" if rk in ("dephase", "dephasing") else rk


def _rung(jl: dict, pr: dict):
    for name, r in jl["placement"]["rungs"].items():
        if r["patch"] == pr["patch"] and int(r["n"]) == int(pr["n"]):
            return name, r
    raise SystemExit(f"probe {pr['id']}: no rung {pr['patch']} n = {pr['n']} in the list's placement block")


def floors_at_channel(p: float, cal, edge, patch_qubits, ch: Channel, masks_full=None, local=None) -> dict:
    """The Deviation 33 floor mode at a channel. Mixture: N^dagger Z = Dz Z + tz I with Dz = (1 - p)(1 - gz) + p (e1 - e0) and
    tz = (1 - p) gz + p (1 - e0 - e1), so c_i = a_i Dz (a_j tz + b_j), floor_grad = 1/2 c_i^2 g_i^2 tz^2, floor_cost = 1/2 tz^2 (c_i^2 g_i^2 +
    c_j^2 g_j^2) (``floors.dial_floor`` with (1 - p) -> Dz and p -> tz). Realised (``floors.realised_floor``'s mode with every class of
    the three mask bits): per mask A_m = a_i g_i Dz(s_i^L) (a_j tz(s_j^L) + b_j) tz(s_i^{L-1}), Dz(0) = 1 - gz, Dz(1) = e1 - e0, tz(0) = gz,
    tz(1) = 1 - e0 - e1; floor_grad = 1/2 [(sum A)^2 - sum A^2] / (K (K - 1)); the cost floor adds the j mode and subtracts S^2(c0) / K
    with c0_m = (a_i tz(s_i^L) + b_i)(a_j tz(s_j^L) + b_j). The bound needs every A_m of one sign: b >= 0 as before, and e1 >= e0."""
    from gradvar.analysis.floors import dial_floor
    f = dial_floor(p, cal, edge, patch_qubits, resilience=0)
    ai, bi, aj, bj, gi, gj = (f[k] for k in ("a_i", "b_i", "a_j", "b_j", "g_i", "g_j"))
    dz = (1.0 - p) * (1.0 - ch.gz) + p * (ch.e1 - ch.e0)
    tz = (1.0 - p) * ch.gz + p * (1.0 - ch.e0 - ch.e1)
    ci, cj = ai * dz * (aj * tz + bj), aj * dz * (ai * tz + bi)
    out = dict(p=float(p), Dz_mix=dz, tz_mix=tz, floor_grad_mix=0.5 * ci ** 2 * gi ** 2 * tz ** 2,
               floor_cost_mix=0.5 * tz ** 2 * (ci ** 2 * gi ** 2 + cj ** 2 * gj ** 2), floor_grad_mix_designed=f["floor_grad"],
               floor_cost_mix_designed=f["floor_cost"], a_i=ai, b_i=bi, a_j=aj, b_j=bj, g_i=gi, g_j=gj,
               sign_condition=bool(bi >= 0 and bj >= 0 and ch.e1 >= ch.e0))
    if masks_full is not None:
        mk = np.asarray(masks_full, dtype=bool)
        K, L = mk.shape[0], mk.shape[1]
        i, j = local
        dzb, tzb = np.array([1.0 - ch.gz, ch.e1 - ch.e0]), np.array([ch.gz, 1.0 - ch.e0 - ch.e1])
        si, sj = mk[:, L - 1, i].astype(int), mk[:, L - 1, j].astype(int)
        pi, pj = mk[:, L - 2, i].astype(int), mk[:, L - 2, j].astype(int)
        A_i = ai * gi * dzb[si] * (aj * tzb[sj] + bj) * tzb[pi]
        A_j = aj * gj * dzb[sj] * (ai * tzb[si] + bi) * tzb[pj]
        pair = lambda A: float((A.sum() ** 2 - (A ** 2).sum()) / (K * (K - 1)))          # noqa: E731
        c0 = (ai * tzb[si] + bi) * (aj * tzb[sj] + bj)
        spread = float(c0.var(ddof=1) / K)
        out.update(K=int(K), floor_grad_realised=0.5 * pair(A_i), floor_cost_realised=0.5 * (pair(A_i) + pair(A_j)) - spread,
                   c0_spread_over_K=spread, c0_mean=float(c0.mean()))
    return out


def run_entry(joblist: str, probe_id: str, ch: Channel, batches: int, paths: int, seed0: int = 0, out: str | None = None, label: str = "") -> dict:
    """One comparator at one channel on a list probe's realised masks: ``batches`` calls of ``pauliprop.propagate_realised`` on the
    Deviation 46 program of the probe's point (cuts l = 2, 4 for an unshifted truncation probe, none for a gradient probe)."""
    from gradvar import pauliprop as pp
    from gradvar.analysis.floors import Calibration
    import redraw_gate1b as rd
    t0 = time.time()
    jl = json.loads(Path(joblist).read_text(encoding="utf-8"))
    pl = jl["placement"]
    csv, props = str(CAL_DIR / pl["snapshot"]), str(CAL_DIR / pl["properties"])
    pr = next(x for x in jl["probes"] if x["id"] == probe_id)
    kind, L, p = _kind(pr), int(pr["L"]), float(pr["p"])
    rung_name, rung = _rung(jl, pr)
    patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
    mask_p = float(pr.get("mask_p", p))
    cuts = (2, 4) if pr.get("unshifted") else ()
    rec = dict(label=label, joblist=Path(joblist).name, placement=pl.get("stamp"), snapshot=pl["snapshot"], probe=probe_id, kind=kind, p=p, L=L,
               rung=rung_name, n=int(rung["n"]), edge=rung["edge"], mask_seed=int(pr["seed"]), mask_p=mask_p, channel=asdict(ch), nominal=ch.nominal(),
               cuts=list(cuts), batches_planned=int(batches), paths_per_batch=int(paths), seed0=int(seed0), commit=os.environ.get("GRADVAR_COMMIT"),
               sampler="pauliprop.propagate_realised (chunk min(25000, paths)); program redraw_gate1b.dial_program(model='unital', zz_layer_on=True)",
               per_batch=[], complete=False)
    with dial_channel(ch):
        prog, _meta = rd.dial_program(patch, rung["patch"], L, edge, csv, props, model="unital", dial_kind=kind, p=p, zz_layer_on=True)
        masks, full, runner = rd.probe_masks(jl, pr, prog, patch, csv)
        K = int(masks.shape[0])
        c0 = pp.realised_prefix_constants(prog, masks, kind, p=p, mask_p=mask_p)
        rec.update(K=K, n_cone=int(prog.m), c0_mean=float(np.mean(c0)), c0_spread_over_K=float(np.var(c0, ddof=1) / K),
                   dial_on_edge_qubit=list(_tuple(next(b for op in prog.ops if op[0] == "dial_zz" for b in [op[1][prog.i]] if b is not None))))
        if kind == "reset":
            rec["floors"] = floors_at_channel(p, Calibration.from_csv(csv), edge, patch.qubits, ch, full, (runner.local(edge[0]), runner.local(edge[1])))
        for b in range(int(batches)):
            res = pp.propagate_realised(prog, masks, kind, p=p, mask_p=mask_p, n_samples=int(paths), seed=int(seed0) + b,
                                        chunk=min(25_000, int(paths)), cuts=cuts)
            rec["per_batch"].append({k: float(v) for k, v in res.items() if k.split("_")[0] in KEEP and isinstance(v, float)})
            rec["runtime_s"] = time.time() - t0
            if out:
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_text(json.dumps(rec), encoding="utf-8")
    rec["complete"] = True
    rec["runtime_s"] = time.time() - t0
    if out:
        Path(out).write_text(json.dumps(rec), encoding="utf-8")
    return rec


# --------------------------------------------------------------------------- the H7 interval on synthetic rows

def synthetic_rows(rng, rms_true: float, resid: float, kurtosis: float, M: int = 100, K: int = 256, shots: int = 64, p: float = 0.5):
    """One synthetic truncation pair (full and l = 2 rows) for ``dial_hypotheses.truncation_rms``.

    Generating model, stated in full. Per draw d the true mean difference is Delta_d = rms_true x z_d with E z = 0, E z^2 = 1: z Gaussian
    (kurtosis 3) or Student t with nu = 4 + 6 / (kurtosis - 3) degrees of freedom scaled to unit variance (kurtosis 9: nu = 5, the
    convention of scripts/h6_control_bounds_sim.py; kurtosis 4: nu = 10). A fixed set of round(p^2 K) masks has both observable qubits
    reset in the last layer: there both circuits return the same value, 0.97, and the per-mask difference is exactly zero. On the other
    K' masks the truncated circuit's value is N(0, 0.30^2) clipped to +-0.60 and the per-mask difference is Delta_d K / K' + eta, eta
    Gaussian with the variance that makes E_d Var_m(difference) = K x resid (``resid`` = the engine's residual_pattern_expected,
    (MSD_diag - MSD_off) / K); the full circuit's value is clipped to +-1 (rare at these levels: a first version with wider levels
    clipped about one value in ten and biased the generated truth low by 8 percent; it was discarded). Each value is then measured with
    ``shots`` +-1 outcomes (binomial). At these levels the shot term of the mean difference is about 8.3e-5 (``_mask_replicates`` quotes
    about 6.7e-5 for the day-3 design, so the synthetic rows are slightly noisier). Returns the two row tables and the sample truth, the
    mean over draws of mean_m(delta)^2 - Var_m(delta) / K on the generated true values delta (what the statistic estimates on this
    sample before shot noise)."""
    import pandas as pd
    if kurtosis <= 3.0:
        z = rng.standard_normal(M)
    else:
        nu = 4.0 + 6.0 / (kurtosis - 3.0)
        z = rng.standard_t(nu, M) / np.sqrt(nu / (nu - 2.0))
    delta = rms_true * z
    n_rr = int(round(p * p * K))
    kp = K - n_rr
    between = (n_rr / K) * (kp / K) * (K / kp) ** 2 * rms_true ** 2            # E_d of the between-class variance of the per-mask difference
    var_eta = max((K * resid - between) * K / kp, 0.0)
    ev_t = np.empty((M, K))
    ev_t[:, :n_rr] = 0.97
    ev_t[:, n_rr:] = np.clip(rng.normal(0.0, 0.30, (M, kp)), -0.60, 0.60)
    diff = np.zeros((M, K))
    diff[:, n_rr:] = delta[:, None] * K / kp + rng.normal(0.0, np.sqrt(var_eta), (M, kp))
    ev_f = np.clip(ev_t + diff, -1.0, 1.0)
    meas = lambda e: 2.0 * rng.binomial(shots, (1.0 + e) / 2.0) / shots - 1.0      # noqa: E731
    d_idx, m_idx = np.repeat(np.arange(M), K), np.tile(np.arange(K), M)
    base = dict(draw=d_idx, mask_index=m_idx, shots=shots, seed=1, mask_seed=m_idx + 2)
    return pd.DataFrame(dict(base, ev=meas(ev_f).reshape(-1))), pd.DataFrame(dict(base, ev=meas(ev_t).reshape(-1))), float(np.mean((ev_f - ev_t).mean(axis=1) ** 2 - (ev_f - ev_t).var(axis=1, ddof=1) / K))


def run_bootstrap(rms_true: float, resid: float, kurtosis: float, reps: int, seed: int, out: str | None = None, label: str = "",
                  M: int = 100, K: int = 256, shots: int = 64, n_boot: int = 10_000) -> dict:
    """``reps`` synthetic day-3 truncation pairs through the registered statistic and interval (``truncation_rms``, its defaults)."""
    from gradvar.analysis import dial_hypotheses as DH
    t0 = time.time()
    rec = dict(label=label, rms_true=float(rms_true), resid=float(resid), kurtosis_generating=float(kurtosis), M=M, K=K, shots=shots, n_boot=n_boot,
               n_mask_replicates=DH.N_MASK_REPLICATES, seed=int(seed), estimator="gradvar.analysis.dial_hypotheses.truncation_rms (unmodified)",
               commit=os.environ.get("GRADVAR_COMMIT"), rms=[], lo=[], hi=[], kurtosis_y=[], sample_truth_ms=[], shot_term=[], complete=False)
    for i in range(int(reps)):
        rng = np.random.default_rng([int(seed), i])
        full, trunc, ms = synthetic_rows(rng, rms_true, resid, kurtosis, M, K, shots)
        s = DH.truncation_rms(full, trunc, K, n_boot)
        rec["shot_term"].append(s["shot_term"]); rec["rms"].append(s["rms"]); rec["lo"].append(s["rms_lo"]); rec["hi"].append(s["rms_hi"]); rec["kurtosis_y"].append(s["kurtosis"])
        rec["sample_truth_ms"].append(ms)
        if out and (i % 25 == 24 or i == int(reps) - 1):
            rec["runtime_s"] = time.time() - t0
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps(rec), encoding="utf-8")
    rec["complete"] = True
    rec["runtime_s"] = time.time() - t0
    if out:
        Path(out).write_text(json.dumps(rec), encoding="utf-8")
    return rec


# --------------------------------------------------------------------------- plan runner

def _run_task(task: dict) -> tuple:
    t0 = time.time()
    try:
        if task["type"] == "entry":
            run_entry(task["joblist"], task["probe"], Channel(**task.get("channel", {})), task["batches"], task["paths"], task.get("seed0", 0),
                      out=task["out"], label=task["name"])
        elif task["type"] == "bootstrap":
            run_bootstrap(task["rms_true"], task["resid"], task["kurtosis"], task["reps"], task.get("seed", 0), out=task["out"], label=task["name"])
        else:
            raise ValueError(task["type"])
        return task["name"], "ok", time.time() - t0
    except Exception as ex:                                                  # a failed task must not lose the others' results
        import traceback
        Path(task["out"] + ".error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return task["name"], f"error: {ex}", time.time() - t0


def run_plan(plan_path: str, out_dir: str, workers: int | None) -> int:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    od = Path(out_dir)
    od.mkdir(parents=True, exist_ok=True)
    tasks = [dict(t, out=str(od / f"{t['name']}.json")) for t in plan["tasks"]]
    t0, log = time.time(), []
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as ex:
        for fut in as_completed([ex.submit(_run_task, t) for t in tasks]):
            name, status, dt = fut.result()
            log.append(dict(name=name, status=status, seconds=round(dt, 1), at=round(time.time() - t0, 1)))
            print(f"{name}: {status} ({dt:.0f} s; t = {time.time() - t0:.0f} s)", flush=True)
            (od / "_plan_log.json").write_text(json.dumps(dict(plan=Path(plan_path).name, commit=os.environ.get("GRADVAR_COMMIT"), log=log)), encoding="utf-8")
    return 0 if all(x["status"] == "ok" for x in log) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("entry")
    e.add_argument("--joblist", required=True); e.add_argument("--probe", required=True); e.add_argument("--channel", default="{}")
    e.add_argument("--batches", type=int, default=16); e.add_argument("--paths", type=int, default=125_000); e.add_argument("--seed0", type=int, default=0)
    e.add_argument("--out", required=True)
    pl = sub.add_parser("plan")
    pl.add_argument("plan"); pl.add_argument("--out-dir", default="out"); pl.add_argument("--workers", type=int, default=None)
    b = sub.add_parser("bootstrap")
    b.add_argument("--rms-true", type=float, required=True); b.add_argument("--resid", type=float, required=True)
    b.add_argument("--kurtosis", type=float, default=3.0); b.add_argument("--reps", type=int, default=100); b.add_argument("--seed", type=int, default=0)
    b.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "entry":
        r = run_entry(a.joblist, a.probe, Channel(**json.loads(a.channel)), a.batches, a.paths, a.seed0, out=a.out)
        print(json.dumps({k: r[k] for k in ("probe", "channel", "K", "n_cone", "runtime_s")}))
        return 0
    if a.cmd == "plan":
        return run_plan(a.plan, a.out_dir, a.workers)
    r = run_bootstrap(a.rms_true, a.resid, a.kurtosis, a.reps, a.seed, out=a.out)
    print(json.dumps(dict(reps=len(r["rms"]), rms_median=float(np.median(r["rms"])), runtime_s=r["runtime_s"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
