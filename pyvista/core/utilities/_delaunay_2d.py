"""Checked 2D Delaunay triangulation behind ``PolyDataFilters.delaunay_2d``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pyvista_validation as _validation

import pyvista as pv
from pyvista import _vtk
from pyvista._warn_external import warn_external
from pyvista.core.errors import VTKExecutionWarning
from pyvista.core.filters import _get_output
from pyvista.core.filters import _update_alg
from pyvista.core.filters.data_object import _copy_active_attributes
from pyvista.core.utilities.arrays import array_from_vtkmatrix

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from pyvista import DataSet
    from pyvista import PolyData
    from pyvista.core.utilities.observers import VtkEvent


def _delaunay_2d(
    mesh: DataSet,
    *,
    tol: float,
    alpha: float,
    offset: float,
    bound: bool,
    edge_source: PolyData | None,
    progress_bar: bool,
) -> PolyData:
    """Triangulate ``mesh`` with ``vtkDelaunay2D``, and raise or warn where it cannot.

    VTK projects the points onto their best-fitting plane and triangulates there. Every
    check that needs that plane uses VTK's own matrix, since the sign of its normal
    decides which polygons are clockwise. With ``bound`` the projection is done here and
    undone afterwards, because VTK drops the bounding triangulation in best-fit mode.
    """
    if edge_source is not None:
        edge_source = pv.wrap(edge_source)
    _validate_input(mesh, edge_source)
    if _points_are_degenerate(mesh, bound=bound):
        output = pv.wrap(_vtk.vtkPolyData())
        output.points = mesh.points.copy()
        _copy_point_and_field_data(mesh, output)
        return output
    has_polygons = edge_source is not None and edge_source.n_faces > 0
    use_bound = bound and mesh.n_points > 0
    matrix = _best_fitting_plane(mesh) if has_polygons or use_bound else None

    alg = _vtk.vtkDelaunay2D()
    if use_bound and matrix is not None:
        # VTK keeps the bounding triangulation only in xy-plane mode
        alg.SetInputDataObject(pv.PolyData(mesh.points @ matrix[:3, :3].T + matrix[:3, 3]))
    else:
        alg.SetProjectionPlaneMode(_vtk.VTK_BEST_FITTING_PLANE)
        alg.SetInputDataObject(mesh)
    alg.SetTolerance(tol)
    alg.SetAlpha(alpha)
    alg.SetOffset(offset)
    alg.SetBoundingTriangulation(use_bound)
    if edge_source is not None:
        alg.SetSourceData(edge_source)
    events: list[VtkEvent] = []
    if has_polygons:
        # VTK only logs an unrecovered polygon edge, so catch it to warn and to skip the fill check
        with pv.vtk_verbosity('off'), pv.VtkErrorCatcher(send_to_logging=False) as catcher:
            _update_alg(alg, progress_bar=progress_bar, message='Computing 2D Triangulation')
        events = catcher.events
        for event in events:
            if 'Edge not recovered' not in event.alert:
                warn_external(event.alert, VTKExecutionWarning)
    else:
        _update_alg(alg, progress_bar=progress_bar, message='Computing 2D Triangulation')
    output = _get_output(alg, output_type=pv.PolyData)

    if use_bound and matrix is not None:
        inverse = np.linalg.inv(matrix)
        points = output.points @ inverse[:3, :3].T + inverse[:3, 3]
        # The eight bounding points come last, so the input points are restored exactly
        points[: mesh.n_points] = mesh.points
        output.points = points.astype(mesh.points.dtype)
        _copy_point_and_field_data(mesh, output)
    if edge_source is None:
        if alpha == 0 and not use_bound and mesh.n_points and output.n_cells == 0:
            warn_external(
                'The points cannot be triangulated, so the output has no cells. Points closer '
                'than tol are merged, so the rest may be collinear.'
            )
        return output
    filled = has_polygons and not any('Edge not recovered' in e.alert for e in events)
    fill = output
    if filled and alpha > 0:
        # Alpha removes triangles after the fill, so the fill is checked on its own
        alg.SetAlpha(0)
        with pv.vtk_verbosity('off'):
            _update_alg(alg, progress_bar=progress_bar, message='Checking the polygon fill')
        fill = _get_output(alg, output_type=pv.PolyData)
    _check_edge_source(edge_source, output, matrix, alpha=alpha, filled=filled, fill=fill)
    return output


def _best_fitting_plane(mesh: DataSet) -> NDArray[np.float64]:
    """Return the 4x4 matrix ``vtkDelaunay2D`` uses to move points onto the xy plane."""
    transform = _vtk.vtkDelaunay2D.ComputeBestFittingPlane(mesh)
    # The wrapper does not take ownership of the returned transform
    if transform.GetReferenceCount() > 1:
        transform.UnRegister(None)
    return array_from_vtkmatrix(transform.GetMatrix())


def _cell_edges(
    connectivity: NDArray[np.signedinteger],
    offsets: NDArray[np.signedinteger],
    *,
    closed: bool,
) -> NDArray[np.int64]:
    """Return the ``(n, 2)`` point id pairs along each cell, closing each cell if asked.

    Consecutive ids in the connectivity array are an edge unless the second one starts a
    new cell, which keeps this vectorized over all cells at once.
    """
    connectivity = connectivity.astype(np.int64)
    offsets = offsets.astype(np.int64)
    starts, ends = offsets[:-1], offsets[1:]
    index = np.arange(max(connectivity.size - 1, 0))
    inside = np.isin(index + 1, ends, invert=True)
    edges = [np.column_stack([connectivity[index[inside]], connectivity[index[inside] + 1]])]
    if closed:
        loops = ends - starts > 2
        edges.append(np.column_stack([connectivity[ends[loops] - 1], connectivity[starts[loops]]]))
    return np.concatenate(edges)


def _edge_source_edges(edge_source: PolyData) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Return the edges of the lines and of the closed polygons of ``edge_source``."""
    lines = _cell_edges(edge_source.line_connectivity, edge_source.line_offsets, closed=False)
    polys = _cell_edges(edge_source.face_connectivity, edge_source.face_offsets, closed=True)
    return lines, polys


