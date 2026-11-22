"""
BabyJev: capture -> detect -> decide -> act -> telemetry.

Defaults to DRY RUN: it logs decisions instead of clicking. Flip dry_run in
config.json ONLY for singleplayer or private worlds you own. Never point this
at public servers; the point is learning, not outcomes.

Modes:
    python triggerbot.py --self-test         # synthetic frames, no game
    python triggerbot.py --dry-run           # live capture, logged, never clicks
    python triggerbot.py                     # fighting mode: your worlds only
Eyes need training first: python train.py   (creates weights/babyjev_mobs.pt)
"""

import argparse
import csv
import json
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from yolo_detector import YoloDetector
except ImportError:
    YoloDetector = None  # ultralytics not needed for self-test / stub modes


# ---------------------------------------------------------------- detection

@dataclass
class Detection:
    """One entity seen by the detector, in frame pixel coordinates."""
    cx: float
    cy: float
    h: float
    confidence: float


class BrightBlobDetector:
    """Self-test detector: finds the brightest blob in a synthetic frame."""

    def detect(self, frame):
        import numpy as np
        grey = frame.mean(axis=2)
        peak = grey.max()
        if peak < 200:
            return None
        ys, xs = np.where(grey >= 200)
        cx = xs.mean()
        cy = ys.mean()
        h = max(40.0, float(ys.max() - ys.min()) + 30.0)
        return Detection(cx=cx, cy=cy, h=h, confidence=float(peak) / 255.0)


class HeuristicDetector:
    """Placeholder from Phase 1. Kept for reference; Phase 2 uses YoloDetector
    once train.py has produced weights/babyjev_mobs.pt."""

    def detect(self, frame):
        return None


# -------------------------------------------------------------- frame source

