"""
BabyJev Phase 2: one-shot trainer for the eyes.

Downloads the Minecraft mobs YOLO dataset (2,585 annotated screenshots:
creeper, skeleton, spider, zombie, enderman) from Hugging Face, fine-tunes
YOLO11n on your machine, and installs the result as weights/babyjev_mobs.pt.

You run this ONCE:
    python train.py                 # auto device (GPU if available)
    python train.py --device cpu    # force CPU (slow: hours)
    python train.py --epochs 15     # quicker, still decent

Notes:
- First run downloads the dataset (once) and yolo11n.pt (once).
- On a 4GB GPU: ~20-40 min for 25 epochs. On CPU: plan for hours.
- If pip cannot find a torch build for your Python version (3.15 is very
  new), install Python 3.12/3.13 alongside and run training with it.
"""

import argparse
import shutil
from pathlib import Path

REPO_ID = "Ivan711a/minecraft-mobs-yolo-dataset"
SRC_DIR = "minecraft_mobs_yolo"
CLASSES = ["creeper", "skeleton", "spider", "zombie", "enderman"]
LOCAL_DATASET = Path("dataset") / SRC_DIR
WEIGHTS_DIR = Path("weights")
WEIGHTS_OUT = WEIGHTS_DIR / "babyjev_mobs.pt"


def ensure_dataset() -> Path:
    if (LOCAL_DATASET / "data.yaml").exists():
        print("[dataset] already downloaded:", LOCAL_DATASET)
        return LOCAL_DATASET
    from huggingface_hub import snapshot_download
    print("[dataset] downloading from Hugging Face (once, a few minutes)...")
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir="dataset",
        allow_patterns=[SRC_DIR + "/*"],
    )
    if not (LOCAL_DATASET / "data.yaml").exists():
        raise SystemExit("Download finished but data.yaml was not found; check the dataset layout.")
    print("[dataset] ready:", LOCAL_DATASET)
    return LOCAL_DATASET


def write_data_yaml(root: Path) -> Path:
    # Ultralytics likes absolute paths with forward slashes, even on Windows.
    y = root / "babyjev.yaml"
    y.write_text("\n".join([
        "path: " + root.resolve().as_posix(),
        "train: train/images",
        "val: val/images",
        "nc: 5",
        "names: ['creeper', 'skeleton', 'spider', 'zombie', 'enderman']",
        "",
    ]))
    return y


def auto_device():
    import torch
    if torch.cuda.is_available():
        print("[device] CUDA:", torch.cuda.get_device_name(0))
        return 0
    print("[device] no CUDA found, using CPU (training will be slow)")
    return "cpu"


def main():
    ap = argparse.ArgumentParser(description="Train BabyJev's eyes (run once)")
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--device", default=None, help="0 for GPU, cpu, or empty for auto")
    args = ap.parse_args()

    root = ensure_dataset()
    data_yaml = write_data_yaml(root)
    device = args.device if args.device is not None else auto_device()

    from ultralytics import YOLO
    print("[train] fine-tuning YOLO11n on", CLASSES)
    model = YOLO("yolo11n.pt")  # auto-downloads once (~5 MB)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        project="runs",
        name="mobtrain",
        exist_ok=True,
    )

    best = Path("runs") / "mobtrain" / "weights" / "best.pt"
    if not best.exists():
        raise SystemExit("Training finished but best.pt was not found; check runs/mobtrain/")
    WEIGHTS_DIR.mkdir(exist_ok=True)
    shutil.copy(str(best), str(WEIGHTS_OUT))
    print()
    print("=== BabyJev has eyes ===")
    print("weights:", WEIGHTS_OUT)
    print("classes:", CLASSES)
    print()
    print("next: python triggerbot.py --dry-run")
    print("(targets are filtered by target_classes in config.json)")


if __name__ == "__main__":
    main()
