"""Synthetic day-3 runs for ``scripts/exploratory_screen.py`` (never an analysis input): for its tests, and for the synthetic
null and injected-effect runs of the plan's Section 4 item 8 (d) and (e) (``scripts/exploratory_screen_calibration.py``). The
screen's own T8 reference uses the same cell model (``exploratory_screen.synthetic_gradients``). The day-3 design
(reset dial, dephasing dial, delay-matched references, truncation pair, characterisation probes) with planted second moments,
either as the screen's in-memory ``Inputs`` (fast: the false-positive tests) or written in the stored format the registered
loader reads (the runner's CSV log, one row per circuit pair, and per-job bundles with the Deviation 48 mask pubs), with the
prediction and calibration files beside it.

Cell model of a gradient probe with K masks shared by all M draws: the expectation values of the two shift circuits of draw d
and mask m are c0_m + H_dm +/- G_dm, with c0_m the readout-folded constant of the mask's last-layer class (the registered
E[C_mix] folding), H_dm = eta_m (sqrt(tau_c) x_d + sqrt(delta_c) y_dm) and G_dm = gamma_m (sqrt(tau) u_d + sqrt(delta) v_dm);
gamma_m is 0 when the dial acts on the differentiated qubit in the last layer of a reset-dial mask and 1 otherwise, u_d is
heavy-tailed and bounded (zero with probability 1 - pi_u and uniform otherwise, scaled to unit variance: kurtosis 1.8 / pi_u;
probes of one seed share u_d and x_d, as they share theta), x_d uniform (kurtosis 1.8), v and y Rademacher, so no expectation
value leaves [-1, 1] and none is clipped. With ``draw_kurtosis`` every per-draw amplitude (u_d, x_d and the draw amplitude of
the truncation difference) takes the heavy-tailed form at that kurtosis instead. The planted truths follow exactly: the off-diagonal moment the shared-mask estimator estimates is
T_g = tau (S1^2 - S2) / (K (K - 1)) with S1 = sum gamma, S2 = sum gamma^2; the pattern floor (D_g - T_g) / K with D_g = (tau +
delta) S2 / K; Var[C_mix] = T_c + T_g - S^2(c0) / K; E[C_mix] = mean c0. Stored values are binomial at the booked shots, with
the reported standard error sqrt((1 - ev^2) / shots).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES                         # noqa: E402
from gradvar.lattice import interior_edge, rect_patch   # noqa: E402

T0 = datetime(2026, 11, 12, 6, 0, 0, tzinfo=timezone.utc)
STAMP = "2026-11-12T050000Z"
SNAPSHOT = f"ibm_phoenix_{STAMP}.csv"
TAG = "2026-11-12T0500"
BACKEND = "ibm_phoenix"
PATCHES = {"4x10": (4, 10, (8, 0)), "6x10": (6, 10, (3, 0)), "10x10": (10, 10, (1, 0))}
_MASKS: Dict[tuple, np.ndarray] = {}


def _patch(spec: str):
    r, c, origin = PATCHES[spec]
    return rect_patch(r, c, exclude=(), origin=origin)


def lottery_masks(seed: int, K: int, L: int, n: int, q: float) -> np.ndarray:
    key = (int(seed), int(K), int(L), int(n), float(q))
    if key not in _MASKS:
        _MASKS[key] = np.stack([np.random.default_rng([int(seed) + 1 + m, ES.MASK_STREAM]).random((L, n)) < q for m in range(K)])
    return _MASKS[key]


# ------------------------------------------------------------------------------------------------ device and calibration sets

def device(seed: int = 11) -> dict:
    """True per-qubit readout (p01 = P(1|0), p10 = P(0|1)), reset error, T1, T2 and per-coupler CZ error and ZZ of the synthetic device."""
    rng = np.random.default_rng(seed)
    q = np.arange(120)
    p01, p10 = rng.uniform(0.003, 0.010, 120), rng.uniform(0.008, 0.020, 120)
    cz, zz = {}, {}
    for a in q:
        for b in (a + 1, a + 10):
            if b < 120 and not (b == a + 1 and a % 10 == 9):
                cz[(int(a), int(b))] = float(rng.uniform(1e-3, 3e-3))
                zz[(int(a), int(b))] = float(rng.uniform(1e-5, 6e-5))
    return dict(p01=p01, p10=p10, eps=rng.uniform(5e-4, 4e-3, 120), T1=rng.uniform(80, 250, 120), T2=rng.uniform(40, 200, 120),
                sx=rng.uniform(1e-4, 4e-4, 120), init=rng.uniform(1e-5, 5e-5, 120), cz=cz, zz=zz)


def properties(dev: dict, when: datetime, readout_scale: Optional[Dict[int, float]] = None, t1_scale: float = 1.0) -> dict:
    """A properties set in the raw backend format (``qubits`` / ``gates`` / ``general``), dated ``when``."""
    date = when.strftime("%Y-%m-%d %H:%M:%S+00:00")
    qubits, gates, general = [], [], []
    for i in range(120):
        s = (readout_scale or {}).get(i, 1.0)
        p01, p10 = float(dev["p01"][i]) * s, float(dev["p10"][i]) * s
        qubits.append([dict(date=date, name="T1", unit="us", value=float(dev["T1"][i]) * t1_scale), dict(date=date, name="T2", unit="us", value=float(dev["T2"][i])),
                       dict(date=date, name="readout_error", unit="", value=(p01 + p10) / 2), dict(date=date, name="init_error", unit="", value=float(dev["init"][i])),
                       dict(date=date, name="prob_meas0_prep1", unit="", value=p10), dict(date=date, name="prob_meas1_prep0", unit="", value=p01)])
        gates.append(dict(qubits=[i], gate="sx", parameters=[dict(date=date, name="gate_error", unit="", value=float(dev["sx"][i]))], name=f"sx{i}"))
    for (a, b), e in dev["cz"].items():
        gates.append(dict(qubits=[a, b], gate="cz", parameters=[dict(date=date, name="gate_error", unit="", value=e)], name=f"cz{a}_{b}"))
        general.append(dict(date=date, name=f"zz_{a}{b}", unit="GHz", value=dev["zz"][(a, b)]))
    return dict(backend_name=BACKEND, backend_version="1.0.0", last_update_date=date, qubits=qubits, gates=gates, general=general)


_PARSED: Dict[int, list] = {}


def _parsed_sets(dev: dict, cal_dicts: List[dict]) -> list:
    if id(dev) not in _PARSED:
        _PARSED[id(dev)] = [ES.parse_properties(d, f"set{i}") for i, d in enumerate(cal_dicts)]
    return _PARSED[id(dev)]


_DEVICE: Dict[int, tuple] = {}


def default_device() -> tuple:
    """(device, its calibration timeline), built once."""
    if 0 not in _DEVICE:
        dev = device()
        _DEVICE[0] = (dev, calibration_timeline(dev))
    return _DEVICE[0]


def calibration_timeline(dev: dict) -> List[dict]:
    """Four committed sets: one 9 h before the run, a change of some readout values 1.5 h before, a re-stamp of that set with the
    same values 0.5 h before (not a change), and a change during the run (T1 values, and qubit 45's readout over the runner cut)."""
    a = properties(dev, T0 - timedelta(hours=9))
    b = properties(dev, T0 - timedelta(hours=1.5), readout_scale={q: 1.15 for q in range(30, 60)})
    b2 = properties(dev, T0 - timedelta(hours=0.5), readout_scale={q: 1.15 for q in range(30, 60)})
    c = properties(dev, T0 + timedelta(hours=0.4), readout_scale={**{q: 1.15 for q in range(30, 60)}, 45: 4.0}, t1_scale=0.9)
    return [a, b, b2, c]


# ------------------------------------------------------------------------------------------------ design

@dataclass
class Spec:
    probe_id: str
    arm: str
    p: float
    patch: str
    L: int
    seed: int
    K: int
    M: int
    shots: int
    T: float                      # planted floor-subtracted k = L variance (off-diagonal moment)
    pf: float = 0.0               # planted pattern floor on the gradient
    tau_c: float = 0.0            # cost fluctuation shared by the masks
    delta_c: float = 0.0          # cost fluctuation per mask
    pi_u: float = 0.5             # kurtosis of the gradient draws = 1.8 / pi_u
    kind: str = "gradient"
    ell: Optional[int] = None
    msd: float = 0.0              # truncation pair: planted MSD(l)
    nu: float = 0.0
    rel_sigma: float = 0.005      # relative sampling error of the prediction file

    @property
    def group(self) -> str:
        return "D" if self.kind == "cost" else {"reset": "A", "dephase": "B", "delay": "C"}[self.arm]

    @property
    def mask_p(self) -> float:
        return self.p / 2.0 if self.arm == "dephase" else (1.0 if self.arm == "delay" else self.p)


def day3_specs(M: int = 100, K: int = 256, M_ref: int = 350) -> List[Spec]:
    """The 15 gradient and cost probes of the day-3 list (``data/joblists/paper1/day3_dial_refs.json``) with the list's seeds;
    planted values of the size of the committed predictions (the pattern floor scales as 1 / K)."""
    s = []
    for rung, patch, sd, T8, T12 in (("n40", "4x10", 22191001, 3.3e-4, 1.1e-5), ("n60", "6x10", 23191001, 2.9e-4, 8.0e-6), ("n100", "10x10", 25191001, 6.0e-4, 3.1e-5)):
        s.append(Spec(f"ref_p0_delay_L8_kL_{rung}", "delay", 0.0, patch, 8, sd, 1, M_ref, 16384, T8, tau_c=T8, pi_u=0.13, rel_sigma=0.03))
        s.append(Spec(f"ref_p0_delay_L12_kL_{rung}", "delay", 0.0, patch, 12, sd + 10000, 1, M_ref, 16384, T12, tau_c=T12, pi_u=0.13, rel_sigma=0.05))
    a25 = dict(T=2.0e-3, pf=2.1e-4 * 256 / K, tau_c=3.5e-3, delta_c=0.04, pi_u=0.4)
    a50 = dict(T=4.0e-3, pf=1.2e-4 * 256 / K, tau_c=4.0e-3, delta_c=0.01, pi_u=0.4)
    s.append(Spec("dial_p0.25_L8_kL", "reset", 0.25, "6x10", 8, 22991001, K, M, 16, **a25))
    s.append(Spec("dial_p0.5_L8_kL", "reset", 0.5, "6x10", 8, 22991001, K, M, 16, **a50))
    s.append(Spec("dial_p0.25_L12_kL", "reset", 0.25, "6x10", 12, 23001001, K, M, 16, **a25))
    s.append(Spec("dial_p0.5_L12_kL", "reset", 0.5, "6x10", 12, 23001001, K, M, 16, **a50))
    s.append(Spec("dial_p0.25_L8_kL_n40", "reset", 0.25, "4x10", 8, 21991001, K, M, 16, **a25))
    s.append(Spec("dial_p0.25_L8_kL_n100", "reset", 0.25, "10x10", 8, 24991001, K, M, 16, **a25))
    s.append(Spec("dephasing_dial_p0.5_L8_kL", "dephase", 0.5, "6x10", 8, 22991001, K, M, 16, T=1.7e-5, pf=1.0e-6 * 256 / K, tau_c=1.0e-5, delta_c=2.0e-4, pi_u=0.4, rel_sigma=0.06))
    s.append(Spec("trunc_full_p0.5_L8", "reset", 0.5, "6x10", 8, 23291001, K, M, 64, T=0.0, tau_c=4.0e-3, delta_c=0.01, kind="cost", ell=0))
    s.append(Spec("trunc_l2_p0.5_L8", "reset", 0.5, "6x10", 8, 23291001, K, M, 64, T=0.0, tau_c=4.0e-3, delta_c=0.01, kind="cost", ell=2, msd=1.85e-3, nu=0.01, rel_sigma=0.004))
    return s


@dataclass
class Planted:
    """Effects planted on top of the null: ``mask_factor`` {probe id: (mask indices, factor on gamma)}; ``size_beta``: every
    gradient probe's variance times (n / 60)^beta; ``drift``: the gradient amplitude of a mask times 1 + drift x (its job's
    running time, scaled to -0.5 .. 0.5 over the probe's jobs); ``variance_factor`` and ``variance_drift``: the injected effects
    of the plan's item 8 (e) on one probe."""
    mask_factor: Dict[str, tuple] = field(default_factory=dict)
    size_beta: float = 0.0
    drift: float = 0.0
    variance_factor: Dict[str, float] = field(default_factory=dict)      # item 8 (e): {probe id: factor on its k = L variance (the part shared by the masks)}
    variance_drift: Dict[str, float] = field(default_factory=dict)       # item 8 (e): {probe id: relative change of its k = L variance from its first to its last job}


@dataclass
class Synthetic:
    specs: List[Spec]
    inputs: "ES.Inputs"
    truth: Dict[tuple, float]
    dev: dict
    cal_dicts: List[dict]
    char: Dict[str, np.ndarray]         # characterisation probes: P(1) per qubit of the 6x10 patch
    char_qubits: List[int]
    job_order: List[str]
    pred_sigma: Dict[tuple, float]


def _stable(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:7], 16)


