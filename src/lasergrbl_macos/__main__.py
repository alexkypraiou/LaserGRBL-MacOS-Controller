from __future__ import annotations

import argparse

from .app import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Control GRBL-compatible laser engravers from macOS.")
    parser.add_argument("--demo", action="store_true", help="Run with a simulated controller and no hardware.")
    arguments = parser.parse_args()
    return run(demo_mode=arguments.demo)


if __name__ == "__main__":
    raise SystemExit(main())
