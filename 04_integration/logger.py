"""
Logger event untuk sistem penyerbukan.

Mencatat tiap deteksi & penyemprotan ke CSV supaya bisa dianalisis di
Bab 4 laporan TA.

Kolom CSV:
- timestamp        : ISO datetime
- event            : DETECTION / SPRAY / READY / ERROR
- yolo_version     : versi YOLO yang dipakai
- class_name       : nama kelas terdeteksi
- confidence       : confidence skor
- distance_mm      : pembacaan sensor ToF
- volume_ml        : volume pollen hasil konversi
- pollen_enough    : True/False (di atas threshold?)
- sprayed          : True kalau spray dieksekusi
- notes            : catatan tambahan
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional


class EventLogger:
    FIELDS = [
        "timestamp",
        "event",
        "yolo_version",
        "class_name",
        "confidence",
        "distance_mm",
        "volume_ml",
        "pollen_enough",
        "sprayed",
        "notes",
    ]

    def __init__(self, csv_path: Path):
        self.path = Path(csv_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Tulis header kalau file baru
        if not self.path.exists() or self.path.stat().st_size == 0:
            with open(self.path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                writer.writeheader()

    def log(self, event: str,
            yolo_version: str = "",
            class_name: str = "",
            confidence: float = 0.0,
            distance_mm: Optional[float] = None,
            volume_ml: Optional[float] = None,
            pollen_enough: Optional[bool] = None,
            sprayed: bool = False,
            notes: str = ""):
        row = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "event": event,
            "yolo_version": yolo_version,
            "class_name": class_name,
            "confidence": round(confidence, 3),
            "distance_mm": "" if distance_mm is None else round(distance_mm, 1),
            "volume_ml": "" if volume_ml is None else round(volume_ml, 3),
            "pollen_enough": "" if pollen_enough is None else pollen_enough,
            "sprayed": sprayed,
            "notes": notes,
        }
        with open(self.path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writerow(row)

    def info(self, msg: str):
        """Tulis catatan umum."""
        self.log(event="INFO", notes=msg)