def _heavy(rng, n: int, pi: float) -> np.ndarray:
    return rng.binomial(1, pi, n) * rng.uniform(-np.sqrt(3), np.sqrt(3), n) / np.sqrt(pi)


def _binom(rng, e: np.ndarray, shots: int):
    if np.abs(e).max() > 1.0 + 1e-12:
        raise ValueError("a planted expectation value leaves [-1, 1] (%.3f): lower the amplitudes of the design" % float(np.abs(e).max()))
    ev = 2.0 * rng.binomial(shots, (1.0 + np.clip(e, -1, 1)) / 2.0) / shots - 1.0
    return ev, np.sqrt(np.clip(1.0 - ev ** 2, 0, None) / shots)


def generate(seed: int = 0, specs: Optional[List[Spec]] = None, planted: Optional[Planted] = None, pubs_per_job: int = 19, dev: Optional[dict] = None,
             with_calibration: bool = True, refs_per_job: int = 4, with_kurtosis: bool = True, deviation65: bool = False,
             draw_kurtosis: Optional[float] = None) -> Synthetic:
    """One synthetic day-3 run as the screen's ``Inputs`` (and everything ``write`` needs to store it). ``draw_kurtosis``: the
    kurtosis of every per-draw amplitude (gradient, cost and truncation difference; at least 1.8), in place of the design's own
    (1.8 / pi_u for the gradient draws, uniform cost draws)."""
    if draw_kurtosis is not None and not draw_kurtosis >= 1.8:
        raise ValueError("draw_kurtosis must be at least 1.8 (the uniform draw)")
    specs = specs if specs is not None else day3_specs()
    planted = planted or Planted()
    dev, cal_dicts = (dev, calibration_timeline(dev)) if dev is not None else default_device()
    rng = np.random.default_rng([20261199, int(seed)])
    parsed = _parsed_sets(dev, cal_dicts)
    calsets = ES.distinct_sets(parsed) if with_calibration else []
    # jobs: the characterisation job, the references two pubs per job, then every probe's masks in order, pubs_per_job per job
    jobs: Dict[str, dict] = {}
    order: List[str] = []
    mask_jobs: Dict[str, np.ndarray] = {}
    clock = T0 + timedelta(seconds=300)

    def add_job(jid: str, created: datetime, seconds: float):
        nonlocal clock
        k = max(i for i, d in enumerate(cal_dicts) if ES.parse_time(d["last_update_date"]) <= created)
        jobs[jid] = dict(created=created, running=clock, finished=clock + timedelta(seconds=seconds), cuts=dict(readout_cut=0.03, cz_cut=5e-3, init_error_cut=5e-4),
                         own_set=parsed[k] if with_calibration else None, status="completed", _own=cal_dicts[k])
        order.append(jid)
        clock = clock + timedelta(seconds=seconds + float(rng.uniform(1, 6)))

    add_job("syn-char", T0, 20)
    refs = [s for s in specs if s.arm == "delay"]
    mask_pos: Dict[str, np.ndarray] = {}
    for i in range(0, len(refs), refs_per_job):
        jid = f"syn-ref-{i // refs_per_job:02d}"
        add_job(jid, T0 + timedelta(seconds=5), 60)
        for k, s in enumerate(refs[i:i + refs_per_job]):
            mask_jobs[s.probe_id] = np.array([jid], dtype=object)
            mask_pos[s.probe_id] = np.array([float(k)])
    for s in [x for x in specs if x.arm != "delay"]:
        ids = []
        for c in range(0, s.K, pubs_per_job):
            jid = f"syn-{s.probe_id}-{c // pubs_per_job:02d}"
            add_job(jid, T0 + timedelta(seconds=60 if s.kind == "gradient" else 120), 25)
            ids += [jid] * min(pubs_per_job, s.K - c)
        mask_jobs[s.probe_id] = np.array(ids, dtype=object)
        mask_pos[s.probe_id] = (np.arange(s.K) % pubs_per_job).astype(float)
    # characterisation: P(1) per qubit of the 6x10 patch at 4096 shots, and the reset error unfolded as the registered rule does
    cq = list(_patch("6x10").qubits)

    def readout(jid: str, q: int):
        """(p01, p10) of qubit q in the properties the job was created on: the bundle's properties.json, which the registered
        folding reads."""
        own = _parsed_sets(dev, cal_dicts)[cal_dicts.index(jobs[jid]["_own"])]
        return own.q[("prob_meas1_prep0", int(q))], own.q[("prob_meas0_prep1", int(q))]

    p01, p10 = (np.array(v) for v in zip(*[readout("syn-char", q) for q in cq]))
    eps_true = dev["eps"][cq]
    char = dict(readout_ref_prep0=rng.binomial(4096, p01) / 4096.0, readout_ref_prep1=rng.binomial(4096, 1 - p10) / 4096.0,
                reset_error_prep1=rng.binomial(4096, p01 + eps_true * (1 - p10 - p01)) / 4096.0)
    den = char["readout_ref_prep1"] - char["readout_ref_prep0"]
    eps_hat = {int(q): float(max((char["reset_error_prep1"][i] - char["readout_ref_prep0"][i]) / den[i], 0.0)) for i, q in enumerate(cq) if den[i] > 0}
    eps_se = {int(q): float(ES.reset_error_se(char["reset_error_prep1"][i], char["readout_ref_prep0"][i], char["readout_ref_prep1"][i], 4096)) for i, q in enumerate(cq) if den[i] > 0}
    shared: Dict[int, tuple] = {}
    probes, preds, truth, sigmas, ab_all = [], {}, {}, {}, {}
    full_cells: Dict[int, np.ndarray] = {}
    for s in specs:
        patch = _patch(s.patch)
        n = patch.n
        edge = interior_edge(patch)
        qi, qj = int(edge[0]), int(edge[1])
        ci, cj = patch.local(qi), patch.local(qj)
        (i01, i10), (j01, j10) = readout(mask_jobs[s.probe_id][0], qi), readout(mask_jobs[s.probe_id][0], qj)
        ai, bi, aj, bj = 1 - i01 - i10, i10 - i01, 1 - j01 - j10, j10 - j01
        K, M = s.K, s.M
        if s.seed not in shared:                              # probes of one seed share their theta draws: the same u_d and x_d
            r2 = np.random.default_rng([20261198, int(seed), s.seed])
            if draw_kurtosis is None:
                shared[s.seed] = (r2, r2.uniform(-np.sqrt(3), np.sqrt(3), M), _heavy(r2, M, s.pi_u), 1.0, s.pi_u)
            else:
                pi_k = 1.8 / float(draw_kurtosis)
                shared[s.seed] = (r2, _heavy(r2, M, pi_k), _heavy(r2, M, pi_k), pi_k, pi_k)
        r2, x, u, pi_x, pi_g = shared[s.seed]
        if s.arm == "reset":
            bits = lottery_masks(s.seed, K, s.L, n, s.mask_p)
            ri, rj = bits[:, s.L - 1, ci], bits[:, s.L - 1, cj]
            ui, uj = 1 - 2 * dev["eps"][qi], 1 - 2 * dev["eps"][qj]
            c0 = np.where(ri, ai * ui + bi, bi) * np.where(rj, aj * uj + bj, bj)
            gamma, eta = (~ri).astype(float), (~(ri & rj)).astype(float)
            uh, uhj = 1 - 2 * eps_hat.get(qi, 0.0), 1 - 2 * eps_hat.get(qj, 0.0)
            folded = float(np.mean(np.where(ri, ai * uh + bi, bi) * np.where(rj, aj * uhj + bj, bj)))
            if qi in eps_se and qj in eps_se:                 # the counting error of the two reset errors, as the screen's loader forms it
                gi = ai * aj * uhj * float((ri & rj).mean()) + ai * bj * float(ri.mean())
                gj = ai * aj * uh * float((ri & rj).mean()) + bi * aj * float(rj.mean())
                folded_sigma = float(np.hypot(2.0 * gi * eps_se[qi], 2.0 * gj * eps_se[qj]))
            else:
                folded_sigma = None
            ab_all[s.probe_id] = (float(ai), float(bi), float(aj), float(bj))
        else:
            c0, gamma, eta, folded, folded_sigma = np.full(K, bi * bj), np.ones(K), np.ones(K), None, None
        jt = np.array([jobs[j]["running"].timestamp() for j in mask_jobs[s.probe_id]])
        tj = (jt - jt.min()) / max(jt.max() - jt.min(), 1e-9) - 0.5 if K > 1 else np.zeros(K)
        S1, S2 = gamma.sum(), (gamma ** 2).sum()
        pid = s.probe_id
        if s.kind == "gradient":
            T_null = s.T
            if K > 1:
                tau = T_null * K * (K - 1) / (S1 ** 2 - S2)
                delta = (K * s.pf + T_null) * K / S2 - tau
                if delta < 0:
                    raise ValueError(f"{pid}: the planted pattern floor is below what the masks allow")
            else:
                tau, delta = T_null, 0.0
            g_eff = gamma * (1.0 + planted.drift * tj) * np.sqrt(np.clip(1.0 + planted.variance_drift.get(pid, 0.0) * tj, 0.0, None))
            if pid in planted.mask_factor:
                idx, fac = planted.mask_factor[pid]
                g_eff = g_eff.copy()
                g_eff[np.asarray(idx, dtype=int)] *= fac
            scale = (n / 60.0) ** (planted.size_beta / 2.0)
            tau = tau * float(planted.variance_factor.get(pid, 1.0))          # item 8 (e): the k = L variance alone (the per-mask part is not scaled)
            v = r2.choice([-1.0, 1.0], size=(M, K))
            y = r2.choice([-1.0, 1.0], size=(M, K))
            bound = (np.abs(c0) + eta * (np.sqrt(3 * s.tau_c / pi_x) + np.sqrt(s.delta_c)) + scale * np.abs(g_eff) * (np.sqrt(3 * tau / pi_g) + np.sqrt(delta))).max()
            if bound > 1.0:
                raise ValueError(f"{pid}: the design allows an expectation value of {bound:.3f} > 1; lower its amplitudes")
            G = scale * g_eff[None, :] * (np.sqrt(tau) * u[:, None] + np.sqrt(delta) * v)
            H = eta[None, :] * (np.sqrt(s.tau_c) * x[:, None] + np.sqrt(s.delta_c) * y)
            ep, sp = _binom(rng, c0[None, :] + H + G, s.shots)
            em, sm = _binom(rng, c0[None, :] + H - G, s.shots)
            S1e, S2e = eta.sum(), (eta ** 2).sum()
            T_c = s.tau_c * (S1e ** 2 - S2e) / (K * (K - 1)) if K > 1 else s.tau_c
            t_var = T_null
            t_cost = T_c + T_null - (float(np.var(c0, ddof=1)) / K if K > 1 else 0.0)
            truth[(pid, "var_kL")], truth[(pid, "var_cmix")], truth[(pid, "mean_cmix")] = t_var, t_cost, float(c0.mean())
            pr = np.random.default_rng([20261196, int(seed), _stable(pid)])
            preds[(pid, "var_kL")] = dict(P=t_var * (1 + s.rel_sigma * pr.standard_normal()), sigma=s.rel_sigma * t_var, source="synthetic")
            sigmas[(pid, "var_kL")] = s.rel_sigma * t_var
            if K > 1:
                preds[(pid, "var_cmix")] = dict(P=t_cost * (1 + s.rel_sigma * pr.standard_normal()), sigma=s.rel_sigma * abs(t_cost), source="synthetic")
                truth[(pid, "pattern_floor")] = s.pf
                preds[(pid, "pattern_floor")] = dict(P=s.pf, sigma=None, source="synthetic")
                preds[(pid, "mean_cmix")] = (dict(P=folded, sigma=folded_sigma, source="synthetic folded value") if folded is not None
                                             else dict(P=None, note="not a member of the registered E[C_mix] family (Deviation 63): no folded value"))
        else:
            y = r2.choice([-1.0, 1.0], size=(M, K))
            if s.ell == 0:
                cells = c0[None, :] + eta[None, :] * (np.sqrt(s.tau_c) * x[:, None] + np.sqrt(s.delta_c) * y)
                full_cells[s.seed] = cells
            else:
                rz = np.random.default_rng([20261195, int(seed), s.seed])
                zed = rz.uniform(-np.sqrt(3), np.sqrt(3), M) if draw_kurtosis is None else _heavy(rz, M, 1.8 / float(draw_kurtosis))
                w = r2.choice([-1.0, 1.0], size=(M, K))
                cells = full_cells[s.seed] - eta[None, :] * (np.sqrt(s.msd * K * (K - 1) / (eta.sum() ** 2 - (eta ** 2).sum())) * zed[:, None] + np.sqrt(s.nu) * w)
                pr = np.random.default_rng([20261196, int(seed), _stable(pid)])
                truth[(pid, "ms_l2")] = s.msd
                rms = float(np.sqrt(s.msd)) * (1 + s.rel_sigma * pr.standard_normal())
                preds[(pid, "ms_l2")] = dict(P=rms ** 2, sigma=2 * rms * s.rel_sigma * float(np.sqrt(s.msd)), source="synthetic", _rms=rms, _rms_sigma=s.rel_sigma * float(np.sqrt(s.msd)))
            ep, sp = _binom(rng, cells, s.shots)
            em, sm = np.full_like(ep, np.nan), np.full_like(ep, np.nan)
        probes.append(ES.Probe(probe_id=pid, group=s.group, arm=s.arm, kind=s.kind, p=s.p, n=n, L=s.L, k=s.L, shots=s.shots, resilience=0, ep=ep, em=em, sp=sp, sm=sm,
                               draw_seeds=s.seed + np.arange(M), mask_seeds=(s.seed + 1 + np.arange(K)).astype(float), mask_index=np.arange(K), mask_jobs=mask_jobs[pid],
                               patch=s.patch, edge=f"{qi}_{qj}", qubits=list(patch.qubits),
                               lattice=dict(lattice_qubits=list(patch.qubits), lattice_edge=f"{qi}_{qj}", origin=list(patch.origin), holes=[], broken_edges=[]),
                               stamp=STAMP, mask_p=s.mask_p, ell=s.ell, K_planned=K, point_id=pid, mask_pos=mask_pos[pid]))
    inp = ES.Inputs(probes=probes, preds=preds, jobs={k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in jobs.items()}, calsets=calsets,
                    eps=eps_hat, eps_se=eps_se, readout_ab=ab_all, deviation65=bool(deviation65),
                    draw_kurtosis={s.probe_id: (1.8 / s.pi_u if draw_kurtosis is None else float(draw_kurtosis)) for s in specs if s.kind == "gradient"} if with_kurtosis else {})
    out = Synthetic(specs=specs, inputs=inp, truth=truth, dev=dev, cal_dicts=cal_dicts, char=char, char_qubits=cq, job_order=order, pred_sigma=sigmas)
    out._jobs_full = jobs
    out.deviation65 = bool(deviation65)
    return out