def _validate_input(mesh: DataSet, edge_source: PolyData | None) -> None:
    """Raise for unusable points or ``edge_source`` ids, and warn for ignored cells."""
    _validation.check_finite(mesh.points, name='Points')
    if edge_source is None:
        return
    _validation.check_instance(edge_source, pv.PolyData, name='edge_source')
    for ids in (edge_source.line_connectivity, edge_source.face_connectivity):
        invalid = ids[(ids < 0) | (ids >= mesh.n_points)]
        if invalid.size:
            msg = (
                f'edge_source references point id {invalid[0]}, but the input has '
                f'{mesh.n_points} points. Its cells must use the point ids of the input.'
            )
            raise ValueError(msg)
    if edge_source.n_strips:
        warn_external(
            'edge_source triangle strips are ignored. Only lines and polygons constrain the '
            'triangulation, so pass the strip edges as lines, for example with '
            'extract_all_edges().'
        )


def _points_are_degenerate(mesh: DataSet, *, bound: bool) -> bool:
    """Return whether the points cannot be triangulated, warning if so.

    VTK needs three points spanning a plane. With ``bound`` the bounding points make
    collinear input triangulable, so only coincident points fail.
    """
    if mesh.n_points == 0:
        return False
    if mesh.n_points >= 3 and mesh.dimensionality >= (1 if bound else 2):
        return False
    warn_external(
        'The points cannot be triangulated, so the output has no cells. There must be at '
        'least three points, and they must not all coincide or lie on one line.'
    )
    return True


def _copy_point_and_field_data(mesh: DataSet, output: PolyData) -> None:
    """Copy point and field data onto ``output``, padding the points it has beyond ``mesh``."""
    n_extra = output.n_points - mesh.n_points
    for name in mesh.point_data.keys():
        array = np.asarray(mesh.point_data[name])
        kind = array.dtype.kind
        fill: object = np.nan if kind in 'fc' else ('' if kind in 'USO' else 0)
        padding = np.full((n_extra, *array.shape[1:]), fill, dtype=array.dtype)
        output.point_data[name] = np.concatenate([array, padding])
    output.point_data.active_scalars_name = mesh.point_data.active_scalars_name
    _copy_active_attributes(mesh, output)
    for name in mesh.field_data.keys():
        output.field_data[name] = mesh.field_data[name]


