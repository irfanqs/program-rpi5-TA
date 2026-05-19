#!/usr/bin/env python3
"""
Tes blower fan via MOSFET (PWM speed control).

WIRING (low-side MOSFET, mis. IRLZ44N atau MOSFET module):
- Blower (+)            -> +7.4V (Li-Po 2S, langsung)
- Blower (-)            -> Drain MOSFET
- Source MOSFET         -> GND baterai (common dengan Pi GND)
- Gate MOSFET           -> GPIO 13 (Pin fisik 33) via resistor 220 ohm
- Gate -> GND           : pull-down resistor 10k ohm
- GND Pi <-> GND batt   : WAJIB common

PERINGATAN:
- Jangan colokkan blower fan langsung ke pin GPIO. Arus blower bisa
  10x lipat dari kemampuan GPIO (16 mA max).
- Pastikan MOSFET yang dipakai logic-level (gate threshold < 3.3V).
- Cek voltase blower sesuai (kalau blower 12V, perlu boost converter
  dari 7.4V Li-Po; atau pakai blower 6-12V wide range).

Mode tes:
- ramp     : naik bertahap 0% -> 100% -> 0%
- pulse    : on/off berulang
- duty     : tahan di duty cycle tertentu
- step     : naik 25%, 50%, 75%, 100% (tahan 2 detik di tiap step)

Jalankan:
    python3 test_blower_fan.py --mode step
    python3 test_blower_fan.py --mode ramp --cycles 2
    python3 test_blower_fan.py --mode duty --duty 70
    python3 test_blower_fan.py --mode pulse --cycles 5
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def init_pwm():
    """Inisialisasi PWM untuk blower fan."""
    try:
        from gpiozero import PWMOutputDevice
        from gpiozero import Device
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
        pwm = PWMOutputDevice(
            config.PIN_BLOWER,
            frequency=config.BLOWER_FREQ_HZ,
            initial_value=0.0,
        )
        return pwm, "gpiozero-lgpio"
    except Exception as e:
        print(f"[WARN] gpiozero+lgpio gagal: {e}")

    from gpiozero import PWMOutputDevice
    pwm = PWMOutputDevice(
        config.PIN_BLOWER,
        frequency=config.BLOWER_FREQ_HZ,
        initial_value=0.0,
    )
    return pwm, "gpiozero-default"


def mode_ramp(pwm, cycles: int):
    print(f"[RAMP] {cycles} siklus")
    for c in range(cycles):
        print(f"  Siklus {c+1}: 0% -> 100%")
        for duty in range(0, 101, 5):
            pwm.value = duty / 100.0
            print(f"    duty = {duty}%")
            time.sleep(0.3)
        print(f"  Siklus {c+1}: 100% -> 0%")
        for duty in range(100, -1, -5):
            pwm.value = duty / 100.0
            time.sleep(0.3)


def mode_pulse(pwm, cycles: int, on_sec: float = 1.0, off_sec: float = 1.0):
    print(f"[PULSE] {cycles}x ON({on_sec}s)/OFF({off_sec}s) @ "
          f"{config.BLOWER_DUTY_DEFAULT}%")
    for c in range(cycles):
        print(f"  {c+1}/{cycles}: ON")
        pwm.value = config.BLOWER_DUTY_DEFAULT / 100.0
        time.sleep(on_sec)
        print(f"  {c+1}/{cycles}: OFF")
        pwm.value = 0.0
        time.sleep(off_sec)


def mode_duty(pwm, duty: float, duration: float):
    print(f"[DUTY] Tahan di {duty}% selama {duration} detik")
    pwm.value = duty / 100.0
    time.sleep(duration)
    pwm.value = 0.0


def mode_step(pwm, hold: float = 2.0):
    print(f"[STEP] 25/50/75/100%, tiap step tahan {hold}s")
    for d in [25, 50, 75, 100, 0]:
        print(f"  duty = {d}%")
        pwm.value = d / 100.0
        time.sleep(hold)


def main():
    parser = argparse.ArgumentParser(description="Tes blower fan PWM")
    parser.add_argument("--mode", choices=["ramp", "pulse", "duty", "step"],
                        default="step")
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--duty", type=float, default=80,
                        help="Duty cycle untuk mode duty (0-100)")
    parser.add_argument("--duration", type=float, default=3.0)
    args = parser.parse_args()

    print("=" * 50)
    print(f"Tes Blower Fan (GPIO {config.PIN_BLOWER}, "
          f"{config.BLOWER_FREQ_HZ} Hz)")
    print("=" * 50)
    print("PENTING: pastikan MOSFET driver sudah terpasang.")
    print("Jangan jalankan dengan blower langsung ke GPIO!\n")

    try:
        pwm, backend = init_pwm()
        print(f"[OK] PWM siap via {backend}\n")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    try:
        if args.mode == "ramp":
            mode_ramp(pwm, args.cycles)
        elif args.mode == "pulse":
            mode_pulse(pwm, args.cycles)
        elif args.mode == "duty":
            mode_duty(pwm, args.duty, args.duration)
        elif args.mode == "step":
            mode_step(pwm)
    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user")
    finally:
        try:
            pwm.value = 0.0
            time.sleep(0.3)
            pwm.close()
        except Exception:
            pass
        print("Blower OFF.")


if __name__ == "__main__":
    main()
