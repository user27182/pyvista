"""Close all plotters to help control memory usage for our doctests."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

import matplotlib as mpl
import pytest

# Stress-test diagnostics: set by .github/workflows/stress-xvfb.yml, written per xdist worker.
_DIAG_DIR = os.environ.get('PYVISTA_STRESS_DIAG_DIR')
if _DIAG_DIR:
    os.environ.setdefault('EGL_LOG_LEVEL', 'debug')
    os.environ.setdefault('LIBGL_DEBUG', 'verbose')

import pyvista as pv  # noqa: E402
from pyvista import _vtk  # noqa: E402

# Need to import all vtk modules eagerly to avoid issues with parallel lazy imports
_vtk.import_all()

collect_ignore = [  # Avoid importing deprecated modules
    'examples/download_3ds.py',
    'examples/gltf.py',
    'examples/vrml.py',
]

# Render windows created and closed during the current test, as "event:class[:flags]".
_WINDOWS: list[str] = []


def _diag(message: str) -> None:
    """Append a timestamped line to this worker's diagnostic log."""
    if not _DIAG_DIR:
        return
    worker = os.environ.get('PYTEST_XDIST_WORKER', 'main')
    path = Path(_DIAG_DIR) / f'{worker}.log'
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    stamp = time.strftime('%H:%M:%S', time.gmtime(now)) + f'.{int(now * 1000) % 1000:03d}'
    with path.open('a') as f:
        f.write(f'{stamp} pid={os.getpid()} {message}\n')


def _run(cmd: str) -> str:
    """Return a shell command's stdout, or the failure."""
    try:
        return subprocess.run(  # noqa: S602
            cmd, shell=True, capture_output=True, text=True, timeout=10, check=False
        ).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        return f'<{exc}>'


def _try_dlopen(name: str) -> str:
    """Report whether ``name`` can be dlopen'ed right now."""
    try:
        ctypes.CDLL(name)
    except OSError as exc:
        return f'FAIL({exc})'
    return 'ok'


def _try_xopen() -> str:
    """Report whether ``XOpenDisplay`` succeeds right now."""
    try:
        lib = ctypes.CDLL('libX11.so.6')
    except OSError as exc:
        return f'FAIL({exc})'
    lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    display = lib.XOpenDisplay(None)
    if not display:
        return 'FAIL(NULL)'
    lib.XCloseDisplay(display)
    return 'ok'


def _process_facts() -> str:
    """Summarize this process's resource state without touching X or GL."""
    status = {}
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            key, _, value = line.partition(':')
            if key in {'VmRSS', 'Threads', 'FDSize'}:
                status[key] = value.strip()
    except OSError:
        pass
    try:
        fds = len(list(Path('/proc/self/fd').iterdir()))
    except OSError:
        fds = -1
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    xauth = os.environ.get('XAUTHORITY', '')
    return (
        f'DISPLAY={os.environ.get("DISPLAY")} XAUTHORITY={xauth} '
        f'exists={Path(xauth).exists()} fds={fds} nofile={soft}/{hard} {status}'
    )


def _snapshot() -> str:
    """Probe X, EGL and GLX now, plus the server and machine state."""
    return ' | '.join(
        [
            _process_facts(),
            f'XOpenDisplay_now={_try_xopen()}',
            f'libEGL_now={_try_dlopen("libEGL.so.1")}',
            f'libGLX_now={_try_dlopen("libGLX.so.0")}',
            f'x11_sockets={_run("ss -xa 2>/dev/null | grep -c X11-unix")}',
            f'Xvfb=[{_run("ps -o pid=,etimes=,rss=,stat=,args= -C Xvfb")}]',
            f'mem=[{_run("free -m | sed -n 2p")}]',
        ]
    )


if _DIAG_DIR:
    _diag(
        f'conftest imported argv={sys.argv[1:4]} python={sys.version.split()[0]} '
        f'libEGL_in_ldcache={_run("ldconfig -p | grep -c libEGL.so.1")} {_process_facts()}'
    )

    _plotter_init = pv.Plotter.__init__

    def _tracking_init(self, *args, **kwargs):
        """Record the backend class of every render window pyvista creates."""
        _plotter_init(self, *args, **kwargs)
        _WINDOWS.append(f'new:{self.ren_win.GetClassName()}')

    pv.Plotter.__init__ = _tracking_init  # type: ignore[method-assign]

    _plotter_close = pv.plotting.plotter.BasePlotter.close

    def _tracking_close(self):
        """Record each window's class, Initialized and NeverRendered flags as it closes."""
        window = getattr(self, 'ren_win', None)
        if window is not None:
            _WINDOWS.append(
                f'close:{window.GetClassName()}'
                f':init{int(window.GetInitialized())}:never{int(window.GetNeverRendered())}'
            )
        _plotter_close(self)

    pv.plotting.plotter.BasePlotter.close = _tracking_close  # type: ignore[method-assign]


def _is_window_anomaly(record: str) -> bool:
    """Flag a non-X backend or a window that rendered without ever initializing."""
    return 'vtkXOpenGLRenderWindow' not in record or record.endswith(':init0:never0')


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Log the end-of-session state of this worker."""
    if _DIAG_DIR:
        _diag(f'session finish exitstatus={int(exitstatus)} {_snapshot()}')


@pytest.fixture(autouse=True)
def fail_on_vtk_output(request):
    """Fail the test when VTK logs an error or warning while it runs.

    Defined here rather than in ``tests`` so that it also applies to the doctests run
    from the installed package, which collect no ``conftest.py`` from the repository.
    """
    with pv.VtkErrorCatcher(send_to_logging=False) as catcher:
        yield
    if events := catcher.events:
        logged = '\n'.join(str(event) for event in events)
        snapshot = _snapshot() if _DIAG_DIR else ''
        _diag(f'VTK OUTPUT during {request.node.nodeid}: {logged!r}\n    {snapshot}')
        msg = f'VTK logged {len(events)} error(s) or warning(s):\n{logged}\n{snapshot}'
        pytest.fail(msg)


@pytest.fixture(autouse=True, scope='session')
def matplotlib_headless():
    """Use a non-interactive Matplotlib backend to avoid Tk issues on Windows CI."""
    if 'CI' in os.environ:
        mpl.use('Agg')


@pytest.fixture(autouse=True)
def autoclose_plotters(request):
    """Close all plotters."""
    yield
    pv.close_all()
    if _DIAG_DIR:
        anomaly = any(_is_window_anomaly(record) for record in _WINDOWS)
        prefix = 'ANOMALY ' if anomaly else ''
        _diag(f'{prefix}{request.node.nodeid} {" ".join(_WINDOWS) or "-"}')
        _WINDOWS.clear()


@pytest.fixture(autouse=True)
def reset_global_theme():
    """Reset ``global_theme``."""
    # this stops any doctest-module tests from overriding the global theme and
    # creating test side effects
    pv.set_plot_theme('document_build')
    yield
    pv.set_plot_theme('document_build')
