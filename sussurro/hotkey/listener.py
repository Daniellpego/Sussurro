"""Push-to-talk global hotkey via pynput.

Logica:
- Track Ctrl e Win pressionados simultaneamente
- Quando ambos pressionados: emite `pressed` (uma vez)
- Quando qualquer um libera: emite `released`

Como Ctrl+Win e prefixo de varios atalhos do Windows
(Ctrl+Win+D/L/seta), monitoramos tambem se uma OUTRA tecla foi
pressionada enquanto Ctrl+Win estao segurados — nesse caso, cancelamos
a gravacao (foi um system shortcut, nao push-to-talk).

Teclas injetadas por programas (inclusive o Ctrl+V e a digitacao do
proprio Sussurro) sao ignoradas: nao sao o usuario apertando teclas.

Roda em sua propria thread (pynput.keyboard.Listener) e emite sinais Qt
thread-safe pra UI thread.
"""
from __future__ import annotations

import sys
import time

from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class PushToTalkListener(QObject):
    pressed = Signal(float)
    released = Signal(float)
    cancelled = Signal()   # tecla extra digitada -> system shortcut

    CTRL_KEYS = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
    WIN_KEYS = {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}

    # virtual-key codes pra conferir o estado fisico das teclas
    _VK_CTRL = (0x11,)          # VK_CONTROL
    _VK_WIN = (0x5B, 0x5C)      # VK_LWIN, VK_RWIN
    _LLKHF_INJECTED = 0x10

    def __init__(self) -> None:
        super().__init__()
        self._ctrl = False
        self._win = False
        self._active = False
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            # so tem efeito no Windows; o pynput ignora nos outros sistemas
            win32_event_filter=self._win32_filter,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None

    # --- handlers ---

    def _win32_filter(self, msg, data) -> bool:
        """False descarta o evento para este listener (nao bloqueia o sistema)."""
        del msg
        return not (getattr(data, "flags", 0) & self._LLKHF_INJECTED)

    def _on_press(self, key) -> None:
        prev_both = self._both_held()

        if key in self.CTRL_KEYS:
            self._ctrl = True
            # o soltar do Win pode ter se perdido (Win+L, Ctrl+Alt+Del)
            self._win = self._win and self._physically_down(self._VK_WIN)
        elif key in self.WIN_KEYS:
            self._win = True
            self._ctrl = self._ctrl and self._physically_down(self._VK_CTRL)
        else:
            # qualquer outra tecla pressionada enquanto Ctrl+Win segurados:
            # esta virando um atalho do sistema, cancela PTT
            if self._active:
                self._active = False
                self.cancelled.emit()
            return

        if not prev_both and self._both_held() and not self._active:
            self._active = True
            self.pressed.emit(time.perf_counter())

    def _on_release(self, key) -> None:
        was_active = self._active
        if key in self.CTRL_KEYS:
            self._ctrl = False
        elif key in self.WIN_KEYS:
            self._win = False
        else:
            return

        if was_active and not self._both_held():
            self._active = False
            self.released.emit(time.perf_counter())

    def _both_held(self) -> bool:
        return self._ctrl and self._win

    @staticmethod
    def _physically_down(vks: tuple[int, ...]) -> bool:
        """Estado fisico da tecla; True quando nao da pra conferir."""
        if sys.platform != "win32":
            return True
        try:
            import ctypes
            get_state = ctypes.windll.user32.GetAsyncKeyState
            return any(get_state(vk) & 0x8000 for vk in vks)
        except Exception:  # noqa: BLE001
            return True
