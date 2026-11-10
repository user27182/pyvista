"""Deprecated shim—use :mod:`trame_pyvista.ui.base_viewer` instead."""

from __future__ import annotations

__lazy_modules__ = [
    'pyvista._warn_external',
    'pyvista.core.errors',
    'trame_pyvista.ui.base_viewer',
]

from trame_pyvista.ui.base_viewer import BaseViewer

from pyvista._warn_external import warn_external
from pyvista.core.errors import PyVistaDeprecationWarning

warn_external(
    'pyvista.trame.ui.base_viewer is deprecated; '
    'import from trame_pyvista.ui.base_viewer instead.',
    PyVistaDeprecationWarning,
)

__all__ = ['BaseViewer']
