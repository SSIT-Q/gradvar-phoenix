"""Backend configuration snapshot (scripts/snapshot_calibration.py): ledger row, gzipped raw configuration,
SHA-256 de-duplication, and the Init/MEASURE columns of the calibration CSV. Uses fake backends only."""
import gzip
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import snapshot_calibration as sc  # noqa: E402
from snapshot_calibration import (CONFIG_COLUMNS, CONFIG_LEDGER, DURATION_OPS, configuration_row,  # noqa: E402
                                  properties_to_rows, write_configuration_snapshot)

warnings.filterwarnings("ignore", category=DeprecationWarning)
fake_provider = pytest.importorskip("qiskit_ibm_runtime.fake_provider")

T0 = datetime(2026, 9, 20, 3, 0, 0, tzinfo=timezone.utc)


def test_configuration_row_fake_nighthawk():
    b = fake_provider.FakeNighthawk()
    row = configuration_row(b, T0, "primary")
    assert list(row) == CONFIG_COLUMNS
    assert row["backend"] == "fake_nighthawk" and row["received_at_utc"] == "2026-09-20T03:00:00Z" and row["instance"] == "primary"
    assert row["n_qubits"] == 120 and row["processor_family"] == "Nighthawk" and row["processor_revision"] == "1"
    assert row["coupling_map_edges"] == 436 and row["basis_gates"] == "cz,id,rz,sx,x"
    assert "measure" in row["supported_instructions"].split(",") and "reset" in row["target_operations"].split(",")
    assert row["default_rep_delay (us)"] == 250.0 and row["rep_delay_range (us)"] == "20.0;500.0"
    assert row["dt (ns)"] == 4.0 and row["dtm (ns)"] == 4.0 and row["max_shots"] == 100000 and row["max_experiments"] == 300
    assert row["delay_granularity (dt)"] == 1 and row["delay_min_length (dt)"] == 2
    assert row["cz duration median (ns)"] == 68.0 and row["sx duration min (ns)"] == 32.0 and row["x duration max (ns)"] == 32.0
    assert row["measure duration median (ns)"] == 2200.0 and row["reset duration median (ns)"] == 2232.0
    assert row["rx duration median (ns)"] == "" and row["xslow duration median (ns)"] == ""   # not in the fake target
    assert len(row["configuration_sha256"]) == 64 and row["online_date"].startswith("2025-11-01")
    for op in DURATION_OPS:
        stats = [row[f"{op} duration {s} (ns)"] for s in ("min", "median", "max")]
        assert all(s == "" for s in stats) or stats[0] <= stats[1] <= stats[2]


def test_write_configuration_snapshot_dedupes_by_sha(tmp_path):
    b = fake_provider.FakeMarrakesh()
    w1 = write_configuration_snapshot(b, tmp_path, T0, "open")
    names = sorted(p.name for p in w1)
    assert names == [CONFIG_LEDGER, "fake_marrakesh_configuration_20260920T030000Z.json.gz"]
    with gzip.open(tmp_path / "fake_marrakesh_configuration_20260920T030000Z.json.gz", "rt") as f:
        cfg = json.load(f)
    assert cfg["n_qubits"] == 156 and cfg["processor_type"] == {"family": "Heron", "revision": "2"}
    # second snapshot a day later with the same configuration: a new ledger row, no second gzip
    t1 = datetime(2026, 9, 21, 3, 0, 0, tzinfo=timezone.utc)
    w2 = write_configuration_snapshot(b, tmp_path, t1, "open")
    assert [p.name for p in w2] == [CONFIG_LEDGER]
    assert sorted(p.name for p in tmp_path.glob("*.json.gz")) == ["fake_marrakesh_configuration_20260920T030000Z.json.gz"]
    ledger = pd.read_csv(tmp_path / CONFIG_LEDGER, dtype=str, keep_default_na=False)
    assert list(ledger.columns) == CONFIG_COLUMNS and len(ledger) == 2
    assert ledger["configuration_file"].tolist() == ["fake_marrakesh_configuration_20260920T030000Z.json.gz"] * 2
    assert ledger["received_at_utc"].tolist() == ["2026-09-20T03:00:00Z", "2026-09-21T03:00:00Z"]
    assert ledger.loc[0, "processor_family"] == "Heron" and ledger.loc[0, "n_qubits"] == "156" and ledger.loc[0, "instance"] == "open"
    # a different backend appended to the same ledger gets its own gzip
    w3 = write_configuration_snapshot(fake_provider.FakeNighthawk(), tmp_path, t1, "primary")
    assert sorted(p.name for p in w3) == [CONFIG_LEDGER, "fake_nighthawk_configuration_20260921T030000Z.json.gz"]
    ledger = pd.read_csv(tmp_path / CONFIG_LEDGER, dtype=str, keep_default_na=False)
    assert ledger["backend"].tolist() == ["fake_marrakesh", "fake_marrakesh", "fake_nighthawk"]


