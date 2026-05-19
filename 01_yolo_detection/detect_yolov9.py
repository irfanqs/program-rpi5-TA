#!/usr/bin/env python3
"""
Deteksi bunga betina kelapa sawit menggunakan YOLOv9.

Karakteristik YOLOv9 (Wang et al., 2024):
- Programmable Gradient Information (PGI)
- Generalized Efficient Layer Aggregation Network (GELAN)
- Akurasi sedikit lebih tinggi dari YOLOv8 dengan parameter setara
- Cocok untuk dataset kecil-menengah

Jalankan:
    python3 detect_yolov9.py
    python3 detect_yolov9.py --ncnn
    python3 detect_yolov9.py --image foto.jpg
"""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_generic import run_detection, detect_single_image
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description="Deteksi YOLOv9")
    parser.add_argument("--source", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    if args.image:
        detect_single_image("yolov9", args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection("yolov9", source, args.ncnn, args.save_video, not args.no_show)


if __name__ == "__main__":
    main()
