"""Captura screenshots de cada pagina sem iniciar o backend ASR.

Util pra comparar com o design Stitch sem esperar 6s de model load.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from sussurro.storage.config import Config
from sussurro.storage.history import History, HistoryEntry
from sussurro.ui.window import MainWindow


def _seed_history(history: History) -> None:
    if history.all():
        return
    import time
    samples = [
        (
            "Preciso que você revise o documento de especificações técnicas do "
            "novo sistema de autenticação até amanhã cedo.", "raw", 4.2,
            time.time() - 120,
        ),
        (
            "Olá equipe, segue o resumo da nossa reunião de planejamento para a "
            "próxima sprint. Os principais pontos discutidos foram alinhamento "
            "de prioridades e definição de owners.", "email", 8.6,
            time.time() - 3600 * 22,
        ),
        (
            "def calculate_total_revenue(sales_data, tax_rate):\n"
            "    return sum(item.price for item in sales_data) * (1 + tax_rate)",
            "code", 6.1, time.time() - 3600 * 27,
        ),
    ]
    for text, mode, dur_a, ts in samples:
        history.append(HistoryEntry(
            timestamp=ts,
            mode=mode,
            text=text,
            duration_audio=dur_a,
            duration_infer=0.5,
            language="pt",
        ))


def main() -> int:
    qt = QApplication(sys.argv)
    qt.setStyle("Fusion")

    cfg = Config.load()
    cfg.window_w = 920
    cfg.window_h = 620
    history = History()
    _seed_history(history)

    win = MainWindow(cfg, history)
    win.show()
    win.raise_()

    out_dir = Path("scratch")
    out_dir.mkdir(exist_ok=True)

    pages = ["home", "history", "modes", "settings", "about"]
    captured: list[str] = []

    def capture_next() -> None:
        if not pages:
            qt.quit()
            return
        page = pages.pop(0)
        win.go_to(page)
        QTimer.singleShot(450, lambda p=page: do_grab(p))

    def do_grab(page: str) -> None:
        pix = win.grab()
        path = out_dir / f"app-{page}.png"
        pix.save(str(path))
        captured.append(str(path))
        print(f"saved {path}")
        QTimer.singleShot(150, capture_next)

    QTimer.singleShot(500, capture_next)

    qt.exec()
    print(f"---{len(captured)} screenshots---")
    for p in captured:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