class ScreenSource:
    """Region capture around the crosshair via dxcam, mss fallback."""

    def __init__(self, region_ratio=0.25):
        import ctypes
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        w = int(sw * region_ratio)
        h = int(sh * region_ratio)
        self.region = ((sw - w) // 2, (sh - h) // 2, (sw + w) // 2, (sh + h) // 2)
        self.shape = (h, w)  # known from the region, no first frame needed
        self._cam = None
        self._sct = None
        try:
            import dxcam
            self._cam = dxcam.create(output_color="BGR", region=self.region, max_buffer_len=2)
            self.backend = "dxcam"
        except Exception:
            import mss
            self._sct = mss.mss()
            self.backend = "mss"

    def grab(self):
        t0 = time.perf_counter()
        if self._cam is not None:
            frame = self._cam.grab()
        else:
            import numpy as np
            left, top, right, bottom = self.region
            m = {"left": left, "top": top, "width": right - left, "height": bottom - top}
            frame = np.asarray(self._sct.grab(m))[:, :, :3]
        dt = (time.perf_counter() - t0) * 1000.0
        if frame is None:
            return None, dt
        return frame, dt


class SelfTestSource:
    """Synthetic frames: a bright blob near centre 80% of the time."""

    def __init__(self):
        self.shape = (480, 640)

    def grab(self):
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        if random.random() < 0.8:
            cx = 320 + random.randint(-30, 30)
            cy = 240 + random.randint(-20, 20)
            frame[cy - 4:cy + 4, cx - 4:cx + 4] = 255
        return frame, 0.2


# -------------------------------------------------------------- actuator

class Actuator:
    """One click. In dry run it only logs."""

    def __init__(self, dry_run=True, jitter_ms=8):
        self.dry_run = dry_run
        self.jitter_ms = jitter_ms
        self._mouse = None
        if not dry_run:
            from pynput.mouse import Controller
            self._mouse = Controller()

    def click(self):
        if self.jitter_ms:
            # Human-ish timing: stop being a metronome.
            time.sleep(random.uniform(0, self.jitter_ms) / 1000.0)
        if self.dry_run:
            return "dry-click"
        self._mouse.click(button="left", count=1)
        return "click"


# ------------------------------------------------------------ decision loop

class DecisionLoop:
    def __init__(self, cfg, detector, actuator, csv_path):
        self.cfg = cfg
        self.detector = detector
        self.actuator = actuator
        self.next_attack_allowed = 0.0
        self.source_shape = None
        self.stats = {"frames": 0, "detections": 0, "clicks": 0, "totals": []}
        self.csv_path = Path(csv_path)
        Path("logs").mkdir(exist_ok=True)
        self._fh = self.csv_path.open("w", newline="")
        self._csv = csv.writer(self._fh)
        self._csv.writerow(["ts", "capture_ms", "detect_ms", "decide_ms", "act_ms", "total_ms", "result"])

    def decide(self, detection):
        """The Jev moment. Three checks, no narration."""
        if self.source_shape is None or detection is None:
            return None
        h, w = self.source_shape
        centre_x, centre_y = w / 2.0, h / 2.0
        offset = ((detection.cx - centre_x) ** 2 + (detection.cy - centre_y) ** 2) ** 0.5
        if offset > self.cfg["trigger_radius_px"]:
            return None
        if detection.h < self.cfg["min_bbox_height_px"]:
            return None
        now = time.perf_counter()
        if now < self.next_attack_allowed:
            return None
        interval = max(1.0 / self.cfg["max_cps"], self.cfg["attack_cooldown_s"])
        self.next_attack_allowed = now + interval
        return "fire"

    def run(self, source, seconds=None):
        if source.shape:
            self.source_shape = source.shape
        t_end = time.perf_counter() + seconds if seconds else None
        try:
            while True:
                frame, capture_ms = source.grab()
                if frame is None:
                    continue
                if self.source_shape is None:
                    self.source_shape = frame.shape[:2]
                t0 = time.perf_counter()
                detection = self.detector.detect(frame)
                decide_in = time.perf_counter()
                result = self.decide(detection)
                t_decide = time.perf_counter()
                act_result = self.actuator.click() if result == "fire" else None
                act_ms = (time.perf_counter() - t_decide) * 1000.0
                detect_ms = (decide_in - t0) * 1000.0
                decide_ms = (t_decide - decide_in) * 1000.0
                total_ms = detect_ms + decide_ms + act_ms + capture_ms

                self.stats["frames"] += 1
                if detection is not None:
                    self.stats["detections"] += 1
                if act_result:
                    self.stats["clicks"] += 1
                self.stats["totals"].append(total_ms)
                self._csv.writerow([round(time.time(), 3), round(capture_ms, 2),
                                    round(detect_ms, 2), round(decide_ms, 2),
                                    round(act_ms, 2), round(total_ms, 2),
                                    result or ""])

                if t_end and time.perf_counter() >= t_end:
                    break
                if not t_end and self.stats["frames"] % 240 == 0:
                    self.report()
        except KeyboardInterrupt:
            print()
        self.report(final=True)
        self._fh.close()

    def report(self, final=False):
        s = self.stats
        if not s["frames"]:
            return
        mean_total = statistics.fmean(s["totals"][-240:])
        fps_cap = 1000.0 / mean_total if mean_total else 0.0
        tag = "final" if final else "progress"
        print("[" + tag + "] frames:", s["frames"],
              "detections:", s["detections"],
              "clicks:", s["clicks"],
              "mean loop:", round(mean_total, 2), "ms",
              "(" + str(round(fps_cap, 1)) + " Hz ceiling)")


def main():
    ap = argparse.ArgumentParser(description="BabyJev reflex loop")
    ap.add_argument("--self-test", action="store_true", help="synthetic frames, no game")
    ap.add_argument("--dry-run", action="store_true", help="force dry run (also config default)")
    ap.add_argument("--seconds", type=float, default=None, help="stop after N seconds")
    ap.add_argument("--weights", default=None, help="path to YOLO weights (default: config)")
    args = ap.parse_args()

    cfg = json.loads(Path("config.json").read_text())
    if args.dry_run:
        cfg["dry_run"] = True

    weights = args.weights or cfg.get("yolo_weights", "")
    have_weights = bool(weights) and Path(weights).exists()

    if args.self_test:
        source = SelfTestSource()
        detector = BrightBlobDetector()
        print("Self-test: synthetic frames, full loop, dry-run clicks only.")
    elif have_weights and YoloDetector is not None:
        source = ScreenSource(cfg["capture_region_ratio"])
        detector = YoloDetector(
            weights=weights,
            target_classes=cfg.get("target_classes"),
            conf=cfg.get("yolo_conf", 0.55),
            imgsz=cfg.get("yolo_imgsz", 320),
        )
        print("Live capture via", source.backend, "with trained eyes.")
    else:
        source = ScreenSource(cfg["capture_region_ratio"])
        detector = HeuristicDetector()
        print("Live capture via", source.backend, "- no trained eyes found.")
        if weights:
            print("Missing weights file:", weights)
        print("Train them once with: python train.py")

    actuator = Actuator(dry_run=cfg["dry_run"], jitter_ms=cfg["jitter_ms"])
    loop = DecisionLoop(cfg, detector, actuator, cfg["telemetry_csv"])
    print("dry_run:", cfg["dry_run"], "; telemetry:", cfg["telemetry_csv"])
    print("Ctrl+C to stop.")
    loop.run(source, seconds=args.seconds)


if __name__ == "__main__":
    main()
