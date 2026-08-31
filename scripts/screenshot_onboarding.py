"""Captura os 3 steps do wizard de onboarding."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from sussurro.ui.onboarding import OnboardingWizard


def main() -> int:
    qt = QApplication(sys.argv)
    qt.setStyle("Fusion")

    wiz = OnboardingWizard()
    wiz.resize(560, 480)
    wiz.show()

    out_dir = Path("scratch")
    out_dir.mkdir(exist_ok=True)

    state = {"idx": 0}

    def grab_and_advance() -> None:
        idx = state["idx"]
        path = Path("scratch") / f"onboarding-{idx + 1}.png"
        wiz.grab().save(str(path))
        print(f"saved {path}")
        if idx < 2:
            wiz._on_next()  # noqa: SLF001
            state["idx"] += 1
            QTimer.singleShot(250, grab_and_advance)
        else:
            qt.quit()

    QTimer.singleShot(400, grab_and_advance)
    return qt.exec()


if __name__ == "__main__":
    raise SystemExit(main())
