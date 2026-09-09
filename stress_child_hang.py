"""Spawn the PyVista CLI child many times and report any that hang."""

from __future__ import annotations

import faulthandler
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

import psutil

import pyvista as pv

ITERS = int(os.environ.get('STRESS_ITERS', '300'))
WORKERS = int(os.environ.get('STRESS_WORKERS', '3'))
TIMEOUT = float(os.environ.get('STRESS_TIMEOUT', '75'))
BUDGET = float(os.environ.get('STRESS_BUDGET_MIN', '40')) * 60
MODES = tuple(os.environ.get('STRESS_MODES', 'wrapper,module,closeall').split(','))
RESULTS = Path('stress_results')
ANT = Path(pv.examples.antfile).as_posix()
SCRIPT = shutil.which('pyvista')
CDB = next(
    (
        c
        for c in (
            shutil.which('cdb'),
            r'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe',
        )
        if c and Path(c).exists()
    ),
    None,
)
TOKENS = [
    '--color=red',
    '--color=red --opacity=0.1',
    '--color=blue --culling=front',
    '--background=blue --color red',
]
WRAPPER = """
import atexit, faulthandler, sys
faulthandler.dump_traceback_later(60, exit=False, file=sys.stderr)
atexit.register(lambda: print('MARK atexit', flush=True))
print('MARK start', flush=True)
from pyvista.__main__ import main
print('MARK imported', flush=True)
main(sys.argv[1:])
print('MARK main returned', flush=True)
"""
CLOSEALL = WRAPPER + """
import gc
import pyvista as pv
pv.close_all()
gc.collect()
print('MARK closed', flush=True)
"""


