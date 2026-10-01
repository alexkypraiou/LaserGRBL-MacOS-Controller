# Contributing

Thank you for helping improve LaserGRBL for macOS. Contributions should keep the application understandable, testable without hardware, and conservative around machine safety.

## Before starting

- Search existing issues and pull requests.
- Open an issue before a large architectural change.
- Keep pull requests focused on one problem.
- Do not include generated build directories, virtual environments, credentials, or machine-specific settings.

## Development setup

```bash
git clone https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller.git
cd LaserGRBL-MacOS-Controller

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the application without hardware:

```bash
lasergrbl-macos --demo
```

## Quality checks

Run all checks before opening a pull request:

```bash
ruff format --check .
ruff check .
pytest
python -m compileall -q src
```

Use `ruff format .` to apply the project's Python formatting.

## Code organization

- Keep protocol parsing and stream state in `src/lasergrbl_macos/grbl.py`.
- Keep hardware-independent G-code generation and preview parsing in `src/lasergrbl_macos/gcode.py`.
- Keep PyQt widgets, serial I/O, and user interactions in `src/lasergrbl_macos/app.py`.
- Add tests for protocol, parser, or generator behavior that does not require physical hardware.
- Prefer small, explicit state transitions over timers or implicit serial behavior.

## Hardware testing

When physical testing is necessary:

- Describe the controller, GRBL version, Mac model, macOS version, and USB interface.
- Remove or disable the laser for initial motion tests whenever possible.
- Start with low feed, low power, and a small machine area.
- Follow `docs/SAFETY.md` and the equipment manufacturer's instructions.
- Never ask maintainers or reviewers to reproduce an unsafe setup.

## Pull requests

Include:

- A concise explanation of the problem and the chosen solution.
- Tests or a clear reason why automated testing is not practical.
- Screenshots for interface changes.
- Hardware details for controller-specific fixes.
- Documentation updates for user-visible behavior.

By contributing, you agree that your contribution is licensed under the project's MIT License.

