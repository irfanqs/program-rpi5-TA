# Program Raspberry Pi 5 — Sistem Penyerbuk Kelapa Sawit

Kumpulan program untuk TA "Pengembangan Sistem Penyerbuk Kelapa Sawit dengan Monitoring Volume Pollen secara Real-Time untuk Integrasi pada Drone".

Author: Irfan Qobus Salim (5027221058)
Target device: Raspberry Pi 5 Model B 4GB RAM, Raspberry Pi OS 64-bit (Bookworm)

## Struktur folder

```
program-rpi5/
├── README.md                       # File ini
├── requirements.txt                # Dependency Python
├── setup_pi.sh                     # Skrip setup awal Pi (jalankan sekali)
├── config.py                       # Konfigurasi global (pin, threshold, path)
│
├── 01_yolo_detection/              # Program deteksi YOLO
│   ├── detect_yolov8.py            # Deteksi pakai YOLOv8
│   ├── detect_yolov9.py            # Deteksi pakai YOLOv9
│   ├── detect_yolov10.py           # Deteksi pakai YOLOv10
│   ├── detect_yolov11.py           # Deteksi pakai YOLOv11
│   ├── detect_yolo26.py            # Deteksi pakai YOLO26 (placeholder, lihat catatan)
│   ├── detect_generic.py           # Universal — pilih versi via argumen
│   ├── benchmark_yolo_versions.py  # Bandingkan FPS & mAP semua versi
│   └── export_to_ncnn.py           # Export .pt ke NCNN/ONNX (run di laptop/Colab)
│
├── 02_sensor_testing/              # Tes sensor VL53L0X
│   ├── test_vl53l0x_basic.py       # Baca jarak mentah
│   ├── calibrate_vl53l0x.py        # Kalibrasi tabung (kosong vs penuh)
│   └── test_vl53l0x_volume.py      # Konversi jarak -> volume pollen
│
├── 03_hardware_control/            # Kontrol aktuator
│   ├── test_camera.py              # Verifikasi Pi Camera / USB Cam
│   ├── test_servo.py               # Buka-tutup katup servo
│   ├── test_blower_fan.py          # PWM blower fan via MOSFET
│   └── test_all_hardware.py        # Tes berurutan semua hardware
│
└── 04_integration/                 # Sistem terpadu
    ├── pollination_system.py       # Main loop end-to-end
    ├── state_machine.py            # State machine penyemprotan
    └── logger.py                   # Logging event ke CSV
```

## Quick start

### 1. Setup awal Pi (sekali saja)

```bash
chmod +x setup_pi.sh
./setup_pi.sh
```

Script ini akan:
- Update sistem
- Install dependency apt (i2c-tools, python3-pip, libcamera-apps)
- Enable I2C, Camera, SPI
- Buat virtualenv di `~/ta-env`
- Install dependency Python dari `requirements.txt`

### 2. Aktifkan virtualenv tiap session

```bash
source ~/ta-env/bin/activate
```

### 3. Tes komponen satu per satu (urutan disarankan)

```bash
# Tes kamera dulu (pastikan Pi Camera/USB cam berfungsi)
python3 03_hardware_control/test_camera.py

# Tes sensor VL53L0X
python3 02_sensor_testing/test_vl53l0x_basic.py

# Tes servo
python3 03_hardware_control/test_servo.py

# Tes blower fan (setelah datang)
python3 03_hardware_control/test_blower_fan.py

# Tes deteksi YOLO (sesuaikan path model di config.py)
python3 01_yolo_detection/detect_yolov8.py
```

### 4. Benchmark semua versi YOLO

```bash
python3 01_yolo_detection/benchmark_yolo_versions.py
```

Output berupa tabel FPS, latency, dan ukuran model untuk tiap versi YOLO. Hasil dipakai untuk Bab 4 laporan (memilih model optimal di Pi 5).

### 5. Jalankan sistem terpadu

```bash
python3 04_integration/pollination_system.py
```

Sistem akan loop: kamera → YOLO → cek ToF → servo buka → blower on → tutup. Semua event tercatat di `logs/pollination_log.csv`.

## Catatan penting

- **Path model YOLO**: edit `config.py` → `MODEL_PATHS` agar menunjuk ke file `best.pt` / folder `best_ncnn_model` masing-masing versi.
- **YOLO26**: Ultralytics belum merilis YOLOv26 secara resmi sampai dokumen ini ditulis (mengacu pada hierarchy YOLOv8–v11). Skrip `detect_yolo26.py` disiapkan sebagai placeholder yang otomatis fallback ke YOLOv11 jika YOLO26 tidak tersedia. Update saat versi resminya keluar.
- **Daya servo & blower**: JANGAN ambil daya dari pin 5V Pi langsung. Pakai BEC/regulator terpisah dari Li-Po, GND harus common dengan Pi.
- **Pinout**: semua pin GPIO didefinisikan di `config.py`. Ubah di satu tempat saja.

## Pinout ringkas

| Komponen        | Pin Pi 5 (BCM) | Pin Fisik |
|-----------------|----------------|-----------|
| VL53L0X SDA     | GPIO 2 (SDA1)  | 3         |
| VL53L0X SCL     | GPIO 3 (SCL1)  | 5         |
| Servo signal    | GPIO 18 (PWM0) | 12        |
| Blower MOSFET   | GPIO 13 (PWM1) | 33        |
| Status LED      | GPIO 25        | 22        |

3.3V Pi (Pin 1) hanya untuk VL53L0X. Servo & blower pakai daya eksternal.
