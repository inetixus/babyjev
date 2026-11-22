"""
BabyJev - Phase 0: capture benchmark.

Measures how fast we can pull frames from a region around the screen centre.
This number caps the whole reflex loop: you cannot react faster than you can see.

Usage:
    python capture_bench.py --seconds 10
    python capture_bench.py --backend mss --seconds 20
"""

import argparse
import statistics
import time


def center_region(screen_w, screen_h, ratio):
    w = int(screen_w * ratio)
    h = int(screen_h * ratio)
    left = (screen_w - w) // 2
    top = (screen_h - h) // 2
    return (left, top, left + w, top + h)


def bench_dxcam(region, seconds):
    import dxcam
    cam = dxcam.create(output_color="BGR", region=tuple(region), max_buffer_len=2)
    warm = cam.grab()
    if warm is None:
        raise RuntimeError("dxcam returned no frame")
    times = []
    t_end = time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        t0 = time.perf_counter()
        frame = cam.grab()
        dt = (time.perf_counter() - t0) * 1000.0
        if frame is not None:
            times.append(dt)
    return times, warm.shape[:2]


def bench_mss(region, seconds):
    import mss
    import numpy as np
    left, top, right, bottom = region
    monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}
    with mss.mss() as sct:
        warm = np.asarray(sct.grab(monitor))[:, :, :3]
        times = []
        t_end = time.perf_counter() + seconds
        while time.perf_counter() < t_end:
            t0 = time.perf_counter()
            frame = np.asarray(sct.grab(monitor))[:, :, :3]
            dt = (time.perf_counter() - t0) * 1000.0
            times.append(dt)
    return times, warm.shape[:2]


def p95(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def report(backend, times, shape):
    if not times:
        print("No frames captured. Is the right display being grabbed?")
        return
    total = sum(times)
    fps = 1000.0 * len(times) / total if total else 0.0
    print()
    print("=== BabyJev Phase 0: capture benchmark ===")
    print("backend          :", backend)
    print("frame shape      :", shape, "(region around screen centre)")
    print("frames captured  :", len(times))
    print("throughput       :", round(fps, 1), "fps")
    print("mean latency     :", round(statistics.fmean(times), 2), "ms")
    print("median latency   :", round(statistics.median(times), 2), "ms")
    print("p95 latency      :", round(p95(times), 2), "ms")
    print()
    print("Loop ceiling: your whole reflex pipeline cannot run faster than")
    print(round(fps, 1), "iterations per second until capture is optimized.")
    print("Budget check: capture should ideally stay under 10 ms.")


def main():
    ap = argparse.ArgumentParser(description="BabyJev capture benchmark")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--backend", choices=["auto", "dxcam", "mss"], default="auto")
    ap.add_argument("--region-ratio", type=float, default=0.25,
                    help="side of captured square as a fraction of screen width")
    args = ap.parse_args()

    import ctypes
    user32 = ctypes.windll.user32
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)
    region = center_region(screen_w, screen_h, args.region_ratio)

    backend, times, shape = args.backend, None, None
    if backend in ("auto", "dxcam"):
        try:
            times, shape = bench_dxcam(region, args.seconds)
            backend = "dxcam"
        except Exception as exc:
            print("dxcam unavailable:", exc)
            if backend == "dxcam":
                return
            backend = "mss"
    if times is None or shape is None:
        times, shape = bench_mss(region, args.seconds)
        backend = "mss"
    report(backend, times, shape)


if __name__ == "__main__":
    main()
