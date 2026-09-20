"""Paper 2: SamplerV2 path of the hardware runner and the pre-registered Q1-Q5 circuit builders.

Pre-registration: "Reset and mid-circuit-measurement characterisation of ibm_phoenix" (Paper 2, v0.4.2, 20 Sep 2026).
A job list with ``primitive: "sampler"`` carries ``sampler_jobs`` (one SamplerV2 job per stage, Section 3 "Job packing")
whose ``circuits`` are compact generator specs expanded deterministically here (``expand_job``): the Q1 reset-error map,
the Q2 spectator-backaction arms on the five stratified target masks, the Q3 frame-tracked reset cycle benchmark, the Q4
reset-as-channel Bloch-map circuits on twelve two-qubit patches with 9/3/3/1 stratified masks, and Q5 (the native-reset
subset of Q1). Every circuit is Clifford (X, H, S, Paulis, reset, delay, measure), so the dry run can execute it on the
Aer stabilizer simulator at 120 qubits (``--simulate``) and exercise the per-shot register capture.

The qubit sets come from the calibration snapshot named in the list (``qubit_set.snapshot``): the 119 operational
qubits (qubit 17 excluded everywhere: no T1 / T2, readout error 0.51), the readout flags (> 3e-2) and the CZ cluster
(flagged, kept), and the Q4 patches (per row the horizontal edge with the lowest summed readout error, both qubits
outside the programme's exclusion set, Paper 1 Deviation 22 rule included, at least three columns from the previous
row's edge). The resolved sets are stored in the list and re-derived from the snapshot at build time (a stale list is
refused); the live ``backend.properties()`` re-check (Paper 1 Deviation 26, ``gradvar.hardware.layout_check``) flags
qubits on the submitting path and refuses only when a Q4 patch qubit fails or a used qubit is not operational.

Nothing here reads credentials; submission happens only through ``execute_sampler_joblist(submit=True)``, reached from
``gradvar.hardware.run_joblist`` after the same refusals as the Estimator path.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister, Instruction, QuantumRegister
from qiskit.transpiler import generate_preset_pass_manager

from .lattice import DEFAULT_EXCLUDE, N_COLS, N_QUBITS, N_ROWS, lattice_neighbours, row_col

PROTOCOLS = ("smoke", "Q1", "Q2", "Q3", "Q4", "Q5")
SPEC_KINDS = ("q1", "q2", "q3", "q4")
RESET_KINDS = ("reset", "measure_reset", "measure_reset_2")
Q1_ARMS = ("a", "b", "c", "d", "e", "f")
AXES = ("X", "Y", "Z")
Q4_INPUTS = ("0", "1", "+", "+i")
Q4_PATTERNS = ((0, 0), (1, 0), (0, 1), (1, 1))
DEAD_QUBITS = (17,)                      # Section 2: excluded everywhere (no T1 / T2, readout error 0.51, no calibrated coupler)
CZ_CLUSTER = tuple(q for q in DEFAULT_EXCLUDE if q not in DEAD_QUBITS)   # 55, 61, 62, 63, 72, 73: flagged on the maps, kept
READOUT_FLAG_CUT = 3e-2                  # Section 3: readout outliers above 3e-2 are flagged, not dropped (Q2: excluded as spectators)
Q2_MIN_DISTANCE = 3
DEFAULT_SEED = 20260919                  # Section 3 "Randomness": Q3 dense masks and Pauli frames, Q4 mask shuffles
Q3_MAX_CYCLES = 64
RESET_NS_DEFAULT = 400.0                 # native reset on 119 qubits; the delay reference and the Q3 spectator delay
RESET_NS_BY_QUBIT = {79: 2140.0}         # qubit 79's reset is 2140 ns (Section 1); its delay reference matches
SQ_GATE_US = 0.04                        # one physical single-qubit gate (sx / x, 40 ns) in the budget's gate length
SAMPLER_LOG_COLUMNS = [
    "backend", "job_id", "timestamp", "job_submit_time", "calibration_snapshot", "stage", "protocol", "circuit_index", "label",
    "reset_kind", "mask_id", "mask_hash", "frame_id", "reps", "prep", "meas_axis", "expected_z", "shots", "rep_delay_granted",
    "init_qubits", "sched_ns", "reset_ns", "n_measured", "counts_path", "qpu_seconds", "transpiled_depth", "notes",
]
_SYNTHETIC: Dict[int, Dict[str, Instruction]] = {}   # id(backend) -> {kind: synthetic instruction added to a fake target}


class Paper2Error(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ qubit sets and masks

def operational_qubits(csv_path: str | Path) -> dict:
    """The Paper 2 qubit set from a calibration CSV: every qubit that is operational, has T1 and T2, and has a readout
    assignment error below 0.5, minus ``DEAD_QUBITS``; plus the flags of Section 3 (readout above ``READOUT_FLAG_CUT``,
    the CZ cluster). ``reasons`` names why each excluded qubit is out."""
    from .noise import load_calibration
    df = load_calibration(csv_path)
    qubits, reasons = [], {}
    for q in range(N_QUBITS):
        why = []
        if q in DEAD_QUBITS:
            why.append("pre-registered dead qubit (Section 2)")
        if q not in df.index:
            why.append("absent from the snapshot")
        else:
            row = df.loc[q]
            if "Operational" in df and str(row["Operational"]).strip().lower() != "yes":
                why.append("not operational")
            if any(np.isnan(float(row[c])) for c in ("T1 (us)", "T2 (us)") if c in df):
                why.append("no T1 or T2")
            if float(row["Readout assignment error"]) >= 0.5:
                why.append(f"readout error {float(row['Readout assignment error']):.3f} >= 0.5")
        if why:
            reasons[q] = why
        else:
            qubits.append(q)
    ro = df["Readout assignment error"].astype(float)
    flagged_readout = sorted(int(q) for q in df.index[ro > READOUT_FLAG_CUT] if int(q) in qubits)
    return dict(rule="all_operational", snapshot=Path(csv_path).name, qubits=qubits, excluded=sorted(reasons),
                reasons={str(q): v for q, v in sorted(reasons.items())}, flagged_readout=flagged_readout,
                flagged_cz_cluster=sorted(q for q in CZ_CLUSTER if q in qubits), readout_flag_cut=READOUT_FLAG_CUT)


def q2_masks() -> List[List[int]]:
    """Section 2, Q2: the five target masks M_s = {q = 10 i + j : (i + 2 j) mod 5 = s}, 24 qubits each (qubit 17 sits
    in M_0 by the formula but is excluded everywhere: nothing acts on it and its neighbours count as controls)."""
    return [[q for q in range(N_QUBITS) if (row_col(q)[0] + 2 * row_col(q)[1]) % 5 == s] for s in range(5)]


def lattice_distance(a: int, b: int) -> int:
    (r1, c1), (r2, c2) = row_col(a), row_col(b)
    return abs(r1 - r2) + abs(c1 - c2)


def q2_roles(mask: Sequence[int], qubits: Sequence[int], spectator_excluded: Iterable[int] = ()) -> dict:
    """Targets (mask members in the qubit set), directed pairs (target, neighbour) over neighbours in the qubit set,
    spectators (pair neighbours not excluded by readout), and the distance-2 controls (non-targets with no target
    neighbour). Every non-target has at most one target neighbour by construction of the masks."""
    qs, ex = set(int(q) for q in qubits), set(int(q) for q in spectator_excluded)
    targets = [q for q in mask if q in qs]
    pairs = [(t, nb) for t in targets for nb in lattice_neighbours(t) if nb in qs]
    spectators = sorted({nb for _, nb in pairs if nb not in ex})
    neighbours = {nb for _, nb in pairs}
    controls = sorted(q for q in qs if q not in set(targets) and q not in neighbours)
    return dict(targets=targets, pairs=pairs, spectators=spectators, excluded_spectators=sorted(neighbours & ex), controls=controls)


def dense_masks(qubits: Sequence[int], n_masks: int, p: float, rng: np.random.Generator) -> List[List[int]]:
    """Q3 dense masks: Bernoulli(p) over the qubit set, drawn from ``rng`` in mask order."""
    return [[int(q) for q, hit in zip(qubits, rng.random(len(qubits)) < p) if hit] for _ in range(n_masks)]


def pauli_frames(qubits: Sequence[int], n_frames: int, cycles: int, rng: np.random.Generator) -> np.ndarray:
    """Q3 Pauli frames: ``(n_frames, cycles, len(qubits))`` array of 0..3 = I, X, Y, Z drawn from ``rng`` after the dense
    masks. A circuit with m cycles uses the first m cycles of its frame, so the m = 1, 16, 64 circuits of one frame nest."""
    return rng.integers(0, 4, size=(n_frames, cycles, len(qubits)), dtype=np.int8)


def q3_randomness(qubits: Sequence[int], n_dense: int = 8, dense_p: float = 0.5, n_frames: int = 4,
                  cycles: int = Q3_MAX_CYCLES, seed: int = DEFAULT_SEED) -> Tuple[List[List[int]], np.ndarray]:
    """Section 3 "Randomness": dense masks first, then the Pauli frames, from one ``default_rng(seed)``."""
    rng = np.random.default_rng(seed)
    return dense_masks(qubits, n_dense, dense_p, rng), pauli_frames(qubits, n_frames, cycles, rng)


def q3_mask_table(qubits: Sequence[int], n_dense: int = 8, dense_p: float = 0.5, seed: int = DEFAULT_SEED) -> Dict[str, List[int]]:
    """``sparse0..4`` (the Q2 masks restricted to the qubit set) and ``dense0..7``."""
    qs = set(int(q) for q in qubits)
    table = {f"sparse{s}": [q for q in m if q in qs] for s, m in enumerate(q2_masks())}
    dense, _ = q3_randomness(qubits, n_dense, dense_p, seed=seed)
    table.update({f"dense{i}": m for i, m in enumerate(dense)})
    return table


def q4_pattern_counts(p: float, K: int) -> Dict[Tuple[int, int], int]:
    """How often each reset pattern (R_a, R_b) appears among K stratified masks at per-qubit probability p: 9/3/3/1 at
    p = 0.25 and 4/4/4/4 at p = 0.5 for K = 16 (Section 2, Q4). Refuses a (p, K) that does not stratify exactly."""
    counts = {(0, 0): (1 - p) ** 2 * K, (1, 0): p * (1 - p) * K, (0, 1): p * (1 - p) * K, (1, 1): p * p * K}
    out = {}
    for pat, c in counts.items():
        if abs(c - round(c)) > 1e-9:
            raise Paper2Error(f"p = {p}, K = {K} does not stratify: pattern {pat} would appear {c} times")
        out[pat] = int(round(c))
    return out


def q4_masks(p: float, K: int, n_patches: int, rng: np.random.Generator) -> np.ndarray:
    """``(K, n_patches, 2)`` boolean array: mask k applies pattern ``masks[k, j]`` to patch j. Per patch the pattern list
    (00 x n00, 10 x n10, 01 x n01, 11 x n11) is permuted with ``rng``, so every patch sees each pattern the stratified
    number of times and the realised per-qubit probability equals p exactly."""
    counts = q4_pattern_counts(p, K)
    base = [pat for pat in Q4_PATTERNS for _ in range(counts[pat])]
    out = np.zeros((K, n_patches, 2), dtype=bool)
    for j in range(n_patches):
        perm = rng.permutation(K)
        for k, idx in enumerate(perm):
            out[k, j] = base[idx]
    return out


def q4_mask_sets(ps: Sequence[float], K: int, n_patches: int, seed: int = DEFAULT_SEED) -> Dict[float, np.ndarray]:
    """Mask arrays for every p in list order from one ``default_rng(seed)`` (Section 3 "Randomness")."""
    rng = np.random.default_rng(seed)
    return {float(p): q4_masks(float(p), K, n_patches, rng) for p in ps}


def q4_row_edges(csv_path: str | Path, exclusion: Iterable[int], min_column_gap: int = 3) -> dict:
    """Section 3, Q4 qubit sets: per row, the horizontal edge with the lowest summed readout assignment error whose two
    qubits are outside ``exclusion`` and whose left column is at least ``min_column_gap`` columns from the previous
    row's edge (rows in order 0..11). The pre-registration states the rule row by row; when the greedy choice leaves a
    later row without any admissible edge (it does on the 2026-09-19 snapshots: row 5's best edge sits in column 6 and
    row 6's admissible edges all lie in columns 4-8), the search backtracks to the previous row's next-best edge, so the
    result is the first complete assignment in the greedy order (identical to the greedy one whenever that exists).
    Returns the twelve edges and, per row, the candidates considered and whether a backtrack was needed."""
    from .noise import load_calibration
    df = load_calibration(csv_path)
    ro = df["Readout assignment error"].astype(float)
    ex = set(int(q) for q in exclusion)
    per_row = []
    for r in range(N_ROWS):
        cands = []
        for c in range(N_COLS - 1):
            a, b = N_COLS * r + c, N_COLS * r + c + 1
            if a in ex or b in ex or a not in ro.index or b not in ro.index:
                continue
            cands.append(dict(edge=[a, b], column=c, readout_sum=float(ro[a] + ro[b])))
        cands.sort(key=lambda d: (d["readout_sum"], d["column"]))
        per_row.append(cands)
    chosen: List[dict] = []
    backtracked = []

    def search(r: int) -> bool:
        if r == N_ROWS:
            return True
        prev = chosen[-1]["column"] if chosen else None
        ok = [d for d in per_row[r] if prev is None or abs(d["column"] - prev) >= min_column_gap]
        for i, d in enumerate(ok):
            chosen.append(d)
            if search(r + 1):
                if i:
                    backtracked.append(dict(row=r, greedy=ok[0]["edge"], chosen=d["edge"]))
                return True
            chosen.pop()
        return False

    if not search(0):
        raise Paper2Error(f"Q4: no assignment of one horizontal edge per row outside the exclusion set {sorted(ex)} with "
                          f"left columns at least {min_column_gap} apart between consecutive rows")
    return dict(rule="row_edges", snapshot=Path(csv_path).name, min_column_gap=min_column_gap, exclusion=sorted(ex),
                edges=[d["edge"] for d in chosen], backtracked=sorted(backtracked, key=lambda d: d["row"]),
                per_row=[dict(row=r, chosen=chosen[r], candidates=per_row[r]) for r in range(N_ROWS)])


def paper2_exclusion(csv_path: str | Path, properties: str | Path | None = None) -> Tuple[int, ...]:
    """The programme's exclusion set for the Q4 edge rule: the pre-registered cut (dead qubit, CZ cluster, readout above
    3e-2) plus, when ``properties`` (raw ``backend.properties()`` JSON of the same snapshot) is given, Paper 1's
    Deviation 22 rule (|ZZ| >= 1 MHz to an excluded qubit, initialisation error >= 5e-4) through
    ``gradvar.noise.exclusion_from_calibration``."""
    from .noise import exclusion_from_calibration
    return exclusion_from_calibration(str(csv_path), properties=properties)


def properties_for_snapshot(csv_path: str | Path) -> str | None:
    """The raw properties file of the same snapshot stamp as ``csv_path`` (``ibm_phoenix_<stamp>.csv`` ->
    ``ibm_phoenix_properties_<stamp without dashes and colons>.json[.gz]``), or None."""
    p = Path(csv_path)
    stem = p.stem
    stamp = (stem[len("ibm_phoenix_"):] if stem.startswith("ibm_phoenix_") else stem).replace("-", "").replace(":", "")
    for cand in (p.parent / f"ibm_phoenix_properties_{stamp}.json.gz", p.parent / f"ibm_phoenix_properties_{stamp}.json"):
        if cand.exists():
            return str(cand)
    return None


def reset_ns(q: int) -> float:
    """Pre-registered native reset duration on ibm_phoenix (400 ns; 2140 ns on qubit 79), also the delay reference."""
    return RESET_NS_BY_QUBIT.get(int(q), RESET_NS_DEFAULT)


def mask_hash(qubits: Iterable[int]) -> str:
    """SHA-256 (first 16 hex) of the sorted qubit list (logging schema ``mask_hash``)."""
    return hashlib.sha256(json.dumps(sorted(int(q) for q in qubits)).encode()).hexdigest()[:16]


# ------------------------------------------------------------------------------------------------ context and specs

@dataclass
class SamplerContext:
    """Resolved qubit sets of a Sampler job list: the operational qubits with their flags, the Q2 masks and roles, the Q3
    mask table and frames, the Q4 patches and mask arrays."""
    qubits: List[int]
    flagged_readout: List[int]
    flagged_cz_cluster: List[int]
    q4_edges: List[List[int]]
    seed: int = DEFAULT_SEED
    n_dense: int = 8
    dense_p: float = 0.5
    n_frames: int = 4
    q4_K: int = 16
    q4_ps: Tuple[float, ...] = (0.25, 0.5)
    snapshot: str | None = None
    exclusion: Tuple[int, ...] = ()
    _cache: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def qubit_set(self) -> set:
        return set(self.qubits)

    def bit_index(self, q: int) -> int:
        return self.qubits.index(int(q))

    @property
    def q3_masks(self) -> Dict[str, List[int]]:
        if "q3" not in self._cache:
            self._cache["q3"] = q3_mask_table(self.qubits, self.n_dense, self.dense_p, self.seed)
        return self._cache["q3"]

    @property
    def frames(self) -> np.ndarray:
        if "frames" not in self._cache:
            _, fr = q3_randomness(self.qubits, self.n_dense, self.dense_p, self.n_frames, Q3_MAX_CYCLES, self.seed)
            self._cache["frames"] = fr
        return self._cache["frames"]

    @property
    def q4_mask_arrays(self) -> Dict[float, np.ndarray]:
        if "q4" not in self._cache:
            self._cache["q4"] = q4_mask_sets(self.q4_ps, self.q4_K, len(self.q4_edges), self.seed)
        return self._cache["q4"]

    @property
    def q4_qubits(self) -> List[int]:
        return [q for e in self.q4_edges for q in e]

    @classmethod
    def from_snapshot(cls, csv_path: str | Path, properties: str | Path | None = "auto", **kw) -> "SamplerContext":
        props = properties_for_snapshot(csv_path) if properties == "auto" else properties
        ex = paper2_exclusion(csv_path, props)
        ops = operational_qubits(csv_path)
        edges = q4_row_edges(csv_path, ex)
        return cls(qubits=ops["qubits"], flagged_readout=ops["flagged_readout"], flagged_cz_cluster=ops["flagged_cz_cluster"],
                   q4_edges=edges["edges"], snapshot=Path(csv_path).name, exclusion=tuple(ex), **kw)

    @classmethod
    def from_joblist(cls, jl: dict, calibration_dir: str | Path | None = None, verify: bool = True) -> "SamplerContext":
        """The context stored in the list (``qubit_set``, ``q4_patches``, ``randomness``); with ``verify`` it is re-derived
        from the named snapshot in ``calibration_dir`` (default data/calibrations) and a mismatch is refused."""
        qs, q4, rnd = jl.get("qubit_set") or {}, jl.get("q4_patches") or {}, jl.get("randomness") or {}
        ctx = cls(qubits=[int(q) for q in qs.get("qubits", [])], flagged_readout=[int(q) for q in qs.get("flagged_readout", [])],
                  flagged_cz_cluster=[int(q) for q in qs.get("flagged_cz_cluster", [])],
                  q4_edges=[[int(a), int(b)] for a, b in q4.get("edges", [])], seed=int(rnd.get("seed", DEFAULT_SEED)),
                  n_dense=int(rnd.get("q3_dense_masks", 8)), dense_p=float(rnd.get("q3_dense_p", 0.5)),
                  n_frames=int(rnd.get("q3_frames", 4)), q4_K=int(rnd.get("q4_masks_per_p", 16)),
                  q4_ps=tuple(float(p) for p in rnd.get("q4_p", (0.25, 0.5))), snapshot=qs.get("snapshot"),
                  exclusion=tuple(int(q) for q in q4.get("exclusion", ())))
        if verify and ctx.snapshot:
            d = Path(calibration_dir) if calibration_dir else Path(__file__).resolve().parents[1] / "data" / "calibrations"
            csv_path = d / ctx.snapshot
            if not csv_path.exists():
                raise Paper2Error(f"calibration snapshot {csv_path} named by the job list is missing")
            fresh = cls.from_snapshot(csv_path, seed=ctx.seed, n_dense=ctx.n_dense, dense_p=ctx.dense_p, n_frames=ctx.n_frames,
                                      q4_K=ctx.q4_K, q4_ps=ctx.q4_ps)
            if fresh.qubits != ctx.qubits:
                raise Paper2Error(f"qubit_set.qubits differs from the {ctx.snapshot} snapshot: list has {len(ctx.qubits)}, "
                                  f"snapshot gives {len(fresh.qubits)} (regenerate the list with scripts/make_paper2_joblists.py)")
            if fresh.flagged_readout != ctx.flagged_readout or fresh.flagged_cz_cluster != ctx.flagged_cz_cluster:
                raise Paper2Error(f"qubit_set flags differ from the {ctx.snapshot} snapshot")
            if ctx.q4_edges and fresh.q4_edges != ctx.q4_edges:
                raise Paper2Error(f"q4_patches.edges differ from the {ctx.snapshot} snapshot: list {ctx.q4_edges}, snapshot {fresh.q4_edges}")
        return ctx

    def as_joblist_fields(self) -> dict:
        ops = dict(rule="all_operational", snapshot=self.snapshot, qubits=list(self.qubits), excluded=sorted(set(range(N_QUBITS)) - self.qubit_set),
                   flagged_readout=list(self.flagged_readout), flagged_cz_cluster=list(self.flagged_cz_cluster), readout_flag_cut=READOUT_FLAG_CUT)
        return dict(qubit_set=ops,
                    q4_patches=dict(rule="row_edges", snapshot=self.snapshot, min_column_gap=3, exclusion=list(self.exclusion), edges=[list(e) for e in self.q4_edges]),
                    randomness=dict(seed=self.seed, q3_dense_masks=self.n_dense, q3_dense_p=self.dense_p, q3_frames=self.n_frames,
                                    q3_max_cycles=Q3_MAX_CYCLES, q4_masks_per_p=self.q4_K, q4_p=list(self.q4_ps),
                                    q3_mask_hashes={k: mask_hash(v) for k, v in self.q3_masks.items()}))


def _as_list(v, default):
    if v is None:
        return list(default)
    return list(v) if isinstance(v, (list, tuple)) else [v]


def expand_spec(spec: dict, ctx: SamplerContext) -> List[dict]:
    """One generator spec of ``sampler_jobs[].circuits`` -> the circuit specs it stands for (protocol, label, params).

    ``q1``: ``arm`` a-f, ``reset_kind`` (a, b, f; default all three), ``m`` (c; default [2, 4]).
    ``q2``: product of ``masks`` (0-4), ``reps`` (1, 4, 16), ``axes`` (X, Y, Z), ``target_prep`` ("0", "1"), ``arms`` (reset, delay).
    ``q3``: product of ``masks`` (names of the mask table, default all 13), ``frames`` (0-3), ``cycles`` (1, 16, 64).
    ``q4``: product of ``p`` (0.25, 0.5), ``masks`` (0-15), ``inputs`` (0, 1, +, +i), ``axes`` (X, Y, Z).
    ``protocol`` may override the label's protocol (the smoke list runs Q1-Q4 circuits under stage ``smoke``)."""
    kind = str(spec.get("kind", ""))
    if kind not in SPEC_KINDS:
        raise Paper2Error(f"circuit spec kind must be one of {SPEC_KINDS}, got {kind!r}")
    proto = str(spec.get("protocol", kind.upper()))
    out = []
    if kind == "q1":
        arms = _as_list(spec.get("arm"), Q1_ARMS)
        for arm in arms:
            if arm not in Q1_ARMS:
                raise Paper2Error(f"q1 arm must be one of {Q1_ARMS}, got {arm!r}")
            if arm in ("a", "b", "f"):
                for rk in _as_list(spec.get("reset_kind"), RESET_KINDS):
                    if rk not in RESET_KINDS:
                        raise Paper2Error(f"q1 reset_kind must be one of {RESET_KINDS}, got {rk!r}")
                    out.append(dict(protocol=proto, kind="q1", arm=arm, reset_kind=rk, m=1, label=f"Q1{arm}_{rk}"))
            elif arm == "c":
                for m in _as_list(spec.get("m"), (2, 4)):
                    out.append(dict(protocol=proto, kind="q1", arm="c", reset_kind="reset", m=int(m), label=f"Q1c_reset_m{int(m)}"))
            elif arm == "d":
                for prep in _as_list(spec.get("prep"), ("1", "0")):
                    out.append(dict(protocol=proto, kind="q1", arm="d", reset_kind="none", m=0, prep=str(prep),
                                    label="Q1d_x_measure" if str(prep) == "1" else "Q1d_measure"))
            else:  # e
                out.append(dict(protocol=proto, kind="q1", arm="e", reset_kind="delay", m=1, label="Q1e_x_delay_measure"))
    elif kind == "q2":
        for s, r, ax, tp, arm in product(_as_list(spec.get("masks"), range(5)), _as_list(spec.get("reps"), (1, 4, 16)),
                                         _as_list(spec.get("axes"), AXES), _as_list(spec.get("target_prep"), ("0", "1")),
                                         _as_list(spec.get("arms"), ("reset", "delay"))):
            if int(s) not in range(5) or ax not in AXES or str(tp) not in ("0", "1") or arm not in ("reset", "delay"):
                raise Paper2Error(f"q2 spec value out of range: mask {s}, axis {ax}, target_prep {tp}, arm {arm}")
            out.append(dict(protocol=proto, kind="q2", mask=int(s), reps=int(r), axis=ax, target_prep=str(tp), arm=arm,
                            label=f"Q2_M{int(s)}_r{int(r)}_{ax}_t{tp}_{arm}"))
    elif kind == "q3":
        names = _as_list(spec.get("masks"), list(ctx.q3_masks))
        for name, f, m in product(names, _as_list(spec.get("frames"), range(ctx.n_frames)), _as_list(spec.get("cycles"), (1, 16, 64))):
            if name not in ctx.q3_masks or int(f) not in range(ctx.n_frames) or not (1 <= int(m) <= Q3_MAX_CYCLES):
                raise Paper2Error(f"q3 spec value out of range: mask {name}, frame {f}, cycles {m}")
            out.append(dict(protocol=proto, kind="q3", mask=str(name), frame=int(f), cycles=int(m), label=f"Q3_{name}_f{int(f)}_m{int(m)}"))
    else:  # q4
        for p, k, inp, ax in product(_as_list(spec.get("p"), ctx.q4_ps), _as_list(spec.get("masks"), range(ctx.q4_K)),
                                     _as_list(spec.get("inputs"), Q4_INPUTS), _as_list(spec.get("axes"), AXES)):
            if float(p) not in ctx.q4_ps or int(k) not in range(ctx.q4_K) or inp not in Q4_INPUTS or ax not in AXES:
                raise Paper2Error(f"q4 spec value out of range: p {p}, mask {k}, input {inp}, axis {ax}")
            out.append(dict(protocol=proto, kind="q4", p=float(p), mask=int(k), input=str(inp), axis=ax,
                            label=f"Q4_p{float(p):g}_k{int(k)}_in{inp}_{ax}"))
    return out


