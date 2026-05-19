"""
Konfigurasi global Sistem Penyerbuk Kelapa Sawit.
Semua pin, threshold, dan path model di-define di sini supaya
mudah diubah dari satu tempat.
"""
from pathlib import Path

# ============================================================
# PATH
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"          # taruh file .pt / folder NCNN di sini
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Path model untuk tiap versi YOLO.
# Ubah ke path file/folder model hasil training Anda.
MODEL_PATHS = {
    "yolov8":  str(MODELS_DIR / "yolov8_best.pt"),
    "yolov9":  str(MODELS_DIR / "yolov9_best.pt"),
    "yolov10": str(MODELS_DIR / "yolov10_best.pt"),
    "yolov11": str(MODELS_DIR / "yolov11_best.pt"),
    "yolo26":  str(MODELS_DIR / "yolo26_best.pt"),  # fallback ke yolov11 kalau belum ada
}

# Versi NCNN (lebih cepat di Pi 5) — kalau sudah di-export.
MODEL_PATHS_NCNN = {
    "yolov8":  str(MODELS_DIR / "yolov8_best_ncnn_model"),
    "yolov9":  str(MODELS_DIR / "yolov9_best_ncnn_model"),
    "yolov10": str(MODELS_DIR / "yolov10_best_ncnn_model"),
    "yolov11": str(MODELS_DIR / "yolov11_best_ncnn_model"),
    "yolo26":  str(MODELS_DIR / "yolo26_best_ncnn_model"),
}

# ============================================================
# GPIO PIN (BCM numbering)
# ============================================================
# Sensor VL53L0X (I2C bus 1 — pin fix di Pi)
PIN_I2C_SDA = 2   # Pin fisik 3
PIN_I2C_SCL = 3   # Pin fisik 5
VL53L0X_I2C_ADDR = 0x29

# Servo motor (PWM)
PIN_SERVO = 18    # Pin fisik 12, hardware PWM0
SERVO_FREQ_HZ = 50
SERVO_ANGLE_CLOSED = 0     # derajat
SERVO_ANGLE_OPEN = 90      # derajat

# Blower fan via MOSFET (PWM)
PIN_BLOWER = 13   # Pin fisik 33, hardware PWM1
BLOWER_FREQ_HZ = 1000
BLOWER_DUTY_DEFAULT = 80   # persen (0-100)

# Status LED (opsional, indikator state)
PIN_STATUS_LED = 25

# ============================================================
# KAMERA
# ============================================================
CAMERA_SOURCE = 0          # 0 = USB cam default; ganti string path untuk Pi Camera
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
USE_PICAMERA2 = False      # True kalau pakai modul Pi Camera (libcamera)

# ============================================================
# YOLO INFERENSI
# ============================================================
IMG_SIZE = 320             # 320 untuk speed di Pi 5, 640 untuk akurasi
CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45
TARGET_CLASS = "matang"    # nama kelas bunga betina reseptif (sesuaikan dengan dataset)
DEVICE = "cpu"             # Pi 5 tanpa GPU; gunakan "cpu"

# ============================================================
# TABUNG POLLEN (untuk konversi ToF -> volume)
# ============================================================
# Dimensi tabung (sesuaikan dengan desain 3D Anda)
TUBE_DIAMETER_MM = 40.0        # diameter dalam tabung
TUBE_HEIGHT_MM = 80.0          # tinggi tabung
TUBE_AREA_MM2 = 3.14159 * (TUBE_DIAMETER_MM / 2) ** 2

# Hasil kalibrasi (di-update via calibrate_vl53l0x.py)
TOF_DISTANCE_EMPTY_MM = 80     # jarak ToF saat tabung kosong
TOF_DISTANCE_FULL_MM = 10      # jarak ToF saat tabung penuh

# Threshold volume minimum untuk boleh menyemprot (mm^3)
VOLUME_MIN_THRESHOLD_MM3 = 5000   # ~5 mL — sesuaikan dengan kebutuhan

# ============================================================
# LOGIKA PENYEMPROTAN
# ============================================================
SPRAY_DURATION_SEC = 2.0        # lama katup terbuka + blower nyala
COOLDOWN_AFTER_SPRAY_SEC = 3.0  # jeda sebelum siap mendeteksi lagi
MIN_DETECTION_FRAMES = 3        # objek harus terdeteksi N frame berturut-turut

# ============================================================
# LOGGING
# ============================================================
LOG_CSV_PATH = LOGS_DIR / "pollination_log.csv"
LOG_VIDEO_PATH = LOGS_DIR / "session.mp4"
SAVE_VIDEO = False
