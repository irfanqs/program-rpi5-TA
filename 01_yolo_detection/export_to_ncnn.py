#!/usr/bin/env python3
"""
Export model YOLO (.pt) ke format NCNN atau ONNX.

NCNN: Tencent's neural network inference framework, sangat cepat di Pi 5.
ONNX: format universal, support semua runtime.

**Jalankan skrip ini di LAPTOP/Google Colab, BUKAN di Raspberry Pi.**
Pi 5 cukup di-load formatnya saja.

Jalankan:
    python3 export_to_ncnn.py --version yolov8
    python3 export_to_ncnn.py --version yolov11 --format onnx
    python3 export_to_ncnn.py --all
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def export_one(version: str, fmt: str = "ncnn"):
    from ultralytics import YOLO

    pt_path = config.MODEL_PATHS.get(version)
    if not pt_path or not Path(pt_path).exists():
        print(f"[SKIP] {version}: file .pt tidak ada ({pt_path})")
        return

    print(f"\n[EXPORT] {version.upper()} -> {fmt.upper()}")
    model = YOLO(pt_path)

    try:
        out = model.export(format=fmt, imgsz=config.IMG_SIZE)
        print(f"  Output: {out}")
    except Exception as e:
        print(f"  [ERROR] Gagal export: {e}")
        if fmt == "ncnn":
            print("  Tip: install paket pendukung dengan:")
            print("    pip install ncnn")


def main():
    parser = argparse.ArgumentParser(description="Export YOLO ke NCNN/ONNX")
    parser.add_argument("--version", default=None,
                        choices=["yolov8", "yolov9", "yolov10", "yolov11", "yolo26"])
    parser.add_argument("--format", default="ncnn",
                        choices=["ncnn", "onnx", "tflite", "openvino"],
                        help="Format target (default: ncnn)")
    parser.add_argument("--all", action="store_true",
                        help="Export semua versi sekaligus")
    args = parser.parse_args()

    versions = list(config.MODEL_PATHS.keys()) if args.all else [args.version]
    if not args.all and not args.version:
        parser.error("Pilih --version atau --all")

    for v in versions:
        export_one(v, args.format)


if __name__ == "__main__":
    main()
