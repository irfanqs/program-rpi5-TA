#!/usr/bin/env bash
# ============================================================
# Setup awal Raspberry Pi 5 untuk TA Sistem Penyerbuk Kelapa Sawit
# Jalankan sekali setelah Pi OS terinstal.
#   chmod +x setup_pi.sh
#   ./setup_pi.sh
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[1/6] Update sistem...${NC}"
sudo apt update
sudo apt full-upgrade -y

echo -e "${GREEN}[2/6] Install paket apt yang dibutuhkan...${NC}"
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    i2c-tools \
    libcamera-apps \
    libcamera-dev \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    cmake \
    build-essential

echo -e "${GREEN}[3/6] Enable interface I2C, Camera, SPI...${NC}"
# raspi-config nonint melakukan konfigurasi tanpa GUI
sudo raspi-config nonint do_i2c 0       # 0 = enable
sudo raspi-config nonint do_camera 0    # 0 = enable (Pi OS legacy)
sudo raspi-config nonint do_spi 0       # opsional

echo -e "${GREEN}[4/6] Buat virtualenv di ~/ta-env...${NC}"
if [ ! -d "$HOME/ta-env" ]; then
    python3 -m venv ~/ta-env
fi

echo -e "${GREEN}[5/6] Install dependency Python ke virtualenv...${NC}"
source ~/ta-env/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r "$(dirname "$0")/requirements.txt"

echo -e "${GREEN}[6/6] Verifikasi instalasi...${NC}"
echo -e "${YELLOW}-- I2C devices terdeteksi:${NC}"
sudo i2cdetect -y 1 || true

echo -e "${YELLOW}-- Ultralytics version:${NC}"
python3 -c "import ultralytics; print(ultralytics.__version__)" || true

echo -e "${YELLOW}-- OpenCV version:${NC}"
python3 -c "import cv2; print(cv2.__version__)" || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup selesai!${NC}"
echo -e "${GREEN}Aktifkan env: source ~/ta-env/bin/activate${NC}"
echo -e "${GREEN}Reboot disarankan agar I2C/Camera aktif: sudo reboot${NC}"
echo -e "${GREEN}========================================${NC}"
