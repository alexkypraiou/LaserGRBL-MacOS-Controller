# Changelog

All notable project changes are documented here. This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Wider real-hardware compatibility testing.
- Arc rendering and vector artwork import.
- Signed and notarized macOS distribution.

## [0.2.0] - 2026-08-16

### Added

- Structured Python package and command-line entry point.
- Built-in no-hardware demo controller.
- GRBL line framing and status-report parser.
- Acknowledgement-driven G-code stream state machine.
- Pause, resume, abort, and prominent stop/reset controls.
- Offline image-to-G-code generation with serpentine raster scanning.
- Modal G-code path preview with metric and inch support.
- Open and save flows for G-code files.
- Automated tests, Ruff checks, CodeQL, dependency review, and macOS release builds.
- Application icon, social preview, interface screenshot, and launch materials.
- Safety, troubleshooting, contribution, security, release, and roadmap documentation.

### Changed

- Replaced the original single-file prototype with a modular implementation.
- Replaced timer-oriented job sending with one-command-at-a-time GRBL acknowledgements.
- Rebuilt the interface around a focused macOS dark workspace.
- Replaced corrupted GitHub workflow files with valid CI and release automation.
- Updated work-zero behavior to use `G10 L20 P1`.

### Removed

- Duplicate source code stored in `PyCode.txt`.
- Undeclared and unused PySerial dependency.

[Unreleased]: https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller/releases/tag/v0.2.0

