#!/usr/bin/env python3
"""
Deteksi bunga betina kelapa sawit menggunakan YOLOv11.

Karakteristik YOLOv11 (Ultralytics, 2024):
- C3K2 block menggantikan C2f
- SPPF + C2PSA attention module
- 22% lebih sedikit parameter dari YOLOv8m dengan mAP lebih tinggi
- Versi paling matang dari ekosistem Ultralytics saat ini

Jalankan:
    python3 detect_yolov11.py
    python3 detect_yolov11.py --ncnn
    python3 detect_yolov11.py --image foto.jpg

Catatan: YOLOv11 di Ultralytics butuh ultralytics>=8.3.0
"""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_generic import run_detection, detect_single_image
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description="Deteksi YOLOv11")
    parser.add_argument("--source", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    if args.image:
        detect_single_image("yolov11", args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection("yolov11", source, args.ncnn, args.save_video, not args.no_show)


if __name__ == "__main__":
    main()
