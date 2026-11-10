"""Deviation 64 (draft), generating model of the H7 interval simulation: kurtosis over theta of Delta = C_mix - C_mix[L-2, L] for the ideal mixture dial on small patches (exact density matrix).
Layer: Ry on every qubit, CZ on every nearest-neighbour edge of the rows x cols grid, N_p on every qubit. Observable Z_i Z_j on a central
horizontal edge. Truncated circuit: the last 2 layers from |0...0>."""
import numpy as np, json, sys, time
def run(rows, cols, L, p, ell, draws, seed):
    n = rows*cols; dim = 2**n
    idx = np.arange(dim)
    bit = lambda q: (idx >> (n-1-q)) & 1
    edges = [(r*cols+c, r*cols+c+1) for r in range(rows) for c in range(cols-1)] + [(r*cols+c, (r+1)*cols+c) for r in range(rows-1) for c in range(cols)]
    czd = np.ones(dim)
    for a, b in edges: czd *= 1 - 2*(bit(a) & bit(b))
    r0 = rows//2 if rows > 1 else 0; c0 = (cols-1)//2
    i, j = r0*cols+c0, r0*cols+c0+1
    obs = (1-2*bit(i))*(1-2*bit(j))
    def ry_all(rho, th):
        t = rho.reshape([2]*(2*n))
        for q in range(n):
            c, s = np.cos(th[q]/2), np.sin(th[q]/2)
            U = np.array([[c, -s], [s, c]])
            t = np.moveaxis(np.tensordot(U, t, axes=([1], [q])), 0, q)
            t = np.moveaxis(np.tensordot(U, t, axes=([1], [n+q])), 0, n+q)
        return t.reshape(dim, dim)
    def dial(rho, q):
        t = rho.reshape([2]*(2*n))
        tr = np.trace(t, axis1=q, axis2=n+q)                      # partial trace over q
        new = np.zeros_like(t)
        sl = [slice(None)]*(2*n); sl[q] = 0; sl[n+q] = 0
        new[tuple(sl)] = tr
        return ((1-p)*t + p*new).reshape(dim, dim)
    def circuit(thetas):
        rho = np.zeros((dim, dim)); rho[0, 0] = 1.0
        for th in thetas:
            rho = ry_all(rho, th)
            rho = rho * czd[:, None] * czd[None, :]
            for q in range(n): rho = dial(rho, q)
        return float(np.sum(np.diag(rho)*obs))
    rng = np.random.default_rng(seed)
    cf, ct = np.empty(draws), np.empty(draws)
    for d in range(draws):
        th = rng.uniform(0, 2*np.pi, (L, n))
        cf[d], ct[d] = circuit(th), circuit(th[L-ell:])
    return cf, ct
out = {}
for (rows, cols, draws) in ((2, 3, 6000), (2, 4, 4000), (3, 3, 1500)):
    t0 = time.time()
    cf, ct = run(rows, cols, 8, 0.5, 2, draws, 20261110)
    dlt = cf - ct
    kur = lambda y: float(np.mean((y-y.mean())**4)/np.var(y)**2)
    # bootstrap s.e. of the kurtosis
    rng = np.random.default_rng(1); bs = [kur(dlt[rng.integers(0, draws, draws)]) for _ in range(400)]
    out[f"{rows}x{cols}"] = dict(n=rows*cols, draws=draws, mean_C=float(cf.mean()), std_C=float(cf.std(ddof=1)), mean_delta=float(dlt.mean()), rms_delta=float(np.sqrt(np.mean(dlt**2))),
                                 kurtosis_delta=kur(dlt), kurtosis_delta_se=float(np.std(bs)), kurtosis_C=kur(cf), kurtosis_delta_sq=kur(dlt**2), seconds=round(time.time()-t0, 1))
    print(json.dumps({f"{rows}x{cols}": out[f"{rows}x{cols}"]}), flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
