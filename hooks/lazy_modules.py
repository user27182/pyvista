"""Regenerate each module's ``__lazy_modules__`` (PEP 810) from its top-level imports."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


def _module_name(path: Path) -> str:
    """Return the dotted module name of ``path``, relative to the working directory."""
    parts = list(path.with_suffix('').parts)
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def _resolve(node: ast.ImportFrom, module: str, *, is_package: bool) -> str:
    """Return the absolute module a ``from`` import names."""
    if node.level == 0:
        return node.module or ''
    base = module.split('.') if is_package else module.split('.')[:-1]
    base = base[: len(base) - (node.level - 1)]
    return '.'.join([*base, node.module] if node.module else base)


def _module_level(body: list[ast.stmt]) -> list[ast.stmt]:
    """Return the statements of ``body``, descending into runtime ``if`` blocks."""
    statements: list[ast.stmt] = []
    for node in body:
        if isinstance(node, ast.If) and ast.unparse(node.test).endswith('TYPE_CHECKING'):
            statements += _module_level(node.orelse)
        elif isinstance(node, ast.If):
            statements += _module_level(node.body) + _module_level(node.orelse)
        else:
            statements.append(node)
    return statements


def _is_lazy_modules(node: ast.stmt) -> bool:
    """Return whether ``node`` assigns ``__lazy_modules__``."""
    return isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == '__lazy_modules__' for target in node.targets
    )


def lazy_modules(source: str, path: Path) -> list[str]:
    """Return the sorted modules that ``source`` can import lazily."""
    tree = ast.parse(source)
    is_package = path.name == '__init__.py'
    module = _module_name(path)
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    exported: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == '__all__' for t in targets):
                exported = set(ast.literal_eval(node.value))
    keep = used | exported

    lines = source.splitlines()
    modules: set[str] = set()
    eager: set[str] = set()
    for node in _module_level(tree.body):
        if '# eager' in lines[node.lineno - 1]:
            if isinstance(node, ast.Import):
                eager.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                eager.add(_resolve(node, module, is_package=is_package))
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split('.')[0]
                if is_package or alias.asname == alias.name or bound in keep:
                    modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == '__future__' or any(a.name == '*' for a in node.names):
                continue
            source_module = _resolve(node, module, is_package=is_package)
            # Loading a same-named submodule later would rebind the name to the module.
            if is_package and any(
                source_module == f'{module}.{alias.asname or alias.name}' for alias in node.names
            ):
                eager.add(source_module)
                continue
            if (
                is_package
                or any(alias.asname == alias.name for alias in node.names)
                or any((alias.asname or alias.name) in keep for alias in node.names)
            ):
                modules.add(source_module)
    return sorted(modules - eager)


def rewrite(source: str, path: Path) -> str:
    """Return ``source`` with its ``__lazy_modules__`` assignment regenerated."""
    lines = source.splitlines(keepends=True)
    for node in reversed(ast.parse(source).body):
        if _is_lazy_modules(node):
            end = node.end_lineno or node.lineno
            while end < len(lines) and not lines[end].strip():
                end += 1
            del lines[node.lineno - 1 : end]
    source = ''.join(lines)

    modules = lazy_modules(source, path)
    if not modules:
        return source
    insert = 0
    tree = ast.parse(source)
    for index, node in enumerate(tree.body):
        is_docstring = (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        if is_docstring or (isinstance(node, ast.ImportFrom) and node.module == '__future__'):
            insert = node.end_lineno or node.lineno
        else:
            break
    block = '__lazy_modules__ = [\n' + ''.join(f'    {m!r},\n' for m in modules) + ']\n\n'
    lines = source.splitlines(keepends=True)
    if insert and lines[insert - 1].strip() and insert < len(lines) and lines[insert].strip():
        block = '\n' + block
    elif insert and insert < len(lines) and not lines[insert].strip():
        insert += 1
    lines[insert:insert] = [block]
    return ''.join(lines)


def main(argv: list[str]) -> int:
    """Rewrite each file in ``argv`` and return 1 if any changed."""
    changed = 0
    for name in argv:
        path = Path(name)
        source = path.read_text(encoding='utf-8')
        new = rewrite(source, path)
        if new != source:
            path.write_text(new, encoding='utf-8')
            sys.stdout.write(f'Updated __lazy_modules__ in {path}\n')
            changed = 1
    return changed


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
