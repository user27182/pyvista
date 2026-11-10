"""Core routines."""

from __future__ import annotations

__lazy_modules__ = [
    'pyvista.core._typing_core',
    'pyvista.core.cell',
    'pyvista.core.celltype',
    'pyvista.core.composite',
    'pyvista.core.config',
    'pyvista.core.dataobject',
    'pyvista.core.dataset',
    'pyvista.core.datasetattributes',
    'pyvista.core.errors',
    'pyvista.core.filters',
    'pyvista.core.filters.data_object',
    'pyvista.core.grid',
    'pyvista.core.objects',
    'pyvista.core.partitioned',
    'pyvista.core.pointset',
    'pyvista.core.utilities',
    'pyvista.core.wrappers',
    'pyvista.typing',
    'typing',
]

from typing import TYPE_CHECKING

from pyvista.typing import _DEPRECATED_ALIASES
from pyvista.typing import _MOVED_TO_TYPING_NAMESPACE
from pyvista.typing import _get_deprecated_alias

from ._typing_core import BoundsTuple as BoundsTuple
from .cell import Cell as Cell
from .cell import CellArray as CellArray
from .celltype import CellType as CellType
from .composite import MultiBlock as MultiBlock
from .config import global_config as global_config
from .dataobject import DataObject as DataObject
from .dataset import DataSet as DataSet
from .datasetattributes import DataSetAttributes as DataSetAttributes
from .errors import AmbiguousDataError as AmbiguousDataError
from .errors import DeprecationError as DeprecationError
from .errors import InvalidMeshError as InvalidMeshError
from .errors import InvalidMeshWarning as InvalidMeshWarning
from .errors import MissingDataError as MissingDataError
from .errors import NotAllTrianglesError as NotAllTrianglesError
from .errors import PointSetCellOperationError as PointSetCellOperationError
from .errors import PointSetDimensionReductionError as PointSetDimensionReductionError
from .errors import PointSetNotSupported as PointSetNotSupported
from .errors import PrecisionWarning as PrecisionWarning
from .errors import PyVistaAttributeError as PyVistaAttributeError
from .errors import PyVistaDeprecationWarning as PyVistaDeprecationWarning
from .errors import PyVistaEfficiencyWarning as PyVistaEfficiencyWarning
from .errors import PyVistaFutureWarning as PyVistaFutureWarning
from .errors import PyVistaPipelineError as PyVistaPipelineError
from .errors import VTKExecutionError as VTKExecutionError
from .errors import VTKExecutionWarning as VTKExecutionWarning
from .errors import VTKVersionError as VTKVersionError
from .filters import CompositeFilters as CompositeFilters
from .filters import DataObjectFilters as DataObjectFilters
from .filters import DataSetFilters as DataSetFilters
from .filters import ImageDataFilters as ImageDataFilters
from .filters import PolyDataFilters as PolyDataFilters
from .filters import UnstructuredGridFilters as UnstructuredGridFilters
from .filters.data_object import CellStatus as CellStatus
from .grid import Grid as Grid
from .grid import ImageData as ImageData
from .grid import RectilinearGrid as RectilinearGrid
from .objects import Table as Table
from .partitioned import PartitionedDataSet as PartitionedDataSet
from .pointset import ExplicitStructuredGrid as ExplicitStructuredGrid
from .pointset import PointGrid as PointGrid
from .pointset import PointSet as PointSet
from .pointset import PolyData as PolyData
from .pointset import StructuredGrid as StructuredGrid
from .pointset import UnstructuredGrid as UnstructuredGrid
from .pyvista_ndarray import pyvista_ndarray as pyvista_ndarray
from .utilities import AccessorRegistration as AccessorRegistration
from .utilities import AnnotatedIntEnum as AnnotatedIntEnum
from .utilities import Arrow as Arrow
from .utilities import ArrowSource as ArrowSource
from .utilities import AVSucdReader as AVSucdReader
from .utilities import AxesGeometrySource as AxesGeometrySource
from .utilities import BaseReader as BaseReader
from .utilities import BaseVTKReader as BaseVTKReader
from .utilities import BaseWriter as BaseWriter
from .utilities import BinaryMarchingCubesReader as BinaryMarchingCubesReader
from .utilities import BMPReader as BMPReader
from .utilities import BMPWriter as BMPWriter
from .utilities import Box as Box
from .utilities import BoxSource as BoxSource
from .utilities import BYUReader as BYUReader
from .utilities import Capsule as Capsule
from .utilities import CGNSReader as CGNSReader
from .utilities import Circle as Circle
from .utilities import CircularArc as CircularArc
from .utilities import CircularArcFromNormal as CircularArcFromNormal
from .utilities import Cone as Cone
from .utilities import ConeSource as ConeSource
from .utilities import Cube as Cube
from .utilities import CubeFacesSource as CubeFacesSource
from .utilities import CubeSource as CubeSource
from .utilities import Cylinder as Cylinder
from .utilities import CylinderSource as CylinderSource
from .utilities import CylinderStructured as CylinderStructured
from .utilities import DataSetAccessor as DataSetAccessor
from .utilities import DataSetWriter as DataSetWriter
from .utilities import DEMReader as DEMReader
from .utilities import DICOMReader as DICOMReader
from .utilities import Disc as Disc
from .utilities import DiscSource as DiscSource
from .utilities import Dodecahedron as Dodecahedron
from .utilities import Ellipse as Ellipse
from .utilities import EnSightReader as EnSightReader
from .utilities import EnSightWriter as EnSightWriter
from .utilities import ExodusIIBlockSet as ExodusIIBlockSet
from .utilities import ExodusIIReader as ExodusIIReader
from .utilities import FacetReader as FacetReader
from .utilities import FieldAssociation as FieldAssociation
from .utilities import FLUENTCFFReader as FLUENTCFFReader
from .utilities import FluentReader as FluentReader
from .utilities import GambitReader as GambitReader
from .utilities import GaussianCubeReader as GaussianCubeReader
from .utilities import GESignaReader as GESignaReader
from .utilities import GIFReader as GIFReader
from .utilities import GLTFReader as GLTFReader
from .utilities import GRDECLReader as GRDECLReader
from .utilities import HDFReader as HDFReader
from .utilities import HDFWriter as HDFWriter
from .utilities import HDRReader as HDRReader
from .utilities import HoudiniPolyDataWriter as HoudiniPolyDataWriter
from .utilities import Icosahedron as Icosahedron
from .utilities import Icosphere as Icosphere
from .utilities import ImageEllipsoidSource as ImageEllipsoidSource
from .utilities import ImageGaussianSource as ImageGaussianSource
from .utilities import ImageGridSource as ImageGridSource
from .utilities import ImageMandelbrotSource as ImageMandelbrotSource
from .utilities import ImageNoiseSource as ImageNoiseSource
from .utilities import ImageSinusoidSource as ImageSinusoidSource
from .utilities import IVWriter as IVWriter
from .utilities import JPEGReader as JPEGReader
from .utilities import JPEGWriter as JPEGWriter
from .utilities import KochanekSpline as KochanekSpline
from .utilities import Line as Line
from .utilities import LineSource as LineSource
from .utilities import LocalFileRequiredError as LocalFileRequiredError
from .utilities import MetaImageReader as MetaImageReader
from .utilities import MFIXReader as MFIXReader
from .utilities import MINCImageReader as MINCImageReader
from .utilities import MultiBlockPlot3DReader as MultiBlockPlot3DReader
from .utilities import MultipleLines as MultipleLines
from .utilities import MultipleLinesSource as MultipleLinesSource
from .utilities import Nek5000Reader as Nek5000Reader
from .utilities import NIFTIImageWriter as NIFTIImageWriter
from .utilities import NIFTIReader as NIFTIReader
from .utilities import NRRDReader as NRRDReader
from .utilities import OBJReader as OBJReader
from .utilities import OBJWriter as OBJWriter
from .utilities import Observer as Observer
from .utilities import Octahedron as Octahedron
from .utilities import OpenFOAMReader as OpenFOAMReader
from .utilities import OrthogonalPlanesSource as OrthogonalPlanesSource
from .utilities import ParametricBohemianDome as ParametricBohemianDome
from .utilities import ParametricBour as ParametricBour
from .utilities import ParametricBoy as ParametricBoy
from .utilities import ParametricCatalanMinimal as ParametricCatalanMinimal
from .utilities import ParametricConicSpiral as ParametricConicSpiral
from .utilities import ParametricCrossCap as ParametricCrossCap
from .utilities import ParametricDini as ParametricDini
from .utilities import ParametricEllipsoid as ParametricEllipsoid
from .utilities import ParametricEnneper as ParametricEnneper
from .utilities import ParametricFigure8Klein as ParametricFigure8Klein
from .utilities import ParametricHenneberg as ParametricHenneberg
from .utilities import ParametricKlein as ParametricKlein
from .utilities import ParametricKuen as ParametricKuen
from .utilities import ParametricMobius as ParametricMobius
from .utilities import ParametricPluckerConoid as ParametricPluckerConoid
from .utilities import ParametricPseudosphere as ParametricPseudosphere
from .utilities import ParametricRandomHills as ParametricRandomHills
from .utilities import ParametricRoman as ParametricRoman
from .utilities import ParametricSuperEllipsoid as ParametricSuperEllipsoid
from .utilities import ParametricSuperToroid as ParametricSuperToroid
from .utilities import ParametricTorus as ParametricTorus
from .utilities import ParticleReader as ParticleReader
from .utilities import PDBReader as PDBReader
from .utilities import PExodusIIReader as PExodusIIReader
from .utilities import Plane as Plane
from .utilities import PlaneSource as PlaneSource
from .utilities import PlatonicSolid as PlatonicSolid
from .utilities import PlatonicSolidSource as PlatonicSolidSource
from .utilities import Plot3DFunctionEnum as Plot3DFunctionEnum
from .utilities import Plot3DMetaReader as Plot3DMetaReader
from .utilities import PLYReader as PLYReader
from .utilities import PLYWriter as PLYWriter
from .utilities import PNGReader as PNGReader
from .utilities import PNGWriter as PNGWriter
from .utilities import PNMReader as PNMReader
from .utilities import PNMWriter as PNMWriter
from .utilities import PointCellDataSelection as PointCellDataSelection
from .utilities import PolyDataWriter as PolyDataWriter
from .utilities import Polygon as Polygon
from .utilities import PolygonSource as PolygonSource
from .utilities import POpenFOAMReader as POpenFOAMReader
from .utilities import ProgressMonitor as ProgressMonitor
from .utilities import ProStarReader as ProStarReader
from .utilities import PTSReader as PTSReader
from .utilities import PVDDataSet as PVDDataSet
from .utilities import PVDReader as PVDReader
from .utilities import Pyramid as Pyramid
from .utilities import Quadrilateral as Quadrilateral
from .utilities import Rectangle as Rectangle
from .utilities import RectilinearGridWriter as RectilinearGridWriter
from .utilities import SegYReader as SegYReader
from .utilities import SeriesDataSet as SeriesDataSet
from .utilities import SeriesReader as SeriesReader
from .utilities import SimplePointsWriter as SimplePointsWriter
from .utilities import SLCReader as SLCReader
from .utilities import SolidSphere as SolidSphere
from .utilities import SolidSphereGeneric as SolidSphereGeneric
from .utilities import Sphere as Sphere
from .utilities import SphereSource as SphereSource
from .utilities import Spline as Spline
from .utilities import STLReader as STLReader
from .utilities import STLWriter as STLWriter
from .utilities import StructuredGridWriter as StructuredGridWriter
from .utilities import StructuredSphere as StructuredSphere
from .utilities import Superquadric as Superquadric
from .utilities import SuperquadricSource as SuperquadricSource
from .utilities import TecplotReader as TecplotReader
from .utilities import Tetrahedron as Tetrahedron
from .utilities import Text3D as Text3D
from .utilities import Text3DSource as Text3DSource
from .utilities import ThreeDSReader as ThreeDSReader
from .utilities import TIFFReader as TIFFReader
from .utilities import TIFFWriter as TIFFWriter
from .utilities import TimeReader as TimeReader
from .utilities import Transform as Transform
from .utilities import Triangle as Triangle
from .utilities import Tube as Tube
from .utilities import UnstructuredGridWriter as UnstructuredGridWriter
from .utilities import VRMLReader as VRMLReader
from .utilities import VTKDataSetReader as VTKDataSetReader
from .utilities import VtkErrorCatcher as VtkErrorCatcher
from .utilities import VTKPDataSetReader as VTKPDataSetReader
from .utilities import Wavelet as Wavelet
from .utilities import XdmfReader as XdmfReader
from .utilities import XMLImageDataReader as XMLImageDataReader
from .utilities import XMLImageDataWriter as XMLImageDataWriter
from .utilities import XMLMultiBlockDataReader as XMLMultiBlockDataReader
from .utilities import XMLMultiBlockDataWriter as XMLMultiBlockDataWriter
from .utilities import XMLPartitionedDataSetReader as XMLPartitionedDataSetReader
from .utilities import XMLPartitionedDataSetWriter as XMLPartitionedDataSetWriter
from .utilities import XMLPImageDataReader as XMLPImageDataReader
from .utilities import XMLPolyDataReader as XMLPolyDataReader
from .utilities import XMLPolyDataWriter as XMLPolyDataWriter
from .utilities import XMLPRectilinearGridReader as XMLPRectilinearGridReader
from .utilities import XMLPUnstructuredGridReader as XMLPUnstructuredGridReader
from .utilities import XMLRectilinearGridReader as XMLRectilinearGridReader
from .utilities import XMLRectilinearGridWriter as XMLRectilinearGridWriter
from .utilities import XMLStructuredGridReader as XMLStructuredGridReader
from .utilities import XMLStructuredGridWriter as XMLStructuredGridWriter
from .utilities import XMLUnstructuredGridReader as XMLUnstructuredGridReader
from .utilities import XMLUnstructuredGridWriter as XMLUnstructuredGridWriter
from .utilities import abstract_class as abstract_class
from .utilities import accessor_registry as accessor_registry
from .utilities import allow_new_attributes as allow_new_attributes
from .utilities import array_from_vtkmatrix as array_from_vtkmatrix
from .utilities import arrays as arrays
from .utilities import assert_empty_kwargs as assert_empty_kwargs
from .utilities import axis_rotation as axis_rotation
from .utilities import cartesian_to_spherical as cartesian_to_spherical
from .utilities import cell_array as cell_array
from .utilities import cell_quality as cell_quality
from .utilities import cell_quality_info as cell_quality_info
from .utilities import cells as cells
from .utilities import check_valid_vector as check_valid_vector
from .utilities import conditional_decorator as conditional_decorator
from .utilities import convert_array as convert_array
from .utilities import convert_string_array as convert_string_array
from .utilities import create_grid as create_grid
from .utilities import create_mixed_cells as create_mixed_cells
from .utilities import enable_smp_tools as enable_smp_tools
from .utilities import features as features
from .utilities import field_array as field_array
from .utilities import fileio as fileio
from .utilities import fit_line_to_points as fit_line_to_points
from .utilities import fit_plane_to_points as fit_plane_to_points
from .utilities import from_meshio as from_meshio
from .utilities import from_trimesh as from_trimesh
from .utilities import generate_plane as generate_plane
from .utilities import geometric_objects as geometric_objects
from .utilities import geometric_sources as geometric_sources
from .utilities import get_array as get_array
from .utilities import get_array_association as get_array_association
from .utilities import get_ext as get_ext
from .utilities import get_mixed_cells as get_mixed_cells
from .utilities import get_reader as get_reader
from .utilities import get_vtk_type as get_vtk_type
from .utilities import grid_from_sph_coords as grid_from_sph_coords
from .utilities import has_module as has_module
from .utilities import has_scheme as has_scheme
from .utilities import helpers as helpers
from .utilities import image_sources as image_sources
from .utilities import is_inside_bounds as is_inside_bounds
from .utilities import is_meshio_mesh as is_meshio_mesh
from .utilities import is_pyvista_dataset as is_pyvista_dataset
from .utilities import is_trimesh_mesh as is_trimesh_mesh
from .utilities import line_segments_from_points as line_segments_from_points
from .utilities import lines_from_points as lines_from_points
from .utilities import make_tri_mesh as make_tri_mesh
from .utilities import merge as merge
from .utilities import misc as misc
from .utilities import ncells_from_cells as ncells_from_cells
from .utilities import numpy_to_idarr as numpy_to_idarr
from .utilities import observers as observers
from .utilities import parametric_keywords as parametric_keywords
from .utilities import parametric_objects as parametric_objects
from .utilities import parse_field_choice as parse_field_choice
from .utilities import perlin_noise as perlin_noise
from .utilities import point_array as point_array
from .utilities import points as points
from .utilities import principal_axes as principal_axes
from .utilities import raise_has_duplicates as raise_has_duplicates
from .utilities import raise_not_matching as raise_not_matching
from .utilities import read as read
from .utilities import read_exodus as read_exodus
from .utilities import read_grdecl as read_grdecl
from .utilities import read_meshio as read_meshio
from .utilities import read_pickle as read_pickle
from .utilities import read_texture as read_texture
from .utilities import reader as reader
from .utilities import reader_registry as reader_registry
from .utilities import register_dataset_accessor as register_dataset_accessor
from .utilities import register_reader as register_reader
from .utilities import register_writer as register_writer
from .utilities import registered_accessors as registered_accessors
from .utilities import row_array as row_array
from .utilities import sample_function as sample_function
from .utilities import save_meshio as save_meshio
from .utilities import save_pickle as save_pickle
from .utilities import send_errors_to_logging as send_errors_to_logging
from .utilities import set_default_active_scalars as set_default_active_scalars
from .utilities import set_default_active_vectors as set_default_active_vectors
from .utilities import set_error_output_file as set_error_output_file
from .utilities import set_new_attribute as set_new_attribute
from .utilities import set_pickle_format as set_pickle_format
from .utilities import spherical_to_cartesian as spherical_to_cartesian
from .utilities import state_manager as state_manager
from .utilities import surface_from_para as surface_from_para
from .utilities import threaded as threaded
from .utilities import to_meshio as to_meshio
from .utilities import to_trimesh as to_trimesh
from .utilities import transform as transform
from .utilities import transform_vectors_sph_to_cart as transform_vectors_sph_to_cart
from .utilities import transformations as transformations
from .utilities import try_callback as try_callback
from .utilities import unregister_dataset_accessor as unregister_dataset_accessor
from .utilities import vector_poly_data as vector_poly_data
from .utilities import vtk_bit_array_to_char as vtk_bit_array_to_char
from .utilities import vtk_id_list_to_array as vtk_id_list_to_array
from .utilities import vtk_points as vtk_points
from .utilities import vtk_snake_case as vtk_snake_case
from .utilities import vtk_verbosity as vtk_verbosity
from .utilities import vtkmatrix_from_array as vtkmatrix_from_array
from .utilities import wrap as wrap
from .utilities import writer as writer
from .utilities import writer_registry as writer_registry
from .wrappers import _wrappers as _wrappers

if not TYPE_CHECKING:  # pragma: no branch

    def __getattr__(name: str) -> object:
        """Forward the type aliases that moved to ``pyvista.typing`` with a deprecation warning."""
        if name in _MOVED_TO_TYPING_NAMESPACE[__name__] or name in _DEPRECATED_ALIASES:
            return _get_deprecated_alias(__name__, name)
        msg = f'module {__name__!r} has no attribute {name!r}'
        raise AttributeError(msg)


# Send VTK messages to the logging module:
send_errors_to_logging()
