#!/usr/bin/env python3
"""
SISTEM PENYERBUKAN TERPADU — Main loop end-to-end.

Menggabungkan:
- Kamera (Pi Camera / USB)
- YOLO inference (versi pilihan user)
- Sensor VL53L0X (volume pollen)
- Servo motor (katup tabung)
- Blower fan (penyemprot)
- State machine + logging

Alur (sesuai proposal Gambar 3.2):
1. Kamera ambil citra bunga
2. YOLO klasifikasi: matang / tidak matang
3. Kalau matang -> cek volume pollen via ToF
4. Kalau cukup -> servo buka katup -> blower nyala -> tutup
5. Cooldown -> kembali ke step 1

Jalankan:
    python3 pollination_system.py
    python3 pollination_system.py --version yolov11 --ncnn
    python3 pollination_system.py --dry-run            # tidak nyalakan aktuator
    python3 pollination_system.py --headless           # tanpa window
    python3 pollination_system.py --duration 60         # auto-stop 60s

PERINGATAN:
Pastikan semua hardware sudah lulus test individu (test_all_hardware.py)
SEBELUM menjalankan sistem terpadu ini.
"""
import argparse
import sys
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from logger import EventLogger
from state_machine import PollinationStateMachine, State

import cv2
import numpy as np


# ============================================================
# Hardware wrappers (dengan dry-run mode untuk debug tanpa aktuator)
# ============================================================
class HardwareController:
    def __init__(self, dry_run: bool = False, skip_blower: bool = False):
        self.dry_run = dry_run
        self.skip_blower = skip_blower
        self.servo = None
        self.blower = None
        self.tof = None
        self._init_devices()

    def _init_devices(self):
        if self.dry_run:
            print("[DRY-RUN] Semua aktuator dimock, tidak ada output GPIO")
            return

        # Set pin factory ke lgpio (Pi 5)
        try:
            from gpiozero import Device
            from gpiozero.pins.lgpio import LGPIOFactory
            Device.pin_factory = LGPIOFactory()
        except Exception as e:
            print(f"[WARN] lgpio factory gagal: {e}")

        # Servo
        try:
            from gpiozero import AngularServo
            self.servo = AngularServo(
                config.PIN_SERVO,
                min_pulse_width=0.5/1000,
                max_pulse_width=2.5/1000,
            )
            self.servo.angle = config.SERVO_ANGLE_CLOSED
            print(f"[OK] Servo init di GPIO {config.PIN_SERVO}")
        except Exception as e:
            print(f"[ERROR] Servo gagal init: {e}")
            self.servo = None

        # Blower
        if not self.skip_blower:
            try:
                from gpiozero import PWMOutputDevice
                self.blower = PWMOutputDevice(
                    config.PIN_BLOWER,
                    frequency=config.BLOWER_FREQ_HZ,
                    initial_value=0.0,
                )
                print(f"[OK] Blower init di GPIO {config.PIN_BLOWER}")
            except Exception as e:
                print(f"[WARN] Blower gagal init: {e}")
                self.blower = None

        # VL53L0X
        try:
            import board, busio, adafruit_vl53l0x
            i2c = busio.I2C(board.SCL, board.SDA)
            self.tof = adafruit_vl53l0x.VL53L0X(i2c)
            self.tof.measurement_timing_budget = 50000
            print("[OK] VL53L0X init")
        except Exception as e:
            print(f"[WARN] VL53L0X gagal init: {e}")
            self.tof = None

    def set_valve(self, opened: bool):
        if self.dry_run or self.servo is None:
            return
        target = config.SERVO_ANGLE_OPEN if opened else config.SERVO_ANGLE_CLOSED
        self.servo.angle = target

    def set_blower(self, duty_percent: float):
        if self.dry_run or self.blower is None:
            return
        self.blower.value = max(0.0, min(1.0, duty_percent / 100.0))

    def read_distance_mm(self) -> float:
        if self.dry_run or self.tof is None:
            # Simulasi: jarak random antara empty dan full
            return float(np.random.randint(config.TOF_DISTANCE_FULL_MM,
                                           config.TOF_DISTANCE_EMPTY_MM))
        try:
            return float(self.tof.range)
        except Exception:
            return -1.0

    def cleanup(self):
        try:
            self.set_valve(False)
            self.set_blower(0)
            time.sleep(0.3)
            if self.servo: self.servo.close()
            if self.blower: self.blower.close()
        except Exception:
            pass


