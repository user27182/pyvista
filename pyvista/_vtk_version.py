"""VTK version information."""

from __future__ import annotations

__lazy_modules__ = [
    'pyvista',
    'pyvista._warn_external',
    'typing',
]

from typing import NamedTuple

from pyvista import _vtk
from pyvista._warn_external import warn_external

_MIN_SUPPORTED_VTK_VERSION = (9, 3, 1)


class VersionInfo(NamedTuple):
    """Version information as a named tuple."""

    major: int
    minor: int
    micro: int

    def __str__(self) -> str:
        return str((self.major, self.minor, self.micro))

    @staticmethod
    def _format(version: tuple[int, ...]) -> str:
        return '.'.join(map(str, version))


def _get_vtk_version() -> VersionInfo:
    """Return the vtk version as a namedtuple.

    Returns
    -------
    VersionInfo
        Version information as a named tuple.

    """
    try:
        ver = _vtk.vtkVersion()
        major = ver.GetVTKMajorVersion()
        minor = ver.GetVTKMinorVersion()
        micro = ver.GetVTKBuildVersion()
    except AttributeError:  # pragma: no cover
        msg = (
            f'Unable to detect VTK version. '
            f'Defaulting to {VersionInfo._format(_MIN_SUPPORTED_VTK_VERSION)}'
        )
        warn_external(msg)
        major, minor, micro = _MIN_SUPPORTED_VTK_VERSION
    return VersionInfo(major, minor, micro)


class VTKVersionInfo(VersionInfo):
    """Version info which rejects comparisons against unsupported VTK versions."""

    def _check_min_supported(self, other: tuple[int, ...]) -> None:
        if isinstance(other, tuple) and other < _MIN_SUPPORTED_VTK_VERSION:  # type: ignore[redundant-expr]
            from pyvista.core.errors import VTKVersionError  # noqa: PLC0415

            msg = (
                f'Comparing against unsupported VTK version {VersionInfo._format(other):}. '
                f'Minimum supported is {VersionInfo._format(_MIN_SUPPORTED_VTK_VERSION):}.'
            )
            raise VTKVersionError(msg)

    def __lt__(self, other: tuple[int, ...]) -> bool:
        self._check_min_supported(other)
        return super().__lt__(other)

    def __le__(self, other: tuple[int, ...]) -> bool:
        self._check_min_supported(other)
        return super().__le__(other)

    def __gt__(self, other: tuple[int, ...]) -> bool:
        self._check_min_supported(other)
        return super().__gt__(other)

    def __ge__(self, other: tuple[int, ...]) -> bool:
        self._check_min_supported(other)
        return super().__ge__(other)


vtk_version_info = VTKVersionInfo(*_get_vtk_version())
