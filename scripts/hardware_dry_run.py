"""Build and transpile the (n=20, L=1,2,4) grid against a fake backend. Submits nothing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gradvar.hardware import dry_run  # noqa: E402

if __name__ == "__main__":
    dry_run(ns=(20,), Ls=(1, 2, 4), k=0)
