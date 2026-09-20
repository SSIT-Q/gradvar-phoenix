"""Paper 1 hardware-analysis pipeline (pre-registration v0.9.9).

Modules: ``loader`` (bundles + CSV -> tidy table, Section 7), ``estimators`` (Section 3 estimate, Section 3b dial
estimator with Deviation 27 floors, Deviation 14 layer-index ratio, Deviation 25 null interval, fits), ``predictions``
(join to data/predictions, z-scores, Deviation 19 anomaly protocol), ``hypotheses`` (H1-H4), ``gates`` (Section 3b kill
rules (a)-(d), Gate 2 (a)-(e)), ``figures`` and ``report`` (CLI: ``python -m gradvar.analysis.report <run_dir> --out
<dir>``). ``synthetic`` builds fake runs in the live bundle format for the tests.
"""
from .loader import RunData, load_run  # noqa: F401
