"""Independent reference for Deviation 60 (H7 comparator bug check): the second-moment chain of the dial-law interpretation note
(docs/memos/dial_law_note_2026-09-24.md, Sections 1-2), copied verbatim from that session's ``dial_law_engine.py`` (artifact
b77a0b3c, 25 Sep 2026) apart from this paragraph. It shares no code with ``gradvar.pauliprop``: bit-packed uint64 strings (n <= 64),
the Ry gate as one rotation (not the transpiled sx-rz-sx), the dial as the ideal mixture, no gate, readout or idle noise. Used by
``tests/test_pauliprop_truncation.py`` and ``scripts/predict_h7_truncation.py``; do not edit (an edit would turn the check into a
self-comparison).

Reset-dial second-moment engines for the Paper 1 Ry/CZ ansatz (idealised model: no gate, readout or idle noise).

Forward layer l = 1..L: Ry(theta_{l,q}) on every qubit; CZ on every live coupler; N_p on every qubit,
N_p(rho) = (1 - p) rho + p |0><0|_q (x) Tr_q rho.  theta i.i.d. uniform on [0, 2 pi).  O = Z_a Z_b, input |0^n>.

1. `chain_*`: squared-Pauli-weight transfer (exact for uniform angles; the Z -> I reset branch is always followed by a
   rotation on the same qubit in the same layer, so its cross terms average to zero).  Bit-packed numpy (n <= 64),
   threshold delta, dropped mass recorded per Heisenberg step.
2. `exact_*`: two-copy density-matrix propagation with the angle average done exactly on an 8-point grid
   (trig degree <= 2 per angle), for n <= 5.  Independent of the path-orthogonality argument.
3. `onebody_*`: closed forms from the single-site sector (rigorous lower bounds, ideal model).
"""
import numpy as np

U1 = np.uint64(1)


def bc(a):
    return np.bitwise_count(a).astype(np.int64)


# ------------------------------------------------------------------------------------------------ geometry
class Patch:
    def __init__(self, qubits, edges, obs):
        self.qubits = list(qubits)
        self.n = len(self.qubits)
        self.idx = {q: i for i, q in enumerate(self.qubits)}
        self.edges = [(self.idx[a], self.idx[b]) for a, b in edges]
        nb = [0] * self.n
        for a, b in self.edges:
            nb[a] |= 1 << b
            nb[b] |= 1 << a
        self.nbr = np.array(nb, dtype=np.uint64)
        self.obs = (self.idx[obs[0]], self.idx[obs[1]])
        self.deg = [bin(x).count("1") for x in nb]


def lattice_patch(rows, cols, origin=(0, 0), width=10, holes=(), broken=(), obs=None):
    r0, c0 = origin
    qid = lambda r, c: (r0 + r) * width + (c0 + c)
    hs = set(holes)
    qubits = [qid(r, c) for r in range(rows) for c in range(cols) if qid(r, c) not in hs]
    br = {tuple(sorted(e)) for e in broken}
    edges = []
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr < rows and cc < cols:
                    e = tuple(sorted((qid(r, c), qid(rr, cc))))
                    if e[0] in hs or e[1] in hs or e in br:
                        continue
                    edges.append(e)
    return Patch(qubits, edges, obs if obs is not None else edges[0])


# ------------------------------------------------------------------------------------------------ chain engine
def _merge(X, Z, W):
    if len(W) <= 1:
        return X, Z, W
    o = np.lexsort((Z, X))
    X, Z, W = X[o], Z[o], W[o]
    d = np.empty(len(W), bool)
    d[0] = True
    d[1:] = (X[1:] != X[:-1]) | (Z[1:] != Z[:-1])
    s = np.flatnonzero(d)
    return X[s], Z[s], np.add.reduceat(W, s)


def _prune(X, Z, W, delta, acc):
    if delta <= 0:
        return X, Z, W
    k = W >= delta
    if k.all():
        return X, Z, W
    acc[0] += float(W[~k].sum())
    return X[k], Z[k], W[k]


def _noise(X, Z, W, n, p, delta, acc, cap, rule=None):
    """Squared-weight rule of the per-layer single-qubit channel (Heisenberg): X -> ax X, Y -> ay Y, Z -> az Z + b I.
    Default: the dial mixture N_p (ax = ay = az = (1-p)^2, b = p^2).  rule = (ax, ay, az, b) for other channels,
    e.g. (1-p, 1-p, 1-p, p) for the per-mask second moment E_mask[C_mask^2] (same mask on both copies)."""
    ax, ay, az, b = rule if rule is not None else ((1 - p) ** 2, (1 - p) ** 2, (1 - p) ** 2, p ** 2)
    W = W * ax ** bc(X & ~Z) * ay ** bc(X & Z)
    for q in range(n):
        bit = U1 << np.uint64(q)
        m = ((Z & ~X) & bit) != 0
        if not m.any():
            continue
        W = W.copy()
        if b == 0:
            W[m] *= az
            continue
        Xn, Zn, Wn = X[m], Z[m] & ~bit, W[m] * b
        W[m] *= az
        X, Z, W = np.concatenate([X, Xn]), np.concatenate([Z, Zn]), np.concatenate([W, Wn])
        X, Z, W = _prune(X, Z, W, delta, acc)
        if len(W) > cap:
            X, Z, W = _merge(X, Z, W)
    return _merge(X, Z, W)


