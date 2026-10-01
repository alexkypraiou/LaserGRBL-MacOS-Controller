# Roadmap

The roadmap prioritizes reliable machine communication and user safety before expanding design features.

## 0.2 — Reliable foundation

- [x] Modular protocol, G-code, and interface layers.
- [x] GRBL status parsing and buffered serial lines.
- [x] Acknowledgement-driven streaming.
- [x] Pause, resume, abort, and demo mode.
- [x] Raster image generation and path preview.
- [x] Automated tests and macOS release workflow.

## 0.3 — Machine confidence

- [ ] Add connection profiles for common controller families.
- [ ] Display GRBL alarm and error descriptions.
- [ ] Add soft-limit-aware workspace bounds.
- [ ] Add framing with the laser disabled or at guarded low power.
- [ ] Add job validation for unsupported or risky commands.
- [ ] Expand real-hardware test coverage across Intel and Apple silicon Macs.

## 0.4 — Better G-code workflows

- [ ] Render `G2` and `G3` arcs.
- [ ] Add line numbers and direct editor-to-console error navigation.
- [ ] Add job statistics for distance, bounds, and estimated duration.
- [ ] Add configurable return-to-origin and parking behavior.
- [ ] Persist safe user preferences and recent files.

## 0.5 — Artwork workflows

- [ ] Import SVG vector paths.
- [ ] Add image dithering modes.
- [ ] Preserve aspect ratio with an explicit lock.
- [ ] Add cropping, inversion, rotation, and material presets.
- [ ] Preview power as a heat map.

## 1.0 — Production-ready macOS release

- [ ] Complete hardware compatibility matrix.
- [ ] Add integration tests with a GRBL simulator.
- [ ] Sign and notarize universal macOS builds.
- [ ] Publish a stable user manual and migration policy.
- [ ] Complete accessibility and keyboard-navigation review.

Priorities may change based on reproducible issues, maintainership capacity, and safety impact.

