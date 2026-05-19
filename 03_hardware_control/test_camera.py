#!/usr/bin/env python3
"""
Verifikasi kamera berfungsi (Pi Camera atau USB cam).

Mengecek:
1. Source bisa dibuka
2. Frame bisa dibaca
3. FPS aktual

Otomatis fallback dari Picamera2 -> OpenCV VideoCapture kalau perlu.

Jalankan:
    python3 test_camera.py
    python3 test_camera.py --source 1            # USB cam kedua
    python3 test_camera.py --duration 10          # tes 10 detik
    python3 test_camera.py --snapshot ./out.jpg   # ambil 1 foto lalu keluar
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

import cv2


def try_picamera2():
    try:
        from picamera2 import Picamera2
        picam = Picamera2()
        picam.configure(picam.create_video_configuration(
            main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)}
        ))
        picam.start()
        time.sleep(0.5)
        return picam
    except Exception as e:
        print(f"[INFO] Picamera2 tidak tersedia: {e}")
        return None


def try_opencv(source):
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    return cap


def main():
    parser = argparse.ArgumentParser(description="Tes kamera")
    parser.add_argument("--source", default=config.CAMERA_SOURCE,
                        help="0 untuk webcam, atau path")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Durasi tes (detik)")
    parser.add_argument("--snapshot", default=None,
                        help="Path output, hanya simpan 1 foto lalu keluar")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    print("=" * 50)
    print("Tes Kamera")
    print("=" * 50)

    cam = None
    kind = None

    if config.USE_PICAMERA2 and args.source == 0:
        cam = try_picamera2()
        if cam is not None:
            kind = "picamera2"

    if cam is None:
        cam = try_opencv(args.source)
        if cam is not None:
            kind = "cv2"

    if cam is None:
        print(f"[ERROR] Tidak ada kamera tersedia di source={args.source}")
        print("\nTroubleshooting:")
        print("  - USB cam: cek dengan 'lsusb' dan 'ls /dev/video*'")
        print("  - Pi Camera: cek 'libcamera-hello' di terminal")
        print("  - Aktifkan camera: sudo raspi-config -> Interface -> Camera")
        sys.exit(1)

    print(f"[OK] Kamera aktif via {kind}")

    # Snapshot mode
    if args.snapshot:
        if kind == "picamera2":
            frame = cam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            ret, frame = cam.read()
            if not ret:
                print("[ERROR] Gagal baca frame")
                sys.exit(1)
        cv2.imwrite(args.snapshot, frame)
        print(f"[OK] Snapshot disimpan: {args.snapshot}  ({frame.shape})")
        if kind == "picamera2":
            cam.stop()
        else:
            cam.release()
        return

    # Live preview mode
    print(f"Test selama {args.duration} detik. Tekan 'q' untuk berhenti.\n")
    t0 = time.time()
    n_frames = 0
    try:
        while time.time() - t0 < args.duration:
            if kind == "picamera2":
                frame = cam.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                ret = frame is not None
            else:
                ret, frame = cam.read()

            if not ret:
                print("  [WARN] Frame kosong")
                continue

            n_frames += 1
            elapsed = time.time() - t0
            fps = n_frames / elapsed if elapsed > 0 else 0

            cv2.putText(frame, f"FPS: {fps:.1f}  frame #{n_frames}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Source: {kind}  {frame.shape[1]}x{frame.shape[0]}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

            if not args.no_show:
                cv2.imshow("Camera Test", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        elapsed = time.time() - t0
        print(f"\n[RESULT] {n_frames} frame dalam {elapsed:.1f}s -> "
              f"{n_frames/elapsed:.1f} FPS rata-rata")

        if kind == "picamera2":
            cam.stop()
        else:
            cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
