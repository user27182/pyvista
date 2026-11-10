"""PyVista package for 3D plotting and mesh analysis."""

from __future__ import annotations

__lazy_modules__ = [
    'importlib',
    'inspect',
    'os',
    'pyvista._plot',
    'pyvista._version',
    'pyvista._vtk_version',
    'pyvista.core',
    'pyvista.core._typing_core._dataset_types',
    'pyvista.core._vtk_utilities',
    'pyvista.core.cell',
    'pyvista.core.errors',
    'pyvista.core.utilities.accessor_registry',
    'pyvista.core.utilities.observers',
    'pyvista.core.utilities.reader_registry',
    'pyvista.core.utilities.writer_registry',
    'pyvista.core.wrappers',
    'pyvista.jupyter',
    'pyvista.report',
    'pyvista.typing',
    'pyvista_validation',
    'sys',
    'types',
    'typing',
]

import importlib
import inspect
import os
import sys
from types import ModuleType

if sys.version_info >= (3, 15):
    from types import LazyImportType
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

import pyvista_validation

from pyvista._plot import plot as plot
from pyvista._version import __version__ as __version__
from pyvista._version import _is_deprecation_due
from pyvista._version import version_info as version_info
from pyvista._vtk_version import _MIN_SUPPORTED_VTK_VERSION
from pyvista._vtk_version import VersionInfo
from pyvista._vtk_version import vtk_version_info as vtk_version_info
from pyvista._warn_external import warn_external as _warn_external
from pyvista.core import AmbiguousDataError as AmbiguousDataError
from pyvista.core import AnnotatedIntEnum as AnnotatedIntEnum
from pyvista.core import Arrow as Arrow
from pyvista.core import ArrowSource as ArrowSource
from pyvista.core import AVSucdReader as AVSucdReader
from pyvista.core import AxesGeometrySource as AxesGeometrySource
from pyvista.core import BaseReader as BaseReader
from pyvista.core import BaseVTKReader as BaseVTKReader
from pyvista.core import BaseWriter as BaseWriter
from pyvista.core import BinaryMarchingCubesReader as BinaryMarchingCubesReader
from pyvista.core import BMPReader as BMPReader
from pyvista.core import BMPWriter as BMPWriter
from pyvista.core import BoundsTuple as BoundsTuple
from pyvista.core import Box as Box
from pyvista.core import BoxSource as BoxSource
from pyvista.core import BYUReader as BYUReader
from pyvista.core import Capsule as Capsule
from pyvista.core import Cell as Cell
from pyvista.core import CellArray as CellArray
from pyvista.core import CellStatus as CellStatus
from pyvista.core import CellType as CellType
from pyvista.core import CGNSReader as CGNSReader
from pyvista.core import Circle as Circle
from pyvista.core import CircularArc as CircularArc
from pyvista.core import CircularArcFromNormal as CircularArcFromNormal
from pyvista.core import CompositeFilters as CompositeFilters
from pyvista.core import Cone as Cone
from pyvista.core import ConeSource as ConeSource
from pyvista.core import Cube as Cube
from pyvista.core import CubeFacesSource as CubeFacesSource
from pyvista.core import CubeSource as CubeSource
from pyvista.core import Cylinder as Cylinder
from pyvista.core import CylinderSource as CylinderSource
from pyvista.core import CylinderStructured as CylinderStructured
from pyvista.core import DataObject as DataObject
from pyvista.core import DataObjectFilters as DataObjectFilters
from pyvista.core import DataSet as DataSet
from pyvista.core import DataSetAttributes as DataSetAttributes
from pyvista.core import DataSetFilters as DataSetFilters
from pyvista.core import DataSetWriter as DataSetWriter
from pyvista.core import DEMReader as DEMReader
from pyvista.core import DeprecationError as DeprecationError
from pyvista.core import DICOMReader as DICOMReader
from pyvista.core import Disc as Disc
from pyvista.core import DiscSource as DiscSource
from pyvista.core import Dodecahedron as Dodecahedron
from pyvista.core import Ellipse as Ellipse
from pyvista.core import EnSightReader as EnSightReader
from pyvista.core import EnSightWriter as EnSightWriter
from pyvista.core import ExodusIIBlockSet as ExodusIIBlockSet
from pyvista.core import ExodusIIReader as ExodusIIReader
from pyvista.core import ExplicitStructuredGrid as ExplicitStructuredGrid
from pyvista.core import FacetReader as FacetReader
from pyvista.core import FieldAssociation as FieldAssociation
from pyvista.core import FLUENTCFFReader as FLUENTCFFReader
from pyvista.core import FluentReader as FluentReader
from pyvista.core import GambitReader as GambitReader
from pyvista.core import GaussianCubeReader as GaussianCubeReader
from pyvista.core import GESignaReader as GESignaReader
from pyvista.core import GIFReader as GIFReader
from pyvista.core import GLTFReader as GLTFReader
from pyvista.core import GRDECLReader as GRDECLReader
from pyvista.core import Grid as Grid
from pyvista.core import HDFReader as HDFReader
from pyvista.core import HDFWriter as HDFWriter
from pyvista.core import HDRReader as HDRReader
from pyvista.core import HoudiniPolyDataWriter as HoudiniPolyDataWriter
from pyvista.core import Icosahedron as Icosahedron
from pyvista.core import Icosphere as Icosphere
from pyvista.core import ImageData as ImageData
from pyvista.core import ImageDataFilters as ImageDataFilters
from pyvista.core import ImageEllipsoidSource as ImageEllipsoidSource
from pyvista.core import ImageGaussianSource as ImageGaussianSource
from pyvista.core import ImageGridSource as ImageGridSource
from pyvista.core import ImageMandelbrotSource as ImageMandelbrotSource
from pyvista.core import ImageNoiseSource as ImageNoiseSource
from pyvista.core import ImageSinusoidSource as ImageSinusoidSource
from pyvista.core import InvalidMeshError as InvalidMeshError
from pyvista.core import InvalidMeshWarning as InvalidMeshWarning
from pyvista.core import IVWriter as IVWriter
from pyvista.core import JPEGReader as JPEGReader
from pyvista.core import JPEGWriter as JPEGWriter
from pyvista.core import KochanekSpline as KochanekSpline
from pyvista.core import Line as Line
from pyvista.core import LineSource as LineSource
from pyvista.core import MetaImageReader as MetaImageReader
from pyvista.core import MFIXReader as MFIXReader
from pyvista.core import MINCImageReader as MINCImageReader
from pyvista.core import MissingDataError as MissingDataError
from pyvista.core import MultiBlock as MultiBlock
from pyvista.core import MultiBlockPlot3DReader as MultiBlockPlot3DReader
from pyvista.core import MultipleLines as MultipleLines
from pyvista.core import MultipleLinesSource as MultipleLinesSource
from pyvista.core import Nek5000Reader as Nek5000Reader
from pyvista.core import NIFTIImageWriter as NIFTIImageWriter
from pyvista.core import NIFTIReader as NIFTIReader
from pyvista.core import NotAllTrianglesError as NotAllTrianglesError
from pyvista.core import NRRDReader as NRRDReader
from pyvista.core import OBJReader as OBJReader
from pyvista.core import OBJWriter as OBJWriter
from pyvista.core import Observer as Observer
from pyvista.core import Octahedron as Octahedron
from pyvista.core import OpenFOAMReader as OpenFOAMReader
from pyvista.core import OrthogonalPlanesSource as OrthogonalPlanesSource
from pyvista.core import ParametricBohemianDome as ParametricBohemianDome
from pyvista.core import ParametricBour as ParametricBour
from pyvista.core import ParametricBoy as ParametricBoy
from pyvista.core import ParametricCatalanMinimal as ParametricCatalanMinimal
from pyvista.core import ParametricConicSpiral as ParametricConicSpiral
from pyvista.core import ParametricCrossCap as ParametricCrossCap
from pyvista.core import ParametricDini as ParametricDini
from pyvista.core import ParametricEllipsoid as ParametricEllipsoid
from pyvista.core import ParametricEnneper as ParametricEnneper
from pyvista.core import ParametricFigure8Klein as ParametricFigure8Klein
from pyvista.core import ParametricHenneberg as ParametricHenneberg
from pyvista.core import ParametricKlein as ParametricKlein
from pyvista.core import ParametricKuen as ParametricKuen
from pyvista.core import ParametricMobius as ParametricMobius
from pyvista.core import ParametricPluckerConoid as ParametricPluckerConoid
from pyvista.core import ParametricPseudosphere as ParametricPseudosphere
from pyvista.core import ParametricRandomHills as ParametricRandomHills
from pyvista.core import ParametricRoman as ParametricRoman
from pyvista.core import ParametricSuperEllipsoid as ParametricSuperEllipsoid
from pyvista.core import ParametricSuperToroid as ParametricSuperToroid
from pyvista.core import ParametricTorus as ParametricTorus
from pyvista.core import ParticleReader as ParticleReader
from pyvista.core import PartitionedDataSet as PartitionedDataSet
from pyvista.core import PDBReader as PDBReader
from pyvista.core import PExodusIIReader as PExodusIIReader
from pyvista.core import Plane as Plane
from pyvista.core import PlaneSource as PlaneSource
from pyvista.core import PlatonicSolid as PlatonicSolid
from pyvista.core import PlatonicSolidSource as PlatonicSolidSource
from pyvista.core import Plot3DFunctionEnum as Plot3DFunctionEnum
from pyvista.core import Plot3DMetaReader as Plot3DMetaReader
from pyvista.core import PLYReader as PLYReader
from pyvista.core import PLYWriter as PLYWriter
from pyvista.core import PNGReader as PNGReader
from pyvista.core import PNGWriter as PNGWriter
from pyvista.core import PNMReader as PNMReader
from pyvista.core import PNMWriter as PNMWriter
from pyvista.core import PointCellDataSelection as PointCellDataSelection
from pyvista.core import PointGrid as PointGrid
from pyvista.core import PointSet as PointSet
from pyvista.core import PointSetCellOperationError as PointSetCellOperationError
from pyvista.core import PointSetDimensionReductionError as PointSetDimensionReductionError
from pyvista.core import PointSetNotSupported as PointSetNotSupported
from pyvista.core import PolyData as PolyData
from pyvista.core import PolyDataFilters as PolyDataFilters
from pyvista.core import PolyDataWriter as PolyDataWriter
from pyvista.core import Polygon as Polygon
from pyvista.core import PolygonSource as PolygonSource
from pyvista.core import POpenFOAMReader as POpenFOAMReader
from pyvista.core import PrecisionWarning as PrecisionWarning
from pyvista.core import ProgressMonitor as ProgressMonitor
from pyvista.core import ProStarReader as ProStarReader
from pyvista.core import PTSReader as PTSReader
from pyvista.core import PVDDataSet as PVDDataSet
from pyvista.core import PVDReader as PVDReader
from pyvista.core import Pyramid as Pyramid
from pyvista.core import PyVistaAttributeError as PyVistaAttributeError
from pyvista.core import PyVistaEfficiencyWarning as PyVistaEfficiencyWarning
from pyvista.core import PyVistaFutureWarning as PyVistaFutureWarning
from pyvista.core import PyVistaPipelineError as PyVistaPipelineError
from pyvista.core import Quadrilateral as Quadrilateral
from pyvista.core import Rectangle as Rectangle
from pyvista.core import RectilinearGrid as RectilinearGrid
from pyvista.core import RectilinearGridWriter as RectilinearGridWriter
from pyvista.core import SegYReader as SegYReader
from pyvista.core import SeriesDataSet as SeriesDataSet
from pyvista.core import SeriesReader as SeriesReader
from pyvista.core import SimplePointsWriter as SimplePointsWriter
from pyvista.core import SLCReader as SLCReader
from pyvista.core import SolidSphere as SolidSphere
from pyvista.core import SolidSphereGeneric as SolidSphereGeneric
from pyvista.core import Sphere as Sphere
from pyvista.core import SphereSource as SphereSource
from pyvista.core import Spline as Spline
from pyvista.core import STLReader as STLReader
from pyvista.core import STLWriter as STLWriter
from pyvista.core import StructuredGrid as StructuredGrid
from pyvista.core import StructuredGridWriter as StructuredGridWriter
from pyvista.core import StructuredSphere as StructuredSphere
from pyvista.core import Superquadric as Superquadric
from pyvista.core import SuperquadricSource as SuperquadricSource
from pyvista.core import Table as Table
from pyvista.core import TecplotReader as TecplotReader
from pyvista.core import Tetrahedron as Tetrahedron
from pyvista.core import Text3D as Text3D
from pyvista.core import Text3DSource as Text3DSource
from pyvista.core import ThreeDSReader as ThreeDSReader
from pyvista.core import TIFFReader as TIFFReader
from pyvista.core import TIFFWriter as TIFFWriter
from pyvista.core import TimeReader as TimeReader
from pyvista.core import Transform as Transform
from pyvista.core import Triangle as Triangle
from pyvista.core import Tube as Tube
from pyvista.core import UnstructuredGrid as UnstructuredGrid
from pyvista.core import UnstructuredGridFilters as UnstructuredGridFilters
from pyvista.core import UnstructuredGridWriter as UnstructuredGridWriter
from pyvista.core import VRMLReader as VRMLReader
from pyvista.core import VTKDataSetReader as VTKDataSetReader
from pyvista.core import VtkErrorCatcher as VtkErrorCatcher
from pyvista.core import VTKExecutionError as VTKExecutionError
from pyvista.core import VTKExecutionWarning as VTKExecutionWarning
from pyvista.core import VTKPDataSetReader as VTKPDataSetReader
from pyvista.core import VTKVersionError as VTKVersionError
from pyvista.core import Wavelet as Wavelet
from pyvista.core import XdmfReader as XdmfReader
from pyvista.core import XMLImageDataReader as XMLImageDataReader
from pyvista.core import XMLImageDataWriter as XMLImageDataWriter
from pyvista.core import XMLMultiBlockDataReader as XMLMultiBlockDataReader
from pyvista.core import XMLMultiBlockDataWriter as XMLMultiBlockDataWriter
from pyvista.core import XMLPartitionedDataSetReader as XMLPartitionedDataSetReader
from pyvista.core import XMLPartitionedDataSetWriter as XMLPartitionedDataSetWriter
from pyvista.core import XMLPImageDataReader as XMLPImageDataReader
from pyvista.core import XMLPolyDataReader as XMLPolyDataReader
from pyvista.core import XMLPolyDataWriter as XMLPolyDataWriter
from pyvista.core import XMLPRectilinearGridReader as XMLPRectilinearGridReader
from pyvista.core import XMLPUnstructuredGridReader as XMLPUnstructuredGridReader
from pyvista.core import XMLRectilinearGridReader as XMLRectilinearGridReader
from pyvista.core import XMLRectilinearGridWriter as XMLRectilinearGridWriter
from pyvista.core import XMLStructuredGridReader as XMLStructuredGridReader
from pyvista.core import XMLStructuredGridWriter as XMLStructuredGridWriter
from pyvista.core import XMLUnstructuredGridReader as XMLUnstructuredGridReader
from pyvista.core import XMLUnstructuredGridWriter as XMLUnstructuredGridWriter
from pyvista.core import abstract_class as abstract_class
from pyvista.core import accessor_registry as accessor_registry
from pyvista.core import allow_new_attributes as allow_new_attributes
from pyvista.core import array_from_vtkmatrix as array_from_vtkmatrix
from pyvista.core import arrays as arrays
from pyvista.core import assert_empty_kwargs as assert_empty_kwargs
from pyvista.core import axis_rotation as axis_rotation
from pyvista.core import cartesian_to_spherical as cartesian_to_spherical
from pyvista.core import cell as cell
from pyvista.core import cell_array as cell_array
from pyvista.core import cell_quality as cell_quality
from pyvista.core import cell_quality_info as cell_quality_info
from pyvista.core import cells as cells
from pyvista.core import celltype as celltype
from pyvista.core import check_valid_vector as check_valid_vector
from pyvista.core import composite as composite
from pyvista.core import conditional_decorator as conditional_decorator
from pyvista.core import config as config
from pyvista.core import convert_array as convert_array
from pyvista.core import convert_string_array as convert_string_array
from pyvista.core import create_grid as create_grid
from pyvista.core import create_mixed_cells as create_mixed_cells
from pyvista.core import dataobject as dataobject
from pyvista.core import dataset as dataset
from pyvista.core import datasetattributes as datasetattributes
from pyvista.core import enable_smp_tools as enable_smp_tools
from pyvista.core import errors as errors
from pyvista.core import features as features
from pyvista.core import field_array as field_array
from pyvista.core import fileio as fileio
from pyvista.core import filters as filters
from pyvista.core import fit_line_to_points as fit_line_to_points
from pyvista.core import fit_plane_to_points as fit_plane_to_points
from pyvista.core import formatting_html as formatting_html
from pyvista.core import from_meshio as from_meshio
from pyvista.core import from_trimesh as from_trimesh
from pyvista.core import generate_plane as generate_plane
from pyvista.core import geometric_objects as geometric_objects
from pyvista.core import geometric_sources as geometric_sources
from pyvista.core import get_array as get_array
from pyvista.core import get_array_association as get_array_association
from pyvista.core import get_ext as get_ext
from pyvista.core import get_mixed_cells as get_mixed_cells
from pyvista.core import get_reader as get_reader
from pyvista.core import get_vtk_type as get_vtk_type
from pyvista.core import global_config as global_config
from pyvista.core import grid as grid
from pyvista.core import grid_from_sph_coords as grid_from_sph_coords
from pyvista.core import has_module as has_module
from pyvista.core import helpers as helpers
from pyvista.core import image_sources as image_sources
from pyvista.core import is_inside_bounds as is_inside_bounds
from pyvista.core import is_meshio_mesh as is_meshio_mesh
from pyvista.core import is_pyvista_dataset as is_pyvista_dataset
from pyvista.core import is_trimesh_mesh as is_trimesh_mesh
from pyvista.core import line_segments_from_points as line_segments_from_points
from pyvista.core import lines_from_points as lines_from_points
from pyvista.core import make_tri_mesh as make_tri_mesh
from pyvista.core import merge as merge
from pyvista.core import misc as misc
from pyvista.core import ncells_from_cells as ncells_from_cells
from pyvista.core import numpy_to_idarr as numpy_to_idarr
from pyvista.core import objects as objects
from pyvista.core import observers as observers
from pyvista.core import parametric_keywords as parametric_keywords
from pyvista.core import parametric_objects as parametric_objects
from pyvista.core import parse_field_choice as parse_field_choice
from pyvista.core import partitioned as partitioned
from pyvista.core import perlin_noise as perlin_noise
from pyvista.core import point_array as point_array
from pyvista.core import points as points
from pyvista.core import pointset as pointset
from pyvista.core import principal_axes as principal_axes
from pyvista.core import pyvista_ndarray as pyvista_ndarray
from pyvista.core import raise_has_duplicates as raise_has_duplicates
from pyvista.core import raise_not_matching as raise_not_matching
from pyvista.core import read as read
from pyvista.core import read_exodus as read_exodus
from pyvista.core import read_grdecl as read_grdecl
from pyvista.core import read_meshio as read_meshio
from pyvista.core import read_pickle as read_pickle
from pyvista.core import read_texture as read_texture
from pyvista.core import reader as reader
from pyvista.core import reader_registry as reader_registry
from pyvista.core import row_array as row_array
from pyvista.core import sample_function as sample_function
from pyvista.core import save_meshio as save_meshio
from pyvista.core import save_pickle as save_pickle
from pyvista.core import set_default_active_scalars as set_default_active_scalars
from pyvista.core import set_default_active_vectors as set_default_active_vectors
from pyvista.core import set_error_output_file as set_error_output_file
from pyvista.core import set_new_attribute as set_new_attribute
from pyvista.core import set_pickle_format as set_pickle_format
from pyvista.core import spherical_to_cartesian as spherical_to_cartesian
from pyvista.core import state_manager as state_manager
from pyvista.core import surface_from_para as surface_from_para
from pyvista.core import threaded as threaded
from pyvista.core import to_meshio as to_meshio
from pyvista.core import to_trimesh as to_trimesh
from pyvista.core import transform as transform
from pyvista.core import transform_vectors_sph_to_cart as transform_vectors_sph_to_cart
from pyvista.core import transformations as transformations
from pyvista.core import try_callback as try_callback
from pyvista.core import vector_poly_data as vector_poly_data
from pyvista.core import vtk_bit_array_to_char as vtk_bit_array_to_char
from pyvista.core import vtk_id_list_to_array as vtk_id_list_to_array
from pyvista.core import vtk_points as vtk_points
from pyvista.core import vtk_snake_case as vtk_snake_case
from pyvista.core import vtk_verbosity as vtk_verbosity
from pyvista.core import vtkmatrix_from_array as vtkmatrix_from_array
from pyvista.core import wrap as wrap
from pyvista.core import wrappers as wrappers
from pyvista.core import writer as writer
from pyvista.core import writer_registry as writer_registry
from pyvista.core._typing_core._dataset_types import _DataObjectType as _DataObjectType
from pyvista.core._typing_core._dataset_types import (
    _DataSetOrMultiBlockType as _DataSetOrMultiBlockType,
)
from pyvista.core._typing_core._dataset_types import _DataSetType as _DataSetType
from pyvista.core._typing_core._dataset_types import _GridType as _GridType
from pyvista.core._typing_core._dataset_types import _PointGridType as _PointGridType
from pyvista.core._typing_core._dataset_types import _PointSetBaseType as _PointSetBaseType
from pyvista.core._vtk_utilities import vtk_backend as vtk_backend
from pyvista.core.cell import _get_vtk_id_type
from pyvista.core.errors import PyVistaDeprecationWarning as PyVistaDeprecationWarning
from pyvista.core.utilities.accessor_registry import AccessorRegistration as AccessorRegistration
from pyvista.core.utilities.accessor_registry import DataSetAccessor as DataSetAccessor
from pyvista.core.utilities.accessor_registry import (
    register_dataset_accessor as register_dataset_accessor,
)
from pyvista.core.utilities.accessor_registry import registered_accessors as registered_accessors
from pyvista.core.utilities.accessor_registry import (
    unregister_dataset_accessor as unregister_dataset_accessor,
)
from pyvista.core.utilities.observers import send_errors_to_logging as send_errors_to_logging
from pyvista.core.utilities.reader_registry import LocalFileRequiredError as LocalFileRequiredError
from pyvista.core.utilities.reader_registry import ReaderRegistration as ReaderRegistration
from pyvista.core.utilities.reader_registry import has_scheme as has_scheme
from pyvista.core.utilities.reader_registry import register_reader as register_reader
from pyvista.core.utilities.reader_registry import registered_readers as registered_readers
from pyvista.core.utilities.writer_registry import WriterRegistration as WriterRegistration
from pyvista.core.utilities.writer_registry import register_writer as register_writer
from pyvista.core.utilities.writer_registry import registered_writers as registered_writers
from pyvista.core.wrappers import _wrappers as _wrappers
from pyvista.jupyter import JupyterBackendRegistration as JupyterBackendRegistration
from pyvista.jupyter import register_jupyter_backend as register_jupyter_backend
from pyvista.jupyter import registered_jupyter_backends as registered_jupyter_backends
from pyvista.jupyter import set_jupyter_backend as set_jupyter_backend
from pyvista.report import GPUInfo as GPUInfo
from pyvista.report import Report as Report
from pyvista.report import check_math_text_support as check_math_text_support
from pyvista.report import check_matplotlib_vtk_compatibility as check_matplotlib_vtk_compatibility
from pyvista.report import get_gpu_info as get_gpu_info
from pyvista.typing import _DEPRECATED_ALIASES
from pyvista.typing import _MOVED_TO_TYPING_NAMESPACE
from pyvista.typing import _get_deprecated_alias