def specs_from_list(path) -> List[Spec]:
    """The synthetic design of a committed job list (``data/joblists/paper1/day3_dial_refs.json``): its gradient and cost probes
    with their ids, dial kinds, strengths, depths, rungs, seeds, masks, draws and shots, and the planted second moments of
    ``day3_specs`` for the same point. Refuses a probe the default design has no moments for."""
    jl = json.loads(Path(path).read_text(encoding="utf-8"))
    default = {s.probe_id: s for s in day3_specs()}
    out = []
    for p in jl["probes"]:
        if p.get("kind") != "reset_dial":
            continue
        d = default.get(p["id"])
        if d is None:
            raise ValueError(f"no planted moments for probe {p['id']} of {path}")
        arm = {"reset": "reset", "dephase": "dephase", "delay": "delay"}[p["reset_kind"]]
        kind = "cost" if p.get("unshifted") else "gradient"
        if (arm, kind, float(p["p"]), int(p["L"]), str(p["patch"])) != (d.arm, d.kind, d.p, d.L, d.patch):
            raise ValueError(f"probe {p['id']} of {path} is not the point the default design plants")
        out.append(Spec(p["id"], arm, float(p["p"]), str(p["patch"]), int(p["L"]), int(p["seed"]), int(p["masks"]), int(p["M"]), int(p["shots"]), d.T, pf=d.pf * d.K / int(p["masks"]),
                        tau_c=d.tau_c, delta_c=d.delta_c, pi_u=d.pi_u, kind=kind, ell=(int(p["truncate_to"]) if p.get("truncate_to") else 0) if kind == "cost" else None,
                        msd=d.msd, nu=d.nu, rel_sigma=d.rel_sigma))
        if arm == "dephase" and abs(float(p.get("mask_p", p["p"] / 2.0)) - out[-1].mask_p) > 1e-12:
            raise ValueError(f"probe {p['id']}: the list's mask_p is not p / 2")
    return out


