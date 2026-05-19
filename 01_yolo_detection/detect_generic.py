#!/usr/bin/env python3
"""
Universal YOLO detector — pilih versi YOLO via argumen CLI.

Contoh:
    python3 detect_generic.py --version yolov8
    python3 detect_generic.py --version yolov11 --ncnn   # pakai model NCNN
    python3 detect_generic.py --version yolov10 --source path/ke/video.mp4
    python3 detect_generic.py --version yolov8 --image path/ke/gambar.jpg

Output: jendela live preview dengan bounding box, FPS counter, dan
log deteksi ke stdout.
"""
import argparse
import sys
import time
from pathlib import Path

# Tambahkan parent dir ke path supaya bisa import config.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

import cv2
import numpy as np


def load_model(version: str, use_ncnn: bool = False):
    """Load model YOLO sesuai versi. Fallback ke .pt kalau NCNN belum di-export."""
    from ultralytics import YOLO

    if use_ncnn:
        path = config.MODEL_PATHS_NCNN.get(version)
        if path and Path(path).exists():
            print(f"[INFO] Load NCNN model: {path}")
            return YOLO(path, task="detect")
        print(f"[WARN] NCNN model untuk {version} tidak ada. Fallback ke .pt")

    path = config.MODEL_PATHS.get(version)
    if not path:
        raise ValueError(f"Versi YOLO '{version}' tidak dikenal.")

    if not Path(path).exists():
        # Untuk yolo26: fallback ke yolov11 kalau belum tersedia
        if version == "yolo26":
            fallback = config.MODEL_PATHS["yolov11"]
            print(f"[WARN] YOLO26 belum tersedia ({path}). Fallback ke YOLOv11.")
            path = fallback
        else:
            raise FileNotFoundError(
                f"Model tidak ditemukan: {path}\n"
                f"Letakkan file .pt di folder models/ atau ubah config.py"
            )

    print(f"[INFO] Load model: {path}")
    return YOLO(path)


def open_video_source(source):
    """Buka kamera atau file video. Support Pi Camera kalau config.USE_PICAMERA2 = True."""
    if config.USE_PICAMERA2 and source == 0:
        try:
            from picamera2 import Picamera2
            picam = Picamera2()
            picam.configure(picam.create_video_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)}
            ))
            picam.start()
            print("[INFO] Pi Camera (picamera2) aktif")
            return picam, "picamera2"
        except Exception as e:
            print(f"[WARN] Picamera2 gagal: {e}. Fallback ke OpenCV VideoCapture.")

    # USB webcam atau file video
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Tidak bisa membuka source: {source}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
    return cap, "cv2"


def read_frame(source, kind):
    if kind == "picamera2":
        frame = source.capture_array()
        # picamera2 default RGB, OpenCV BGR
        return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return source.read()


def run_detection(version: str, source, use_ncnn: bool, save_video: bool, show: bool):
    model = load_model(version, use_ncnn)
    cap, kind = open_video_source(source)

    writer = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            str(config.LOG_VIDEO_PATH), fourcc, 15,
            (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)
        )

    frame_count = 0
    t_start = time.time()
    inference_times = []

    print(f"\n[INFO] Mulai deteksi pakai {version.upper()}. Tekan 'q' untuk keluar.\n")

    try:
        while True:
            ret, frame = read_frame(cap, kind)
            if not ret or frame is None:
                print("[INFO] Frame habis / kamera berhenti.")
                break

            t0 = time.time()
            results = model(
                frame,
                imgsz=config.IMG_SIZE,
                conf=config.CONF_THRESHOLD,
                iou=config.IOU_THRESHOLD,
                device=config.DEVICE,
                verbose=False,
            )
            t1 = time.time()
            inference_times.append(t1 - t0)

            annotated = results[0].plot()
            fps = 1.0 / (t1 - t0) if (t1 - t0) > 0 else 0.0

            # Overlay info
            label_text = f"{version.upper()} | {fps:.1f} FPS | imgsz={config.IMG_SIZE}"
            cv2.putText(annotated, label_text, (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Print deteksi ke stdout
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = model.names.get(cls_id, str(cls_id))
                if frame_count % 15 == 0:  # print tiap 15 frame supaya tidak spam
                    print(f"  [{frame_count}] {cls_name} ({conf:.2f})")

            if writer is not None:
                writer.write(annotated)

            if show:
                cv2.imshow(f"YOLO {version}", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            frame_count += 1
    finally:
        elapsed = time.time() - t_start
        avg_inf = float(np.mean(inference_times)) if inference_times else 0
        print("\n========== RINGKASAN ==========")
        print(f"Versi          : {version.upper()}")
        print(f"Frame diproses : {frame_count}")
        print(f"Durasi total   : {elapsed:.2f} s")
        print(f"Avg FPS        : {frame_count/elapsed:.2f}")
        print(f"Avg inference  : {avg_inf*1000:.1f} ms/frame")
        print("===============================\n")

        if kind == "picamera2":
            cap.stop()
        else:
            cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


def detect_single_image(version: str, image_path: str, use_ncnn: bool):
    """Deteksi pada satu file gambar saja."""
    model = load_model(version, use_ncnn)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    t0 = time.time()
    results = model(img, imgsz=config.IMG_SIZE,
                    conf=config.CONF_THRESHOLD, verbose=False)
    t1 = time.time()

    annotated = results[0].plot()
    out_path = Path(image_path).with_suffix(f".{version}.jpg")
    cv2.imwrite(str(out_path), annotated)

    print(f"[INFO] Hasil disimpan: {out_path}")
    print(f"[INFO] Inference time: {(t1-t0)*1000:.1f} ms")
    for box in results[0].boxes:
        cls_name = model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        print(f"  - {cls_name}: {conf:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Universal YOLO detector untuk TA")
    parser.add_argument("--version", required=True,
                        choices=["yolov8", "yolov9", "yolov10", "yolov11", "yolo26"],
                        help="Versi YOLO yang dipakai")
    parser.add_argument("--source", default=None,
                        help="Source: 0 untuk webcam, path file video, atau path RTSP")
    parser.add_argument("--image", default=None,
                        help="Deteksi pada satu gambar saja (tidak butuh kamera)")
    parser.add_argument("--ncnn", action="store_true",
                        help="Pakai model NCNN (lebih cepat di Pi 5)")
    parser.add_argument("--save-video", action="store_true",
                        help="Rekam hasil deteksi ke logs/session.mp4")
    parser.add_argument("--no-show", action="store_true",
                        help="Jangan tampilkan window (untuk headless / SSH)")
    args = parser.parse_args()

    if args.image:
        detect_single_image(args.version, args.image, args.ncnn)
    else:
        source = args.source if args.source is not None else config.CAMERA_SOURCE
        run_detection(
            version=args.version,
            source=source,
            use_ncnn=args.ncnn,
            save_video=args.save_video,
            show=not args.no_show,
        )


if __name__ == "__main__":
    main()
