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
RESULTS = Path('stress_results')
ANT = Path(pv.examples.antfile).as_posix()
SCRIPT = shutil.which('pyvista')
TOKENS = [
    '--color=red',
    '--color=red --opacity=0.1',
    '--color=blue --culling=front',
    '--background=blue --color red',
]
MODES = ('wrapper', 'module', 'script')
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


def command(i: int, out: str) -> tuple[str, list[str]]:
    """Build the child command for iteration ``i``."""
    args = f'plot {ANT} --off-screen --screenshot={out} {TOKENS[i % len(TOKENS)]}'.split()
    mode = MODES[(i // len(TOKENS)) % len(MODES)]
    if mode == 'wrapper':
        return mode, [sys.executable, '-c', WRAPPER, *args]
    if mode == 'module':
        return mode, [sys.executable, '-m', 'pyvista', *args]
    return mode, [SCRIPT or 'pyvista', *args]


def pyspy(pid: int) -> str:
    """Dump the stacks of every python process in the tree, native first."""
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
        for extra in (['--native'], []):
            cmd = ['py-spy', 'dump', '--pid', str(proc.pid), *extra]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
            except Exception as exc:  # noqa: BLE001
                chunks.append(f'$ {" ".join(cmd)}\n{exc!r}')
                continue
            chunks.append(f'$ {" ".join(cmd)} -> rc {r.returncode}\n{r.stdout}\n{r.stderr}')
            if r.returncode == 0 and r.stdout.strip():
                break
    return '\n\n'.join(chunks)


def run_one(i: int, tmp: Path) -> dict:
    """Run one child and describe what happened."""
    out = (tmp / f'out_{i}.png').as_posix()
    mode, cmd = command(i, out)
    t0 = time.monotonic()
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='replace'
    )
    try:
        so, se = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f'!!! iteration {i} ({mode}) pid {p.pid}: hang detected, dumping', flush=True)
        dump = pyspy(p.pid)
        print(f'!!! iteration {i}: dump done, killing tree', flush=True)
        try:
            k = subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(p.pid)],
                capture_output=True, text=True, timeout=60, check=False,
            )
            kill_note = f'taskkill rc {k.returncode}: {k.stdout.strip()} {k.stderr.strip()}'
        except subprocess.TimeoutExpired:
            kill_note = 'taskkill timed out'
        except FileNotFoundError:
            p.kill()
            kill_note = 'p.kill()'
        print(f'!!! iteration {i}: {kill_note}; collecting output', flush=True)
        try:
            so, se = p.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            so, se = '<output unavailable: pipes still open after kill>', ''
        print(f'!!! iteration {i}: handled', flush=True)
        return {
            'kill': kill_note,
            'i': i,
            'mode': mode,
            'hang': True,
            'seconds': round(time.monotonic() - t0, 1),
            'screenshot_written': Path(out).exists(),
            'cmd': cmd,
            'stdout': so,
            'stderr': se,
            'pyspy': dump,
        }
    return {
        'i': i,
        'mode': mode,
        'hang': False,
        'rc': p.returncode,
        'seconds': round(time.monotonic() - t0, 1),
        'screenshot_written': Path(out).exists(),
        'stdout': so if p.returncode else '',
        'stderr': se if p.returncode else '',
    }


def main() -> int:
    """Run the stress loop on ``WORKERS`` threads and summarize."""
    RESULTS.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='stress_'))
    results: list[dict] = []
    lock = threading.Lock()
    counter = iter(range(ITERS))
    t_start = time.monotonic()

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
                bad = [x for x in results if x['hang'] or x.get('rc')]
                if r['hang'] or r.get('rc'):
                    print(f'!!! iteration {i} ({r["mode"]}): {json.dumps(r, indent=1)}', flush=True)
                    (RESULTS / f'hang_{i}.json').write_text(json.dumps(r, indent=1))
                if n % 25 == 0:
                    el = time.monotonic() - t_start
                    print(f'{n}/{ITERS} done, {len(bad)} bad, {el / 60:.1f} min', flush=True)

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
            'hang_modes': [r['mode'] for r in hangs],
            'hang_tokens': [r['cmd'][-2:] for r in hangs],
            'hang_screenshot_written': [r['screenshot_written'] for r in hangs],
            'median_seconds': secs[len(secs) // 2] if secs else None,
            'max_seconds': secs[-1] if secs else None,
        }

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

    hangs = [r for r in results if r['hang']]
    crashes = [r for r in results if not r['hang'] and r.get('rc')]
    summary = summarize()
    (RESULTS / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1), flush=True)
    return 1 if hangs or crashes else 0


if __name__ == '__main__':
    sys.exit(main())
