"""Empirical kurtosis of the k = L gradient at L = 8 (noiseless statevector, 4x5 patch, M draws) for the Deviation 28 2-sigma."""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from qiskit.circuit import ParameterVector
from gradvar import noise, predict
from gradvar.circuits import hea_observable, hea_on_qubits, light_cone
M = int(sys.argv[1]) if len(sys.argv) > 1 else 400
csv = str(noise.DEFAULT_CALIBRATION)
patch = predict.parse_patch("4x5", csv)
_, edge = hea_observable(patch); cone = light_cone(patch, 8, edge); m = len(cone); i, j = cone.index(edge[0]), cone.index(edge[1])
obs = predict.measured_zz(m, i, j)
tmpl = hea_on_qubits(patch, 8, cone, ParameterVector("theta", m * 8))
runner = predict.ExpvalRunner(tmpl, obs, "statevector")
t0 = time.time()
grads, evp, evm, var, lo, hi = predict.predict_variance(tmpl, 7 * m + i, M, runner, seed=2028, n_boot=2000)
g = grads - grads.mean()
kurt = float(np.mean(g ** 4) / np.mean(g ** 2) ** 2)
out = dict(patch="4x5", n=patch.n, L=8, k=8, M=M, model="noiseless", var=var, ci_lo=lo, ci_hi=hi, kurtosis=kurt, rel_2sigma_M200=2 * np.sqrt((kurt - 197 / 199) / 200), runtime_s=time.time() - t0)
print(json.dumps(out, indent=1))
json.dump(out, open(Path(__file__).resolve().parents[1] / "data" / "predictions" / "pauliprop_kurtosis.json", "w"))