def _cz(X, Z, nbr, n):
    Z = Z.copy()
    for q in range(n):
        m = (X & (U1 << np.uint64(q))) != 0
        if m.any():
            Z[m] ^= nbr[q]
    return X, Z


def _ry(X, Z, W, n, delta, acc, cap, mark=None):
    if mark is not None:
        k = ((X ^ Z) & (U1 << np.uint64(mark))) != 0
        X, Z, W = X[k], Z[k], W[k]
    for q in range(n):
        bit = U1 << np.uint64(q)
        m = ((X ^ Z) & bit) != 0
        if not m.any():
            continue
        Xm, Zm, Wm = X[m], Z[m], W[m] * 0.5
        keep = ~m
        X = np.concatenate([X[keep], Xm & ~bit, Xm | bit])
        Z = np.concatenate([Z[keep], Zm | bit, Zm & ~bit])
        W = np.concatenate([W[keep], Wm, Wm])
        X, Z, W = _prune(X, Z, W, delta, acc)
        if len(W) > cap:
            X, Z, W = _merge(X, Z, W)
    return _merge(X, Z, W)


def chain_run(patch, p, L, cuts=(), mark=None, delta=1e-12, cap=2_000_000, start=None, rule=None):
    """Back-propagate O through L layers.  mark = (k, local qubit): derivative at forward layer k.
    start: optional initial (X, Z, W) arrays (default: the observable Z_a Z_b).
    Returns EC2 (sum of final diagonal weights), per-cut (A, B, diagonal-weight histogram by Z-count),
    cumulative dropped mass per Heisenberg step and the peak string count."""
    n = patch.n
    if start is None:
        a, b = patch.obs
        X = np.zeros(1, np.uint64)
        Z = np.array([(1 << a) | (1 << b)], dtype=np.uint64)
        W = np.ones(1)
    else:
        X, Z, W = start
    acc, drop, nmax, cut_out = [0.0], [], 1, {}
    for step in range(1, L + 1):
        layer = L - step + 1
        X, Z, W = _noise(X, Z, W, n, p, delta, acc, cap, rule)
        X, Z = _cz(X, Z, patch.nbr, n)
        mk = mark[1] if (mark is not None and mark[0] == layer) else None
        X, Z, W = _ry(X, Z, W, n, delta, acc, cap, mark=mk)
        drop.append(acc[0])
        nmax = max(nmax, len(W))
        if step in cuts:
            d = X == 0
            zc = bc(Z[d])
            cut_out[step] = dict(A=float(W[d].sum()), B=float((W[d] * p ** zc).sum()),
                                 hist={int(k): float(W[d][zc == k].sum()) for k in np.unique(zc)})
    d = X == 0
    return dict(EC2=float(W[d].sum()), cuts=cut_out, drop=drop, nmax=nmax, nfinal=len(W))


def chain_quantities(patch, p, L, ells=(1, 2, 3, 4), delta=1e-12, grads=True, q0=None):
    r = chain_run(patch, p, L, cuts=ells, delta=delta)
    out = dict(EC2=r["EC2"], var_c=r["EC2"] - p ** 4, drop_total=r["drop"][-1], nmax=r["nmax"])
    out["msd"] = {l: r["EC2"] - 2 * c["B"] + c["A"] for l, c in r["cuts"].items()}
    out["msd_bound"] = {l: 4 * r["drop"][l - 1] + (r["drop"][-1] - r["drop"][l - 1]) for l in r["cuts"]}
    out["cut_hist"] = {l: c["hist"] for l, c in r["cuts"].items()}
    if grads:
        q = patch.obs[0] if q0 is None else q0
        for k, name in ((L, "vk_L"), (1, "vk_1")):
            g = chain_run(patch, p, L, mark=(k, q), delta=delta)
            out[name], out[name + "_drop"] = g["EC2"], g["drop"][-1]
    return out


# ------------------------------------------------------------------------------------------------ exact two-copy engine
def _ry_mat(t):
    c, s = np.cos(t / 2), np.sin(t / 2)
    return np.array([[c, -s], [s, c]])


def _apply_1q(rho, U, j, N):
    D = 2 ** N
    r = rho.reshape(2 ** j, 2, 2 ** (N - j - 1), D)
    r = np.einsum("ab,ibkm->iakm", U, r).reshape(D, D)
    r = r.reshape(D, 2 ** j, 2, 2 ** (N - j - 1))
    r = np.einsum("ab,mibk->miak", U.conj(), r).reshape(D, D)
    return r


def _reset_mix(rho, p, j, N):
    D = 2 ** N
    R = rho.reshape(2 ** j, 2, 2 ** (N - j - 1), 2 ** j, 2, 2 ** (N - j - 1))
    T = R[:, 0, :, :, 0, :] + R[:, 1, :, :, 1, :]
    out = (1 - p) * R
    out[:, 0, :, :, 0, :] += p * T
    return out.reshape(D, D)


