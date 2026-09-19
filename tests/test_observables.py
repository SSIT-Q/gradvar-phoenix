import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from gradvar.observables import pauli_label, z_observable, zz_observable


def test_little_endian_label():
    assert pauli_label(4, {0: "Z"}) == "IIIZ"
    assert pauli_label(4, {3: "Z"}) == "ZIII"
    assert zz_observable(5, 1, 3).paulis.to_labels() == ["IZIZI"]


def test_little_endian_placement_by_expectation():
    n = 4
    qc = QuantumCircuit(n)
    qc.x(0)  # flip qubit 0 only
    sv = Statevector(qc)
    assert np.isclose(sv.expectation_value(z_observable(n, 0)).real, -1.0)
    for q in range(1, n):
        assert np.isclose(sv.expectation_value(z_observable(n, q)).real, +1.0)
    assert np.isclose(sv.expectation_value(zz_observable(n, 0, 2)).real, -1.0)
    assert np.isclose(sv.expectation_value(zz_observable(n, 1, 2)).real, +1.0)