if TYPE_CHECKING:
    import numpy as np

    from pyvista.plotting.themes import Theme

# get the int type from vtk
if TYPE_CHECKING:
    ID_TYPE: type[np.int32 | np.longlong]

if vtk_version_info < _MIN_SUPPORTED_VTK_VERSION:  # pragma: no cover
    from pyvista.core.errors import VTKVersionError

    msg = f'VTK version must be {VersionInfo._format(_MIN_SUPPORTED_VTK_VERSION)} or greater.'
    raise VTKVersionError(msg)

# A simple flag to set when generating the documentation
OFF_SCREEN = os.environ.get('PYVISTA_OFF_SCREEN', 'false').lower() == 'true'

# flag for when building the sphinx_gallery
BUILDING_GALLERY = os.environ.get('PYVISTA_BUILDING_GALLERY', 'false').lower() == 'true'
# Set by the pyvista-plot directive while it runs code, overriding the gallery scraper
_GALLERY_FORCE_STATIC: bool | None = None
# Set while the sphinx-gallery scraper last created is the static Scraper
_GALLERY_STATIC_SCRAPER = False

# Set where figures are saved
FIGURE_PATH = os.environ.get('PYVISTA_FIGURE_PATH', None)

ON_SCREENSHOT = os.environ.get('PYVISTA_ON_SCREENSHOT', 'false').lower() == 'true'

