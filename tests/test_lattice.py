from collections import deque

import pytest

from gradvar.lattice import (DEFAULT_EXCLUDE, N_COLS, interior_edge, lattice_neighbours, patch_for_n,
                             rect_patch, row_col)


def _connected(patch):
    adj = {q: set() for q in patch.qubits}
    for a, b in patch.edges():
        adj[a].add(b)
        adj[b].add(a)
    seen, dq = {patch.qubits[0]}, deque([patch.qubits[0]])
    while dq:
        q = dq.popleft()
        for nb in adj[q]:
            if nb not in seen:
                seen.add(nb)
                dq.append(nb)
    return len(seen) == patch.n


@pytest.mark.parametrize("n", [20, 40, 60, 80, 100])
def test_patch_builder_excludes_and_is_connected_rectangle(n):
    patch = patch_for_n(n)
    assert patch.n + len(patch.holes) == n
    assert not set(DEFAULT_EXCLUDE).intersection(patch.qubits)
    assert set(patch.holes) <= set(DEFAULT_EXCLUDE)
    if n <= 40:
        assert patch.n == n and patch.holes == ()
    else:  # no clean rectangle exists for these sizes on the default exclusion list
        with pytest.raises(ValueError):
            patch_for_n(n, strict=True)
        assert patch.n >= n - len(DEFAULT_EXCLUDE)
    r0, c0 = patch.origin
    rows = {row_col(q)[0] for q in patch.qubits}
    cols = {row_col(q)[1] for q in patch.qubits}
    assert rows == set(range(r0, r0 + patch.n_rows))
    assert cols == set(range(c0, c0 + patch.n_cols))
    assert all(r0 <= row_col(q)[0] < r0 + patch.n_rows and c0 <= row_col(q)[1] < c0 + patch.n_cols for q in patch.qubits)
    assert _connected(patch)
    # every edge is a true lattice edge, and sub-layers are disjoint matchings
    for sub in patch.edges_by_sublayer():
        touched = [q for e in sub for q in e]
        assert len(touched) == len(set(touched))
        for a, b in sub:
            assert b in lattice_neighbours(a)
    if not patch.holes:
        assert len(patch.edges()) == patch.n_rows * (patch.n_cols - 1) + (patch.n_rows - 1) * patch.n_cols


def test_neighbours_are_row_bounded():
    assert 10 not in lattice_neighbours(9)  # 9 and 10 are in different rows
    assert set(lattice_neighbours(11)) == {10, 12, 1, 21}


def test_interior_edge_is_interior():
    patch = rect_patch(4, 5)
    a, b = interior_edge(patch)
    qs = set(patch.qubits)
    for q in (a, b):
        assert len(lattice_neighbours(q)) == 4 and all(nb in qs for nb in lattice_neighbours(q))
    assert b == a + 1 or b == a + N_COLS


def test_exclusion_moves_patch():
    p_default = rect_patch(4, 10, exclude=())
    assert 17 in p_default.qubits
    p = rect_patch(4, 10)
    assert 17 not in p.qubits and 55 not in p.qubits
