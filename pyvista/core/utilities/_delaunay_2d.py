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
    """Triangulate ``mesh`` with ``vtkDelaunay2D``, and raise or warn where it cannot."""
    _validate_input(mesh, edge_source)
    if not bound and _points_are_degenerate(mesh):
        output = pv.PolyData()
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
        points[: mesh.n_points] = mesh.points
        output.points = points.astype(mesh.points.dtype)
        _copy_point_and_field_data(mesh, output)
    if edge_source is not None:
        filled = has_polygons and not any('Edge not recovered' in e.alert for e in events)
        _check_edge_source(edge_source, output, matrix, alpha=alpha, filled=filled)
    return output


def _best_fitting_plane(mesh: DataSet) -> NDArray[np.float64]:
    """Return the 4x4 matrix ``vtkDelaunay2D`` uses to move points onto the xy plane."""
    transform = _vtk.vtkDelaunay2D.ComputeBestFittingPlane(mesh)
    # The wrapper does not take ownership of the returned transform
    if transform.GetReferenceCount() > 1:
        transform.UnRegister(None)
    return array_from_vtkmatrix(transform.GetMatrix())


def _cell_edges(cells: _vtk.vtkCellArray, *, closed: bool) -> NDArray[np.int64]:
    """Return the ``(n, 2)`` point id pairs along each cell, closing each cell if asked."""
    connectivity = _vtk.vtk_to_numpy(cells.GetConnectivityArray()).astype(np.int64)
    offsets = _vtk.vtk_to_numpy(cells.GetOffsetsArray()).astype(np.int64)
    starts, ends = offsets[:-1], offsets[1:]
    index = np.arange(max(connectivity.size - 1, 0))
    inside = np.isin(index + 1, ends, invert=True)
    edges = [np.column_stack([connectivity[index[inside]], connectivity[index[inside] + 1]])]
    if closed:
        loops = ends - starts > 2
        edges.append(np.column_stack([connectivity[ends[loops] - 1], connectivity[starts[loops]]]))
    return np.concatenate(edges)


def _validate_input(mesh: DataSet, edge_source: PolyData | None) -> None:
    """Raise for unusable points or ``edge_source`` ids, and warn for ignored cells."""
    if not np.isfinite(mesh.points).all():
        msg = 'Points must be finite to be triangulated, but some are NaN or infinite.'
        raise ValueError(msg)
    if edge_source is None:
        return
    _validation.check_instance(edge_source, pv.PolyData, name='edge_source')
    for cells in (edge_source.GetLines(), edge_source.GetPolys()):
        ids = _vtk.vtk_to_numpy(cells.GetConnectivityArray())
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
            'triangulation, so convert strips with triangulate().'
        )
    edges = np.concatenate(
        [
            _cell_edges(edge_source.GetLines(), closed=False),
            _cell_edges(edge_source.GetPolys(), closed=True),
        ]
    )
    if np.any(edges[:, 0] == edges[:, 1]):
        warn_external(
            'edge_source repeats a point id in consecutive positions of a line or polygon. '
            'The zero-length edge cannot be recovered, so remove the repeated id.'
        )


def _points_are_degenerate(mesh: DataSet) -> bool:
    """Return whether the points are coincident or collinear, warning if so."""
    if mesh.n_points == 0:
        return False
    points = mesh.points.astype(np.float64)
    singular = np.linalg.svd(points - points.mean(axis=0), compute_uv=False)
    # Rounding of the stored coordinates alone spreads points by about this much
    noise = np.finfo(mesh.points.dtype).eps * np.abs(points).max() * np.sqrt(mesh.n_points)
    if singular.size > 1 and singular[1] > max(1e-10 * singular[0], noise):
        return False
    warn_external(
        'The points are coincident or collinear, so they cannot be triangulated and the '
        'output has no cells. At least three points that do not lie on one line are required.'
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
) -> None:
    """Warn for ``edge_source`` edges the output lacks and polygons it did not fill as wound."""
    linked = output.copy(deep=False)
    linked.BuildLinks()
    lines = _cell_edges(edge_source.GetLines(), closed=False)
    polys = _cell_edges(edge_source.GetPolys(), closed=True)
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
            'constrain it. Edges must not cross each other, and points closer than tol are merged.'
        )
        if len(missing_polys):
            msg += ' Since a polygon edge is missing, no polygon insides or holes are removed.'
        warn_external(msg)
    if filled and alpha == 0 and matrix is not None:
        _check_fill(linked, edge_source, flat=output.points @ matrix[:2, :3].T, polys=polys)


def _missing_edges(
    linked: PolyData, edges: NDArray[np.int64], *, alpha: float
) -> NDArray[np.int64]:
    """Return the non-degenerate edges that ``linked`` lacks and that ``alpha`` would keep."""
    edges = edges[edges[:, 0] != edges[:, 1]]
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
    """Warn when triangles are missing on the side a polygon keeps, or remain on the other."""
    faces = linked.regular_faces if linked.n_faces else np.empty((0, 3), dtype=np.int64)
    stride = linked.n_points + 1
    poly_keys = set((np.sort(polys, axis=1) @ [stride, 1]).tolist())
    neighbors = _vtk.vtkIdList()
    problems: set[str] = set()
    for ids in edge_source.irregular_faces:
        ring = flat[ids]
        area = np.sum(ring[:, 0] * np.roll(ring[:, 1], -1) - np.roll(ring[:, 0], -1) * ring[:, 1])
        kept, removed = ('inside', 'outside') if area > 0 else ('outside', 'inside')
        wound = 'counter-clockwise' if area > 0 else 'clockwise'
        n = len(ids)
        for i in range(0, n, max(1, n // 4)):
            p, q = int(ids[i]), int(ids[(i + 1) % n])
            linked.GetCellEdgeNeighbors(-1, p, q, neighbors)
            left = None
            for j in range(neighbors.GetNumberOfIds()):
                cell = neighbors.GetId(j)
                tri = faces[cell]
                r = int(tri[(tri != p) & (tri != q)][0])
                a, b, c = flat[p], flat[q], flat[r]
                # The fill keeps the triangle left of p->q and removes the one right of it
                if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) > 0:
                    left = (cell, r)
                else:
                    problems.add(f'triangles remain {removed} a {wound} polygon')
            if left is None:
                problems.add(f'triangles are missing {kept} a {wound} polygon')
                continue
            cell, r = left
            for a, b in ((q, r), (r, p)):
                if min(a, b) * stride + max(a, b) in poly_keys:
                    continue
                linked.GetCellEdgeNeighbors(cell, a, b, neighbors)
                if neighbors.GetNumberOfIds() == 0:
                    problems.add(f'triangles are missing {kept} a {wound} polygon')
    if problems:
        found = ' and '.join(sorted(problems))
        msg = (
            f'The edge_source polygons were not filled as wound: {found}. Order the outer '
            'boundary counter-clockwise and holes clockwise as seen from the projection plane, '
            'which may view the input from either side.'
        )
        warn_external(msg)
