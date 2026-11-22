# Roadmap

## Phase 0 - Sight (done)
- [x] Region capture around the crosshair (dxcam, mss fallback)
- [x] Benchmark: fps, mean/median/p95 capture latency
- Target: capture under 10 ms

## Phase 1 - Heuristic sight + full loop (scaffold done)
- [x] Decision loop: radius, proximity, cooldown, CPS cap, jitter
- [x] Telemetry CSV per stage
- [x] Self-test mode (no game needed)
- [ ] Fill in HeuristicDetector.detect(): nametag strip or mob palette
- [ ] Tune trigger_radius_px and min_bbox_height_px in a creative world

## Phase 2 - Model sight
- [ ] Collect + label a few hundred frames (free from Phase 1 debugging)
- [ ] Train YOLO11n (fp16, under 1.5 GB VRAM on a 4GB card)
- [ ] Swap HeuristicDetector for YoloDetector, keep everything else identical

## Phase 3 - Polish
- [ ] Weighted attack decisions (Jev-like score, not just yes/no)
- [ ] On-screen overlay for live tuning
- [ ] Latency write-up: your loop vs. Jev's 24 ms
