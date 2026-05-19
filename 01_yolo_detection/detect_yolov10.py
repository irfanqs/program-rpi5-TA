#!/usr/bin/env python3
"""
Deteksi bunga betina kelapa sawit menggunakan YOLOv10.

Karakteristik YOLOv10 (Tsinghua, 2024):
- NMS-free training (consistent dual assignments)
- Latency lebih rendah karena tanpa post-processing NMS
- Sangat cocok untuk real-time edge deployment
- Ukuran model: n/s/m/b/l/x

Jalankan:
    python3 detect_yolov10.py
    python3 detect_yolov10.py --ncnn
    python3 detect_yolov10.py --image foto.jpg

Catatan: YOLOv10 di Ultralytics butuh ultralytics>=8.1.34
"""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_generic import run_detection, detect_single_image
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description="Deteksi YOLOv10")
    parser.add_argument("--source", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    if args.image:
        detect_single_image("yolov10", args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection("yolov10", source, args.ncnn, args.save_video, not args.no_show)


if __name__ == "__main__":
    main()
