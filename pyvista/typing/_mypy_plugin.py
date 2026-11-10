"""Mypy plugin implementation, loaded only by mypy."""

from __future__ import annotations

__lazy_modules__ = [
    'mypy.nodes',
    'mypy.plugin',
    'pyvista.typing.mypy_plugin',
    'typing',
]

from typing import TYPE_CHECKING
from typing import Any

from mypy.nodes import CallExpr
from mypy.nodes import NameExpr
from mypy.nodes import RefExpr
from mypy.plugin import Plugin

from pyvista.typing.mypy_plugin import promote_type

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Self

    from mypy.plugin import ClassDefContext
    from mypy.types import Instance


def _promote_type_callback(ctx: ClassDefContext) -> None:
    """Apply the ``promote_type`` decorator.

    The decorated class is captured and promoted to the types provided
    by the decorator's arguments.
    """
    for decorator in ctx.cls.decorators:
        if isinstance(decorator, CallExpr):
            callee = decorator.callee
            if isinstance(callee, NameExpr):
                name = callee.name
                if name == promote_type.__name__:
                    decorated_type: Instance = ctx.api.named_type(ctx.cls.fullname)
                    args = decorator.args
                    for arg in args:
                        if isinstance(arg, RefExpr):
                            named_type: Instance = ctx.api.named_type(arg.fullname)
                            decorated_type.type._promote.append(named_type)


class _PyVistaPlugin(Plugin):
    """Mypy plugin to enable static type promotions."""

    def get_class_decorator_hook(  # numpydoc ignore=PR01,RT01
        self: Self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        """Return the callback for the ``promote_type`` decorator."""

        def _get_type_fullname(typ: Any) -> str:
            return f'{typ.__module__}.{typ.__qualname__}'

        if fullname == _get_type_fullname(promote_type):
            return _promote_type_callback
        return None