# theme to use by default for the plot directive
PLOT_DIRECTIVE_THEME: Theme | str | None = None

# Set a parameter to control default print format for floats outside
# of the plotter
FLOAT_FORMAT = '{:.3e}'

# Serialization format to be used when pickling `DataObject`
_PICKLE_FORMAT: Literal['vtk', 'xml', 'legacy'] = 'vtk'

# Name used for unnamed scalars
DEFAULT_SCALARS_NAME = 'Data'

MAX_N_COLOR_BARS = 10

# Allow setting new private -- but not public -- attributes by default
_ALLOW_NEW_ATTRIBUTES_MODE: Literal['private', True, False] = 'private'


if not TYPE_CHECKING:
    from pyvista.core import utilities as utilities

# Import all modules for type checkers and linters
if TYPE_CHECKING:
    from pyvista import demos as demos
    from pyvista import examples as examples
    from pyvista import ext as ext
    from pyvista import trame as trame
    from pyvista import typing as typing
    from pyvista import utilities as utilities
    from pyvista.plotting import *


# Tracks whether the ``PYVISTA_PLOT_THEME`` environment variable has been
# applied yet. Applying a plugin theme runs arbitrary plugin code that can
# call back into ``pyvista`` before this module has finished the caller's
# original request; the flag keeps the apply single-shot.
_env_theme_applied: bool = False


