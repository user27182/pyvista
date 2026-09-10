"""Reproduce the Xvfb reset race outside of pytest; see the mode help strings."""

# ruff: noqa: ANN001, ANN201, ANN202, E501, INP001, PLC0415, PLR0917, T201, TID251
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import multiprocessing as mp
import os
import random
import sys
import time

EXPECTED_CLASS = 'vtkXOpenGLRenderWindow'

MODE_HELP = {
    'x11': 'each of --procs processes opens and closes the display --iters times as fast as it can',
    'vtk': 'each of --rounds rounds starts --procs fresh interpreters that build one render window after a random delay',
    'vtk-self': 'one interpreter creates and destroys --iters render windows back to back, --repeats times over',
}


def _open_x11():
    """Return ``libX11`` with ``XOpenDisplay``/``XCloseDisplay`` typed."""
    lib = ctypes.CDLL(ctypes.util.find_library('X11') or 'libX11.so.6')
    lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    return lib


def _x11_worker(idx, iters, queue):
    """Open and close the display ``iters`` times; report the iterations that failed."""
    lib = _open_x11()
    failed = []
    for i in range(iters):
        display = lib.XOpenDisplay(None)
        if not display:
            failed.append(i)
            continue
        lib.XCloseDisplay(display)
    queue.put((idx, failed))


def _vtk_window_once():
    """Create, render and destroy one off-screen window; return (class, initialized, never rendered, output)."""
    from vtkmodules.vtkCommonCore import vtkOutputWindow
    from vtkmodules.vtkCommonCore import vtkStringOutputWindow
    from vtkmodules.vtkRenderingCore import vtkRenderer
    from vtkmodules.vtkRenderingCore import vtkRenderWindow
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

    output = vtkStringOutputWindow()
    previous = vtkOutputWindow.GetInstance()
    vtkOutputWindow.SetInstance(output)
    try:
        window = vtkRenderWindow()
        window.SetOffScreenRendering(True)
        window.SetSize(300, 300)
        renderer = vtkRenderer()
        window.AddRenderer(renderer)
        window.Render()
        result = (
            window.GetClassName(),
            int(window.GetInitialized()),
            int(window.GetNeverRendered()),
        )
        window.Finalize()
        del renderer
        del window
    finally:
        vtkOutputWindow.SetInstance(previous)
    return (*result, output.GetOutput().strip())


def _is_anomaly(cls, initialized, never_rendered, output):
    """Return whether the window is anything but a clean, initialized X window."""
    return bool(output) or cls != EXPECTED_CLASS or (not never_rendered and not initialized)


def _vtk_worker(idx, barrier, delay, queue):
    """Import VTK, line up with the other processes, wait ``delay`` seconds, then build one window."""
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

    barrier.wait()
    time.sleep(delay)
    started = time.monotonic()
    cls, initialized, never_rendered, output = _vtk_window_once()
    queue.put((idx, delay, time.monotonic() - started, cls, initialized, never_rendered, output))


def _vtk_self_worker(idx, iters, queue):
    """Create and destroy windows back to back until one comes out wrong."""
    for i in range(iters):
        cls, initialized, never_rendered, output = _vtk_window_once()
        if _is_anomaly(cls, initialized, never_rendered, output):
            queue.put((idx, i, cls, initialized, never_rendered, output))
            return
    queue.put((idx, None, cls, initialized, never_rendered, output))


def run_x11(args):
    """Race plain X clients against each other."""
    ctx = mp.get_context('spawn')
    queue = ctx.Queue()
    procs = [
        ctx.Process(target=_x11_worker, args=(i, args.iters, queue)) for i in range(args.procs)
    ]
    started = time.monotonic()
    for proc in procs:
        proc.start()
    results = [queue.get() for _ in procs]
    for proc in procs:
        proc.join()
    failures = 0
    for idx, failed in sorted(results):
        failures += len(failed)
        print(
            f'proc {idx}: {len(failed)}/{args.iters} XOpenDisplay failures at iterations {failed[:20]}'
        )
    print(f'elapsed {time.monotonic() - started:.1f}s')
    return failures


def run_vtk(args):
    """Race fresh VTK processes' first render windows against each other."""
    ctx = mp.get_context('spawn')
    rng = random.Random(args.seed)
    failures = 0
    for round_no in range(args.rounds):
        queue = ctx.Queue()
        barrier = ctx.Barrier(args.procs)
        delays = [rng.uniform(0, args.jitter) for _ in range(args.procs)]
        procs = [
            ctx.Process(target=_vtk_worker, args=(i, barrier, delays[i], queue))
            for i in range(args.procs)
        ]
        for proc in procs:
            proc.start()
        results = [queue.get() for _ in procs]
        for proc in procs:
            proc.join()
        bad = [r for r in results if _is_anomaly(*r[3:])]
        failures += len(bad)
        summary = ' '.join(f'{r[3]}:{r[4]}{r[5]}' for r in sorted(results))
        print(f'round {round_no}: {len(bad)} anomalies  [{summary}]')
        for idx, delay, took, cls, initialized, never_rendered, output in sorted(bad):
            print(
                f'  proc {idx}: delay={delay * 1000:.0f}ms took={took * 1000:.0f}ms '
                f'class={cls} initialized={initialized} never_rendered={never_rendered}'
            )
            for line in output.splitlines():
                print(f'    {line}')
    return failures


def run_vtk_self(args):
    """Race one process's new window against its own previous window's disconnect."""
    ctx = mp.get_context('spawn')
    failures = 0
    for repeat in range(args.repeats):
        queue = ctx.Queue()
        proc = ctx.Process(target=_vtk_self_worker, args=(repeat, args.iters, queue))
        proc.start()
        idx, iteration, cls, initialized, never_rendered, output = queue.get()
        proc.join()
        if iteration is None:
            print(f'repeat {idx}: {args.iters} windows, no anomaly')
            continue
        failures += 1
        print(
            f'repeat {idx}: anomaly at window {iteration}: class={cls} '
            f'initialized={initialized} never_rendered={never_rendered}'
        )
        for line in output.splitlines():
            print(f'    {line}')
    return failures


def main(argv=None):
    """Run one probe mode and print a ``FAILURES`` line."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    x11 = sub.add_parser('x11', help=MODE_HELP['x11'])
    x11.add_argument('--procs', type=int, default=4)
    x11.add_argument('--iters', type=int, default=300)
    vtk = sub.add_parser('vtk', help=MODE_HELP['vtk'])
    vtk.add_argument('--procs', type=int, default=4)
    vtk.add_argument('--rounds', type=int, default=40)
    vtk.add_argument('--jitter', type=float, default=0.3, help='max start delay in seconds')
    vtk.add_argument('--seed', type=int, default=0)
    vtk_self = sub.add_parser('vtk-self', help=MODE_HELP['vtk-self'])
    vtk_self.add_argument('--repeats', type=int, default=5)
    vtk_self.add_argument('--iters', type=int, default=100)
    args = parser.parse_args(argv)

    print(
        f'DISPLAY={os.environ.get("DISPLAY")} XAUTHORITY={os.environ.get("XAUTHORITY")} '
        f'python={sys.version.split()[0]}'
    )
    runner = {'x11': run_x11, 'vtk': run_vtk, 'vtk-self': run_vtk_self}[args.mode]
    failures = runner(args)
    variant = os.environ.get('XVFB_VARIANT', 'default')
    print(f'FAILURES: {failures} (mode={args.mode}, variant={variant})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