def expand_job(job: dict, ctx: SamplerContext) -> List[dict]:
    specs = [c for spec in job.get("circuits", []) or [] for c in expand_spec(spec, ctx)]
    labels = [c["label"] for c in specs]
    if len(set(labels)) != len(labels):
        dup = sorted({l for l in labels if labels.count(l) > 1})
        raise Paper2Error(f"sampler job {job.get('id')}: repeated circuits {dup[:5]}")
    return specs


# ------------------------------------------------------------------------------------------------ budget

def circuit_gate_us(c: dict, dial_us: Dict[str, float]) -> Tuple[float, int]:
    """(gate-only length in us, mid-circuit measurements) of one circuit spec for the budget: single-qubit gates at
    ``SQ_GATE_US`` each (parallel gates on different qubits count once), reset kinds and delays at ``dial_us``
    (ibm_phoenix target durations: reset 0.40, measure_reset 1.94, measure_reset_2 1.14, delay 0.40 us). A
    measurement-based reset counts as one mid-circuit measurement whose t_meas is its own duration."""
    kind = c["kind"]
    if kind == "q1":
        rk, arm = c["reset_kind"], c["arm"]
        mcm = 1 if rk in ("measure_reset", "measure_reset_2") else 0
        if arm == "a":
            return SQ_GATE_US + dial_us[rk], mcm
        if arm == "b":
            return dial_us[rk], mcm
        if arm == "c":
            return SQ_GATE_US + c["m"] * dial_us["reset"], 0
        if arm == "d":
            return (SQ_GATE_US if c.get("prep", "1") == "1" else 0.0), 0
        if arm == "e":
            return SQ_GATE_US + dial_us["delay"], 0
        return 2 * SQ_GATE_US + dial_us[rk], mcm
    if kind == "q2":
        prep = SQ_GATE_US if (c["axis"] != "Z" or c["target_prep"] == "1") else 0.0
        read = SQ_GATE_US if c["axis"] != "Z" else 0.0
        return prep + c["reps"] * dial_us["reset" if c["arm"] == "reset" else "delay"] + read, 0
    if kind == "q3":
        return SQ_GATE_US + c["cycles"] * (2 * SQ_GATE_US + dial_us["reset"]) + SQ_GATE_US, 0
    prep = 0.0 if c["input"] == "0" else SQ_GATE_US
    read = SQ_GATE_US if c["axis"] != "Z" else 0.0
    return prep + dial_us["reset"] + read, 0


