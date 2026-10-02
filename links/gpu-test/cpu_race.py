"""The race version: the same 4096 x 4096 multiply done 50 times back to back, wall-clock total.
CPU: numpy/OpenBLAS on all 16 threads, then on 1 thread for a sample of runs (scaled shown separately).
Run: python cpu_race.py  (writes cpu_race_result.txt)"""
import os, sys, json, subprocess

RUNS = 50
code = f"""
import numpy as np, time
rng = np.random.default_rng(0)
a = rng.standard_normal((4096,4096), dtype=np.float32); b = rng.standard_normal((4096,4096), dtype=np.float32)
a @ b
t = time.perf_counter()
for _ in range({RUNS}): c = a @ b
print(time.perf_counter() - t)
"""
res = {'job': '4096x4096 @ 4096x4096 float32, 50 times back to back', 'multiply_adds_total': 50 * 4096 ** 3}
for th in (16, 1):
    env = dict(os.environ, OPENBLAS_NUM_THREADS=str(th))
    s = float(subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env).stdout)
    res[f'threads_{th}_total_s'] = round(s, 2)
    print(th, 'threads total:', round(s, 2), 's')
open(os.path.join(os.path.dirname(__file__), 'cpu_race_result.txt'), 'w').write(json.dumps(res, indent=2))