def command(i: int, out: str) -> tuple[str, list[str]]:
    """Build the child command for iteration ``i``."""
    args = f'plot {ANT} --off-screen --screenshot={out} {TOKENS[i % len(TOKENS)]}'.split()
    mode = MODES[(i // len(TOKENS)) % len(MODES)]
    if mode == 'wrapper':
        return mode, [sys.executable, '-c', WRAPPER, *args]
    if mode == 'closeall':
        return mode, [sys.executable, '-c', CLOSEALL, *args]
    if mode == 'module':
        return mode, [sys.executable, '-m', 'pyvista', *args]
    return mode, [SCRIPT or 'pyvista', *args]


def run_tool(cmd: list[str], timeout: float = 120) -> str:
    """Run a diagnostic command and return its combined output."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception as exc:  # noqa: BLE001
        return f'$ {" ".join(cmd)}\n{exc!r}'
    return f'$ {" ".join(cmd)} -> rc {r.returncode}\n{r.stdout}\n{r.stderr}'


def diagnose(pid: int) -> str:
    """Describe the process tree and dump native stacks where possible."""
    chunks = []
    try:
        tree = [psutil.Process(pid), *psutil.Process(pid).children(recursive=True)]
    except psutil.Error as exc:
        return f'psutil: {exc!r}'
    for proc in tree:
        try:
            desc = f'pid {proc.pid} {proc.name()} threads={proc.num_threads()} status={proc.status()}'
        except psutil.Error as exc:
            desc = f'pid {proc.pid} {exc!r}'
        chunks.append(desc)
        if 'python' not in desc.lower():
            continue
        if CDB:
            chunks.append(run_tool([CDB, '-pv', '-p', str(proc.pid), '-c', '~*kv; lm; q'], 240))
        chunks.append(run_tool(['py-spy', 'dump', '--pid', str(proc.pid), '--native']))
    return '\n\n'.join(chunks)


def run_one(i: int, tmp: Path) -> dict:
    """Run one child and describe what happened."""
    out = (tmp / f'out_{i}.png').as_posix()
    mode, cmd = command(i, out)
    so_path, se_path = tmp / f'stdout_{i}.txt', tmp / f'stderr_{i}.txt'
    t0 = time.monotonic()
    with so_path.open('w') as so_f, se_path.open('w') as se_f:
        p = subprocess.Popen(cmd, stdout=so_f, stderr=se_f)
        try:
            p.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f'!!! iteration {i} ({mode}) pid {p.pid}: hang detected, dumping', flush=True)
            dump = diagnose(p.pid)
            print(f'!!! iteration {i}: dump done, killing tree', flush=True)
            kill_note = run_tool(['taskkill', '/F', '/T', '/PID', str(p.pid)], 60)
            print(f'!!! iteration {i}: handled', flush=True)
            return {
                'i': i,
                'mode': mode,
                'hang': True,
                'seconds': round(time.monotonic() - t0, 1),
                'screenshot_written': Path(out).exists(),
                'cmd': cmd,
                'stdout': so_path.read_text(errors='replace'),
                'stderr': se_path.read_text(errors='replace'),
                'diagnose': dump,
                'kill': kill_note,
            }
    return {
        'i': i,
        'mode': mode,
        'hang': False,
        'rc': p.returncode,
        'seconds': round(time.monotonic() - t0, 1),
        'screenshot_written': Path(out).exists(),
        'stdout': so_path.read_text(errors='replace') if p.returncode else '',
        'stderr': se_path.read_text(errors='replace') if p.returncode else '',
    }


def main() -> int:
    """Run the stress loop on ``WORKERS`` threads and summarize."""
    RESULTS.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='stress_'))
    results: list[dict] = []
    lock = threading.Lock()
    counter = iter(range(ITERS))
    t_start = time.monotonic()
    print(
        f'modes={MODES} cdb={CDB} LP_NUM_THREADS={os.environ.get("LP_NUM_THREADS")!r} '
        f'MESA_SHADER_CACHE_DISABLE={os.environ.get("MESA_SHADER_CACHE_DISABLE")!r}',
        flush=True,
    )

    def summarize() -> dict:
        """Summarize the results collected so far."""
        hangs = [r for r in results if r['hang']]
        crashes = [r for r in results if not r['hang'] and r.get('rc')]
        secs = sorted(r['seconds'] for r in results)
        return {
            'iterations': len(results),
            'hangs': len(hangs),
            'crashes': len(crashes),
            'per_mode': {m: sum(1 for r in results if r['mode'] == m) for m in MODES},
            'hangs_per_mode': {m: sum(1 for r in hangs if r['mode'] == m) for m in MODES},
            'hang_tokens': [r['cmd'][-2:] for r in hangs],
            'hang_screenshot_written': [r['screenshot_written'] for r in hangs],
            'hang_last_mark': [(r['stdout'].strip().splitlines() or ['<none>'])[-1] for r in hangs],
            'median_seconds': secs[len(secs) // 2] if secs else None,
            'max_seconds': secs[-1] if secs else None,
        }

    def worker() -> None:
        """Pull iterations until they run out."""
        while True:
            with lock:
                i = next(counter, None)
            if i is None or time.monotonic() - t_start > BUDGET:
                return
            r = run_one(i, tmp)
            with lock:
                results.append(r)
                n = len(results)
                if r['hang'] or r.get('rc'):
                    print(f'!!! iteration {i} ({r["mode"]}): {json.dumps(r, indent=1)}', flush=True)
                    (RESULTS / f'hang_{i}.json').write_text(json.dumps(r, indent=1))
                if n % 50 == 0:
                    s = summarize()
                    print(
                        f'{n}/{ITERS} done, {s["hangs"]} hangs {s["hangs_per_mode"]}, '
                        f'{(time.monotonic() - t_start) / 60:.1f} min',
                        flush=True,
                    )

    def watchdog() -> None:
        """Dump the parent's stacks and bail out if the loop overruns its budget."""
        time.sleep(BUDGET + 180)
        print('WATCHDOG: parent overran the budget; dumping its threads', flush=True)
        faulthandler.dump_traceback(all_threads=True)
        with lock:
            summary = summarize()
            summary['watchdog'] = True
            (RESULTS / 'summary.json').write_text(json.dumps(summary, indent=1))
            print(json.dumps(summary, indent=1), flush=True)
        os._exit(3)

    threading.Thread(target=watchdog, daemon=True).start()
    threads = [threading.Thread(target=worker) for _ in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    summary = summarize()
    (RESULTS / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1), flush=True)
    return 1 if summary['hangs'] or summary['crashes'] else 0


if __name__ == '__main__':
    sys.exit(main())