def estimate_budget_sampler(jl: dict, rep_delays_us: Sequence[float], backend=None) -> dict:
    """Budget model version 2 for a Sampler list (pre-registration Deviation 2 with the TREX term identically zero: every
    Paper 2 job is SamplerV2 at resilience 0, no twirling, no measurement-noise learning):

        T_job = 2 s + sum over circuits of shots x (rep_delay + gate length + t_meas + 10 us)

    with t_meas counted once for the terminal readout of every circuit and once more for each mid-circuit
    measure_reset through its own target duration (``circuit_gate_us``). Same keys as ``gradvar.hardware.estimate_budget``
    plus ``primitive`` and per-job ``init_qubits`` / ``mcm_executions``. A job with its own ``rep_delay_us`` is timed at
    that value in every column."""
    from .hardware import (BUDGET_MODEL_VERSION, EXEC_OVERHEAD_US, TREX_RANDOMIZATIONS, ZNE_NOISE_FACTORS, dial_durations_us, readout_us)
    dial_us = dial_durations_us(backend)
    t_meas, t_meas_source = readout_us(backend, jl.get("backend"))
    ctx = SamplerContext.from_joblist(jl, verify=False)
    per_job = []
    for job in jl.get("sampler_jobs", []) or []:
        shots = int(job["shots"])
        circuits = expand_job(job, ctx)
        rd_own = job.get("rep_delay_us")
        lengths = [circuit_gate_us(c, dial_us) for c in circuits]
        entry = dict(tag=str(job["id"]), primitive="sampler", resilience_level=0, shots=shots,
                     init_qubits=bool(job.get("init_qubits", jl.get("init_qubits", True))),
                     rep_delay_us=None if rd_own is None else float(rd_own), circuits=len(circuits), executions=len(circuits) * shots,
                     zne_factor=1, n_bases=1, trex_executions=0, mcm_executions=shots * sum(m for _, m in lengths),
                     mean_gate_us=round(float(np.mean([g for g, _ in lengths])) if lengths else 0.0, 4))
        for rd_sweep in rep_delays_us:
            rd = rd_sweep if rd_own is None else float(rd_own)
            circ = sum(shots * (rd + g + t_meas + EXEC_OVERHEAD_US) for g, _ in lengths) * 1e-6
            tag = f"{rd_sweep:g}us"
            entry[f"circuit_seconds_at_{tag}"] = round(circ, 3)
            entry[f"trex_seconds_at_{tag}"] = 0.0
            entry[f"seconds_at_{tag}"] = round(2.0 + circ, 3)
        per_job.append(entry)
    out = dict(model_version=BUDGET_MODEL_VERSION, primitive="sampler",
               formula="2 s per job + (rep_delay + gate length + t_meas + 10 us) x executions; SamplerV2 at resilience 0: "
                       "no ZNE, no TREX term; t_meas once per terminal readout plus each measure_reset's own duration",
               readout_us=round(t_meas, 3), readout_source=t_meas_source, exec_overhead_us=EXEC_OVERHEAD_US,
               trex_randomizations=TREX_RANDOMIZATIONS, zne_noise_factors=ZNE_NOISE_FACTORS, sq_gate_us=SQ_GATE_US,
               dial_durations_us={k: round(v, 3) for k, v in dial_us.items()},
               dial_durations_source=getattr(backend, "name", None) if backend is not None else "ibm_phoenix target (2026-09-19)",
               jobs=len(per_job), circuits=sum(e["circuits"] for e in per_job), executions=sum(e["executions"] for e in per_job),
               executions_with_zne=sum(e["executions"] for e in per_job), trex_executions=0,
               mcm_executions=sum(e["mcm_executions"] for e in per_job))
    for rd in rep_delays_us:
        tag = f"{rd:g}us"
        secs = sum(e[f"seconds_at_{tag}"] for e in per_job)
        out[f"seconds_at_{tag}"] = round(secs, 2)
        out[f"minutes_at_{tag}"] = round(secs / 60.0, 3)
    out["per_job"] = per_job
    return out


