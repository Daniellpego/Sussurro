"""Push-to-talk global hotkey via pynput.

Logica:
- Track das teclas do atalho escolhido (Ctrl+Win por padrao)
- Quando todas pressionadas: emite `pressed` (uma vez)
- Quando qualquer uma libera: emite `released`

Como Ctrl+Win e prefixo de varios atalhos do Windows
(Ctrl+Win+D/L/seta), monitoramos tambem se uma OUTRA tecla foi
pressionada enquanto o atalho esta segurado — nesse caso, cancelamos
a gravacao (foi um system shortcut, nao push-to-talk).

Teclas injetadas por programas (inclusive o Ctrl+V e a digitacao do
proprio Sussurro) sao ignoradas: nao sao o usuario apertando teclas.

Roda em sua propria thread (pynput.keyboard.Listener) e emite sinais Qt
thread-safe pra UI thread. O atalho pode ser trocado em runtime via
`set_hotkey()`.
"""
from __future__ import annotations

import sys
import time

from pynput import keyboard
from PySide6.QtCore import QObject, Signal

from sussurro.hotkey.presets import DEFAULT_HOTKEY, HOTKEY_LABELS, normalize_hotkey

# Cada tecla do atalho: (teclas pynput aceitas, virtual-key codes pra
# conferir o estado fisico).
_K = keyboard.Key
_CTRL = ({_K.ctrl, _K.ctrl_l, _K.ctrl_r}, (0x11,))      # VK_CONTROL
_WIN = ({_K.cmd, _K.cmd_l, _K.cmd_r}, (0x5B, 0x5C))     # VK_LWIN/RWIN
_SHIFT = ({_K.shift, _K.shift_l, _K.shift_r}, (0x10,))  # VK_SHIFT
# so o Alt esquerdo: o AltGr dos teclados ABNT2 chega como Ctrl + AltGr e
# dispararia o atalho a cada "/" ou "°" digitado
_ALT_L = ({_K.alt, _K.alt_l}, (0xA4,))                  # VK_LMENU
_CTRL_R = ({_K.ctrl_r}, (0xA3,))                        # VK_RCONTROL

# valor salvo em Config.hotkey_label -> teclas
HOTKEYS: dict[str, tuple] = {
    "Ctrl+Win": (_CTRL, _WIN),
    "Ctrl+Shift": (_CTRL, _SHIFT),
    "Ctrl+Alt": (_CTRL, _ALT_L),
    "Ctrl direito": (_CTRL_R,),
}
assert HOTKEYS.keys() == HOTKEY_LABELS.keys()


class PushToTalkListener(QObject):
    pressed = Signal(float)
    released = Signal(float)
    cancelled = Signal()   # tecla extra digitada -> system shortcut

    _LLKHF_INJECTED = 0x10

    def __init__(self, hotkey: str = DEFAULT_HOTKEY) -> None:
        super().__init__()
        self._keys = HOTKEYS[normalize_hotkey(hotkey)]
        self._held = [False] * len(self._keys)
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

    def set_hotkey(self, hotkey: str) -> None:
        """Troca o atalho em runtime, sem reiniciar o listener."""
        keys = HOTKEYS[normalize_hotkey(hotkey)]
        if keys == self._keys:
            return
        if self._active:
            self._active = False
            self.cancelled.emit()
        self._keys = keys
        self._held = [False] * len(keys)

    # --- handlers ---

    def _win32_filter(self, msg, data) -> bool:
        """False descarta o evento para este listener (nao bloqueia o sistema)."""
        del msg
        return not (getattr(data, "flags", 0) & self._LLKHF_INJECTED)

    def _index(self, key) -> int | None:
        for i, (pynput_keys, _vks) in enumerate(self._keys):
            if key in pynput_keys:
                return i
        return None

    def _on_press(self, key) -> None:
        prev_all = self._all_held()

        i = self._index(key)
        if i is None:
            # qualquer outra tecla pressionada enquanto o atalho esta segurado:
            # esta virando um atalho do sistema, cancela PTT
            if self._active:
                self._active = False
                self.cancelled.emit()
            return

        self._held[i] = True
        # o soltar das outras pode ter se perdido (Win+L, Ctrl+Alt+Del)
        for j, (_keys, vks) in enumerate(self._keys):
            if j != i:
                self._held[j] = self._held[j] and self._physically_down(vks)

        if not prev_all and self._all_held() and not self._active:
            self._active = True
            self.pressed.emit(time.perf_counter())

    def _on_release(self, key) -> None:
        was_active = self._active
        i = self._index(key)
        if i is None:
            return
        self._held[i] = False

        if was_active and not self._all_held():
            self._active = False
            self.released.emit(time.perf_counter())

    def _all_held(self) -> bool:
        return all(self._held)

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
