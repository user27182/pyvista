"""Plotting routines."""

from __future__ import annotations

__lazy_modules__ = [
    'pyvista',
    'pyvista._plot',
    'pyvista.plotting',
    'pyvista.plotting._property',
    'pyvista.plotting.actor',
    'pyvista.plotting.actor_properties',
    'pyvista.plotting.affine_widget',
    'pyvista.plotting.axes',
    'pyvista.plotting.axes_actor',
    'pyvista.plotting.axes_assembly',
    'pyvista.plotting.camera',
    'pyvista.plotting.charts',
    'pyvista.plotting.colors',
    'pyvista.plotting.component_registry',
    'pyvista.plotting.composite_mapper',
    'pyvista.plotting.cube_axes_actor',
    'pyvista.plotting.errors',
    'pyvista.plotting.follower',
    'pyvista.plotting.helpers',
    'pyvista.plotting.interactor_style_registry',
    'pyvista.plotting.lights',
    'pyvista.plotting.lookup_table',
    'pyvista.plotting.mapper',
    'pyvista.plotting.opts',
    'pyvista.plotting.picking',
    'pyvista.plotting.plotter',
    'pyvista.plotting.prop3d',
    'pyvista.plotting.render_window_interactor',
    'pyvista.plotting.renderer',
    'pyvista.plotting.text',
    'pyvista.plotting.texture',
    'pyvista.plotting.theme_registry',
    'pyvista.plotting.themes',
    'pyvista.plotting.tools',
    'pyvista.plotting.utilities',
    'pyvista.plotting.utilities.sphinx_gallery',
    'pyvista.plotting.volume',
    'pyvista.plotting.volume_property',
    'pyvista.plotting.widgets',
    'pyvista.typing',
    'typing',
]

# isort: off
# Must come first: registers the VTK rendering factories (and LaTeX support) via
# the active backend before any rendering class below is imported.
import pyvista.plotting._rendering_imports  # noqa: F401  # eager: registers rendering factories

# isort: on

from typing import Any

from pyvista import MAX_N_COLOR_BARS as MAX_N_COLOR_BARS
from pyvista._plot import plot as plot
from pyvista.typing import _MOVED_TO_TYPING_NAMESPACE
from pyvista.typing import _get_deprecated_alias

