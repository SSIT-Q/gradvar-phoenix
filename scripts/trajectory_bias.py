"""Measure the trajectory-sampling bias of the noisy predictions: Var from n_traj trajectories minus the exact
density-matrix Var on the same theta draws (2x5 patch, L = 4, k = 1). Quoted in the README."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gradvar import predict  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--patch", default="2x5")
    p.add_argument("--L", type=int, default=4)
    p.add_argument("--M", type=int, default=100)
    p.add_argument("--traj", nargs="+", type=int, default=[8, 32])
    p.add_argument("--calibration", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"))
    a = p.parse_args(argv)
    patch = predict.parse_patch(a.patch, a.calibration)
    print(f"patch {a.patch} n={patch.n} origin={patch.origin}; L={a.L}, k=1, M={a.M}")
    for model in ("unital", "nonunital"):
        exact = predict.hea_point(patch, a.L, 1, model, a.M, a.calibration, dm_max=patch.n, n_boot=1000)
        print(f"{model:10s} exact DM      var={exact.var:.4e} ({exact.runtime_s:.0f}s)")
        for t in a.traj:
            r = predict.hea_point(patch, a.L, 1, model, a.M, a.calibration, n_traj=t, dm_max=0, n_boot=1000)
            print(f"{model:10s} {t:3d} trajectories var={r.var:.4e}  bias={r.var - exact.var:+.2e} ({100 * (r.var / exact.var - 1):+.1f}%) ({r.runtime_s:.0f}s)")


if __name__ == "__main__":
    main()
