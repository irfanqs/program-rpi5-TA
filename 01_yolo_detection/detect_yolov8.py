#!/usr/bin/env python3
"""
Deteksi bunga betina kelapa sawit menggunakan YOLOv8.

Karakteristik YOLOv8 (Ultralytics, 2023):
- Anchor-free, head decoupled
- Backbone CSPDarknet53 termodifikasi
- Mendukung n/s/m/l/x ukuran model
- Baseline yang stabil dan banyak referensi

Jalankan:
    python3 detect_yolov8.py
    python3 detect_yolov8.py --ncnn          # pakai model NCNN
    python3 detect_yolov8.py --image foto.jpg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_generic import run_detection, detect_single_image
import argparse
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description="Deteksi YOLOv8")
    parser.add_argument("--source", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    if args.image:
        detect_single_image("yolov8", args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection("yolov8", source, args.ncnn, args.save_video, not args.no_show)


if __name__ == "__main__":
    main()