def _check_edge_source(
    edge_source: PolyData,
    output: PolyData,
    matrix: NDArray[np.float64] | None,
    *,
    alpha: float,
    filled: bool,
    fill: PolyData,
) -> None:
    """Warn for ``edge_source`` edges the output lacks and polygons it did not fill as wound.

    ``filled`` says VTK ran its polygon fill, which it skips entirely when any polygon
    edge is unrecovered, and ``fill`` is the output before alpha pruned it. After a fill,
    a missing polygon edge means both of its triangles were removed, which the fill check
    reports, and a missing line may just lie inside a removed region, which the locator
    rules out.
    """
    # Links on a shallow copy keep the point-to-cell cache off the returned mesh
    linked = output.copy(deep=False)
    linked.BuildLinks()
    lines, polys = _edge_source_edges(edge_source)
    missing_lines = _missing_edges(linked, lines, alpha=alpha)
    missing_polys = lines[:0]
    if filled:
        missing_lines = _outside_removed_regions(missing_lines, output, matrix)
    else:
        missing_polys = _missing_edges(linked, polys, alpha=alpha)
    n_missing = len(missing_lines) + len(missing_polys)
    if n_missing:
        msg = (
            f'{n_missing} edge_source edges are not edges of the triangulation, so they do not '
            'constrain it. Edges must not cross each other or pass through other points, and '
            'points closer than tol are merged.'
        )
        if len(missing_polys):
            msg += ' Since a polygon edge is missing, no polygon insides or holes are removed.'
        warn_external(msg)
    if filled and matrix is not None:
        if fill is not output:
            linked = fill.copy(deep=False)
            linked.BuildLinks()
        _check_fill(linked, edge_source, flat=fill.points @ matrix[:2, :3].T, polys=polys)


def _missing_edges(
    linked: PolyData, edges: NDArray[np.int64], *, alpha: float
) -> NDArray[np.int64]:
    """Return the non-degenerate edges that ``linked`` lacks and that ``alpha`` would keep."""
    edges = edges[edges[:, 0] != edges[:, 1]]
    # One IsEdge lookup per constraint costs O(constraints), not O(output edges)
    edges = edges[[not linked.IsEdge(p, q) for p, q in edges.tolist()]]
    if alpha > 0 and len(edges):
        lengths = np.linalg.norm(np.diff(linked.points[edges], axis=1)[:, 0], axis=1)
        edges = edges[lengths / 2 <= alpha]
    return edges


def _outside_removed_regions(
    edges: NDArray[np.int64], output: PolyData, matrix: NDArray[np.float64] | None
) -> NDArray[np.int64]:
    """Return the edges whose midpoint still lies on a triangle after the polygon fill."""
    if not len(edges) or matrix is None:
        return edges
    if not output.n_faces:
        return edges[:0]
    # The locator over the flattened output is only built once some edge is missing
    flat = output.points @ matrix[:2, :3].T
    covered = pv.PolyData.from_regular_faces(
        np.column_stack([flat, np.zeros(len(flat))]), output.regular_faces
    )
    midpoints = covered.points[edges].mean(axis=1)
    return edges[covered.find_containing_cell(midpoints) >= 0]


