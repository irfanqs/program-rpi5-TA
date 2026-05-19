#!/usr/bin/env python3
"""
Tes servo motor (katup buka-tutup tabung pollen).

WIRING:
- Signal (oranye/kuning) -> GPIO 18 (Pin fisik 12) - hardware PWM0
- VCC (merah)            -> 5V EKSTERNAL (BEC dari Li-Po, JANGAN dari Pi)
- GND (coklat)           -> GND eksternal + GND Pi (common ground)

PERINGATAN:
Servo bisa tarik arus tinggi saat stall. Mengambil daya dari pin 5V Pi
bisa bikin Pi restart. Selalu pakai BEC/regulator terpisah dari Li-Po.

Mode tes:
- sweep: gerakan kontinyu kiri-kanan
- toggle: ulang buka -> tutup
- angle: tahan di sudut tertentu

Jalankan:
    python3 test_servo.py --mode toggle --cycles 5
    python3 test_servo.py --mode sweep
    python3 test_servo.py --mode angle --angle 45
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def angle_to_pulse_width(angle: float) -> float:
    """Konversi derajat (0-180) ke pulse width (0.5-2.5 ms)."""
    return 0.5 + (angle / 180.0) * 2.0


def init_servo():
    """Coba beberapa library, ambil yang berhasil. gpiozero paling stabil di Pi 5."""
    try:
        from gpiozero import AngularServo
        from gpiozero.pins.lgpio import LGPIOFactory
        from gpiozero import Device
        # Pi 5 perlu lgpio backend
        Device.pin_factory = LGPIOFactory()
        servo = AngularServo(
            config.PIN_SERVO,
            min_angle=0, max_angle=180,
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
        )
        return servo, "gpiozero-lgpio"
    except Exception as e:
        print(f"[INFO] gpiozero+lgpio gagal: {e}")

    try:
        from gpiozero import AngularServo
        servo = AngularServo(
            config.PIN_SERVO,
            min_angle=0, max_angle=180,
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
        )
        return servo, "gpiozero-default"
    except Exception as e:
        print(f"[ERROR] gpiozero gagal: {e}")
        raise


def mode_sweep(servo, cycles: int, step: int = 5, delay: float = 0.02):
    print(f"[SWEEP] {cycles} siklus, step {step} derajat")
    for c in range(cycles):
        print(f"  Siklus {c+1}/{cycles}: 0 -> 180")
        for a in range(0, 181, step):
            servo.angle = a
            time.sleep(delay)
        print(f"  Siklus {c+1}/{cycles}: 180 -> 0")
        for a in range(180, -1, -step):
            servo.angle = a
            time.sleep(delay)


def mode_toggle(servo, cycles: int):
    closed = config.SERVO_ANGLE_CLOSED
    opened = config.SERVO_ANGLE_OPEN
    print(f"[TOGGLE] {cycles}x buka-tutup ({closed} <-> {opened} derajat)")
    for c in range(cycles):
        print(f"  Siklus {c+1}: TUTUP ({closed} deg)")
        servo.angle = closed
        time.sleep(1.0)
        print(f"  Siklus {c+1}: BUKA ({opened} deg)")
        servo.angle = opened
        time.sleep(1.0)
    servo.angle = closed
    print("  Selesai. Servo posisi TUTUP.")


def mode_angle(servo, angle: float, duration: float):
    print(f"[ANGLE] Tahan di {angle} derajat selama {duration} detik")
    servo.angle = angle
    time.sleep(duration)


def main():
    parser = argparse.ArgumentParser(description="Tes servo motor")
    parser.add_argument("--mode", choices=["sweep", "toggle", "angle"],
                        default="toggle")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--angle", type=float, default=90,
                        help="Sudut target (mode angle)")
    parser.add_argument("--duration", type=float, default=3.0,
                        help="Lama tahan (mode angle)")
    args = parser.parse_args()

    print("=" * 50)
    print(f"Tes Servo Motor (GPIO {config.PIN_SERVO})")
    print("=" * 50)

    try:
        servo, backend = init_servo()
        print(f"[OK] Servo siap via {backend}")
    except Exception as e:
        print(f"[ERROR] Gagal inisialisasi servo: {e}")
        print("\nTroubleshooting:")
        print("  - Install lgpio: pip install lgpio")
        print("  - Cek wiring: signal->GPIO 18, VCC->5V eksternal, GND common")
        sys.exit(1)

    try:
        if args.mode == "sweep":
            mode_sweep(servo, args.cycles)
        elif args.mode == "toggle":
            mode_toggle(servo, args.cycles)
        elif args.mode == "angle":
            mode_angle(servo, args.angle, args.duration)
    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user")
    finally:
        try:
            servo.angle = config.SERVO_ANGLE_CLOSED
            time.sleep(0.5)
            servo.close()
        except Exception:
            pass
        print("Servo distop, posisi TUTUP.")


if __name__ == "__main__":
    main()