# ------------------------------------------------------------------------------------------------ the stored format

LOG_COLUMNS = ["backend", "job_id", "timestamp", "job_submit_time", "calibration_snapshot", "n", "patch_qubits", "observable_edge", "L", "k", "resilience_level",
               "shots", "seed", "param_hash", "arm", "p", "K", "mask_seed", "rep_delay_submitted", "rep_delay_submitted_us", "ev_plus", "ev_minus", "std_plus",
               "std_minus", "ensemble_se_plus", "ensemble_se_minus", "gradient", "transpiled_depth", "two_qubit_gates", "fractional_gates"]   # = gradvar.hardware.LOG_COLUMNS (a test pins it)


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _phash(seed: int) -> str:
    return hashlib.sha256(f"theta-{int(seed)}".encode()).hexdigest()


def _pub(evs: np.ndarray, stds: np.ndarray, shots: int) -> dict:
    from gradvar.analysis.loader import encode_ndarray
    return {"__type__": "PubResult", "__value__": {"data": {"__type__": "DataBin", "__value__": {"field_names": ["evs", "stds"], "shape": list(evs.shape[:-1]) if evs.ndim > 1 else [],
            "fields": {"evs": encode_ndarray(evs), "stds": encode_ndarray(stds)}}}, "metadata": {"shots": int(shots)}}}


