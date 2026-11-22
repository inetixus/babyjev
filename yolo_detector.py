"""
BabyJev Phase 2: real eyes.

Wraps an Ultralytics YOLO model (built by train.py) and speaks the same
protocol as the stub detectors: detect(frame) -> Detection-shaped or None,
so the decision loop never changes.
"""

from dataclasses import dataclass


@dataclass
class Detection:
    """Same shape as triggerbot.Detection; the loop duck-types it."""
    cx: float
    cy: float
    h: float
    confidence: float


class YoloDetector:
    def __init__(self, weights, target_classes=None, conf=0.55, imgsz=320):
        import torch
        from ultralytics import YOLO

        self.model = YOLO(weights)
        self.conf = conf
        self.imgsz = imgsz
        self.device = 0 if torch.cuda.is_available() else "cpu"
        self.half = bool(self.device == 0)

        names = self.model.names or {}
        pairs = list(names.items()) if isinstance(names, dict) else list(enumerate(names))
        wanted = set(target_classes or [])
        self.class_ids = [i for i, n in pairs if n in wanted] or None
        if self.class_ids is None and wanted:
            print("[yolo] warning: none of", sorted(wanted), "matched model classes:",
                  [n for _, n in pairs])
            print("[yolo] falling back to watching ALL classes")
        used = [n for i, n in pairs if self.class_ids is None or i in self.class_ids]
        print("[yolo] eyes:", weights)
        print("[yolo] watching:", used, "| conf >=", conf,
              "| imgsz", imgsz, "| device", self.device)

    def detect(self, frame):
        r = self.model.predict(
            frame,
            imgsz=self.imgsz,
            conf=self.conf,
            classes=self.class_ids,
            verbose=False,
            device=self.device,
            half=self.half,
        )[0]
        best, best_conf = None, 0.0
        for box in r.boxes:
            c = float(box.conf)
            if c > best_conf:
                best, best_conf = box, c
        if best is None:
            return None
        x1, y1, x2, y2 = [float(v) for v in best.xyxy[0]]
        return Detection(cx=(x1 + x2) / 2.0, cy=(y1 + y2) / 2.0,
                         h=y2 - y1, confidence=best_conf)
