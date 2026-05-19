"""
State machine sistem penyerbukan.

States:
- IDLE          : sistem standby, kamera streaming, YOLO running
- DETECTING     : objek terdeteksi (confidence di atas threshold)
- VERIFY_POLLEN : cek volume pollen via ToF
- SPRAYING      : katup terbuka & blower nyala
- COOLDOWN      : jeda setelah semprot supaya tidak retrigger
- INSUFFICIENT  : pollen kurang, sistem berhenti / pindah pohon
- ERROR         : ada error, butuh intervensi

Transitions diatur supaya proses penyerbukan otomatis, terkontrol,
dan efisien sesuai proposal Bab 3.1.6.
"""
from enum import Enum, auto
import time


class State(Enum):
    IDLE = auto()
    DETECTING = auto()
    VERIFY_POLLEN = auto()
    SPRAYING = auto()
    COOLDOWN = auto()
    INSUFFICIENT = auto()
    ERROR = auto()


class PollinationStateMachine:
    """Manage state transitions untuk sistem penyerbukan."""

    def __init__(self, config_module):
        self.cfg = config_module
        self.state = State.IDLE
        self.last_transition_t = time.time()
        self.consecutive_detections = 0
        self.spray_count = 0
        self.last_volume_ml = 0.0

    def transition_to(self, new_state: State, reason: str = ""):
        if self.state != new_state:
            print(f"  [STATE] {self.state.name} -> {new_state.name}  ({reason})")
        self.state = new_state
        self.last_transition_t = time.time()

    def time_in_state(self) -> float:
        return time.time() - self.last_transition_t

    def update(self, *, detected: bool, confidence: float = 0.0,
               volume_ml: float = 0.0, distance_mm: float = 0.0):
        """
        Update state berdasarkan input deteksi & sensor.
        Return action dict: {"spray": bool, "open_valve": bool, "blower_duty": float}
        """
        action = {"spray": False, "open_valve": False, "blower_duty": 0.0}

        if detected:
            self.consecutive_detections += 1
        else:
            self.consecutive_detections = 0

        # -------- IDLE --------
        if self.state == State.IDLE:
            if (self.consecutive_detections >= self.cfg.MIN_DETECTION_FRAMES
                    and confidence >= self.cfg.CONF_THRESHOLD):
                self.transition_to(State.DETECTING,
                                   f"target detect {self.consecutive_detections}x")

        # -------- DETECTING --------
        elif self.state == State.DETECTING:
            # langsung lanjut ke verifikasi volume pollen
            self.transition_to(State.VERIFY_POLLEN, "cek volume pollen")

        # -------- VERIFY_POLLEN --------
        elif self.state == State.VERIFY_POLLEN:
            self.last_volume_ml = volume_ml
            volume_mm3 = volume_ml * 1000
            if volume_mm3 >= self.cfg.VOLUME_MIN_THRESHOLD_MM3:
                self.transition_to(State.SPRAYING,
                                   f"pollen cukup {volume_ml:.2f}mL")
            else:
                self.transition_to(State.INSUFFICIENT,
                                   f"pollen kurang {volume_ml:.2f}mL")

        # -------- SPRAYING --------
        elif self.state == State.SPRAYING:
            elapsed = self.time_in_state()
            if elapsed < self.cfg.SPRAY_DURATION_SEC:
                action["open_valve"] = True
                action["blower_duty"] = self.cfg.BLOWER_DUTY_DEFAULT
                action["spray"] = True
            else:
                self.spray_count += 1
                self.transition_to(State.COOLDOWN,
                                   f"selesai semprot #{self.spray_count}")

        # -------- COOLDOWN --------
        elif self.state == State.COOLDOWN:
            if self.time_in_state() >= self.cfg.COOLDOWN_AFTER_SPRAY_SEC:
                self.transition_to(State.IDLE, "cooldown selesai")

        # -------- INSUFFICIENT --------
        elif self.state == State.INSUFFICIENT:
            # Tetap di state ini sampai user reset / refill
            # (sinyal: drone diarahkan ke pohon lain / return-to-home)
            if self.time_in_state() > 5.0:
                # auto reset setelah 5 detik supaya tidak stuck
                self.transition_to(State.IDLE, "auto-reset insufficient")

        # -------- ERROR --------
        elif self.state == State.ERROR:
            if self.time_in_state() > 3.0:
                self.transition_to(State.IDLE, "auto-recover dari error")

        return action

    def force_error(self, reason: str):
        self.transition_to(State.ERROR, f"ERROR: {reason}")

    def summary(self) -> dict:
        return {
            "current_state": self.state.name,
            "spray_count": self.spray_count,
            "last_volume_ml": self.last_volume_ml,
        }