def write(syn: Synthetic, root, name: str = "synthetic_day3") -> Dict[str, str]:
    """Store a synthetic run as the runner stores a retrieved run, and the files the registered analysis reads beside it:
    ``<root>/run/jobs/<name>.csv`` (one row per circuit pair, ``gradvar.hardware.LOG_COLUMNS``), ``<root>/run/runs/2026-11-12/<job
    id>/`` with ``job.json`` (one point per pub: a Deviation 48 mask pub carries its M draws, ``param_hashes`` and
    ``theta_seeds``), ``result.json`` (RuntimeEncoder ``PrimitiveResult``) and ``properties.json``; ``<root>/predictions`` with the
    mixture rows (``dial_redraw_<tag>.csv``), the realised-mask rows (``dial_realised_<tag>.csv``) and the H7 comparators;
    ``<root>/calibrations`` with the dated properties sets. Returns the paths."""
    root = Path(root)
    run_dir, pred_dir, cal_dir = root / "run", root / "predictions", root / "calibrations"
    day = run_dir / "runs" / "2026-11-12"
    for d in (run_dir / "jobs", day, pred_dir, cal_dir):
        d.mkdir(parents=True, exist_ok=True)
    inp, jobs = syn.inputs, syn._jobs_full
    by_job: Dict[str, list] = {j: [] for j in syn.job_order}
    for pr in inp.probes:
        for m in range(pr.K):
            by_job[str(pr.mask_jobs[m])].append((pr, m))
    rows = []
    stamp = _iso(T0 + timedelta(hours=2))

    def row(jid, pr_like, **kw):
        base = {c: "" for c in LOG_COLUMNS}
        base.update(backend=BACKEND, job_id=jid, timestamp=stamp, job_submit_time=_iso(jobs[jid]["created"]), calibration_snapshot=f"data/calibrations/{SNAPSHOT}",
                    resilience_level=0, rep_delay_submitted="default", rep_delay_submitted_us="default", ensemble_se_plus=float("nan"), ensemble_se_minus=float("nan"),
                    transpiled_depth=80, two_qubit_gates=600, fractional_gates=False)
        base.update(kw)
        rows.append(base)

    for jid in syn.job_order:
        job = jobs[jid]
        points, pubs, shots = [], [], None
        if jid == "syn-char":
            shots = 4096
            for pid, kind, prep in (("reset_error_prep1", "reset", "1"), ("readout_ref_prep0", "none", "0"), ("readout_ref_prep1", "none", "1")):
                evs = 1.0 - 2.0 * syn.char[pid]
                points.append(dict(probe_id=pid, kind="reset_error", reset_kind=kind, mask_index=None, mask_hash="", n=len(syn.char_qubits), L=None, k_1based=None, p=None,
                                   prep=prep, seed=23361001, qubits=list(syn.char_qubits), edge=None, layout=None, param_hash=None, masks=None, mask_seed=None,
                                   rep_delay_us=None, patch="6x10"))
                pubs.append(_pub(evs, np.sqrt(np.clip(1 - evs ** 2, 0, None) / shots), shots))
                row(jid, None, n=len(syn.char_qubits), patch_qubits=" ".join(map(str, syn.char_qubits)), observable_edge=f"probe:{pid}", shots=shots, seed=23361001,
                    arm=kind, ev_plus=float(evs.mean()), ev_minus=float("nan"), std_plus=float("nan"), std_minus=float("nan"), gradient=float("nan"))
        for pr, m in by_job[jid]:
            shots = pr.shots
            spec = next(s for s in syn.specs if s.probe_id == pr.probe_id)
            bits = lottery_masks(spec.seed, pr.K, pr.L, pr.n, spec.mask_p)[m] if pr.arm != "delay" else np.ones((pr.L, pr.n), dtype=bool)
            seeds = [int(x) for x in pr.draw_seeds]
            unshifted = pr.kind == "cost"
            points.append(dict(probe_id=pr.probe_id, kind="reset_dial", reset_kind=pr.arm, null_qubit=None, draw=None, mask_index=int(m),
                               mask_hash=hashlib.sha256(np.ascontiguousarray(bits).tobytes()).hexdigest()[:16], n=pr.n, L=pr.L, k_1based=pr.k, p=pr.p, prep="1",
                               seed=spec.seed, qubits=list(pr.qubits), edge=pr.edge, layout=None, param_hash=None, draws=pr.M, param_hashes=[_phash(x) for x in seeds],
                               theta_seeds=seeds, masks=pr.K, mask_seed=spec.seed + 1 + int(m), dial_delay_ns=400.0 if pr.arm in ("delay", "dephase") else None,
                               rep_delay_us=None, unshifted=unshifted, truncate_to=pr.ell if pr.ell else None, M=pr.M, mask_p=spec.mask_p if pr.arm != "reset" else None,
                               synthetic_target_instructions=[], patch=pr.patch, origin=pr.lattice["origin"], holes=[], broken_edges=[],
                               lattice_qubits=pr.lattice["lattice_qubits"], lattice_edge=pr.lattice["lattice_edge"]))
            if unshifted:
                pubs.append(_pub(pr.ep[:, m], pr.sp[:, m], shots))
            else:
                pubs.append(_pub(np.stack([pr.ep[:, m], pr.em[:, m]], axis=1), np.stack([pr.sp[:, m], pr.sm[:, m]], axis=1), shots))
            for d, sd in enumerate(seeds):
                evm = float("nan") if unshifted else float(pr.em[d, m])
                row(jid, pr, n=pr.n, patch_qubits=" ".join(map(str, pr.qubits)), observable_edge=f"probe:{pr.probe_id}", L=pr.L, k=pr.k, shots=shots, seed=sd,
                    param_hash=_phash(sd), arm=pr.arm, p=pr.p, K=pr.K, mask_seed=spec.seed + 1 + int(m), ev_plus=float(pr.ep[d, m]), ev_minus=evm,
                    std_plus=float(pr.sp[d, m]), std_minus=float("nan") if unshifted else float(pr.sm[d, m]),
                    gradient=float("nan") if unshifted else (float(pr.ep[d, m]) - evm) / 2.0)
        bdir = day / jid
        bdir.mkdir(parents=True, exist_ok=True)
        ts = dict(created=_iso(job["created"]), running=_iso(job["running"]), finished=_iso(job["finished"]))
        (bdir / "job.json").write_text(json.dumps(dict(
            job_id=jid, dry_run=False, job_kind="probes", status="completed", error=None, timestamps=ts, metrics=dict(timestamps=ts),
            usage_qpu_seconds=int((job["finished"] - job["running"]).total_seconds()), backend_name=BACKEND, backend_version="1.0.0", instance="flex",
            joblist_name=name, resilience_level=0, shots=shots, runner_git_commit="synthetic", rep_delay=dict(default_rep_delay_s=1e-6, rep_delay_range_s=[0.0, 0.002],
            dynamic_reprate_enabled=True, source="synthetic"), rep_delay_submitted_s="default", dynamic_reprate_enabled=True,
            layout_check=dict(job["cuts"], verdict="pass", enforced=True, action="submit"), job_tag=f"L0-probes-s{shots}", points=points, placement_snapshot=SNAPSHOT)), encoding="utf-8")
        (bdir / "result.json").write_text(json.dumps({"__type__": "PrimitiveResult", "__value__": {"pub_results": pubs, "metadata": {"version": 2}}}), encoding="utf-8")
        (bdir / "properties.json").write_text(json.dumps(job["_own"]), encoding="utf-8")
        if getattr(syn, "deviation65", False):               # the Deviation 65 record of the job's execution-time calibration (draft contract)
            dated = sorted(syn.cal_dicts, key=lambda d: ES.parse_time(d["last_update_date"]))
            at = [d for d in dated if ES.parse_time(d["last_update_date"]) <= job["running"]]
            between = [d for d in dated if job["running"] < ES.parse_time(d["last_update_date"]) <= job["finished"]]
            after = [d for d in dated if ES.parse_time(d["last_update_date"]) > job["finished"]]
            (bdir / "properties_at_running.json").write_text(json.dumps(dict(job_properties=job["_own"], backend_properties=at[-1] if at else job["_own"])), encoding="utf-8")
            (bdir / "properties_between.json").write_text(json.dumps(dict(complete=True, note="synthetic", sets=[dict(properties=d) for d in between])), encoding="utf-8")
            (bdir / "properties_after_finished.json").write_text(json.dumps(dict(sets=[dict(properties=after[0])]) if after else dict(status="pending")), encoding="utf-8")
    csv_path = run_dir / "jobs" / f"{name}_retrieved_20261112T080000Z.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    for i, d in enumerate(syn.cal_dicts):                    # the committed sets, named by a snapshot time a few minutes after IBM's stamp
        t = ES.parse_time(d["last_update_date"]) + timedelta(minutes=7)
        (cal_dir / f"{BACKEND}_properties_{t.strftime('%Y-%m-%dT%H%M%SZ')}.json").write_text(json.dumps(d), encoding="utf-8")
    mix, real = [], []
    for pr in inp.probes:
        if pr.kind != "gradient":
            continue
        spec = next(s for s in syn.specs if s.probe_id == pr.probe_id)
        qkey = " ".join(str(q) for q in sorted(pr.qubits))
        v, c = inp.preds[(pr.probe_id, "var_kL")], inp.preds.get((pr.probe_id, "var_cmix"))
        base = dict(model="unital", n=pr.n, L=pr.L, k=pr.L, edge=pr.edge, patch=pr.patch, dial=pr.arm, p=pr.p, qubits=qkey, snapshot_stamp=STAMP, rung=pr.patch, joblist=name)
        f = 1.3 if pr.lottery else 1.0                        # a lottery probe's mixture row is recorded and not used: give it another value
        mix.append(dict(base, var_kL_mc=f * v["P"], se_kL_mc=v["sigma"], var_kL_pp=f * v["P"], var_k1_mc=float("nan"), se_k1_mc=float("nan"), var_k1_pp=float("nan"),
                        var_cost_mc=f * (c["P"] if c else v["P"]), se_cost_mc=(c["sigma"] if c else v["sigma"]), var_cost_pp=f * (c["P"] if c else v["P"]), mean_cost=0.0,
                        var_mask=float("nan"), pattern_floor=float("nan"), status="converged"))
        if pr.lottery:
            real.append(dict(base, probe_id=pr.probe_id, mask_seed=spec.seed, K=pr.K, mask_p=spec.mask_p, var_kL_realised=v["P"], se_kL_realised=v["sigma"],
                             var_k1_realised=float("nan"), se_k1_realised=float("nan"), var_cost_realised=c["P"], se_cost_realised=c["sigma"],
                             pattern_floor_kL_realised=inp.preds[(pr.probe_id, "pattern_floor")]["P"], pattern_floor_cost_realised=float("nan"), status="realised"))
    for fname, recs in ((f"dial_redraw_{TAG}.csv", mix), (f"dial_realised_{TAG}.csv", real)):
        with open(pred_dir / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(recs[0]))
            w.writeheader()
            w.writerows(recs)
    cuts = [p for p in inp.probes if p.kind == "cost" and p.ell == 2]
    for fname, realised in ((f"h7_truncation_{TAG}.json", False), (f"h7_realised_{TAG}.json", True)):
        entries = []
        for pr in cuts:
            spec = next(s for s in syn.specs if s.probe_id == pr.probe_id)
            pd_ = inp.preds[(pr.probe_id, "ms_l2")]
            e = dict(point=dict(patch=pr.patch, edge=pr.edge, n=pr.n, p=pr.p, L=pr.L, qubits=sorted(pr.qubits)), rms_l2=pd_["_rms"] * (1.0 if realised else 1.3),
                     rms_l2_sigma=pd_["_rms_sigma"])
            if realised:
                e.update(mask_seed=spec.seed, K=pr.K)
            entries.append(e)
        (pred_dir / fname).write_text(json.dumps(dict(snapshot=dict(stamp=STAMP, csv=SNAPSHOT), entries=entries)), encoding="utf-8")
    return dict(run_dir=str(run_dir), predictions=str(pred_dir), calibrations=str(cal_dir), csv=str(csv_path))


