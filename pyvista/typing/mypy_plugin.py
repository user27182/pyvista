"""PyVista plugin for static type-checking with mypy."""

from __future__ import annotations

__lazy_modules__ = [
    'typing',
]

__all__: list[str] = ['promote_type']

from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from typing import Any

    from mypy.plugin import Plugin


_T = TypeVar('_T', bound=type)


def promote_type(*types: type[Any]) -> Callable[[_T], _T]:  # noqa: ARG001
    """Duck-type type-promotion decorator used by the mypy plugin.

    Apply this decorator to a class to promote its type statically.
    This tells ``mypy`` to treat the decorated class as though it's
    equivalent to another class.

    .. note::
        This decorator does nothing at runtime and merely passes the object through.

    Parameters
    ----------
    *types : type
        Types to promote the class to. The types are only used statically by mypy.

    Returns
    -------
    Callable
        Decorated class.

    """
    return lambda obj: obj


def plugin(version: str) -> type[Plugin]:  # noqa: ARG001  # numpydoc ignore=PR01,RT01
    """Entry-point for mypy."""
    from pyvista.typing._mypy_plugin import _PyVistaPlugin  # noqa: PLC0415

    return _PyVistaPlugin