# ------------------------------------------------------------------------------------------------ validation

def validate_sampler_joblist(jl: dict) -> None:
    """Schema of the Sampler fields (data/joblists/README.md, "Sampler lists"). Raises ``Paper2Error``."""
    if "init_qubits" in jl and not isinstance(jl["init_qubits"], bool):
        raise Paper2Error("init_qubits must be a JSON boolean")
    if str(jl.get("protocol", "smoke")) not in PROTOCOLS:
        raise Paper2Error(f"protocol must be one of {PROTOCOLS}")
    jobs = jl.get("sampler_jobs")
    if not isinstance(jobs, list) or not jobs:
        raise Paper2Error('a job list with primitive "sampler" needs a non-empty sampler_jobs list')
    if jl.get("points") or jl.get("probes"):
        raise Paper2Error('a job list with primitive "sampler" cannot also carry Estimator points or probes')
    for key in ("qubit_set", "q4_patches"):
        if key not in jl or not isinstance(jl[key], dict):
            raise Paper2Error(f"sampler list is missing the {key!r} object (run scripts/make_paper2_joblists.py)")
    qs = jl["qubit_set"].get("qubits")
    if not isinstance(qs, list) or not qs or len(set(qs)) != len(qs) or any(int(q) in DEAD_QUBITS for q in qs):
        raise Paper2Error("qubit_set.qubits must list distinct qubits and exclude the dead qubit 17")
    if not jl["qubit_set"].get("snapshot"):
        raise Paper2Error("qubit_set.snapshot must name the calibration CSV the list was built from")
    ids = [str(j.get("id", "")) for j in jobs]
    if len(set(ids)) != len(ids) or "" in ids:
        raise Paper2Error("every sampler job needs a unique non-empty id")
    ctx = SamplerContext.from_joblist(jl, verify=False)
    needs_q4 = False
    for j in jobs:
        if "shots" not in j or int(j["shots"]) <= 0:
            raise Paper2Error(f"sampler job {j.get('id')}: shots is required and positive")
        if "init_qubits" in j and not isinstance(j["init_qubits"], bool):
            raise Paper2Error(f"sampler job {j.get('id')}: init_qubits must be a JSON boolean")
        if "rep_delay_us" in j and j["rep_delay_us"] is not None:
            rd = j["rep_delay_us"]
            if isinstance(rd, bool) or not isinstance(rd, (int, float)) or not (0.0 < float(rd) <= 2000.0):
                raise Paper2Error(f"sampler job {j.get('id')}: rep_delay_us must be a number in (0, 2000] microseconds")
        if not isinstance(j.get("circuits"), list) or not j["circuits"]:
            raise Paper2Error(f"sampler job {j.get('id')}: circuits must be a non-empty list of specs")
        specs = expand_job(j, ctx)
        needs_q4 = needs_q4 or any(c["kind"] == "q4" for c in specs)
    if needs_q4 and len(ctx.q4_edges) != N_ROWS:
        raise Paper2Error(f"q4_patches.edges must hold one edge per row ({N_ROWS}), got {len(ctx.q4_edges)}")


