#!/usr/bin/env python3
"""
Konversi pembacaan ToF -> volume pollen real-time.

Memakai nilai kalibrasi (TOF_DISTANCE_EMPTY_MM, TOF_DISTANCE_FULL_MM)
dan dimensi tabung (TUBE_AREA_MM2) dari config.py.

Output:
- Jarak (mm)
- Tinggi pollen di tabung (mm)
- Volume (mm^3 dan mL)
- Persen terhadap kapasitas maksimum
- Status: CUKUP / KURANG (berdasar VOLUME_MIN_THRESHOLD_MM3)

Termasuk moving average filter untuk meredam noise sensor (sesuai
proposal Bab 2.2.6).

Jalankan:
    python3 test_vl53l0x_volume.py
    python3 test_vl53l0x_volume.py --window 10   # window moving avg
"""
import argparse
import sys
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def distance_to_volume(d_mm: float) -> dict:
    """Konversi jarak ToF ke berbagai metrik volume."""
    # Tinggi pollen di tabung = jarak_kosong - jarak_terbaca
    pollen_height = max(0, config.TOF_DISTANCE_EMPTY_MM - d_mm)
    pollen_height = min(pollen_height,
                        config.TOF_DISTANCE_EMPTY_MM - config.TOF_DISTANCE_FULL_MM)

    volume_mm3 = pollen_height * config.TUBE_AREA_MM2
    volume_ml = volume_mm3 / 1000.0

    max_height = config.TOF_DISTANCE_EMPTY_MM - config.TOF_DISTANCE_FULL_MM
    percent = (pollen_height / max_height * 100) if max_height > 0 else 0

    return {
        "distance_mm": d_mm,
        "pollen_height_mm": pollen_height,
        "volume_mm3": volume_mm3,
        "volume_ml": volume_ml,
        "percent": percent,
        "is_enough": volume_mm3 >= config.VOLUME_MIN_THRESHOLD_MM3,
    }


def print_status(metrics: dict, raw: int):
    """Visualisasi status di terminal."""
    bar_len = 30
    filled = int(metrics["percent"] / 100 * bar_len)
    bar = "#" * filled + "-" * (bar_len - filled)
    status = "CUKUP " if metrics["is_enough"] else "KURANG"
    color = "\033[32m" if metrics["is_enough"] else "\033[31m"
    print(f"  raw={raw:4d}mm  height={metrics['pollen_height_mm']:5.1f}mm  "
          f"vol={metrics['volume_ml']:5.2f}mL  [{bar}] {metrics['percent']:5.1f}%  "
          f"{color}{status}\033[0m")


def main():
    parser = argparse.ArgumentParser(description="Konversi ToF -> volume pollen")
    parser.add_argument("--window", type=int, default=5,
                        help="Window size untuk moving average (default 5)")
    parser.add_argument("--interval", type=float, default=0.3)
    parser.add_argument("--samples", type=int, default=0,
                        help="Total sample (0 = loop)")
    args = parser.parse_args()

    print("=" * 70)
    print("Konversi VL53L0X -> Volume Pollen")
    print("=" * 70)
    print(f"  Kalibrasi : kosong={config.TOF_DISTANCE_EMPTY_MM}mm  "
          f"penuh={config.TOF_DISTANCE_FULL_MM}mm")
    print(f"  Tabung    : diameter={config.TUBE_DIAMETER_MM}mm  "
          f"area={config.TUBE_AREA_MM2:.1f}mm^2")
    print(f"  Threshold : {config.VOLUME_MIN_THRESHOLD_MM3} mm^3 "
          f"(~{config.VOLUME_MIN_THRESHOLD_MM3/1000:.2f} mL)")
    print(f"  Moving avg window: {args.window}")
    print("=" * 70 + "\n")

    try:
        import board, busio, adafruit_vl53l0x
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        sensor.measurement_timing_budget = 50000
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    window = deque(maxlen=args.window)
    count = 0

    try:
        while True:
            try:
                raw = sensor.range
                window.append(raw)
                smoothed = sum(window) / len(window)
                metrics = distance_to_volume(smoothed)
                print_status(metrics, raw)
            except Exception as e:
                print(f"  ERROR: {e}")

            count += 1
            if args.samples > 0 and count >= args.samples:
                break
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user.")


if __name__ == "__main__":
    main()
