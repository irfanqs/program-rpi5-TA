#!/usr/bin/env python3
"""
Tes berurutan semua hardware: kamera -> ToF -> servo -> blower.

Pakai skrip ini untuk smoke-test sebelum integrasi penuh. Tiap komponen
diuji singkat lalu hasilnya ditampilkan sebagai PASS/FAIL.

Jalankan:
    python3 test_all_hardware.py
    python3 test_all_hardware.py --skip blower   # lewati blower (belum punya)
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def test_camera() -> bool:
    print("\n[1/4] Tes kamera...")
    try:
        import cv2
        cap = cv2.VideoCapture(config.CAMERA_SOURCE)
        if not cap.isOpened():
            return False
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            print(f"  [OK] Kamera bisa baca frame {frame.shape}")
            return True
        return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tof() -> bool:
    print("\n[2/4] Tes sensor VL53L0X...")
    try:
        import board, busio, adafruit_vl53l0x
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        sensor.measurement_timing_budget = 50000
        readings = []
        for _ in range(5):
            readings.append(sensor.range)
            time.sleep(0.1)
        avg = sum(readings) / len(readings)
        print(f"  [OK] Sensor baca rata-rata {avg:.1f} mm dari 5 sample")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_servo() -> bool:
    print("\n[3/4] Tes servo motor...")
    try:
        from gpiozero import AngularServo, Device
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
        servo = AngularServo(config.PIN_SERVO,
                             min_pulse_width=0.5/1000,
                             max_pulse_width=2.5/1000)
        print("  Buka katup...")
        servo.angle = config.SERVO_ANGLE_OPEN
        time.sleep(1)
        print("  Tutup katup...")
        servo.angle = config.SERVO_ANGLE_CLOSED
        time.sleep(1)
        servo.close()
        print("  [OK] Servo bergerak buka-tutup")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_blower() -> bool:
    print("\n[4/4] Tes blower fan...")
    try:
        from gpiozero import PWMOutputDevice, Device
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
        pwm = PWMOutputDevice(config.PIN_BLOWER,
                              frequency=config.BLOWER_FREQ_HZ)
        print("  Blower 50% selama 2 detik...")
        pwm.value = 0.5
        time.sleep(2)
        print("  Blower OFF")
        pwm.value = 0.0
        pwm.close()
        print("  [OK] Blower merespons PWM")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Smoke test semua hardware")
    parser.add_argument("--skip", nargs="+", default=[],
                        choices=["camera", "tof", "servo", "blower"],
                        help="Lewati komponen tertentu (mis. blower belum datang)")
    args = parser.parse_args()

    print("=" * 50)
    print("SMOKE TEST SEMUA HARDWARE")
    print("=" * 50)

    results = {}
    if "camera" not in args.skip:
        results["camera"] = test_camera()
    if "tof" not in args.skip:
        results["tof"] = test_tof()
    if "servo" not in args.skip:
        results["servo"] = test_servo()
    if "blower" not in args.skip:
        results["blower"] = test_blower()

    print("\n" + "=" * 50)
    print("RINGKASAN")
    print("=" * 50)
    for name, ok in results.items():
        mark = "[OK]  " if ok else "[FAIL]"
        print(f"  {mark} {name}")
    skipped = set(args.skip)
    for s in skipped:
        print(f"  [SKIP] {s}")

    all_ok = all(results.values())
    print()
    if all_ok:
        print("Semua komponen yang dites berfungsi.")
        sys.exit(0)
    else:
        print("Ada komponen yang FAIL. Cek wiring dan log di atas.")
        sys.exit(1)


if __name__ == "__main__":
    main()