# ------------------------------------------------------------------------------------------------ circuit builders

def reset_operation(kind: str, backend, qubits: Sequence[int]):
    """``(apply(qc, q, mcm_bit), synthetic)`` for a reset kind. ``reset`` and ``delay`` are Qiskit standard instructions;
    ``measure_reset`` / ``measure_reset_2`` come from ``backend.target`` (ibm_phoenix) or, on a fake target that lacks
    them, a synthetic one-qubit one-clbit instruction whose definition is measure + reset, so the dry run transpiles
    and (``--simulate``) executes them and the ``mcm`` register path is exercised. ``mcm_bit`` receives the classical
    bit(s) of a measurement-based reset when the instruction carries any."""
    if kind == "none":
        return (lambda qc, q, mcm_bit=None: None), False
    if kind == "delay":
        return (lambda qc, q, mcm_bit=None: qc.delay(reset_ns(qc.find_bit(q).index), q, unit="ns")), False
    if kind == "reset":
        return (lambda qc, q, mcm_bit=None: qc.reset(q)), False
    if kind not in RESET_KINDS:
        raise Paper2Error(f"unknown reset kind {kind!r}")
    target = backend.target
    added = _SYNTHETIC.setdefault(id(backend), {})
    if kind in added:
        op, synthetic = added[kind], True
    elif kind in target.operation_names:
        op, synthetic = target.operation_from_name(kind), False
    else:
        op = Instruction(kind, 1, 1, [])
        defn = QuantumCircuit(1, 1, name=f"{kind}_definition")
        defn.measure(0, 0)
        defn.reset(0)
        op.definition = defn
        target.add_instruction(op, {(int(q),): None for q in range(getattr(backend, "num_qubits", max(qubits) + 1))})
        added[kind] = op
        synthetic = True

    def apply(qc, q, mcm_bit=None, op=op):
        if op.num_clbits:
            if mcm_bit is None:
                raise Paper2Error(f"{kind} carries {op.num_clbits} classical bit(s) but no mcm bit was allocated")
            qc.append(op, [q], [mcm_bit] * op.num_clbits)
        else:
            qc.append(op, [q])
    return apply, synthetic


def _rotate_to_axis(qc, q, axis: str):
    if axis == "X":
        qc.h(q)
    elif axis == "Y":
        qc.sdg(q)
        qc.h(q)


def _prepare(qc, q, state: str):
    if state == "1":
        qc.x(q)
    elif state == "+":
        qc.h(q)
    elif state == "+i":
        qc.h(q)
        qc.s(q)


