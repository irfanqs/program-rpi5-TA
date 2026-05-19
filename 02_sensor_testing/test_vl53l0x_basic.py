#!/usr/bin/env python3
"""
Tes dasar sensor Time of Flight VL53L0X.

Membaca jarak mentah (mm) secara terus-menerus dari sensor.
Pakai ini untuk verifikasi:
1. Wiring I2C sudah benar (SDA pin 3, SCL pin 5, VCC 3.3V, GND)
2. I2C sudah enable di raspi-config
3. Sensor mendapat alamat I2C 0x29

Sebelum jalankan, cek alamat I2C di terminal:
    sudo i2cdetect -y 1
Harus muncul angka "29" di kolom 9 baris 20.

Jalankan:
    python3 test_vl53l0x_basic.py
    python3 test_vl53l0x_basic.py --samples 100   # 100 kali baca lalu berhenti
    python3 test_vl53l0x_basic.py --interval 0.1  # interval 100ms
"""
import argparse
import sys
import time
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def init_sensor():
    """Inisialisasi sensor VL53L0X via Adafruit Blinka."""
    try:
        import board
        import busio
        import adafruit_vl53l0x
    except ImportError as e:
        print("[ERROR] Library tidak terinstal.")
        print("Install dengan:")
        print("  pip install adafruit-blinka adafruit-circuitpython-vl53l0x")
        raise e

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_vl53l0x.VL53L0X(i2c)

    # Set measurement timing budget (lebih lama = lebih akurat, lebih lambat)
    # Default 33000us, range 20000-200000
    sensor.measurement_timing_budget = 50000  # 50ms per pembacaan

    return sensor


def main():
    parser = argparse.ArgumentParser(description="Tes baca VL53L0X")
    parser.add_argument("--samples", type=int, default=0,
                        help="Jumlah sample (0 = loop tak terbatas)")
    parser.add_argument("--interval", type=float, default=0.2,
                        help="Interval baca (detik)")
    parser.add_argument("--quiet", action="store_true",
                        help="Hanya tampilkan ringkasan di akhir")
    args = parser.parse_args()

    print("=" * 50)
    print("VL53L0X Distance Sensor Test")
    print("=" * 50)

    try:
        sensor = init_sensor()
        print(f"[OK] Sensor terdeteksi di I2C address 0x{config.VL53L0X_I2C_ADDR:02X}")
        print(f"Timing budget: {sensor.measurement_timing_budget} us")
        print("\nTekan Ctrl+C untuk berhenti.\n")
    except Exception as e:
        print(f"[ERROR] Gagal inisialisasi sensor: {e}")
        print("\nTroubleshooting:")
        print("  1. Cek wiring: SDA->pin3, SCL->pin5, VCC->pin1 (3.3V), GND->pin6")
        print("  2. Cek I2C aktif: sudo raspi-config -> Interface -> I2C -> Enable")
        print("  3. Scan I2C: sudo i2cdetect -y 1 (harus muncul 0x29)")
        sys.exit(1)

    readings = []
    count = 0
    t_start = time.time()

    try:
        while True:
            try:
                d_mm = sensor.range
                readings.append(d_mm)
                if not args.quiet:
                    bar = "#" * min(int(d_mm / 10), 50)
                    print(f"  [{count+1:4d}]  {d_mm:5d} mm  |{bar}")
            except Exception as e:
                print(f"  [{count+1:4d}]  ERROR: {e}")

            count += 1
            if args.samples > 0 and count >= args.samples:
                break
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user")

    elapsed = time.time() - t_start

    if readings:
        print("\n" + "=" * 50)
        print("RINGKASAN STATISTIK")
        print("=" * 50)
        print(f"  Jumlah sample : {len(readings)}")
        print(f"  Durasi        : {elapsed:.1f} s")
        print(f"  Rate          : {len(readings)/elapsed:.1f} Hz")
        print(f"  Min           : {min(readings)} mm")
        print(f"  Max           : {max(readings)} mm")
        print(f"  Mean          : {mean(readings):.1f} mm")
        if len(readings) > 1:
            print(f"  Std dev       : {stdev(readings):.1f} mm")
        print("=" * 50)


if __name__ == "__main__":
    main()