# Lazily import/access the plotting module
def _get_deprecated_validation() -> ModuleType:
    """Forward ``pyvista._validation`` to the ``pyvista_validation`` package with a warning."""
    msg = (
        '`pyvista._validation` has moved to the `pyvista_validation` package; '
        'use `from pyvista_validation import ...` instead.'
    )
    _warn_external(msg, PyVistaDeprecationWarning)
    if version_info >= (0, 51):  # pragma: no cover
        msg = 'Convert this deprecation warning into an error.'
        raise RuntimeError(msg)
    if version_info >= (0, 52):  # pragma: no cover
        msg = 'Remove the _validation forward.'
        raise RuntimeError(msg)
    return pyvista_validation


def _warn_deprecated_pickle_format() -> None:
    """Warn that the pickle format selector is deprecated."""
    msg = (
        '`pyvista.PICKLE_FORMAT` is deprecated. The `vtk` format is the only supported '
        'pickle format and is always used.'
    )
    _warn_external(msg, PyVistaDeprecationWarning)
    if _is_deprecation_due((0, 53)):  # pragma: no cover
        msg = 'Convert this deprecation warning into an error.'
        raise RuntimeError(msg)
    if _is_deprecation_due((0, 54)):  # pragma: no cover
        msg = 'Remove the PICKLE_FORMAT deprecation.'
        raise RuntimeError(msg)