def build_circuit(c: dict, ctx: SamplerContext, backend) -> Tuple[QuantumCircuit, dict, List[str]]:
    """The circuit of one expanded spec on the full device register, its description (logging schema fields: reset_kind,
    mask_id, mask_hash, frame_id, reps, prep, meas_axis, expected_z, measured / reset qubits, register maps) and the
    synthetic target instructions it needed. Register ``meas`` holds the terminal readout (bit i <-> ``measured_qubits[i]``);
    register ``mcm`` (when present) the classical bits of measurement-based resets (bit i <-> ``mcm_qubits[i]``)."""
    n_dev = getattr(backend, "num_qubits", N_QUBITS)
    qr = QuantumRegister(n_dev, "q")
    kind = c["kind"]
    d: Dict[str, Any] = dict(protocol=c["protocol"], label=c["label"], kind=kind, reset_kind=None, mask_id=None, mask_hash=None,
                             frame_id=None, reps=None, prep=None, meas_axis="Z", expected_z=None, notes="")
    synthetic: List[str] = []
    if kind == "q1":
        qubits, rk, arm, m = list(ctx.qubits), c["reset_kind"], c["arm"], int(c["m"])
        measured, reset_q = qubits, (qubits if rk not in ("none", "delay") else [])
        d.update(reset_kind=rk, reps=m, prep={"a": "1", "b": "0", "c": "1", "d": c.get("prep", "1"), "e": "1", "f": "+"}[arm],
                 meas_axis="X" if arm == "f" else "Z", arm=arm)
        qc = QuantumCircuit(qr, ClassicalRegister(len(measured), "meas"), name=c["label"])
        apply, syn = reset_operation(rk, backend, qubits)
        mcm_bits = _mcm_register(qc, apply, qubits) if rk in ("measure_reset", "measure_reset_2") else None
        for q in qubits:
            _prepare(qc, qr[q], d["prep"])
        qc.barrier(qr)
        for _ in range(m):
            for i, q in enumerate(qubits):
                apply(qc, qr[q], None if mcm_bits is None else mcm_bits[i])
        if arm == "f":
            qc.barrier(qr)
            for q in qubits:
                qc.h(qr[q])
        if syn:
            synthetic.append(rk)
        d["mcm_qubits"] = list(qubits) if mcm_bits is not None else []
    elif kind == "q2":
        s, r, ax, tp, arm = int(c["mask"]), int(c["reps"]), c["axis"], c["target_prep"], c["arm"]
        roles = q2_roles(q2_masks()[s], ctx.qubits, ctx.flagged_readout)
        targets, spect = roles["targets"], roles["spectators"]
        others = [q for q in ctx.qubits if q not in set(targets)]         # spectators (kept and excluded) and controls
        measured, reset_q = list(ctx.qubits), (targets if arm == "reset" else [])
        d.update(reset_kind=arm, mask_id=f"M{s}", mask_hash=mask_hash(targets), reps=r, prep=("+" if ax != "Z" else "0") + f"/t{tp}",
                 meas_axis=ax, targets=targets, spectators=spect, excluded_spectators=roles["excluded_spectators"],
                 controls=roles["controls"], directed_pairs=len(roles["pairs"]), pairs=[list(p) for p in roles["pairs"]],
                 spectator_prep="+" if ax != "Z" else "0", target_prep=tp,
                 delay_ns_by_target={str(t): reset_ns(t) for t in targets} if arm == "delay" else None)
        qc = QuantumCircuit(qr, ClassicalRegister(len(measured), "meas"), name=c["label"])
        if ax != "Z":
            for q in others:
                qc.h(qr[q])
        if tp == "1":
            for t in targets:
                qc.x(qr[t])
        qc.barrier(qr)
        apply, _ = reset_operation("reset" if arm == "reset" else "delay", backend, targets)
        for _ in range(r):
            for t in targets:
                apply(qc, qr[t])
        qc.barrier(qr)
        for q in others:
            _rotate_to_axis(qc, qr[q], ax)
    elif kind == "q3":
        name, f, m = c["mask"], int(c["frame"]), int(c["cycles"])
        mask = ctx.q3_masks[name]
        mset = set(mask)
        spect = [q for q in ctx.qubits if q not in mset]
        frame = ctx.frames[f, :m, :]                                        # (m, n_qubits) Paulis 0..3 = I X Y Z
        final = frame[-1]
        expected = {str(q): int(final[ctx.bit_index(q)] in (1, 2)) for q in mask}   # X or Y in the last cycle -> |1>
        measured, reset_q = list(ctx.qubits), list(mask)
        d.update(reset_kind="reset", mask_id=name, mask_hash=mask_hash(mask), frame_id=f, reps=m, prep="1/+", meas_axis="Z/X",
                 expected_z=expected, expected_z_string="".join(str(expected[str(q)]) for q in mask), mask_qubits=list(mask),
                 spectators=spect, dense=name.startswith("dense"), frame_hash=hashlib.sha256(np.ascontiguousarray(frame).tobytes()).hexdigest()[:16])
        qc = QuantumCircuit(qr, ClassicalRegister(len(measured), "meas"), name=c["label"])
        for q in mask:
            qc.x(qr[q])
        for q in spect:
            qc.h(qr[q])
        qc.barrier(qr)
        for cyc in range(m):
            row = frame[cyc]
            for q in ctx.qubits:
                _pauli(qc, qr[q], int(row[ctx.bit_index(q)]))
            for q in mask:
                qc.reset(qr[q])
            for q in spect:
                qc.delay(RESET_NS_DEFAULT, qr[q], unit="ns")
            for q in ctx.qubits:
                _pauli(qc, qr[q], int(row[ctx.bit_index(q)]))
            qc.barrier(qr)
        for q in spect:
            qc.h(qr[q])
    else:  # q4
        p, k, inp, ax = float(c["p"]), int(c["mask"]), c["input"], c["axis"]
        patterns = ctx.q4_mask_arrays[p][k]                                # (n_patches, 2)
        patch_qubits = ctx.q4_qubits
        reset_q = [q for (a, b), (ra, rb) in zip(ctx.q4_edges, patterns) for q, hit in ((a, ra), (b, rb)) if hit]
        measured = patch_qubits
        d.update(reset_kind="reset", mask_id=f"p{p:g}_k{k}", mask_hash=mask_hash(reset_q), reps=1, prep=inp, meas_axis=ax, p=p,
                 patterns=[f"{int(ra)}{int(rb)}" for ra, rb in patterns], patches=[list(e) for e in ctx.q4_edges],
                 delay_qubits=[q for q in patch_qubits if q not in set(reset_q)])
        qc = QuantumCircuit(qr, ClassicalRegister(len(measured), "meas"), name=c["label"])
        for q in patch_qubits:
            _prepare(qc, qr[q], inp)
        qc.barrier(*[qr[q] for q in patch_qubits])
        rset = set(reset_q)
        for q in patch_qubits:
            if q in rset:
                qc.reset(qr[q])
            else:
                qc.delay(reset_ns(q), qr[q], unit="ns")
        qc.barrier(*[qr[q] for q in patch_qubits])
        for q in patch_qubits:
            _rotate_to_axis(qc, qr[q], ax)
    for i, q in enumerate(measured):
        qc.measure(qr[q], qc.cregs[0][i])
    d.update(measured_qubits=list(measured), reset_qubits=list(reset_q), n_measured=len(measured),
             reset_ns_assumed=sorted({reset_ns(q) for q in reset_q}) if reset_q else [],
             registers={cr.name: (list(measured) if cr.name == "meas" else d.get("mcm_qubits", [])) for cr in qc.cregs})
    return qc, d, synthetic


def _pauli(qc, q, code: int):
    if code == 1:
        qc.x(q)
    elif code == 2:
        qc.y(q)
    elif code == 3:
        qc.z(q)


def _mcm_register(qc, apply, qubits):
    """Allocate the ``mcm`` register (one bit per qubit) when the reset kind carries classical bits; None otherwise."""
    op = getattr(apply, "__defaults__", None)
    op = op[-1] if op else None
    if op is None or not getattr(op, "num_clbits", 0):
        return None
    cr = ClassicalRegister(len(qubits), "mcm")
    qc.add_register(cr)
    return [cr[i] for i in range(len(qubits))]


@dataclass
class BuiltSampler:
    """One transpiled Sampler circuit; duck-types the interface ``gradvar.hardware.write_job_bundle`` uses."""
    spec: dict
    desc: dict
    isa_circuit: object
    depth: int
    two_qubit_gates: int
    joblist_entry: dict
    synthetic_target_instructions: List[str] = field(default_factory=list)
    sched_ns: float | None = None
    reset_ns_target: Dict[str, float] = field(default_factory=dict)
    job_kind: str = "sampler"
    patch = None
    edge = None
    layout = None

    @property
    def qubits(self) -> Tuple[int, ...]:
        return tuple(sorted(set(self.desc["measured_qubits"]) | set(self.desc["reset_qubits"])))

    def pub(self):
        return (self.isa_circuit,)

    def describe(self) -> dict:
        d = dict(self.desc)
        d.update(n=self.desc["n_measured"], L=None, k_1based=None, probe_id=self.desc["label"], qubits=list(self.qubits),
                 sched_ns=self.sched_ns, reset_ns_target=self.reset_ns_target,
                 synthetic_target_instructions=list(self.synthetic_target_instructions), spec=dict(self.spec))
        return d

    def payload(self) -> dict:
        return dict(observables=None, param_values=None, register_sizes={k: len(v) for k, v in self.desc["registers"].items()})


def scheduled_ns(isa, backend) -> float | None:
    """Scheduled duration of an ISA circuit from the target's instruction durations (``QuantumCircuit.estimate_duration``),
    None when an instruction has no duration (synthetic stand-ins on a fake target)."""
    try:
        return round(float(isa.estimate_duration(backend.target, unit="s")) * 1e9, 3)
    except Exception:
        return None


def target_reset_ns(backend, qubits: Iterable[int]) -> Dict[str, float]:
    t = getattr(backend, "target", None)
    if t is None or "reset" not in t.operation_names or not t["reset"]:
        return {}
    out = {}
    for q in qubits:
        p = t["reset"].get((int(q),))
        if p is not None and getattr(p, "duration", None):
            out[str(int(q))] = round(float(p.duration) * 1e9, 3)
    return out


def build_job(job: dict, ctx: SamplerContext, backend, optimization_level: int = 1, seed_transpiler: int | None = None) -> List[BuiltSampler]:
    """Expand and transpile one sampler job (identity initial layout on the device register; one pass manager per job)."""
    from .hardware import two_qubit_count
    specs = expand_job(job, ctx)
    n_dev = getattr(backend, "num_qubits", N_QUBITS)
    pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend, initial_layout=list(range(n_dev)),
                                      seed_transpiler=ctx.seed if seed_transpiler is None else seed_transpiler)
    built = []
    for c in specs:
        qc, desc, synthetic = build_circuit(c, ctx, backend)
        isa = pm.run(qc)
        built.append(BuiltSampler(spec=c, desc=desc, isa_circuit=isa, depth=isa.depth(), two_qubit_gates=two_qubit_count(isa),
                                  joblist_entry=job, synthetic_target_instructions=synthetic, sched_ns=scheduled_ns(isa, backend),
                                  reset_ns_target=target_reset_ns(backend, desc["reset_qubits"])))
    return built


# ------------------------------------------------------------------------------------------------ results and logging

