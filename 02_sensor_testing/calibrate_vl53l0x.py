#!/usr/bin/env python3
"""
Kalibrasi sensor VL53L0X untuk tabung pollen.

Tujuan: tentukan dua nilai referensi yang dibutuhkan untuk konversi
jarak ToF -> volume pollen:
- TOF_DISTANCE_EMPTY_MM: jarak yang dibaca sensor saat tabung KOSONG
- TOF_DISTANCE_FULL_MM : jarak yang dibaca sensor saat tabung PENUH

Hasil ditampilkan dan diberikan saran nilai untuk ditulis ulang di
config.py.

Prosedur:
1. Pasang sensor di tutup atas tabung (menghadap ke bawah).
2. Jalankan skrip, ikuti prompt yang muncul.
3. Salin nilai yang disarankan ke config.py.

Jalankan:
    python3 calibrate_vl53l0x.py
    python3 calibrate_vl53l0x.py --samples 50   # 50 pembacaan per kondisi
"""
import argparse
import sys
import time
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def capture_readings(sensor, n_samples: int, label: str):
    """Ambil n_samples pembacaan dan return mean."""
    print(f"\n[{label}]")
    print(f"Mengambil {n_samples} sample...")

    readings = []
    for i in range(n_samples):
        try:
            d = sensor.range
            readings.append(d)
            if (i + 1) % 10 == 0:
                print(f"  Sample {i+1}/{n_samples}: terakhir={d} mm  "
                      f"avg-so-far={mean(readings):.1f} mm")
        except Exception as e:
            print(f"  Sample {i+1}/{n_samples}: ERROR {e}")
        time.sleep(0.1)

    if not readings:
        return None

    m = mean(readings)
    s = stdev(readings) if len(readings) > 1 else 0
    print(f"\n  Hasil [{label}]:")
    print(f"    Mean   : {m:.1f} mm")
    print(f"    Std    : {s:.1f} mm")
    print(f"    Min/Max: {min(readings)}/{max(readings)} mm")
    return m, s


def main():
    parser = argparse.ArgumentParser(description="Kalibrasi VL53L0X untuk tabung pollen")
    parser.add_argument("--samples", type=int, default=30,
                        help="Sample per kondisi (default 30)")
    args = parser.parse_args()

    print("=" * 60)
    print("KALIBRASI SENSOR VL53L0X UNTUK TABUNG POLLEN")
    print("=" * 60)

    try:
        import board, busio, adafruit_vl53l0x
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        sensor.measurement_timing_budget = 50000
        print(f"[OK] Sensor terdeteksi di 0x{config.VL53L0X_I2C_ADDR:02X}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\nKonfigurasi tabung saat ini (dari config.py):")
    print(f"  Diameter dalam : {config.TUBE_DIAMETER_MM} mm")
    print(f"  Tinggi         : {config.TUBE_HEIGHT_MM} mm")
    print(f"  Luas penampang : {config.TUBE_AREA_MM2:.1f} mm^2")

    # ----- Step 1: Tabung KOSONG -----
    input("\n>> Pastikan tabung KOSONG dan sensor terpasang di tutup atas.\n"
          "   Tekan Enter untuk mulai...")
    empty_mean, empty_std = capture_readings(sensor, args.samples, "TABUNG KOSONG")

    # ----- Step 2: Tabung PENUH -----
    input("\n>> Sekarang isi tabung PENUH dengan pollen (atau material penanda).\n"
          "   Tekan Enter untuk mulai...")
    full_mean, full_std = capture_readings(sensor, args.samples, "TABUNG PENUH")

    # ----- Hasil & saran -----
    print("\n" + "=" * 60)
    print("HASIL KALIBRASI")
    print("=" * 60)
    print(f"  TOF_DISTANCE_EMPTY_MM = {round(empty_mean)}")
    print(f"  TOF_DISTANCE_FULL_MM  = {round(full_mean)}")

    delta = empty_mean - full_mean
    print(f"\n  Rentang efektif sensor: {delta:.1f} mm")
    print(f"  Tinggi tabung config  : {config.TUBE_HEIGHT_MM} mm")

    if abs(delta - config.TUBE_HEIGHT_MM) > 10:
        print("\n  [WARN] Selisih besar antara rentang sensor dan tinggi tabung di config.")
        print("         Cek apakah TUBE_HEIGHT_MM di config.py sudah sesuai tabung Anda.")

    volume_max_ml = config.TUBE_AREA_MM2 * delta / 1000  # mm^3 -> mL
    print(f"  Volume maks usable    : {volume_max_ml:.1f} mL")

    print("\n>> SALIN nilai ini ke config.py:")
    print(f"   TOF_DISTANCE_EMPTY_MM = {round(empty_mean)}")
    print(f"   TOF_DISTANCE_FULL_MM  = {round(full_mean)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
