# Roadmap

## Phase 0 - Sight (done)
- [x] Region capture around the crosshair (dxcam, mss fallback)
- [x] Benchmark: fps, mean/median/p95 capture latency
- Target: capture under 10 ms (currently ~13.5 ms via mss; dxcam fails on Insider build 26340)

## Phase 1 - Loop (done)
- [x] Decision loop: radius, proximity, cooldown, CPS cap, jitter
- [x] Telemetry CSV per stage
- [x] Self-test mode (no game needed)
- [x] Palette heuristics: skipped (correctly judged too fragile), kept as stub

## Phase 2 - Model sight (code done)
- [x] train.py: download + fine-tune YOLO11n on 2,585 annotated mob screenshots
- [x] YoloDetector with class whitelist (config: target_classes)
- [ ] Run python train.py on the dev machine
- [ ] Tune yolo_conf (0.55 default) while dry-running against real zombies
- [ ] Measure end-to-end loop with eyes on; compare vs the 50 ms budget

## Phase 3 - Polish
- [ ] Weighted attack decisions (Jev-like score, not just yes/no)
- [ ] On-screen overlay for live tuning
- [ ] Latency write-up: your loop vs. Jev's 24 ms
