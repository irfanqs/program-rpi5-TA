#!/usr/bin/env python3
"""
Evaluasi performa semua versi NCNN menggunakan dataset test dari Roboflow.

Jalankan dengan:
    python3 evaluate_ncnn.py
"""
import sys
import os
from pathlib import Path
from roboflow import Roboflow
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

def main():
    print("Mendownload dataset dari Roboflow...")
    rf = Roboflow(api_key="K7xkuijfZJvATClBgWtk")
    project = rf.workspace("irfan-i5y8i").project("kematangan-bunga-sawit-betina-rw7ci-0q3va")
    version = project.version(1)
    dataset = version.download("yolov8")
    
    yaml_path = f"{dataset.location}/data.yaml"
    print(f"\nDataset berhasi didownload di: {dataset.location}")
    print(f"Menggunakan file konfigurasi data: {yaml_path}\n")

    # Pastikan folder onnx tersedia
    onnx_dir = config.MODELS_DIR / "onnx"
    onnx_dir.mkdir(parents=True, exist_ok=True)

    results_summary = {}

    for version_name, path in config.MODEL_PATHS_NCNN.items():
        if not path or not Path(path).exists():
            print(f"[SKIP] Model NCNN {version_name} tidak ditemukan di {path}")
            continue
            
        print("=" * 60)
        print(f"Mengevaluasi Model: {version_name.upper()} (NCNN)")
        print("=" * 60)
        
        try:
            model = YOLO(path, task='detect')
            
            # Evaluasi performa (Validasi) menggunakan dataset test
            print(f"\nMenjalankan evaluasi (test split) untuk {version_name}...")
            # Menggunakan split='test' jika dataset mendukungnya, jika tidak fallback ke 'val'
            metrics = model.val(data=yaml_path, split='test', imgsz=config.IMG_SIZE, device=config.DEVICE)
            
            # Simpan ringkasan metrik
            results_summary[version_name] = {
                'mAP50': metrics.box.map50,
                'mAP50-95': metrics.box.map
            }
            
            print(f"\n[INFO] {version_name} NCNN mAP@0.5: {metrics.box.map50:.4f}, mAP@0.5:0.95: {metrics.box.map:.4f}")

        except Exception as e:
            print(f"[ERROR] Terjadi permsalahan saat memproses {version_name}: {e}")

    print("=" * 60)
    print("Ringkasan Hasil Evaluasi (mAP@0.5 Test Dataset di Raspberry Pi):")
    print("=" * 60)
    for model_name, res in results_summary.items():
        print(f" - {model_name.upper()}: mAP@0.5 = {res['mAP50']:.4f} | mAP@0.5:0.95 = {res['mAP50-95']:.4f}")

if __name__ == "__main__":
    main()