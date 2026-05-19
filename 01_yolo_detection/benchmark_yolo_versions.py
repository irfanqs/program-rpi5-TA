#!/usr/bin/env python3
"""
Benchmark semua versi YOLO pada Raspberry Pi 5.

Mengukur:
- Waktu inferensi rata-rata (ms)
- FPS rata-rata
- Ukuran model (MB)
- Akurasi (mAP@0.5) — hanya jika data uji tersedia

Hasil disimpan ke logs/benchmark_results.csv dan ditampilkan dalam tabel.
Output ini langsung dipakai untuk Bab 4 laporan (Tabel Perbandingan Model).

Jalankan:
    python3 benchmark_yolo_versions.py
    python3 benchmark_yolo_versions.py --images path/ke/folder/uji
    python3 benchmark_yolo_versions.py --ncnn         # benchmark versi NCNN
    python3 benchmark_yolo_versions.py --n-frames 100 # tentukan jumlah frame
"""
import argparse
import csv
import sys
import time
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

import numpy as np


def get_model_size_mb(path: str) -> float:
    p = Path(path)
    if p.is_file():
        return p.stat().st_size / (1024 * 1024)
    if p.is_dir():
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return total / (1024 * 1024)
    return 0.0


def benchmark_one(version: str, use_ncnn: bool, n_frames: int, test_image=None):
    """Benchmark satu versi YOLO."""
    from ultralytics import YOLO

    path = (config.MODEL_PATHS_NCNN if use_ncnn else config.MODEL_PATHS).get(version)
    if not path or not Path(path).exists():
        print(f"[SKIP] {version}: model tidak ditemukan ({path})")
        return None

    print(f"\n[BENCH] {version.upper()} ...")
    size_mb = get_model_size_mb(path)
    model = YOLO(path, task="detect") if use_ncnn else YOLO(path)

    # Generate dummy frame kalau tidak ada image
    if test_image is None:
        import cv2
        dummy = np.random.randint(0, 255, (config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3),
                                  dtype=np.uint8)
        frames = [dummy] * n_frames
    else:
        import cv2
        img = cv2.imread(test_image)
        frames = [img] * n_frames

    # Warm-up (model pertama selalu lambat)
    print("  Warm-up 3 frame...")
    for _ in range(3):
        model(frames[0], imgsz=config.IMG_SIZE,
              conf=config.CONF_THRESHOLD, device=config.DEVICE, verbose=False)

    # Benchmark
    times = []
    for i, frame in enumerate(frames):
        t0 = time.time()
        model(frame, imgsz=config.IMG_SIZE,
              conf=config.CONF_THRESHOLD, device=config.DEVICE, verbose=False)
        t1 = time.time()
        times.append((t1 - t0) * 1000)  # ms
        if (i + 1) % 20 == 0:
            print(f"  frame {i+1}/{n_frames}  avg={mean(times):.1f} ms")

    result = {
        "version": version.upper(),
        "format": "NCNN" if use_ncnn else "PyTorch",
        "size_mb": round(size_mb, 2),
        "avg_ms": round(mean(times), 2),
        "std_ms": round(stdev(times) if len(times) > 1 else 0, 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "avg_fps": round(1000 / mean(times), 2),
        "imgsz": config.IMG_SIZE,
        "n_frames": n_frames,
    }
    return result


def print_table(results):
    """Cetak hasil benchmark sebagai tabel rapi."""
    if not results:
        print("Tidak ada hasil benchmark.")
        return

    headers = ["Versi", "Format", "Size MB", "Avg ms", "Std ms",
               "Min ms", "Max ms", "FPS", "imgsz"]
    rows = [[r["version"], r["format"], r["size_mb"], r["avg_ms"],
             r["std_ms"], r["min_ms"], r["max_ms"], r["avg_fps"], r["imgsz"]]
            for r in results]

    # Lebar kolom
    widths = [max(len(str(h)), max(len(str(row[i])) for row in rows))
              for i, h in enumerate(headers)]

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    line = lambda vals: "| " + " | ".join(str(v).ljust(w) for v, w in zip(vals, widths)) + " |"

    print("\n" + sep)
    print(line(headers))
    print(sep)
    for row in rows:
        print(line(row))
    print(sep)

    # Cari yang paling cepat
    fastest = min(results, key=lambda r: r["avg_ms"])
    print(f"\n>>> Tercepat: {fastest['version']} ({fastest['avg_ms']} ms = "
          f"{fastest['avg_fps']} FPS)")


def save_csv(results, path):
    if not results:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[INFO] Hasil disimpan ke: {path}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark semua versi YOLO")
    parser.add_argument("--versions", nargs="+",
                        default=["yolov8", "yolov9", "yolov10", "yolov11", "yolo26"],
                        help="Daftar versi YOLO yang dibandingkan")
    parser.add_argument("--ncnn", action="store_true",
                        help="Benchmark versi NCNN")
    parser.add_argument("--n-frames", type=int, default=50,
                        help="Jumlah frame untuk benchmark (default 50)")
    parser.add_argument("--test-image", default=None,
                        help="Path gambar uji (kalau tidak ada, pakai dummy random)")
    args = parser.parse_args()

    print("=" * 60)
    print("Benchmark YOLO — Raspberry Pi 5")
    print(f"Format: {'NCNN' if args.ncnn else 'PyTorch (.pt)'}")
    print(f"imgsz : {config.IMG_SIZE}")
    print(f"Frame : {args.n_frames}")
    print("=" * 60)

    results = []
    for v in args.versions:
        r = benchmark_one(v, args.ncnn, args.n_frames, args.test_image)
        if r:
            results.append(r)

    print_table(results)

    out_csv = config.LOGS_DIR / f"benchmark_{'ncnn' if args.ncnn else 'pt'}.csv"
    save_csv(results, out_csv)


if __name__ == "__main__":
    main()
