"""Examples module."""

from __future__ import annotations

__lazy_modules__ = [
    'importlib',
    'pyvista.examples',
    'pyvista.examples._get_example',
    'pyvista.examples.cells',
    'pyvista.examples.downloads',
    'pyvista.examples.examples',
    'typing',
]

import importlib
from typing import TYPE_CHECKING

from . import planets as planets
from ._get_example import Example as Example
from ._get_example import get_example as get_example
from .cells import generate_cell_blocks as generate_cell_blocks
from .cells import plot_cell as plot_cell
from .downloads import CACHE_VERSION as CACHE_VERSION
from .downloads import FETCHER as FETCHER
from .downloads import POOCH_LOGGER as POOCH_LOGGER
from .downloads import SOURCE as SOURCE
from .downloads import USER_DATA_PATH as USER_DATA_PATH
from .downloads import delete_downloads as delete_downloads
from .downloads import download_3gqp as download_3gqp
from .downloads import download_action_figure as download_action_figure
from .downloads import download_aero_bracket as download_aero_bracket
from .downloads import download_angular_sector as download_angular_sector
from .downloads import download_antarctica_velocity as download_antarctica_velocity
from .downloads import download_armadillo as download_armadillo
from .downloads import download_avocado as download_avocado
from .downloads import download_backward_facing_step as download_backward_facing_step
from .downloads import download_beach as download_beach
from .downloads import download_biplane as download_biplane
from .downloads import download_bird as download_bird
from .downloads import download_bird_bath as download_bird_bath
from .downloads import download_bird_texture as download_bird_texture
from .downloads import download_black_vase as download_black_vase
from .downloads import download_blood_vessels as download_blood_vessels
from .downloads import download_blow as download_blow
from .downloads import download_bolt_nut as download_bolt_nut
from .downloads import download_brain as download_brain
from .downloads import download_brain_atlas_with_sides as download_brain_atlas_with_sides
from .downloads import download_bunny as download_bunny
from .downloads import download_bunny_coarse as download_bunny_coarse
from .downloads import download_cad_model as download_cad_model
from .downloads import download_cad_model_case as download_cad_model_case
from .downloads import download_caffeine as download_caffeine
from .downloads import download_cake_easy as download_cake_easy
from .downloads import download_cake_easy_texture as download_cake_easy_texture
from .downloads import download_can_crushed_hdf as download_can_crushed_hdf
from .downloads import download_can_crushed_vtu as download_can_crushed_vtu
from .downloads import download_carburetor as download_carburetor
from .downloads import download_carotid as download_carotid
from .downloads import download_cavity as download_cavity
from .downloads import download_cells_nd as download_cells_nd
from .downloads import download_cgns_multi as download_cgns_multi
from .downloads import download_cgns_structured as download_cgns_structured
from .downloads import download_chest as download_chest
from .downloads import download_cloud_dark_matter as download_cloud_dark_matter
from .downloads import download_cloud_dark_matter_dense as download_cloud_dark_matter_dense
from .downloads import download_clown as download_clown
from .downloads import download_coastlines as download_coastlines
from .downloads import download_coil_magnetic_field as download_coil_magnetic_field
from .downloads import download_cow as download_cow
from .downloads import download_cow_head as download_cow_head
from .downloads import download_crater_imagery as download_crater_imagery
from .downloads import download_crater_topo as download_crater_topo
from .downloads import download_cubemap_park as download_cubemap_park
from .downloads import download_cubemap_space_4k as download_cubemap_space_4k
from .downloads import download_cubemap_space_16k as download_cubemap_space_16k
from .downloads import download_cylinder_crossflow as download_cylinder_crossflow
from .downloads import download_damaged_helmet as download_damaged_helmet
from .downloads import download_damavand_volcano as download_damavand_volcano
from .downloads import download_delaunay_example as download_delaunay_example
from .downloads import download_dicom_stack as download_dicom_stack
from .downloads import download_dikhololo_night as download_dikhololo_night
from .downloads import download_disc_quads as download_disc_quads
from .downloads import download_dolfin as download_dolfin
from .downloads import download_doorman as download_doorman
from .downloads import download_dragon as download_dragon
from .downloads import download_drill as download_drill
from .downloads import download_dual_sphere_animation as download_dual_sphere_animation
from .downloads import download_e07733s002i009 as download_e07733s002i009
from .downloads import download_electronics_cooling as download_electronics_cooling
from .downloads import download_embryo as download_embryo
from .downloads import download_emoji as download_emoji
from .downloads import download_emoji_texture as download_emoji_texture
from .downloads import download_exodus as download_exodus
from .downloads import download_face as download_face
from .downloads import download_face2 as download_face2
from .downloads import download_faults as download_faults
from .downloads import download_fea_bracket as download_fea_bracket
from .downloads import (
    download_fea_hertzian_contact_cylinder as download_fea_hertzian_contact_cylinder,
)
from .downloads import download_file as download_file
from .downloads import download_filled_contours as download_filled_contours
from .downloads import download_flamingo as download_flamingo
from .downloads import download_foot_bones as download_foot_bones
from .downloads import download_frd as download_frd
from .downloads import download_frog as download_frog
from .downloads import download_full_head as download_full_head
from .downloads import download_gearbox as download_gearbox
from .downloads import download_gears as download_gears
from .downloads import download_gif_simple as download_gif_simple
from .downloads import download_gourds as download_gourds
from .downloads import download_gourds_pnm as download_gourds_pnm
from .downloads import download_gourds_texture as download_gourds_texture
from .downloads import download_gpr_data_array as download_gpr_data_array
from .downloads import download_gpr_path as download_gpr_path
from .downloads import download_grasshopper as download_grasshopper
from .downloads import download_great_white_shark as download_great_white_shark
from .downloads import download_grey_nurse_shark as download_grey_nurse_shark
from .downloads import download_guitar as download_guitar
from .downloads import download_head as download_head
from .downloads import download_head_2 as download_head_2
from .downloads import download_headsq as download_headsq
from .downloads import download_honolulu as download_honolulu
from .downloads import download_horse as download_horse
from .downloads import download_horse_points as download_horse_points
from .downloads import download_human as download_human
from .downloads import download_iron_protein as download_iron_protein
from .downloads import download_ivan_angel as download_ivan_angel
from .downloads import download_kitchen as download_kitchen
from .downloads import download_knee as download_knee
from .downloads import download_knee_full as download_knee_full
from .downloads import download_letter_a as download_letter_a
from .downloads import download_letter_k as download_letter_k
from .downloads import download_lidar as download_lidar
from .downloads import download_lincoln_life_mask as download_lincoln_life_mask
from .downloads import download_lobster as download_lobster
from .downloads import download_louis_louvre as download_louis_louvre
from .downloads import download_lshape as download_lshape
from .downloads import download_lucy as download_lucy
from .downloads import download_m4_total_density as download_m4_total_density
from .downloads import download_masonry_texture as download_masonry_texture
from .downloads import download_meshio_xdmf as download_meshio_xdmf
from .downloads import download_milk_truck as download_milk_truck
from .downloads import download_model_with_variance as download_model_with_variance
from .downloads import download_moonlanding_image as download_moonlanding_image
from .downloads import download_motor as download_motor
from .downloads import download_mount_damavand as download_mount_damavand
from .downloads import download_mug as download_mug
from .downloads import download_naca as download_naca
from .downloads import download_nefertiti as download_nefertiti
from .downloads import download_nek5000 as download_nek5000
from .downloads import download_notch_displacement as download_notch_displacement
from .downloads import download_notch_stress as download_notch_stress
from .downloads import download_oblique_cone as download_oblique_cone
from .downloads import download_office as download_office
from .downloads import download_openfoam_tubes as download_openfoam_tubes
from .downloads import download_owl as download_owl
from .downloads import download_parallel_exodus as download_parallel_exodus
from .downloads import download_parched_canal_4k as download_parched_canal_4k
from .downloads import download_particles as download_particles
from .downloads import download_particles_lethe as download_particles_lethe
from .downloads import download_pepper as download_pepper
from .downloads import download_pine_roots as download_pine_roots
from .downloads import download_plastic_vase as download_plastic_vase
from .downloads import download_poly_line as download_poly_line
from .downloads import download_prism as download_prism
from .downloads import download_procedural_cow as download_procedural_cow
from .downloads import download_prostar as download_prostar
from .downloads import download_prostate as download_prostate
from .downloads import download_pump_bracket as download_pump_bracket
from .downloads import download_puppy as download_puppy
from .downloads import download_puppy_texture as download_puppy_texture
from .downloads import download_quadratic_pyramid as download_quadratic_pyramid
from .downloads import download_rectilinear_grid as download_rectilinear_grid
from .downloads import download_reservoir as download_reservoir
from .downloads import download_rgba_texture as download_rgba_texture
from .downloads import download_room_cff as download_room_cff
from .downloads import download_room_surface_mesh as download_room_surface_mesh
from .downloads import download_saddle_surface as download_saddle_surface
from .downloads import download_sea_vase as download_sea_vase
from .downloads import download_sextant as download_sextant
from .downloads import download_shark as download_shark
from .downloads import download_single_sphere_animation as download_single_sphere_animation
from .downloads import download_sky_box_cube_map as download_sky_box_cube_map
from .downloads import download_sky_box_nz as download_sky_box_nz
from .downloads import download_sky_box_nz_texture as download_sky_box_nz_texture
from .downloads import download_sparse_points as download_sparse_points
from .downloads import download_spider as download_spider
from .downloads import download_st_helens as download_st_helens
from .downloads import download_stars_cloud_hyg as download_stars_cloud_hyg
from .downloads import download_structured_grid as download_structured_grid
from .downloads import download_structured_grid_two as download_structured_grid_two
from .downloads import download_t3_grid_0 as download_t3_grid_0
from .downloads import download_teapot as download_teapot
from .downloads import download_teapot_vrml as download_teapot_vrml
from .downloads import download_tecplot_ascii as download_tecplot_ascii
from .downloads import download_tensors as download_tensors
from .downloads import download_tetra_dc_mesh as download_tetra_dc_mesh
from .downloads import download_tetrahedron as download_tetrahedron
from .downloads import download_thermal_probes as download_thermal_probes
from .downloads import download_topo_global as download_topo_global
from .downloads import download_topo_land as download_topo_land
from .downloads import download_torso as download_torso
from .downloads import download_tri_quadratic_hexahedron as download_tri_quadratic_hexahedron
from .downloads import download_trumpet as download_trumpet
from .downloads import download_turbine_blade as download_turbine_blade
from .downloads import download_unstructured_grid as download_unstructured_grid
from .downloads import download_urn as download_urn
from .downloads import download_usa as download_usa
from .downloads import download_usa_texture as download_usa_texture
from .downloads import (
    download_victorian_goblet_face_illusion as download_victorian_goblet_face_illusion,
)
from .downloads import download_vtk as download_vtk
from .downloads import download_vtk_logo as download_vtk_logo
from .downloads import download_warping_spheres as download_warping_spheres
from .downloads import download_washington_bust as download_washington_bust
from .downloads import download_wavy as download_wavy
from .downloads import download_whole_body_ct_female as download_whole_body_ct_female
from .downloads import download_whole_body_ct_male as download_whole_body_ct_male
from .downloads import download_woman as download_woman
from .downloads import download_yinyang as download_yinyang
from .downloads import file_from_files as file_from_files
from .examples import antfile as antfile
from .examples import channelsfile as channelsfile
from .examples import dir_path as dir_path
from .examples import frogtissuesfile as frogtissuesfile
from .examples import globefile as globefile
from .examples import hexbeamfile as hexbeamfile
from .examples import load_airplane as load_airplane
from .examples import load_ant as load_ant
from .examples import load_channels as load_channels
from .examples import load_explicit_structured as load_explicit_structured
from .examples import load_frog_tissues as load_frog_tissues
from .examples import load_globe as load_globe
from .examples import load_globe_texture as load_globe_texture
from .examples import load_hexbeam as load_hexbeam
from .examples import load_hydrogen_orbital as load_hydrogen_orbital
from .examples import load_logo as load_logo
from .examples import load_nut as load_nut
from .examples import load_random_hills as load_random_hills
from .examples import load_rectilinear as load_rectilinear
from .examples import load_sphere as load_sphere
from .examples import load_sphere_vectors as load_sphere_vectors
from .examples import load_spline as load_spline
from .examples import load_structured as load_structured
from .examples import load_tetbeam as load_tetbeam
from .examples import load_uniform as load_uniform
from .examples import logofile as logofile
from .examples import mapfile as mapfile
from .examples import nutfile as nutfile
from .examples import planefile as planefile
from .examples import rectfile as rectfile
from .examples import spherefile as spherefile
from .examples import uniformfile as uniformfile

if TYPE_CHECKING:
    from typing import Any

_DEPRECATED_SUBMODULES = {'vrml', 'download_3ds', 'gltf'}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED_SUBMODULES:  # pragma: no cover
        module = importlib.import_module(f'.{name}', __name__)
        globals()[name] = module  # cache on the package so this only runs once
        return module
    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)