# Bound so the submodule is also reachable as ``pyvista._typing``
from . import _typing as _typing
from ._property import Property as Property
from .actor import Actor as Actor
from .actor_properties import ActorProperties as ActorProperties
from .affine_widget import AffineWidget3D as AffineWidget3D
from .axes import Axes as Axes
from .axes_actor import AxesActor as AxesActor
from .axes_assembly import AxesAssembly as AxesAssembly
from .axes_assembly import AxesAssemblySymmetric as AxesAssemblySymmetric
from .axes_assembly import PlanesAssembly as PlanesAssembly
from .camera import Camera as Camera
from .charts import Chart2D as Chart2D
from .charts import ChartBox as ChartBox
from .charts import ChartMPL as ChartMPL
from .charts import ChartPie as ChartPie
from .colors import PARAVIEW_BACKGROUND as PARAVIEW_BACKGROUND
from .colors import Color as Color
from .colors import __getattr__ as _colors_getattr
from .colors import color_char_to_word as color_char_to_word
from .colors import get_cmap_safe as get_cmap_safe
from .colors import hex_colors as hex_colors
from .component_registry import ComponentRegistration as ComponentRegistration
from .component_registry import PlotterComponent as PlotterComponent
from .component_registry import register_plotter_component as register_plotter_component
from .component_registry import registered_plotter_components as registered_plotter_components
from .component_registry import unregister_plotter_component as unregister_plotter_component
from .composite_mapper import BlockAttributes as BlockAttributes
from .composite_mapper import CompositeAttributes as CompositeAttributes
from .composite_mapper import CompositePolyDataMapper as CompositePolyDataMapper
from .cube_axes_actor import CubeAxesActor as CubeAxesActor
from .errors import InvalidCameraError as InvalidCameraError
from .errors import RenderWindowUnavailable as RenderWindowUnavailable
from .follower import Follower as Follower
from .helpers import plot_arrows as plot_arrows
from .helpers import plot_compare_four as plot_compare_four
from .interactor_style_registry import register_interactor_style as register_interactor_style
from .lights import Light as Light
from .lookup_table import LookupTable as LookupTable
from .mapper import DataSetMapper as DataSetMapper
from .mapper import FixedPointVolumeRayCastMapper as FixedPointVolumeRayCastMapper
from .mapper import GPUVolumeRayCastMapper as GPUVolumeRayCastMapper
from .mapper import OpenGLGPUVolumeRayCastMapper as OpenGLGPUVolumeRayCastMapper
from .mapper import PointGaussianMapper as PointGaussianMapper
from .mapper import SmartVolumeMapper as SmartVolumeMapper
from .mapper import UnstructuredGridVolumeRayCastMapper as UnstructuredGridVolumeRayCastMapper
from .opts import PointSpriteShape as PointSpriteShape
from .opts import ShaderType as ShaderType
from .picking import PickingComponent as PickingComponent
from .plot_compare import plot_compare as plot_compare
from .plotter import _ALL_PLOTTERS as _ALL_PLOTTERS
from .plotter import BasePlotter as BasePlotter
from .plotter import Plotter as Plotter
from .plotter import close_all as close_all
from .prop3d import Prop3D as Prop3D
from .render_window_interactor import RenderWindowInteractor as RenderWindowInteractor
from .render_window_interactor import Timer as Timer
from .renderer import CameraPosition as CameraPosition
from .renderer import Renderer as Renderer
from .renderer import scale_point as scale_point
from .text import CornerAnnotation as CornerAnnotation
from .text import Label as Label
from .text import Text as Text
from .text import TextProperty as TextProperty
from .texture import Texture as Texture
from .texture import image_to_texture as image_to_texture
from .texture import numpy_to_texture as numpy_to_texture
from .theme_registry import ThemeRegistration as ThemeRegistration
from .theme_registry import registered_themes as registered_themes
from .themes import DocumentTheme as _GlobalTheme
from .themes import _set_plot_theme_from_env as _set_plot_theme_from_env
from .themes import load_theme as load_theme
from .themes import set_plot_theme as set_plot_theme
from .tools import FONTS as FONTS
from .tools import check_math_text_support as check_math_text_support
from .tools import check_matplotlib_vtk_compatibility as check_matplotlib_vtk_compatibility
from .tools import create_axes_marker as create_axes_marker
from .tools import create_axes_orientation_box as create_axes_orientation_box
from .tools import normalize as normalize
from .tools import opacity_transfer_function as opacity_transfer_function
from .tools import parse_font_family as parse_font_family
from .tools import system_supports_plotting as system_supports_plotting
from .utilities import Scraper as Scraper
from .utilities import active_scalars_algorithm as active_scalars_algorithm
from .utilities import add_ids_algorithm as add_ids_algorithm
from .utilities import algorithm_to_mesh_handler as algorithm_to_mesh_handler
from .utilities import algorithms as algorithms
from .utilities import callback_algorithm as callback_algorithm
from .utilities import cell_data_to_point_data_algorithm as cell_data_to_point_data_algorithm
from .utilities import check_depth_peeling as check_depth_peeling
from .utilities import compare_images as compare_images
from .utilities import crinkle_algorithm as crinkle_algorithm
from .utilities import cubemap as cubemap
from .utilities import cubemap_from_filenames as cubemap_from_filenames
from .utilities import decimation_algorithm as decimation_algorithm
from .utilities import extract_surface_algorithm as extract_surface_algorithm
from .utilities import gl_checks as gl_checks
from .utilities import image_from_window as image_from_window
from .utilities import outline_algorithm as outline_algorithm
from .utilities import point_data_to_cell_data_algorithm as point_data_to_cell_data_algorithm
from .utilities import pointset_to_polydata_algorithm as pointset_to_polydata_algorithm
from .utilities import regression as regression
from .utilities import remove_alpha as remove_alpha
from .utilities import run_image_filter as run_image_filter
from .utilities import set_algorithm_input as set_algorithm_input
from .utilities import smooth_shading_algorithm as smooth_shading_algorithm
from .utilities import source_algorithm as source_algorithm
from .utilities import sphinx_gallery as sphinx_gallery
from .utilities import triangulate_algorithm as triangulate_algorithm
from .utilities import uses_egl as uses_egl
from .utilities import wrap_image_array as wrap_image_array
from .utilities.sphinx_gallery import _get_sg_image_scraper as _get_sg_image_scraper
from .volume import Volume as Volume
from .volume_property import VolumeProperty as VolumeProperty
from .widgets import WidgetComponent as WidgetComponent


class QtDeprecationError(Exception):  # numpydoc ignore=PR01
    """Deprecation Error for features that moved to ``pyvistaqt``."""

    message = """`{}` has moved to pyvistaqt.
    You can install this from PyPI with: `pip install pyvistaqt`
    Then import it via: `from pyvistaqt import {}`
    `{}` is no longer accessible by `pyvista.{}`
    See https://github.com/pyvista/pyvistaqt
"""

    def __init__(self, feature_name: str) -> None:
        """Empty init."""
        Exception.__init__(self, self.message.format(*[feature_name] * 4))


class BackgroundPlotter:  # numpydoc ignore=PR01
    """This class has been moved to pyvistaqt."""  # noqa: D404

    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
        """Empty init."""
        msg = 'BackgroundPlotter'
        raise QtDeprecationError(msg)


class QtInteractor:  # numpydoc ignore=PR01
    """This class has been moved to pyvistaqt."""  # noqa: D404

    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
        """Empty init."""
        msg = 'QtInteractor'
        raise QtDeprecationError(msg)


global_theme: _GlobalTheme = _GlobalTheme()


def __getattr__(name: str) -> Any:
    """Forward the deprecated attributes of this module with a warning."""
    if name in _MOVED_TO_TYPING_NAMESPACE[__name__]:
        return _get_deprecated_alias(__name__, name)
    return _colors_getattr(name)
