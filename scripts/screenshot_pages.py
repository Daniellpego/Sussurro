"""Gera capturas das janelas reais do Sussurro, sem carregar o modelo.

Usa uma pasta de dados temporária com histórico de exemplo, então não toca
na configuração de quem roda o script.

Uso:
    python scripts/screenshot_pages.py                  # salva em scratch/
    python scripts/screenshot_pages.py --out docs/images --theme dark
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_SAMPLES = (
    ("Preciso que você revise o documento de especificações técnicas do novo "
     "sistema de autenticação até amanhã cedo.", "raw", 4.2, 120),
    ("Olá equipe, segue o resumo da reunião de planejamento da próxima sprint. "
     "Os principais pontos foram o alinhamento de prioridades e a definição "
     "de responsáveis.", "email", 8.6, 3600 * 22),
    ("Lembrar de enviar a petição ao cliente e confirmar a audiência de "
     "quinta-feira.", "clean", 5.3, 3600 * 27),
)


def _pump(app, seconds: float) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


def _save(widget, app, path: Path) -> None:
    _pump(app, 0.35)
    widget.grab().save(str(path))
    print(f"saved {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "scratch")
    parser.add_argument("--theme", choices=("dark", "light"), default="dark")
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else Path.cwd() / args.out
    out.mkdir(parents=True, exist_ok=True)

    # dados isolados: nada do usuário é lido nem alterado
    os.environ["APPDATA"] = tempfile.mkdtemp(prefix="sussurro-shots-")

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    from sussurro.ui import fonts, theme
    fonts.load_fonts()
    theme.set_theme(args.theme)
    app.setStyleSheet(theme.app_base_qss())

    from sussurro.llm.modes import ModeStore
    from sussurro.storage.config import Config
    from sussurro.storage.dictionary import Dictionary
    from sussurro.storage.history import History, HistoryEntry
    from sussurro.ui.history_ui import HistoryWindow
    from sussurro.ui.overlay import Overlay
    from sussurro.ui.settings_ui import SettingsWindow
    from sussurro.ui.window import MainWindow

    cfg = Config.load()
    cfg.first_run_done = True
    history = History()
    now = time.time()
    # do mais antigo para o mais novo, como no uso real
    for text, mode, duration, age in sorted(_SAMPLES, key=lambda x: -x[3]):
        history.append(HistoryEntry(
            timestamp=now - age, mode=mode, text=text,
            duration_audio=duration, duration_infer=0.6, language="pt"))
    store = ModeStore.load()

    main_win = MainWindow(cfg, history, store)
    main_win.set_status("ready", f"pronto · {cfg.hotkey_label}")
    main_win.show()
    _save(main_win, app, out / "janela-principal.png")
    main_win.hide()

    hist_win = HistoryWindow(history)
    hist_win.show()
    _save(hist_win, app, out / "historico.png")
    hist_win.hide()

    settings = SettingsWindow(cfg, store, active_mode_getter=lambda: "raw",
                              dictionary=Dictionary())
    settings.show()
    for key in ("geral", "modelos", "modos", "dicionario"):
        settings._select_tab(key)  # noqa: SLF001
        _save(settings, app, out / f"ajustes-{key}.png")
    settings.hide()

    # assistente de primeira execução, com um microfone falso
    import math

    import sussurro.ui.onboarding as onboarding

    class _FakeRecorder:
        level = 0.4

        def __init__(self, *args, **kwargs) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def recent_levels(self, n: int) -> list[float]:
            return [0.25 + 0.35 * abs(math.sin(i * 0.7)) for i in range(n)]

    onboarding.Recorder = _FakeRecorder
    wizard = onboarding.OnboardingWizard()
    wizard.show()
    for step in range(1, 4):
        _save(wizard, app, out / f"boas-vindas-{step}.png")
        if step < 3:
            wizard._next()  # noqa: SLF001
    wizard.hide()

    overlay = Overlay(level_source=lambda: 0.55)
    overlay.show_recording("raw")
    _pump(app, 1.2)
    _save(overlay, app, out / "hud-gravando.png")
    overlay.show_done(ok=True, mode="email")
    _save(overlay, app, out / "hud-colado.png")
    overlay.hide()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
