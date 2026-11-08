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
    if has_polygons:
        with pv.vtk_verbosity('off'), pv.VtkErrorCatcher(send_to_logging=False) as catcher:
            _update_alg(alg, progress_bar=progress_bar, message='Computing 2D Triangulation')
        for event in catcher.events:
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
        _check_constraint_edges(edge_source, output, matrix, alpha=alpha)
    if edge_source is not None and matrix is not None and has_polygons:
        emptied = output.n_cells == 0 and alpha == 0
        _check_winding(mesh, edge_source, matrix, emptied=emptied)
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


def _check_constraint_edges(
    edge_source: PolyData, output: PolyData, matrix: NDArray[np.float64] | None, *, alpha: float
) -> None:
    """Warn when ``edge_source`` edges were not recovered by the triangulation."""
    found = np.concatenate(
        [_cell_edges(output.GetPolys(), closed=True), _cell_edges(output.GetLines(), closed=False)]
    )
    stride = [output.n_points + 1, 1]
    found_keys = np.sort(found, axis=1) @ stride
    covered = None
    if matrix is not None and output.n_faces:
        flat = output.points @ matrix[:2, :3].T
        covered = pv.PolyData.from_regular_faces(
            np.column_stack([flat, np.zeros(len(flat))]), output.regular_faces
        )

    def _unrecovered(edges: NDArray[np.int64]) -> int:
        """Return how many non-degenerate edges are missing from the output."""
        edges = edges[edges[:, 0] != edges[:, 1]]
        edges = edges[np.isin(np.sort(edges, axis=1) @ stride, found_keys, invert=True)]
        if alpha > 0:
            lengths = np.linalg.norm(np.diff(output.points[edges], axis=1)[:, 0], axis=1)
            edges = edges[lengths / 2 <= alpha]
        if matrix is None or not len(edges):
            return len(edges)
        if covered is None:
            return 0
        # Edges inside removed polygon regions are absent, not unrecovered
        midpoints = covered.points[edges].mean(axis=1)
        return int(np.count_nonzero(covered.find_containing_cell(midpoints) >= 0))

    n_lines = _unrecovered(_cell_edges(edge_source.GetLines(), closed=False))
    n_polys = _unrecovered(_cell_edges(edge_source.GetPolys(), closed=True))
    if not n_lines + n_polys:
        return
    msg = (
        f'{n_lines + n_polys} edge_source edges are not edges of the triangulation, so they do '
        'not constrain it. Edges must not cross each other, and points closer than tol are merged.'
    )
    if n_polys:
        msg += ' Since a polygon edge is missing, no polygon insides or holes are removed.'
    warn_external(msg)


def _check_winding(
    mesh: DataSet, edge_source: PolyData, matrix: NDArray[np.float64], *, emptied: bool
) -> None:
    """Warn when ``edge_source`` polygons are not one outer boundary with holes."""
    points = mesh.points @ matrix[:2, :3].T
    rings = [points[ids] for ids in edge_source.irregular_faces]
    areas = [
        np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1]) for r in rings
    ]
    ccw = [r for r, area in zip(rings, areas, strict=True) if area > 0]
    cw = [r for r, area in zip(rings, areas, strict=True) if area < 0]
    advice = (
        'Order at most one outer boundary counter-clockwise and the holes inside it '
        'clockwise, as seen from the projection plane.'
    )
    if len(cw) == 1 and ccw and all(_ring_in_ring(r, cw[0]) for r in ccw):
        problem = 'every polygon is wound opposite to the projection plane'
        advice = 'Reverse all of them, for example with flip_faces().'
    elif len(ccw) > 1:
        problem = f'{len(ccw)} polygons are counter-clockwise'
    elif ccw and not all(_ring_in_ring(r, ccw[0]) for r in cw):
        problem = 'a clockwise polygon lies outside the counter-clockwise polygon'
    elif _any_ring_nested(cw):
        problem = 'a clockwise polygon lies inside another clockwise polygon'
    elif not ccw and emptied:
        problem = 'every polygon is clockwise, so the whole triangulation is a hole'
    else:
        return
    msg = f'The edge_source polygons cannot be triangulated as intended: {problem}. {advice}'
    warn_external(msg)


def _ring_in_ring(ring: NDArray[np.float64], other: NDArray[np.float64]) -> bool:
    """Return whether most of a sample of a 2D ring's vertices lie inside another 2D ring."""
    sample = ring[:: max(1, len(ring) // 32)]
    x, y = sample[:, :1], sample[:, 1:]
    x0, y0 = other[:, 0], other[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    straddles = (y0 > y) != (y1 > y)
    with np.errstate(divide='ignore', invalid='ignore'):
        crossing_x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    inside = np.count_nonzero(straddles & (x < crossing_x), axis=1) % 2 == 1
    return bool(np.mean(inside) > 0.5)


def _any_ring_nested(rings: list[NDArray[np.float64]]) -> bool:
    """Return whether any 2D ring lies inside another one."""
    if len(rings) < 2:
        return False
    lower = np.array([r.min(axis=0) for r in rings])
    upper = np.array([r.max(axis=0) for r in rings])
    overlap = np.all((lower[:, None] <= upper[None]) & (upper[:, None] >= lower[None]), axis=2)
    np.fill_diagonal(overlap, val=False)
    return any(_ring_in_ring(rings[i], rings[j]) for i, j in np.argwhere(overlap))
