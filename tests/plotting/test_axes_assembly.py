from __future__ import annotations

import numpy as np
import pytest

import pyvista as pv


@pytest.fixture()
def axes_assembly():
    return pv.AxesAssembly()


def test_axes_assembly_repr(axes_assembly):
    repr_ = repr(axes_assembly)
    actual_lines = repr_.splitlines()[1:]
    expected_lines = [
        "  Shaft type:                 'cylinder'",
        "  Shaft radius:               0.025",
        "  Shaft length:               (0.8, 0.8, 0.8)",
        "  Tip type:                   'cone'",
        "  Tip radius:                 0.1",
        "  Tip length:                 (0.2, 0.2, 0.2)",
        "  Visible:                    True",
        "  X Bounds                    -1.000E-01, 1.000E+00",
        "  Y Bounds                    -1.000E-01, 1.000E+00",
        "  Z Bounds                    -1.000E-01, 1.000E+00",
    ]
    assert len(actual_lines) == len(expected_lines)
    assert actual_lines == expected_lines

    axes_assembly.user_matrix = np.eye(4) * 2
    repr_ = repr(axes_assembly)
    assert "User matrix:                Set" in repr_


@pytest.fixture()
def _config_axes_theme():
    # Store values
    x_color = pv.global_theme.axes.x_color
    y_color = pv.global_theme.axes.y_color
    z_color = pv.global_theme.axes.z_color
    yield
    # Restore values
    pv.global_theme.axes.x_color = x_color
    pv.global_theme.axes.y_color = y_color
    pv.global_theme.axes.z_color = z_color


@pytest.mark.usefixtures('_config_axes_theme')
def test_axes_geometry_source_theme(axes_assembly):
    assert axes_assembly.x_color[0].name == 'tomato'
    assert axes_assembly.x_color[1].name == 'tomato'
    assert axes_assembly.y_color[0].name == 'seagreen'
    assert axes_assembly.y_color[1].name == 'seagreen'
    assert axes_assembly.z_color[0].name == 'mediumblue'
    assert axes_assembly.z_color[1].name == 'mediumblue'

    pv.global_theme.axes.x_color = 'black'
    pv.global_theme.axes.y_color = 'white'
    pv.global_theme.axes.z_color = 'gray'

    axes_geometry_source = pv.AxesAssembly()
    assert axes_geometry_source.x_color[0].name == 'black'
    assert axes_geometry_source.x_color[1].name == 'black'
    assert axes_geometry_source.y_color[0].name == 'white'
    assert axes_geometry_source.y_color[1].name == 'white'
    assert axes_geometry_source.z_color[0].name == 'gray'
    assert axes_geometry_source.z_color[1].name == 'gray'
