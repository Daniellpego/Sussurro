"""Sons de feedback (opt-in) — tick ao gravar, confirmação ao concluir.

Usa winsound (Windows, built-in) de forma assíncrona pra não travar a UI.
Tolerante a falha: se o som não tocar, segue a vida.
"""
from __future__ import annotations

from sussurro.storage.paths import asset_path


def play(name: str, enabled: bool = True) -> None:
    """Toca assets/sounds/<name>.wav sem bloquear (se enabled)."""
    if not enabled:
        return
    try:
        import winsound
        path = asset_path("sounds", f"{name}.wav")
        if path.exists():
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
    except Exception:  # noqa: BLE001 - som é cosmético, nunca deve quebrar nada
        pass
