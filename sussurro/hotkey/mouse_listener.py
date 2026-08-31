"""Push-to-talk via botao do mouse (pynput.mouse).

Pensado pra mouses gamer: o botao do meio (scroll click) e os dois
botoes laterais (x1 = "voltar", x2 = "avancar") podem virar push-to-talk.

Logica:
- Botao configurado pressionado  -> emite `pressed` (uma vez)
- Mesmo botao liberado           -> emite `released`

Roda na propria thread (pynput.mouse.Listener) e emite sinais Qt
thread-safe pra UI thread. Pode ser reconfigurado em runtime via
`set_button()` sem precisar reiniciar o app.
"""
from __future__ import annotations

import logging

from pynput import mouse
from PySide6.QtCore import QObject, Signal

log = logging.getLogger("sussurro")


# Mapa nome-config -> pynput Button. Só botoes que NAO sao left/right,
# pra nao sequestrar o clique normal do usuario.
def _button_map() -> dict[str, object]:
    m: dict[str, object] = {}
    for name in ("middle", "x1", "x2"):
        btn = getattr(mouse.Button, name, None)
        if btn is not None:
            m[name] = btn
    return m


# rotulos amigaveis pra UI / status
BUTTON_LABELS = {
    "none": "Desativado",
    "middle": "Scroll (botão do meio)",
    "x1": "Lateral 1 (voltar)",
    "x2": "Lateral 2 (avançar)",
}


class MouseButtonListener(QObject):
    pressed = Signal()
    released = Signal()

    def __init__(self, button: str = "none") -> None:
        super().__init__()
        self._map = _button_map()
        self._target = self._map.get(button)
        self._active = False
        self._listener: mouse.Listener | None = None

    # --- lifecycle ---

    def start(self) -> None:
        if self._listener is not None:
            return
        if self._target is None:
            # nenhum botao configurado: nao instala listener
            return
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()
        log.info("mouse PTT ativo: %s", self._button_name())

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None
        self._active = False

    def set_button(self, button: str) -> None:
        """Troca o botao em runtime. Reinicia o listener se preciso."""
        new_target = self._map.get(button)
        if new_target is self._target and self._listener is not None:
            return
        self.stop()
        self._target = new_target
        self.start()

    # --- handler ---

    def _on_click(self, _x, _y, btn, is_pressed) -> None:
        if btn is not self._target:
            return
        if is_pressed:
            if not self._active:
                self._active = True
                self.pressed.emit()
        else:
            if self._active:
                self._active = False
                self.released.emit()

    def _button_name(self) -> str:
        for name, btn in self._map.items():
            if btn is self._target:
                return name
        return "none"