def _check_fill(
    linked: PolyData,
    edge_source: PolyData,
    *,
    flat: NDArray[np.float64],
    polys: NDArray[np.int64],
) -> None:
    """Warn when triangles are missing on the side a polygon keeps, or remain on the other.

    ``vtkDelaunay2D::FillPolygons`` walks each polygon in order, keeps the triangle left
    of every edge and flood-removes the one right of it. The flood stops at triangles
    an earlier polygon kept, and a later polygon keeps its left triangles even inside a
    removed region, so a wrongly wound polygon leaves either an empty kept side or a
    one-triangle ring whose inner neighbors are gone. Both are read from the output with
    one edge-neighbor lookup per polygon edge, and the geometry is vectorized, so the cost
    is linear in the polygon edges. An edge on the convex hull has nothing beyond it, so
    a missing triangle there is expected.
    """
    connectivity = edge_source.face_connectivity.astype(np.int64)
    offsets = edge_source.face_offsets.astype(np.int64)
    sizes = np.diff(offsets)
    # Each polygon vertex paired with the next one around its polygon
    following = np.arange(1, connectivity.size + 1)
    following[offsets[1:] - 1] = offsets[:-1]
    p, q = connectivity, connectivity[following]
    # Shoelace signed area per polygon: positive is counter-clockwise in the projection plane
    cross = flat[p, 0] * flat[q, 1] - flat[q, 0] * flat[p, 1]
    ccw = (np.add.reduceat(cross, offsets[:-1]) > 0)[np.repeat(np.arange(sizes.size), sizes)]
    distinct = p != q
    p, q, ccw = p[distinct], q[distinct], ccw[distinct]

    neighbors = _vtk.vtkIdList()
    cells, owners = [], []
    for i, (a, b) in enumerate(zip(p.tolist(), q.tolist(), strict=True)):
        linked.GetCellEdgeNeighbors(-1, a, b, neighbors)
        for j in range(neighbors.GetNumberOfIds()):
            cells.append(neighbors.GetId(j))
            owners.append(i)
    cell = np.array(cells, dtype=np.int64)
    owner = np.array(owners, dtype=np.int64)
    tri = linked.regular_faces[cell] if cell.size else np.empty((0, 3), dtype=np.int64)
    a, b = p[owner], q[owner]
    third = tri[np.arange(len(tri)), np.argmax((tri != a[:, None]) & (tri != b[:, None]), axis=1)]
    # The fill keeps the triangle left of p->q and removes the one right of it
    ab, ac = flat[b] - flat[a], flat[third] - flat[a]
    left = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0] > 0
    remains = np.zeros(p.size, dtype=bool)
    remains[owner[~left]] = True
    has_kept = np.zeros(p.size, dtype=bool)
    has_kept[owner[left]] = True

    # Off the hull, a polygon edge needs a kept triangle and that triangle's free edges a neighbor
    stride = linked.n_points + 1
    poly_keys = np.sort(polys, axis=1) @ [stride, 1]
    candidates = [(i, p[i], q[i]) for i in np.flatnonzero(~has_kept).tolist()]
    kept_cell, kept_owner = cell[left], owner[left]
    for u, v in ((b[left], third[left]), (third[left], a[left])):
        owned = np.isin(np.minimum(u, v) * stride + np.maximum(u, v), poly_keys)
        for c, x, y, o in zip(
            kept_cell[~owned].tolist(),
            u[~owned].tolist(),
            v[~owned].tolist(),
            kept_owner[~owned].tolist(),
            strict=True,
        ):
            linked.GetCellEdgeNeighbors(c, x, y, neighbors)
            if neighbors.GetNumberOfIds() == 0:
                candidates.append((o, x, y))
    missing = np.zeros(p.size, dtype=bool)
    on_hull: dict[tuple[int, int], bool] = {}
    for o, x, y in candidates:
        if missing[o]:
            continue
        key = (min(x, y), max(x, y))
        if key not in on_hull:
            on_hull[key] = _on_hull(flat, x, y)
        missing[o] = not on_hull[key]

    problems = set() if linked.n_cells else {'every triangle was removed'}
    for wound_ccw in np.unique(ccw[missing]).tolist():
        side, wound = ('inside', 'counter-clockwise') if wound_ccw else ('outside', 'clockwise')
        problems.add(f'triangles are missing {side} a {wound} polygon')
    for wound_ccw in np.unique(ccw[remains]).tolist():
        side, wound = ('outside', 'counter-clockwise') if wound_ccw else ('inside', 'clockwise')
        problems.add(f'triangles remain {side} a {wound} polygon')
    if problems:
        found = ' and '.join(sorted(problems))
        msg = (
            f'The edge_source polygons were not filled as wound: {found}. Order the outer '
            'boundary counter-clockwise and holes clockwise as seen from the projection plane, '
            'which may view the input from either side.'
        )
        warn_external(msg)


def _on_hull(flat: NDArray[np.float64], a: int, b: int) -> bool:
    """Return whether every point lies on one side of the line through ``a`` and ``b``."""
    direction = flat[b] - flat[a]
    offset = flat - flat[a]
    side = direction[0] * offset[:, 1] - direction[1] * offset[:, 0]
    tol = 1e-9 * np.abs(side).max()
    return bool(side.min() >= -tol or side.max() <= tol)
