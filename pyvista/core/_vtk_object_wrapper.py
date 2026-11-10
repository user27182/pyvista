"""Python wrapper base class for VTK objects with the VTK snake case API disabled."""

from __future__ import annotations

__lazy_modules__ = [
    'pyvista',
    'pyvista.core._vtk_utilities',
    'typing',
]

from typing import Any

from pyvista import _vtk
from pyvista.core._vtk_utilities import DisableVtkSnakeCase


class VTKObjectWrapperCheckSnakeCase(_vtk.VTKObjectWrapper):
    """Superclass for classes that wrap VTK objects with Python objects.

    This class overrides ``__getattr__`` to disable the VTK snake case API.
    """

    def __getattr__(self, name: str) -> Any:
        """Forward unknown attribute requests to the wrapped VTK object."""
        if self.VTKObject is not None:
            # Check if forwarding snake_case attributes
            DisableVtkSnakeCase.check_attribute(self.VTKObject, name)
            return getattr(self.VTKObject, name)
        msg = f'{type(self).__name__!r} object has no attribute {name!r}'
        raise AttributeError(msg)
