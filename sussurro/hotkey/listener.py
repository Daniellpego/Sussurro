"""Push-to-talk global hotkey via pynput.

Logica:
- Track Ctrl e Win pressionados simultaneamente
- Modo "push_to_talk": quando ambos pressionados: emite `pressed`; quando qualquer um libera: emite `released`
- Modo "toggle" (Hands-Free): quando ambos pressionados: alterna estado (emite `pressed` ou `released`)
- Teclas extras durante Ctrl+Win: cancela (atalho do sistema)

Roda em sua propria thread (pynput.keyboard.Listener) e emite sinais Qt
thread-safe pra UI thread.
"""
from __future__ import annotations

import time

from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class PushToTalkListener(QObject):
    pressed = Signal(float)
    released = Signal(float)
    cancelled = Signal()   # tecla extra digitada -> system shortcut

    CTRL_KEYS = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
    WIN_KEYS = {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}

    def __init__(self, mode: str = "push_to_talk") -> None:
        super().__init__()
        self._mode = mode
        self._ctrl = False
        self._win = False
        self._active = False
        self._last_toggle_time = 0.0
        self._listener: keyboard.Listener | None = None

    def set_mode(self, mode: str) -> None:
        """Define o modo de gravacao ('push_to_talk' ou 'toggle')."""
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None
        self._active = False

    # --- handlers ---

    def _on_press(self, key) -> None:
        prev_both = self._both_held()

        if key in self.CTRL_KEYS:
            self._ctrl = True
        elif key in self.WIN_KEYS:
            self._win = True
        else:
            # qualquer outra tecla pressionada enquanto Ctrl+Win segurados:
            # esta virando um atalho do sistema, cancela
            if self._both_held() and self._active:
                self._active = False
                self.cancelled.emit()
            return

        now = time.perf_counter()
        if not prev_both and self._both_held():
            if self._mode == "toggle":
                if (now - self._last_toggle_time) > 0.25:
                    self._last_toggle_time = now
                    if not self._active:
                        self._active = True
                        self.pressed.emit(now)
                    else:
                        self._active = False
                        self.released.emit(now)
            else:
                if not self._active:
                    self._active = True
                    self.pressed.emit(now)

    def _on_release(self, key) -> None:
        was_active = self._active
        if key in self.CTRL_KEYS:
            self._ctrl = False
        elif key in self.WIN_KEYS:
            self._win = False
        else:
            return

        if self._mode != "toggle":
            if was_active and not self._both_held():
                self._active = False
                self.released.emit(time.perf_counter())

    def _both_held(self) -> bool:
        return self._ctrl and self._win