def distance_to_volume_ml(d_mm: float) -> float:
    """Konversi jarak ToF ke volume (mL)."""
    pollen_height = max(0, config.TOF_DISTANCE_EMPTY_MM - d_mm)
    pollen_height = min(pollen_height,
                        config.TOF_DISTANCE_EMPTY_MM - config.TOF_DISTANCE_FULL_MM)
    volume_mm3 = pollen_height * config.TUBE_AREA_MM2
    return volume_mm3 / 1000.0


def load_yolo(version: str, use_ncnn: bool):
    from ultralytics import YOLO
    paths = config.MODEL_PATHS_NCNN if use_ncnn else config.MODEL_PATHS
    path = paths.get(version)
    if not path or not Path(path).exists():
        if version == "yolo26":
            path = config.MODEL_PATHS["yolov11"]
            print(f"[WARN] YOLO26 fallback ke YOLOv11: {path}")
        else:
            raise FileNotFoundError(f"Model tidak ada: {path}")
    print(f"[OK] Load YOLO ({version}): {path}")
    return YOLO(path, task="detect") if use_ncnn else YOLO(path)


def open_camera():
    if config.USE_PICAMERA2:
        try:
            from picamera2 import Picamera2
            picam = Picamera2()
            picam.configure(picam.create_video_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)}
            ))
            picam.start()
            return picam, "picamera2"
        except Exception as e:
            print(f"[WARN] Picamera2 gagal: {e}")
    cap = cv2.VideoCapture(config.CAMERA_SOURCE)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError("Kamera gagal dibuka")
    return cap, "cv2"