def __getattr__(name: str) -> Any:
    """Fetch an attribute ``name`` from ``globals()`` or the ``pyvista.plotting`` module.

    This override is implemented to prevent importing all of the plotting module
    and GL-dependent VTK modules when importing PyVista.

    Raises
    ------
    AttributeError
        If the attribute is not found.

    """

    def _cache_attr_and_return(obj: Any) -> Any:
        # Cache the attr on this module to avoid calls to __getattr__ on next access
        globals()[name] = obj
        return obj

    if name == 'hexcolors':
        from pyvista.plotting.colors import _get_deprecated_hexcolors  # noqa: PLC0415

        # Do not cache since we want to re-issue the deprecation warning
        return _get_deprecated_hexcolors()
    if name == '_validation':
        # Not cached either, so the deprecation warning is re-issued on each access
        return _get_deprecated_validation()
    if name == 'PICKLE_FORMAT':
        # Not cached either, so the deprecation warning is re-issued on each access
        _warn_deprecated_pickle_format()
        return _PICKLE_FORMAT

    if name in _MOVED_TO_TYPING_NAMESPACE[__name__] or name in _DEPRECATED_ALIASES:
        # Not cached either, so the deprecation warning is re-issued on each access
        return _get_deprecated_alias(__name__, name)

    allow = {
        'demos',
        'examples',
        'ext',
        'trame',
        'utilities',
    }
    # A name bound by a pending lazy import is this module's own, not a plotting attribute.
    lazy = globals().get(name)
    is_lazy = sys.version_info >= (3, 15) and isinstance(lazy, LazyImportType)
    if name in allow or name == 'ID_TYPE' or is_lazy:
        if is_lazy:
            obj = lazy.resolve()  # type: ignore[union-attr]
        elif name == 'ID_TYPE':
            obj = _get_vtk_id_type()
        else:
            obj = importlib.import_module(f'pyvista.{name}')
        return _cache_attr_and_return(obj)

    # avoid recursive import
    if 'pyvista.plotting' not in sys.modules:
        import pyvista.plotting  # noqa: F401, PLC0415

    plotting = sys.modules['pyvista.plotting']
    try:
        feature = inspect.getattr_static(plotting, name)
    except AttributeError:
        msg = f"module 'pyvista' has no attribute '{name}'"
        raise AttributeError(msg) from None
    if sys.version_info >= (3, 15) and isinstance(feature, LazyImportType):
        feature = getattr(plotting, name)

    # Apply ``PYVISTA_PLOT_THEME`` once, now that ``pyvista.plotting`` is fully
    # loaded and the caller's requested attribute is already resolved. Doing
    # this inside ``pyvista.plotting.__init__`` invites re-entrant access to a
    # partially-initialized module when an entry-point-registered plugin is
    # imported (Python 3.12 evaluates annotations like ``pv.Plotter`` eagerly
    # at plugin module load). The flag is set before the call to prevent
    # re-entrant double-application if a plugin's module body accesses
    # attributes on ``pyvista`` during the theme apply.
    global _env_theme_applied  # noqa: PLW0603
    if not _env_theme_applied:
        _env_theme_applied = True
        sys.modules['pyvista.plotting']._set_plot_theme_from_env()

    return _cache_attr_and_return(feature)


class _PyVistaModule(ModuleType):
    """Module type which intercepts assignment of deprecated module attributes."""

    def __setattr__(self, name: str, value: Any) -> None:
        """Set a module attribute, redirecting deprecated names to their replacement."""
        if name == 'PICKLE_FORMAT':
            _warn_deprecated_pickle_format()
            name = '_PICKLE_FORMAT'
        super().__setattr__(name, value)


# Module-level `__getattr__` covers reads only, so a subclass is needed to deprecate writes
sys.modules[__name__].__class__ = _PyVistaModule