def small_specs() -> List[Spec]:
    """The day-3 design at a size a unit test can store and load: 24 draws, 32 masks, 40 draws for the references."""
    return day3_specs(M=24, K=32, M_ref=40)


def fill_dry_run(root, seed: int = 5) -> str:
    """Turn a dry run written by the runner itself (``gradvar.hardware.run_joblist(..., submit=False)`` with ``run_root =
    <root>/run/runs`` and ``log_dir = <root>/run/jobs``) into the files of a retrieved run, with made-up values: every bundle and
    every row of the CSV log keeps the fields the runner wrote; only the status, the three job times and the expectation values
    with their binomial standard errors are filled in, and the characterisation job gets a ``result.json`` (RuntimeEncoder
    ``PrimitiveResult``). The values mean nothing: this is for testing that the screen reads the runner's own files (probe ids,
    mask hashes, pub positions, placement records), which the synthetic writer above cannot show. Returns the CSV path."""
    import glob
    import os

    import pandas as pd
    root = Path(root)
    csvs = sorted(glob.glob(str(root / "run" / "jobs" / "*.csv")))
    if len(csvs) != 1:
        raise ValueError(f"one CSV log expected under {root / 'run' / 'jobs'}, found {len(csvs)}")
    c = pd.read_csv(csvs[0], dtype=str, keep_default_na=False)
    order = list(dict.fromkeys(c.job_id))
    times = {}
    for j, jid in enumerate(order):
        running = T0 + timedelta(minutes=25, seconds=14 * j)
        times[jid] = dict(created=_iso(T0 + timedelta(seconds=3 * j)), running=_iso(running), finished=_iso(running + timedelta(seconds=9)))
    rng = np.random.default_rng(seed)
    probe = c.observable_edge.str.replace("probe:", "", regex=False)
    shots = c.shots.astype(int).to_numpy()
    char = (c.arm.isin(["none"]) | probe.str.startswith("reset_error") | probe.str.startswith("readout_ref")).to_numpy()
    unshifted = probe.str.startswith("trunc_").to_numpy()
    sd = pd.to_numeric(c.seed, errors="coerce").fillna(0).astype(np.int64).to_numpy()
    ms = pd.to_numeric(c.mask_seed, errors="coerce").fillna(0).astype(np.int64).to_numpy()
    u = np.sin(sd * 0.7310) * 0.35                               # a per-draw amplitude, shared by the probes of one seed
    c0 = 0.15 + 0.1 * np.cos(ms * 0.37)                          # a per-mask level

    def measure(e):
        return 1.0 - 2.0 * rng.binomial(shots, (1.0 - e) / 2.0) / shots
    ep, em = measure(np.clip(c0 + u, -0.95, 0.95)), measure(np.clip(c0 - u, -0.95, 0.95))
    sp, sm = np.sqrt((1 - ep ** 2) / shots), np.sqrt((1 - em ** 2) / shots)
    em[unshifted | char] = np.nan
    sm[unshifted | char] = np.nan
    sp[char] = np.nan

    def text(a):
        return ["nan" if not np.isfinite(x) else repr(float(x)) for x in a]
    c["ev_plus"], c["ev_minus"], c["std_plus"], c["std_minus"], c["gradient"] = text(ep), text(em), text(sp), text(sm), text((ep - em) / 2.0)
    c["backend"] = BACKEND
    for b in sorted(glob.glob(str(root / "run" / "runs" / "*" / "*"))):
        jf = Path(b) / "job.json"
        j = json.loads(jf.read_text(encoding="utf-8"))
        ts = times[j["job_id"]]
        j.update(status="completed", dry_run=False, timestamps=dict(ts, submitted_local=ts["created"]), usage_qpu_seconds=9, backend_name=BACKEND,
                 metrics=dict(timestamps=ts, usage=dict(qpu_charge_time_seconds=9, status="complete")))
        jf.write_text(json.dumps(j), encoding="utf-8")
        pts = j.get("points") or []
        if not any(pt.get("kind") == "reset_error" for pt in pts):
            continue
        pubs = []
        for pt in pts:
            nq = len(pt.get("qubits") or [])
            level = 0.02 if pt.get("reset_kind") != "none" else (0.012 if str(pt.get("prep")) == "0" else 0.985)
            p1 = rng.binomial(4096, np.clip(level + 0.004 * rng.standard_normal(nq), 0.001, 0.999)) / 4096.0
            evs = 1.0 - 2.0 * p1
            pubs.append(_pub(evs, np.sqrt((1 - evs ** 2) / 4096.0), 4096))
            c.loc[(c.job_id == j["job_id"]) & (probe == pt["probe_id"]), "ev_plus"] = repr(float(evs.mean()))
        (Path(b) / "result.json").write_text(json.dumps({"__type__": "PrimitiveResult", "__value__": {"pub_results": pubs, "metadata": {"version": 2}}}), encoding="utf-8")
    out = Path(csvs[0]).with_name(Path(csvs[0]).name.replace("_dryrun_", "_retrieved_"))
    c.to_csv(out, index=False, lineterminator="\n")
    if out != Path(csvs[0]):
        os.remove(csvs[0])
    return str(out)
