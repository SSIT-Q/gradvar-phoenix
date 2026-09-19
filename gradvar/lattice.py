"""ibm_phoenix device model: a 12 (rows) by 10 (columns) square lattice of 120 qubits.

Qubit index q = 10*row + col. Neighbours of q are q +/- 1 within its row and q +/- 10.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

N_ROWS = 12
N_COLS = 10
N_QUBITS = N_ROWS * N_COLS

DEFAULT_EXCLUDE: Tuple[int, ...] = (17, 55, 61, 62, 63, 72, 73)


def qubit_index(row: int, col: int) -> int:
    if not (0 <= row < N_ROWS and 0 <= col < N_COLS):
        raise ValueError(f"(row={row}, col={col}) outside the {N_ROWS}x{N_COLS} lattice")
    return N_COLS * row + col


def row_col(q: int) -> Tuple[int, int]:
    if not (0 <= q < N_QUBITS):
        raise ValueError(f"qubit {q} outside the lattice (0..{N_QUBITS - 1})")
    return divmod(q, N_COLS)


def lattice_neighbours(q: int) -> List[int]:
    r, c = row_col(q)
    out = []
    if c > 0:
        out.append(q - 1)
    if c < N_COLS - 1:
        out.append(q + 1)
    if r > 0:
        out.append(q - N_COLS)
    if r < N_ROWS - 1:
        out.append(q + N_COLS)
    return out


def lattice_edges() -> List[Tuple[int, int]]:
    edges = []
    for q in range(N_QUBITS):
        for nb in lattice_neighbours(q):
            if nb > q:
                edges.append((q, nb))
    return edges


@dataclass(frozen=True)
class Patch:
    """A rectangular sub-lattice. `qubits` are physical indices in row-major order."""

    qubits: Tuple[int, ...]
    n_rows: int
    n_cols: int
    origin: Tuple[int, int] = (0, 0)   # (row, col) of the rectangle's top-left corner
    holes: Tuple[int, ...] = ()        # excluded qubits removed from the rectangle (large patches only)
    broken_edges: Tuple[Tuple[int, int], ...] = ()   # couplers above the CZ-error cut (Deviation 26): no CZ is applied on them

    @property
    def n(self) -> int:
        return len(self.qubits)

    def local(self, q: int) -> int:
        """Physical qubit -> local circuit index."""
        return self.qubits.index(q)

    def position(self, q: int) -> Tuple[int, int]:
        """Physical qubit -> (row, col) relative to the patch origin."""
        r0, c0 = self.origin
        r, c = row_col(q)
        return r - r0, c - c0

    def edges_by_sublayer(self) -> List[List[Tuple[int, int]]]:
        """Lattice edges of the patch as four sub-layers of *physical* qubit pairs:
        horizontal even, horizontal odd, vertical even, vertical odd.
        'Even/odd' refers to the column (horizontal) or row (vertical) of the first endpoint
        relative to the patch origin, so every sub-layer is a set of disjoint edges.
        """
        qs = set(self.qubits)
        broken = {(min(a, b), max(a, b)) for a, b in self.broken_edges}
        h_even, h_odd, v_even, v_odd = [], [], [], []
        for q in self.qubits:
            r, c = self.position(q)
            if q + 1 in qs and c < self.n_cols - 1 and (q, q + 1) not in broken:
                (h_even if c % 2 == 0 else h_odd).append((q, q + 1))
            if q + N_COLS in qs and r < self.n_rows - 1 and (q, q + N_COLS) not in broken:
                (v_even if r % 2 == 0 else v_odd).append((q, q + N_COLS))
        return [h_even, h_odd, v_even, v_odd]

    def edges(self) -> List[Tuple[int, int]]:
        return [e for sub in self.edges_by_sublayer() for e in sub]


def as_qubits(patch: Sequence) -> List[int]:
    """Accept a list of (row, col) tuples or of qubit indices; return qubit indices."""
    out = []
    for p in patch:
        if isinstance(p, (tuple, list)):
            out.append(qubit_index(int(p[0]), int(p[1])))
        else:
            out.append(int(p))
    return out


def rect_patch(n_rows: int, n_cols: int, exclude: Iterable[int] = DEFAULT_EXCLUDE,
               origin: Tuple[int, int] | None = None, allow_holes: bool = False) -> Patch:
    """Build an n_rows x n_cols rectangle inside the lattice that avoids `exclude`.

    If `origin` is None, scan origins in row-major order and return the first rectangle
    that is fully inside the lattice and contains no excluded qubit. With `allow_holes=True`
    (used for the 60/80/100 patches, for which no clean rectangle exists on this exclusion list)
    the rectangle with the fewest excluded qubits is chosen and those qubits are removed, so the
    patch is a rectangle with holes and `patch.n` is below n_rows*n_cols. The result must stay
    connected.
    """
    if n_rows > N_ROWS or n_cols > N_COLS:
        raise ValueError(f"{n_rows}x{n_cols} does not fit in the {N_ROWS}x{N_COLS} lattice")
    ex = set(int(q) for q in exclude)
    origins = [origin] if origin is not None else [
        (r, c) for r in range(N_ROWS - n_rows + 1) for c in range(N_COLS - n_cols + 1)
    ]
    best = None
    for r0, c0 in origins:
        qubits = tuple(qubit_index(r0 + dr, c0 + dc) for dr in range(n_rows) for dc in range(n_cols))
        hit = ex.intersection(qubits)
        if not hit:
            return Patch(qubits=qubits, n_rows=n_rows, n_cols=n_cols, origin=(r0, c0))
        if allow_holes and (best is None or len(hit) < len(best[2])):
            best = ((r0, c0), qubits, hit)
    if best is None:
        raise ValueError(f"no {n_rows}x{n_cols} rectangle avoids the exclusion list {sorted(ex)}"
                         " (pass allow_holes=True to drop the excluded qubits)")
    (r0, c0), qubits, hit = best
    patch = Patch(qubits=tuple(q for q in qubits if q not in hit), n_rows=n_rows, n_cols=n_cols,
                  origin=(r0, c0), holes=tuple(sorted(hit)))
    if not is_connected(patch):
        raise ValueError(f"{n_rows}x{n_cols} patch at origin {(r0, c0)} is disconnected after removing {sorted(hit)}")
    return patch


def is_connected(patch: Patch) -> bool:
    adj = {q: set() for q in patch.qubits}
    for a, b in patch.edges():
        adj[a].add(b)
        adj[b].add(a)
    seen, stack = {patch.qubits[0]}, [patch.qubits[0]]
    while stack:
        q = stack.pop()
        for nb in adj[q]:
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) == patch.n


PATCH_SHAPES = {20: (4, 5), 40: (4, 10), 60: (6, 10), 80: (8, 10), 100: (10, 10)}


def patch_for_n(n: int, exclude: Iterable[int] = DEFAULT_EXCLUDE, strict: bool = False) -> Patch:
    """Standard patches of the study: 20 (4x5), 40 (4x10), 60 (6x10), 80 (8x10), 100 (10x10).

    With the default exclusion list no clean 6x10 / 8x10 / 10x10 rectangle exists, so unless
    `strict=True` those patches are rectangles with the excluded qubits removed (see README,
    Deviations); their `patch.n` is then 54-55, 74 and 94 rather than 60, 80, 100.
    """
    if n not in PATCH_SHAPES:
        raise ValueError(f"no standard patch for n={n}; choose from {sorted(PATCH_SHAPES)}")
    return rect_patch(*PATCH_SHAPES[n], exclude=exclude, allow_holes=not strict)


def interior_edge(patch: Patch) -> Tuple[int, int]:
    """Pick the observable edge: a lattice edge whose endpoints are both interior to the
    patch (all four lattice neighbours inside the patch) and closest to the patch centre.
    Falls back to the edge closest to the centre if the patch has no interior edges
    (e.g. 4x3 has interior qubits only in the middle rows/columns of size >= 3).
    """
    qs = set(patch.qubits)
    cr, cc = (patch.n_rows - 1) / 2, (patch.n_cols - 1) / 2

    def is_interior(q):
        return all(nb in qs for nb in lattice_neighbours(q)) and len(lattice_neighbours(q)) == 4

    def dist(e):
        (r1, c1), (r2, c2) = patch.position(e[0]), patch.position(e[1])
        return ((r1 + r2) / 2 - cr) ** 2 + ((c1 + c2) / 2 - cc) ** 2

    edges = patch.edges()
    interior = [e for e in edges if is_interior(e[0]) and is_interior(e[1])]
    pool = interior if interior else edges
    return min(pool, key=dist)