def exact_pair(n, edges, obs, p, L, mode, ell=None, mark=None, G=8):
    """E[C1 C2] for two copies of the circuit, angle-averaged exactly.
    mode 'full': both copies run L layers.  'cross': copy 1 full, copy 2 = last ell layers from |0>.
    'trunc': both copies last ell layers from |0>.  'grad': both full, copy 1 shifted +pi/2 and copy 2 -pi/2 at
    mark = (k, q) (forward layer k)."""
    N = 2 * n
    D = 2 ** N
    rho = np.zeros((D, D), complex)
    rho[0, 0] = 1.0
    bits = (np.arange(D)[:, None] >> (N - 1 - np.arange(N))[None, :]) & 1  # qubit j = bit (N-1-j) (big-endian)
    thetas = 2 * np.pi * np.arange(G) / G
    def cz_sign(active):
        ph = np.zeros(D, int)
        for c in active:
            off = c * n
            for u, v in edges:
                ph += bits[:, off + u] * bits[:, off + v]
        return (-1.0) ** ph
    s_both, s_1 = cz_sign((0, 1)), cz_sign((0,))
    for layer in range(1, L + 1):
        if mode in ("cross", "trunc"):
            shared = layer > L - ell
            active = (0, 1) if shared else ((0,) if mode == "cross" else ())
        else:
            active = (0, 1)
        if not active:
            continue
        for q in range(n):
            acc = np.zeros_like(rho)
            for t in thetas:
                r = rho
                for c in active:
                    tt = t
                    if mode == "grad" and mark == (layer, q):
                        tt = t + (np.pi / 2 if c == 0 else -np.pi / 2)
                    r = _apply_1q(r, _ry_mat(tt), c * n + q, N)
                acc += r
            rho = acc / G
        sg = s_both if active == (0, 1) else s_1
        rho = rho * sg[:, None] * sg[None, :]
        for c in active:
            for q in range(n):
                rho = _reset_mix(rho, p, c * n + q, N)
    a, b = obs
    o1 = (1 - 2 * bits[:, a]) * (1 - 2 * bits[:, b])
    o2 = (1 - 2 * bits[:, n + a]) * (1 - 2 * bits[:, n + b])
    return float(np.real(np.sum(np.diag(rho) * o1 * o2)))


def exact_quantities(n, edges, obs, p, L, ells=(1, 2), q0=None):
    EC2 = exact_pair(n, edges, obs, p, L, "full")
    out = dict(EC2=EC2, var_c=EC2 - p ** 4, msd={})
    for l in ells:
        cr = exact_pair(n, edges, obs, p, L, "cross", ell=l)
        tr = exact_pair(n, edges, obs, p, L, "trunc", ell=l)
        out["msd"][l] = EC2 - 2 * cr + tr
    q = obs[0] if q0 is None else q0
    for k, name in ((L, "vk_L"), (1, "vk_1")):
        out[name] = 0.5 * (EC2 - exact_pair(n, edges, obs, p, L, "grad", mark=(k, q)))
    return out


# ------------------------------------------------------------------------------------------------ one-body law
def onebody(p, L, ells=(1, 2, 3, 4)):
    """Single-site-sector closed forms (ideal model, interior edge, rigorous lower bounds).
    r = (1-p)^2/2 per layer for a lone Z (Ry keeps Z half the time; the X half spreads through the CZs);
    ZZ decays as r^2 and feeds each lone Z at p^2 r per layer; each lone Z feeds the identity at p^2 per layer."""
    r = 0.5 * (1 - p) ** 2
    z1 = lambda j: p ** 2 * r ** j * (1 - r ** j) / (1 - r)
    z2 = lambda j: r ** (2 * j)
    s = lambda m: p ** 2 * (1 - r ** m) / (1 - r) + r ** m          # E_m[<Z_q>^2] after m layers
    def ec2(m):                                                      # E_m[C^2] after m layers
        if m == 0:
            return 1.0
        return p ** 4 + sum(2 * p ** 2 * z1(j) + p ** 4 * z2(j) for j in range(1, m)) + 2 * z1(m) + z2(m)
    var_c = ec2(L) - p ** 4
    vk_L = p ** 2 * r * s(L - 1) + r ** 2 * ec2(L - 1)
    vk_1 = z1(L) + r ** 2 * z2(L - 1)                                # formula (B) at k = 1 (s_0 = 1, E_0[C^2] = 1)
    msd = {l: 2 * z1(l) * (s(L - l) - 2 * p + 1) + z2(l) * (ec2(L - l) - 2 * p ** 2 + 1) for l in ells if l < L}
    var_inf = p ** 4 * r / (1 - r ** 2) * (2 / (1 - r) + r)
    return dict(r=r, var_c=var_c, var_inf=var_inf, vk_L=vk_L, vk_1=vk_1, msd=msd,
                floor_var=p ** 4 * (1 - p) ** 2, floor_kL=0.5 * p ** 4 * (1 - p) ** 2)