def capture_registers(result, group: Sequence[BuiltSampler]) -> Tuple[dict, dict]:
    """Per-shot capture of every classical register of every pub: ``arrays`` maps ``pub<i>__<register>`` to the packed
    uint8 BitArray (shape (shots, ceil(bits / 8)), Qiskit bit order) plus ``__num_bits``; ``summary`` gives per register
    the shot and bit counts, the per-bit P(1) marginals (bit i <-> the register's qubit i in the description), the
    number of distinct outcomes and, when there are at most 1024 distinct outcomes, the counts dict."""
    arrays, summary = {}, {}
    for i, (pub, b) in enumerate(zip(result, group)):
        data = pub.data
        regs = {}
        names = list(data.keys()) if hasattr(data, "keys") else [k for k in vars(data) if not k.startswith("_")]
        for name in names:
            ba = getattr(data, name)
            if not hasattr(ba, "num_shots"):
                continue
            arr = np.asarray(ba.array, dtype=np.uint8)
            arrays[f"pub{i}__{name}"] = arr
            arrays[f"pub{i}__{name}__num_bits"] = np.asarray([ba.num_bits], dtype=np.int64)
            bits = np.unpackbits(arr, axis=1, bitorder="big")[:, -ba.num_bits:][:, ::-1]   # column j <-> register bit j
            marg = bits.mean(axis=0) if ba.num_shots else np.zeros(ba.num_bits)
            counts = ba.get_counts()
            regs[name] = dict(num_shots=int(ba.num_shots), num_bits=int(ba.num_bits), qubits=list(b.desc["registers"].get(name, [])),
                              p1_per_bit=[round(float(x), 8) for x in marg], distinct_outcomes=len(counts),
                              counts=counts if len(counts) <= 1024 else None,
                              all_zero_fraction=round(float(counts.get("0" * ba.num_bits, 0)) / max(1, ba.num_shots), 8))
        summary[str(i)] = dict(label=b.desc["label"], registers=regs)
    return arrays, summary


def write_counts(bundle_dir: Path, result, group: Sequence[BuiltSampler]) -> Tuple[str, dict]:
    """``bitarrays.npz`` (compressed per-shot registers) and ``counts.json`` (per-register summary); returns the npz path."""
    arrays, summary = capture_registers(result, group)
    npz = bundle_dir / "bitarrays.npz"
    np.savez_compressed(npz, **arrays)
    (bundle_dir / "counts.json").write_text(json.dumps(dict(bit_order="column j of the unpacked array is register bit j (qubit registers[name][j])",
                                                            pubs=summary), indent=1))
    return str(npz), summary


def sampler_rows(backend, job_id: str, snapshot: str, stage: str, group: Sequence[BuiltSampler], shots: int, init_qubits: bool,
                 options=None, submit_time: str | None = None, counts_path: str | None = None, qpu_seconds=None, notes: str = "") -> List[dict]:
    """One CSV row per circuit (pre-registration Section 5 logging schema)."""
    from .hardware import granted_rep_delay
    rows = []
    for i, b in enumerate(group):
        d = b.desc
        ez = d.get("expected_z_string") if d.get("expected_z") is not None else ""
        rows.append({
            "backend": getattr(backend, "name", str(backend)), "job_id": job_id, "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_submit_time": submit_time or "", "calibration_snapshot": snapshot, "stage": stage, "protocol": d["protocol"],
            "circuit_index": i, "label": d["label"], "reset_kind": d.get("reset_kind") or "", "mask_id": d.get("mask_id") or "",
            "mask_hash": d.get("mask_hash") or "", "frame_id": "" if d.get("frame_id") is None else d["frame_id"],
            "reps": "" if d.get("reps") is None else d["reps"], "prep": d.get("prep") or "", "meas_axis": d.get("meas_axis") or "",
            "expected_z": ez or "", "shots": shots, "rep_delay_granted": granted_rep_delay(options), "init_qubits": init_qubits,
            "sched_ns": "" if b.sched_ns is None else b.sched_ns,
            "reset_ns": " ".join(f"{v:g}" for v in d.get("reset_ns_assumed", [])), "n_measured": d["n_measured"],
            "counts_path": counts_path or "", "qpu_seconds": "" if qpu_seconds is None else qpu_seconds,
            "transpiled_depth": b.depth, "notes": notes,
        })
    return rows


def append_sampler_rows(log_path: str, rows: List[dict]):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    new = not Path(log_path).exists()
    with open(log_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SAMPLER_LOG_COLUMNS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in SAMPLER_LOG_COLUMNS})


def configure_sampler(sampler, job: dict, jl: dict):
    """SamplerV2 options of a Paper 2 job: shots, ``execution.init_qubits`` (Section 3 "Execution": True except the one
    Q1 job), resilience 0 (no gate or measurement twirling, no dynamical decoupling), and the job's own ``rep_delay_us``
    when set (Deviation 1). Returns the resolved ``init_qubits``."""
    init = bool(job.get("init_qubits", jl.get("init_qubits", True)))
    o = sampler.options
    o.default_shots = int(job["shots"])
    o.execution.init_qubits = init
    try:
        o.twirling.enable_gates = False
        o.twirling.enable_measure = False
        o.dynamical_decoupling.enable = False
    except Exception:  # pragma: no cover - a stand-in options object without these groups
        pass
    rd = job.get("rep_delay_us")
    if rd is not None:
        o.execution.rep_delay = float(rd) / 1e6
    return init


def sampler_layout_check(jl: dict, ctx: SamplerContext, groups: Sequence[Tuple[dict, List[BuiltSampler]]], backend, enforce: bool) -> dict:
    """Paper 1 Deviation 26 live re-check over every qubit the list uses (no couplers: no two-qubit gate in any Paper 2
    circuit), with the Paper 2 policy: qubits failing the readout cut are *flagged* (Section 3: outliers are flagged on
    the maps, not dropped; Q2 spectators above the cut are already excluded at build time from the snapshot), a
    non-operational used qubit or a failing Q4 patch qubit refuses on the submitting path (the pre-registered sets must
    be regenerated from the day's snapshot; ``layout_check: "override"`` is never accepted for a Q4 patch qubit)."""
    from .hardware import layout_check
    used = sorted({q for _, g in groups for b in g for q in b.qubits})
    chk = layout_check(backend, used, couplers=())
    q4_used = sorted(set(ctx.q4_qubits) & set(used)) if any(b.desc["kind"] == "q4" for _, g in groups for b in g) else []
    failing = set(chk["failing_qubits"])
    dead_live = sorted(q for q in used if chk["qubits"].get(str(q), {}).get("operational") is False)
    protected_failing = sorted(q for q in q4_used if q in failing)
    flagged_live = sorted(q for q in failing if q not in set(protected_failing) | set(dead_live))
    override = str(jl.get("layout_check_reason", "")).strip() if str(jl.get("layout_check", "")).lower() == "override" else None
    denied = None
    if override and protected_failing:
        denied = f"override not accepted for failing Q4 patch qubit(s) {protected_failing}: the pair is the measured observable (Deviation 26)"
    chk.update(enforced=bool(enforce), override=override, layout_qubits=used, layout_couplers=[], edge_cone_qubits=q4_used,
               failing_protected_qubits=protected_failing, non_operational_qubits=dead_live, flagged_live_qubits=flagged_live,
               snapshot_flags=dict(readout=list(ctx.flagged_readout), cz_cluster=list(ctx.flagged_cz_cluster)), override_denied=denied,
               policy="Paper 2: readout failures are flagged, not dropped; refuse on a non-operational used qubit or a failing Q4 patch qubit")
    if not enforce:
        chk["action"] = "logged"
    elif chk["verdict"] == "unavailable":
        chk["action"] = "refuse"
        chk["reason"] = chk.get("reason") or "live properties unavailable"
    elif dead_live or (protected_failing and (not override or denied)):
        chk["action"] = "refuse"
    elif protected_failing:
        chk["action"] = "submit-with-override"
    else:
        chk["action"] = "submit-flagged" if flagged_live else "submit"
    return chk


def _layout_message(chk: dict) -> str:
    msg = f"layout check {chk['verdict']} over {len(chk.get('layout_qubits', []))} qubits (readout cut {chk['readout_cut']:g}, " \
          f"init error cut {chk['init_error_cut']:g}; properties {chk.get('properties_last_update')}): "
    parts = []
    if chk.get("flagged_live_qubits"):
        parts.append(f"flagged (kept) {chk['flagged_live_qubits']}")
    if chk.get("non_operational_qubits"):
        parts.append(f"NOT OPERATIONAL {chk['non_operational_qubits']}")
    if chk.get("failing_protected_qubits"):
        parts.append(f"Q4 patch qubits failing {chk['failing_protected_qubits']}")
    if chk.get("override_denied"):
        parts.append(chk["override_denied"])
    return msg + ("; ".join(parts) or chk.get("reason") or "all within the cuts") + f"; action {chk.get('action')}"


