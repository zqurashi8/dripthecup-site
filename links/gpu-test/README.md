# CPU vs GPU: the same multiply (2026-10-01)

Machine: our test PC (the one in the video). Intel Core i7-10700F (8 cores, 16 threads, no integrated graphics), 48 GB DDR4 running at
2400 MT/s (4 sticks, dual channel), AMD Radeon RX 9060 XT (driver 32.0.22042.14002), Windows 11.

The job: multiply two 4096 x 4096 grids of float32 numbers (C = A x B). That is 4096^3 = 68.7 billion
multiply-adds (137 GFLOP). Every output number is its own row-times-column sum, so they can all be worked on at once.

- CPU: `python cpu_matmul.py` (numpy 2.4.6 + OpenBLAS 0.3.31, AVX2-tuned: the processor gets its best library),
  medians of 5 after a warm-up. Then `python cpu_race.py`: 50 multiplies back to back.
- GPU: `gpu_matmul.html?n=4096&reps=10&race=50` served by `python -m http.server 8796` (launch.json "gpu-test"),
  opened in the built-in browser; our own simple tiled WebGPU shader (not AMD's tuned library), median of 10 after
  2 warm-ups, 5 answers checked against a CPU sum (max relative error 9e-7). Then 50 multiplies in one submit.

## Results

| | one multiply (median) | speed | 50 in a row |
|---|---|---|---|
| i7-10700F, 1 core (1 thread) | 1.055 s | 130 GFLOPS | 52.8 s |
| i7-10700F, all 8 cores (16 threads) | 0.192 s | 716 GFLOPS | 10.16 s |
| Radeon RX 9060 XT (WebGPU, our shader) | 0.024 s | 5,727 GFLOPS | 1.12 s |

GPU vs all 8 cores: about 8x (one multiply) and 9.1x (the race). GPU vs one core: about 44x / 47x.
Raw output: `cpu_result.txt`, `cpu_race_result.txt`, `gpu_result.txt`.

Fairness notes: the comparison leans toward the CPU (tuned BLAS vs our simple browser shader at roughly a fifth of
the card's rated FP32 peak). Upload time to the card is not counted (data was already on it), the same as the CPU's
data already being in RAM.

Raw page output (window.RESULT, copied verbatim from the browser): `gpu_window_RESULT_raw.json`. The browser hid the
adapter description (privacy), so the card is identified by Windows: the Radeon RX 9060 XT is the only display
adapter (PNP subsystem 1458 = Gigabyte board), and the i7-10700F has no integrated graphics.
Inputs differ (numpy normal, seed 0, vs an LCG uniform -0.5..0.5): same size, same float32 type, same operation;
the values don't change the timing of a dense multiply.
