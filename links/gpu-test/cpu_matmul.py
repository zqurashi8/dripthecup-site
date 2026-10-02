"""CPU side of the CPU vs GPU test: the same job (multiply two 4096 x 4096 grids of numbers, float32)
on the i7-10700F, once on 1 core and once on all cores, with numpy's OpenBLAS (a fast, AVX2-tuned library:
the processor gets its best tool). Run:  python cpu_matmul.py  (writes cpu_result.txt)
"""
import os, sys, time, json, platform, subprocess

N = int(os.environ.get('N', 4096))
REPS = int(os.environ.get('REPS', 5))


def run(threads):
    code = f"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '{threads}'
import numpy as np, time
rng = np.random.default_rng(0)
a = rng.standard_normal(({N},{N}), dtype=np.float32)
b = rng.standard_normal(({N},{N}), dtype=np.float32)
a @ b  # warm-up
ts = []
for _ in range({REPS}):
    t = time.perf_counter(); c = a @ b; ts.append(time.perf_counter() - t)
ts.sort()
print(ts[len(ts)//2], ts[0], float(c[0,0]))
"""
    env = dict(os.environ, OPENBLAS_NUM_THREADS=str(threads))
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env).stdout.split()
    return float(out[0]), float(out[1])


flops = 2 * N ** 3
res = {'job': f'{N}x{N} @ {N}x{N} float32', 'multiply_adds': N ** 3, 'flops': flops,
       'cpu': platform.processor(), 'python': sys.version.split()[0]}
for th in (1, 8, 16):
    med, best = run(th)
    res[f'threads_{th}'] = {'median_s': round(med, 4), 'best_s': round(best, 4),
                            'gflops_median': round(flops / med / 1e9, 1)}
    print(th, 'threads:', res[f'threads_{th}'])
open(os.path.join(os.path.dirname(__file__), 'cpu_result.txt'), 'w').write(json.dumps(res, indent=2))