def test_calibration_csv_keeps_init_and_measure_columns():
    gz = ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T155931Z.json.gz"
    with gzip.open(gz, "rt") as f:
        props = json.load(f)
    df = properties_to_rows(props)
    for col in ("MEASURE error", "MEASURE_2 error", "XSLOW error", "RX error"):
        assert (df[col] != "").all(), col
    # init_error is missing for a few qubits in the raw properties; every reported value must land in the CSV
    n_init = sum(any(x["name"] == "init_error" for x in ps) for ps in props["qubits"])
    assert 0 < n_init <= 120 and int((df["Init error"] != "").sum()) == n_init
    q0 = props["qubits"][0]
    init0 = next(p["value"] for p in q0 if p["name"] == "init_error")
    meas0 = next(p["value"] for g in props["gates"] if g["gate"] == "measure" and g["qubits"] == [0] for p in g["parameters"] if p["name"] == "gate_error")
    meas2_0 = next(p["value"] for g in props["gates"] if g["gate"] == "measure_2" and g["qubits"] == [0] for p in g["parameters"] if p["name"] == "gate_error")
    assert df.loc[0, "Init error"] == init0 and df.loc[0, "MEASURE error"] == meas0 and df.loc[0, "MEASURE_2 error"] == meas2_0
    # the fake backend's properties convert too; fields a backend does not report (measure_2 here) stay empty
    fake = json.loads(json.dumps(fake_provider.FakeNighthawk().properties().to_dict(), default=str))
    dff = properties_to_rows(fake)
    assert len(dff) == 120 and (dff["MEASURE error"] != "").all() and (dff["MEASURE_2 error"] == "").all()
    bare = {"qubits": [[{"name": "T1", "value": 100.0}]], "gates": []}
    assert properties_to_rows(bare).loc[0, "Init error"] == "" and properties_to_rows(bare).loc[0, "MEASURE error"] == ""


def test_main_survives_open_instance_failure(tmp_path, monkeypatch, capsys):
    """The ibm_phoenix calibration is written and main() returns normally when the open-plan service cannot be
    constructed (bad CRN) and the primary configuration fetch fails; nothing is submitted."""
    class _Svc:
        def backend(self, name, **kw):
            raise RuntimeError(f"{name} is not in this instance")

    def fake_make_service(env="QISKIT_IBM_INSTANCE"):
        if env == "QISKIT_IBM_INSTANCE_OPEN":
            raise ValueError("crn:bad is not a valid instance.")
        return _Svc()

    with gzip.open(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T155931Z.json.gz", "rt") as f:
        props = json.load(f)
    monkeypatch.setattr(sc, "make_service", fake_make_service)
    monkeypatch.setattr(sc, "fetch_properties", lambda name, service=None: props)
    sc.main(["--backend", "ibm_phoenix", "--out-dir", str(tmp_path), "--config-backends", "ibm_phoenix",
             "--open-config-backends", "ibm_marrakesh", "ibm_torino"])
    assert len(list(tmp_path.glob("ibm_phoenix_*.csv"))) == 1 and len(list(tmp_path.glob("ibm_phoenix_properties_*.json.gz"))) == 1
    assert not (tmp_path / CONFIG_LEDGER).exists()
    out = capsys.readouterr().out
    assert "skipped configuration for ibm_phoenix (primary instance)" in out and "skipped configuration snapshot (open instance): ValueError" in out