def read_frame(cap, kind):
    if kind == "picamera2":
        f = cap.capture_array()
        return True, cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
    return cap.read()


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Sistem Penyerbuk Kelapa Sawit")
    parser.add_argument("--version", default="yolov11",
                        choices=["yolov8", "yolov9", "yolov10", "yolov11", "yolo26"])
    parser.add_argument("--ncnn", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Tidak nyalakan aktuator (untuk debug software)")
    parser.add_argument("--skip-blower", action="store_true",
                        help="Lewati init blower (kalau belum punya)")
    parser.add_argument("--headless", action="store_true",
                        help="Tanpa window OpenCV (untuk SSH)")
    parser.add_argument("--duration", type=float, default=0,
                        help="Auto-stop setelah N detik (0 = unlimited)")
    args = parser.parse_args()

    print("=" * 60)
    print("SISTEM PENYERBUK KELAPA SAWIT — TERPADU")
    print(f"YOLO version : {args.version}")
    print(f"NCNN model   : {args.ncnn}")
    print(f"Dry run      : {args.dry_run}")
    print(f"Skip blower  : {args.skip_blower}")
    print("=" * 60)

    # Init components
    logger = EventLogger(config.LOG_CSV_PATH)
    logger.info(f"START version={args.version} ncnn={args.ncnn} dry={args.dry_run}")

    sm = PollinationStateMachine(config)

    try:
        model = load_yolo(args.version, args.ncnn)
    except Exception as e:
        print(f"[FATAL] {e}")
        sys.exit(1)

    try:
        cam, cam_kind = open_camera()
        print(f"[OK] Kamera ({cam_kind})")
    except Exception as e:
        print(f"[FATAL] {e}")
        sys.exit(1)

    hw = HardwareController(dry_run=args.dry_run, skip_blower=args.skip_blower)

    # ToF moving average buffer
    tof_buffer = deque(maxlen=5)

    print("\n[RUN] Loop mulai. Tekan 'q' untuk berhenti.\n")
    t_start = time.time()
    frame_count = 0

    try:
        while True:
            ret, frame = read_frame(cam, cam_kind)
            if not ret or frame is None:
                print("[WARN] Frame kosong, skip")
                continue

            frame_count += 1

            # ---- YOLO inference ----
            results = model(frame,
                            imgsz=config.IMG_SIZE,
                            conf=config.CONF_THRESHOLD,
                            iou=config.IOU_THRESHOLD,
                            device=config.DEVICE,
                            verbose=False)

            # Cari deteksi target (bunga matang)
            detected = False
            best_conf = 0.0
            best_cls_name = ""
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names.get(cls_id, str(cls_id))
                conf = float(box.conf[0])
                if cls_name.lower() == config.TARGET_CLASS.lower() and conf > best_conf:
                    detected = True
                    best_conf = conf
                    best_cls_name = cls_name

            # ---- ToF reading ----
            d = hw.read_distance_mm()
            if d > 0:
                tof_buffer.append(d)
            d_smooth = sum(tof_buffer) / len(tof_buffer) if tof_buffer else 0
            volume_ml = distance_to_volume_ml(d_smooth) if d_smooth > 0 else 0.0

            # ---- State machine ----
            action = sm.update(detected=detected,
                                confidence=best_conf,
                                volume_ml=volume_ml,
                                distance_mm=d_smooth)

            # ---- Execute action ----
            hw.set_valve(action["open_valve"])
            hw.set_blower(action["blower_duty"])

            # ---- Log saat state transition penting ----
            if sm.state == State.SPRAYING and action["spray"]:
                if frame_count % 5 == 0:  # log tiap 5 frame saat semprot
                    logger.log("SPRAY", args.version, best_cls_name, best_conf,
                               d_smooth, volume_ml, True, True)
            elif sm.state == State.DETECTING:
                logger.log("DETECTION", args.version, best_cls_name, best_conf,
                           d_smooth, volume_ml, volume_ml*1000 >= config.VOLUME_MIN_THRESHOLD_MM3,
                           False)
            elif sm.state == State.INSUFFICIENT:
                if frame_count % 30 == 0:
                    logger.log("READY", args.version, "", 0,
                               d_smooth, volume_ml, False, False,
                               "Volume pollen di bawah threshold")

            # ---- Visualisasi ----
            if not args.headless:
                annotated = results[0].plot()
                state_color = (0, 255, 0) if sm.state == State.IDLE else \
                              (0, 165, 255) if sm.state == State.SPRAYING else \
                              (0, 0, 255) if sm.state in [State.ERROR, State.INSUFFICIENT] else \
                              (255, 200, 0)
                lines = [
                    f"State: {sm.state.name}",
                    f"YOLO : {args.version}  conf={best_conf:.2f}",
                    f"ToF  : {d_smooth:.0f} mm  Vol={volume_ml:.2f} mL",
                    f"Spray count: {sm.spray_count}",
                ]
                for i, line in enumerate(lines):
                    cv2.putText(annotated, line, (10, 30 + i*25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)
                cv2.imshow("TA - Pollination System", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Auto-stop berdasarkan durasi
            if args.duration > 0 and (time.time() - t_start) > args.duration:
                print(f"\n[INFO] Auto-stop setelah {args.duration} detik")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user")

    finally:
        elapsed = time.time() - t_start
        summary = sm.summary()
        logger.info(f"STOP frames={frame_count} duration={elapsed:.1f}s "
                    f"sprays={summary['spray_count']}")
        print("\n" + "=" * 60)
        print("RINGKASAN SESI")
        print("=" * 60)
        print(f"  Total frame  : {frame_count}")
        print(f"  Durasi       : {elapsed:.1f} s")
        print(f"  Avg FPS      : {frame_count/elapsed:.2f}")
        print(f"  Spray events : {summary['spray_count']}")
        print(f"  Log CSV      : {config.LOG_CSV_PATH}")
        print("=" * 60)

        hw.cleanup()
        if cam_kind == "picamera2":
            cam.stop()
        else:
            cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
