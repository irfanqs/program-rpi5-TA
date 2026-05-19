#!/usr/bin/env python3
"""
Deteksi bunga betina kelapa sawit menggunakan YOLO26 (placeholder).

CATATAN PENTING:
Sampai dokumen ini ditulis (Mei 2026), Ultralytics belum merilis versi
"YOLO26" sebagai versi resmi (urutan resmi: v8 -> v9 -> v10 -> v11 -> v12).
Skrip ini disediakan sesuai proposal Anda (Bab 3.1.4) sebagai placeholder.

Perilaku otomatis:
- Jika file model `yolo26_best.pt` ada di folder models/, akan dipakai.
- Jika tidak ada, akan FALLBACK ke YOLOv11 dengan pesan peringatan.

Saat versi YOLO26 resmi keluar, cukup:
1. Train model dengan API resmi
2. Simpan sebagai `models/yolo26_best.pt`
3. Skrip ini langsung pakai versi tersebut tanpa perubahan kode

Jalankan:
    python3 detect_yolo26.py
    python3 detect_yolo26.py --ncnn
    python3 detect_yolo26.py --image foto.jpg
"""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_generic import run_detection, detect_single_image
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description="Deteksi YOLO26 (fallback YOLOv11)")
    parser.add_argument("--source", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    if args.image:
        detect_single_image("yolo26", args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection("yolo26", source, args.ncnn, args.save_video, not args.no_show)


if __name__ == "__main__":
    main()