def aer_sampler():
    from qiskit_aer.primitives import SamplerV2 as AerSampler
    return AerSampler(options=dict(backend_options=dict(method="stabilizer")))


def simulate_group(group: Sequence[BuiltSampler], shots: int):
    """Run the ISA circuits of one job on the Aer stabilizer simulator (all Paper 2 circuits are Clifford), decomposing
    synthetic measurement-based resets through their definitions; returns the PrimitiveResult."""
    circs = []
    for b in group:
        c = b.isa_circuit
        if b.synthetic_target_instructions:
            c = c.decompose(gates_to_decompose=list(b.synthetic_target_instructions))
        circs.append(c)
    return aer_sampler().run([(c,) for c in circs], shots=int(shots)).result()


def execute_sampler_joblist(jl: dict, backend, submit: bool, run_root: str = "data/runs", log_path: str | None = None,
                            calibration_csv: str | None = None, instance_plan: str | None = None, simulate: bool = False,
                            simulate_shots: int | None = None) -> List[dict]:
    """Build every ``sampler_jobs`` entry, run one SamplerV2 job per entry (one Batch when submitting), write one bundle per
    job (``gradvar.hardware.write_job_bundle`` layout plus ``bitarrays.npz`` / ``counts.json`` when a result exists) and
    append one row per circuit to ``log_path``. ``submit=False`` writes the same layout against the fake backend with job
    ids ``dryrun-<utc>-<job id>``; ``simulate`` additionally executes each job on the Aer stabilizer simulator (at
    ``simulate_shots`` if given) so the result files are exercised. A job whose ``result()`` raises gets a bundle with the
    error; the runner continues and exits non-zero at the end. THIS FUNCTION SUBMITS ONLY WHEN ``submit`` IS TRUE."""
    from qiskit_ibm_runtime import SamplerV2
    from .hardware import estimate_budget, rep_delay_info, snapshot_calibration, write_job_bundle
    cal_dir = Path(calibration_csv).parent if calibration_csv else None
    ctx = SamplerContext.from_joblist(jl, calibration_dir=cal_dir, verify=True)
    stage = str(jl.get("protocol", "smoke"))
    groups = [(job, build_job(job, ctx, backend)) for job in jl["sampler_jobs"]]
    rd = rep_delay_info(backend)
    if jl.get("rep_delay_probe"):
        print(f"rep_delay probe: {getattr(backend, 'name', backend)} default_rep_delay={rd['default_rep_delay_s']} s, "
              f"rep_delay_range={rd['rep_delay_range_s']} s, dynamic_reprate_enabled={rd['dynamic_reprate_enabled']} (source: {rd['source']})")
    budget_target = estimate_budget(jl, backend=backend)
    print(f"budget (model v{budget_target['model_version']}, sampler) with {getattr(backend, 'name', 'backend')} target durations: "
          f"{budget_target['minutes_at_250us']} min at 250 us, {budget_target['minutes_at_1us']} min at 1 us (t_meas {budget_target['readout_us']} us)")
    chk = sampler_layout_check(jl, ctx, groups, backend, enforce=submit)
    print(_layout_message(chk))
    if submit and chk["action"] == "refuse":
        raise SystemExit(f"refusing to submit: {_layout_message(chk)}; regenerate the Paper 2 lists from the day's snapshot")
    extra_base = dict(instance_plan=instance_plan, budget=jl.get("budget"), budget_estimate_with_target_durations=budget_target,
                      layout_check=chk, primitive="sampler", protocol=stage,
                      qubit_set=dict(qubits=list(ctx.qubits), flagged_readout=list(ctx.flagged_readout), flagged_cz_cluster=list(ctx.flagged_cz_cluster),
                                     snapshot=ctx.snapshot, exclusion=list(ctx.exclusion)),
                      q4_patches=[list(e) for e in ctx.q4_edges], randomness=jl.get("randomness"))
    root = Path(run_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows: List[dict] = []
    failures: List[str] = []

    def finish(d: Path, job_id, job, group, result, shots, init, options, created, qpu=None, note=""):
        counts_path = None
        if result is not None:
            counts_path, summary = write_counts(d, result, group)
            regs = sorted({r for s in summary.values() for r in s["registers"]})
            print(f"  registers captured: {regs} ({sum(len(s['registers']) for s in summary.values())} register arrays) -> {counts_path}")
        rows.extend(sampler_rows(backend, job_id, snapshot, stage, group, shots, init, options=options, submit_time=created,
                                 counts_path=counts_path, qpu_seconds=qpu, notes=note))

    if not submit:
        snapshot = calibration_csv or (ctx.snapshot or "dry-run: no snapshot")
        for job, group in groups:
            sampler = SamplerV2(mode=backend)
            init = configure_sampler(sampler, job, jl)
            shots = int(job["shots"])
            job_id = f"dryrun-{stamp}-{job['id']}"
            created = datetime.now(timezone.utc).isoformat()
            result, note = None, ""
            if simulate:
                sim_shots = int(simulate_shots or shots)
                result = simulate_group(group, sim_shots)
                note = f"dry run simulated on AerSimulator(stabilizer) at {sim_shots} shots"
            extra = dict(extra_base, init_qubits=init, sampler_job=job["id"], simulated=bool(simulate),
                         simulate_shots=None if not simulate else int(simulate_shots or shots),
                         synthetic_target_instructions=sorted({s for b in group for s in b.synthetic_target_instructions}))
            d = write_job_bundle(root, job_id, group, backend, sampler.options, 0, shots, jl, dry=True, result=result,
                                 timestamps=dict(created=created), extra=extra)
            finish(d, job_id, job, group, result, shots, init, sampler.options, created, note=note)
            names = sorted({n for b in group for n in b.isa_circuit.count_ops() if n != "barrier"})
            print(f"dry run: wrote {d} ({len(group)} circuits, sampler, shots {shots}, init_qubits {init}, ISA ops {names}); nothing submitted")
    else:
        from qiskit_ibm_runtime import Batch
        snapshot = calibration_csv or snapshot_calibration(backend)
        with Batch(backend=backend) as batch:
            jobs = []
            for job, group in groups:
                sampler = SamplerV2(mode=batch)
                init = configure_sampler(sampler, job, jl)
                shots = int(job["shots"])
                created = datetime.now(timezone.utc).isoformat()
                rj = sampler.run([b.pub() for b in group])
                jobs.append((job, group, rj, sampler.options, created, init, shots))
                print(f"submitted job {rj.job_id()} ({job['id']}: sampler, {len(group)} circuits, shots {shots}, init_qubits {init})")
            for job, group, rj, options, created, init, shots in jobs:
                job_id = rj.job_id()
                extra = dict(extra_base, init_qubits=init, sampler_job=job["id"], simulated=False,
                             synthetic_target_instructions=sorted({s for b in group for s in b.synthetic_target_instructions}))
                try:
                    result = rj.result()
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    failures.append(f"{job_id} ({job['id']}): {err}")
                    d = write_job_bundle(root, job_id, group, backend, options, 0, shots, jl, job=rj, error=err,
                                         timestamps=dict(submitted_local=created, failed_local=datetime.now(timezone.utc).isoformat()), extra=extra)
                    print(f"job {job_id} ({job['id']}) FAILED: {err}; wrote {d}; continuing with the remaining jobs", file=sys.stderr)
                    continue
                completed = datetime.now(timezone.utc).isoformat()
                d = write_job_bundle(root, job_id, group, backend, options, 0, shots, jl, result=result, job=rj,
                                     timestamps=dict(submitted_local=created, result_received_local=completed), extra=extra)
                qpu = None
                try:
                    qpu = rj.usage()
                except Exception:
                    pass
                finish(d, job_id, job, group, result, shots, init, options, created, qpu=qpu)
                print(f"wrote {d}")
    if log_path:
        append_sampler_rows(log_path, rows)
        print(f"logged {len(rows)} rows to {log_path}")
    if failures:
        raise SystemExit(f"{len(failures)} of {len(groups)} jobs failed (bundles written, rows of the succeeded jobs logged):\n  "
                         + "\n  ".join(failures))
    return rows
