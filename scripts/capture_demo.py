from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from lasergrbl_macos.app import LaserControllerWindow  # noqa: E402


def main() -> None:
    application = QApplication([])
    window = LaserControllerWindow(demo_mode=True)
    window.resize(1_440, 900)
    window.show()
    window.toggle_connection()
    application.processEvents()
    destination = ROOT / "assets" / "app-screenshot.png"
    if not window.grab().save(str(destination), "PNG"):
        raise RuntimeError(f"Could not write {destination}")
    window.close()


if __name__ == "__main__":
    main()
