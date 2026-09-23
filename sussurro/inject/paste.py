"""Cola texto no app ativo — robusto em editores, browsers e terminais.

Estrategias (config `paste_method`):
- "ctrl+v"       clipboard + Ctrl+V (maioria dos apps)
- "shift+insert" clipboard + Shift+Insert (Git Bash / mintty)
- "type"         digita char-a-char (último recurso / paste bloqueado)
- "auto"         tenta a cadeia: preferido → shift+insert → digitar

No Windows prefere SendInput (não depende de hook global do `keyboard`).
Detecta app em foco elevado (UIPI) e devolve mensagem humana.
"""
from __future__ import annotations

import logging
import sys
import threading
import time
from dataclasses import dataclass

import pyperclip

log = logging.getLogger("sussurro.paste")

_lock = threading.Lock()

# curta o bastante para caber na pílula do HUD
ELEVATED_COPIED_MESSAGE = "janela admin: texto copiado, use Ctrl+V"

_PASTE_CHORD = {
    "ctrl+v": "ctrl+v",
    "shift+insert": "shift+insert",
}


@dataclass
class PasteResult:
    """Resultado da tentativa de colar — a UI usa `ok` + `message`."""
    ok: bool
    method: str = ""          # método que funcionou (ou o tentado)
    message: str = ""         # legível pro HUD/status se falhou (ou aviso)
    elevated_block: bool = False


# ---------------------------------------------------------------------------
# Elevação (UIPI): processo normal não injeta tecla em janela admin
# ---------------------------------------------------------------------------

def is_self_elevated() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def foreground_is_elevated() -> bool | None:
    """True se a janela em foco roda elevada; None se não deu pra checar."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            # sem handle costuma ser processo protegido/elevado
            return True
        try:
            # Token elevation
            TOKEN_QUERY = 0x0008
            token = wintypes.HANDLE()
            if not ctypes.windll.advapi32.OpenProcessToken(
                    handle, TOKEN_QUERY, ctypes.byref(token)):
                return None
            try:
                class TOKEN_ELEVATION(ctypes.Structure):
                    _fields_ = [("TokenIsElevated", wintypes.DWORD)]

                elev = TOKEN_ELEVATION()
                size = wintypes.DWORD()
                # TokenElevation = 20
                ok = ctypes.windll.advapi32.GetTokenInformation(
                    token, 20, ctypes.byref(elev),
                    ctypes.sizeof(elev), ctypes.byref(size))
                if not ok:
                    return None
                return bool(elev.TokenIsElevated)
            finally:
                kernel32.CloseHandle(token)
        finally:
            kernel32.CloseHandle(handle)
    except Exception:  # noqa: BLE001
        return None


def modifier_keys_held() -> bool:
    """True enquanto Ctrl, Win, Shift ou Alt estão fisicamente pressionados.

    Colar nesse momento mistura o Ctrl+V com as teclas do usuário (com o
    atalho Ctrl+Win ainda seguro, o Windows recebe Win+Ctrl+V).
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        get_state = ctypes.windll.user32.GetAsyncKeyState
        # VK_CONTROL, VK_LWIN, VK_RWIN, VK_SHIFT, VK_MENU
        return any(get_state(vk) & 0x8000 for vk in (0x11, 0x5B, 0x5C, 0x10, 0x12))
    except Exception:  # noqa: BLE001
        return False


def wait_until_keyboard_free(
    is_recording,
    *,
    recording_timeout: float,
    keys_timeout: float,
    keys_held=None,
    poll: float = 0.03,
) -> None:
    """Espera uma gravação em curso terminar e os modificadores serem soltos.

    Um ditado que termina enquanto o próximo já está sendo gravado não pode
    colar com Ctrl+Win pressionados: o Windows veria Win+Ctrl+V. Os limites
    de tempo evitam que a fila de colagem trave para sempre.
    """
    keys_held = keys_held or modifier_keys_held
    deadline = time.monotonic() + recording_timeout
    while is_recording() and time.monotonic() < deadline:
        time.sleep(poll)
    deadline = time.monotonic() + keys_timeout
    while keys_held() and time.monotonic() < deadline:
        time.sleep(poll)


def elevation_blocks_paste() -> bool:
    """True quando o alvo é admin e o Sussurro não é — UIPI bloqueia input."""
    if is_self_elevated():
        return False
    fg = foreground_is_elevated()
    return fg is True


# ---------------------------------------------------------------------------
# Win32 SendInput
# ---------------------------------------------------------------------------

def _win_send_chord(chord: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_EXTENDEDKEY = 0x0001

        VK = {"ctrl": 0x11, "shift": 0x10, "v": 0x56, "insert": 0x2D}

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            )

        class INPUT(ctypes.Structure):
            class _I(ctypes.Union):
                _fields_ = (("ki", KEYBDINPUT),)
            _anonymous_ = ("i",)
            _fields_ = (("type", wintypes.DWORD), ("i", _I))

        def _key(vk: int, up: bool = False, extended: bool = False) -> INPUT:
            flags = KEYEVENTF_KEYUP if up else 0
            if extended:
                flags |= KEYEVENTF_EXTENDEDKEY
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.ki = KEYBDINPUT(vk, 0, flags, 0, None)
            return inp

        if chord == "ctrl+v":
            seq = [
                _key(VK["ctrl"]), _key(VK["v"]),
                _key(VK["v"], up=True), _key(VK["ctrl"], up=True),
            ]
        elif chord == "shift+insert":
            seq = [
                _key(VK["shift"]), _key(VK["insert"], extended=True),
                _key(VK["insert"], up=True, extended=True),
                _key(VK["shift"], up=True),
            ]
        else:
            return False

        n = len(seq)
        arr = (INPUT * n)(*seq)
        sent = user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
        return sent == n
    except Exception:  # noqa: BLE001
        log.debug("SendInput chord falhou", exc_info=True)
        return False


def _win_type_unicode(text: str) -> bool:
    if sys.platform != "win32" or not text:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        INPUT_KEYBOARD = 1
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            )

        class INPUT(ctypes.Structure):
            class _I(ctypes.Union):
                _fields_ = (("ki", KEYBDINPUT),)
            _anonymous_ = ("i",)
            _fields_ = (("type", wintypes.DWORD), ("i", _I))

        batch = 64
        for start in range(0, len(text), batch):
            chunk = text[start:start + batch]
            events: list[INPUT] = []
            for ch in chunk:
                if ch == "\r":
                    continue
                if ch == "\n":
                    for up in (False, True):
                        inp = INPUT()
                        inp.type = INPUT_KEYBOARD
                        inp.ki = KEYBDINPUT(
                            0x0D, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
                        events.append(inp)
                    continue
                # SendInput/KEYEVENTF_UNICODE recebe unidades UTF-16. Para
                # caracteres fora do BMP (ex.: emoji), é preciso enviar o par
                # substituto em vez de truncar ord(ch) para WORD.
                units = ch.encode("utf-16-le")
                for i in range(0, len(units), 2):
                    code = int.from_bytes(units[i:i + 2], "little")
                    for up in (False, True):
                        inp = INPUT()
                        inp.type = INPUT_KEYBOARD
                        flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
                        inp.ki = KEYBDINPUT(0, code, flags, 0, None)
                        events.append(inp)
            n = len(events)
            if not n:
                continue
            arr = (INPUT * n)(*events)
            if user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT)) != n:
                return False
        return True
    except Exception:  # noqa: BLE001
        log.debug("SendInput unicode falhou", exc_info=True)
        return False


def _keyboard_send(chord: str) -> bool:
    try:
        import keyboard
        keyboard.send(chord)
        return True
    except Exception:  # noqa: BLE001
        return False


def _keyboard_write(text: str) -> bool:
    try:
        import keyboard
        keyboard.write(text, delay=0)
        return True
    except Exception:  # noqa: BLE001
        return False


def _copy_to_clipboard(text: str) -> bool:
    try:
        pyperclip.copy(text)
    except Exception:  # noqa: BLE001
        return False
    for _ in range(6):
        try:
            if pyperclip.paste() == text:
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.015)
    return True  # alguns apps mentem no paste(); segue mesmo assim


def _restore_clipboard(previous: str | None, text: str) -> None:
    if previous is None:
        return
    time.sleep(0.28)
    try:
        if pyperclip.paste() == text:
            pyperclip.copy(previous)
    except Exception:  # noqa: BLE001
        pass


def _clipboard_has_non_text() -> bool:
    """True quando o clipboard guarda algo que não é texto (imagem, arquivos).

    O pyperclip só lê texto, então esse conteúdo não teria como ser
    restaurado depois de usar o clipboard para colar.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        CF_UNICODETEXT = 13
        return (user32.CountClipboardFormats() > 0
                and not user32.IsClipboardFormatAvailable(CF_UNICODETEXT))
    except Exception:  # noqa: BLE001
        return False


def _typing_first(chain: list[str]) -> list[str]:
    """Põe "digitar" na frente, que não toca no clipboard."""
    if "type" not in chain:
        return chain
    return ["type"] + [step for step in chain if step != "type"]


def _try_chord(chord: str) -> bool:
    if _win_send_chord(chord):
        return True
    return _keyboard_send(chord)


def _try_type(text: str) -> bool:
    if _win_type_unicode(text):
        return True
    return _keyboard_write(text)


def _chain_for(preferred: str) -> list[str]:
    """Ordem de tentativas. 'auto' e preferidos de clipboard ganham fallbacks."""
    if preferred == "type":
        return ["type"]
    if preferred == "auto":
        return ["ctrl+v", "shift+insert", "type"]
    # preferido primeiro, depois os outros
    order = [preferred]
    for m in ("ctrl+v", "shift+insert", "type"):
        if m not in order:
            order.append(m)
    return order


def paste_text(
    text: str,
    method: str = "ctrl+v",
    restore_clipboard: bool = True,
    auto_fallback: bool = True,
) -> PasteResult:
    """Insere `text` no app ativo. Sempre devolve PasteResult (nunca silencia)."""
    if not text:
        return PasteResult(ok=True, method=method, message="")

    with _lock:
        # UIPI: o Windows descarta em silêncio teclas injetadas numa janela de
        # administrador (Ctrl+V e digitação), e o SendInput ainda devolve
        # sucesso. Deixa o texto no clipboard para o usuário colar.
        if elevation_blocks_paste():
            log.warning("janela em foco é elevada e o Sussurro não — "
                        "texto deixado no clipboard (UIPI)")
            copied = _copy_to_clipboard(text)
            msg = (ELEVATED_COPIED_MESSAGE if copied
                   else "janela de administrador bloqueia a colagem")
            return PasteResult(ok=False, method=method, message=msg,
                               elevated_block=True)

        chain = _chain_for(method if auto_fallback or method == "auto"
                           else method)
        if not auto_fallback and method != "auto":
            chain = [method]

        previous: str | None = None
        if restore_clipboard:
            if _clipboard_has_non_text():
                # imagem ou arquivos copiados: digitar preserva o clipboard
                if "type" in chain:
                    chain = _typing_first(chain)
                    log.info("clipboard com conteúdo não textual — digitando")
                else:
                    log.warning("clipboard com conteúdo não textual será "
                                "substituído (método %s sem fallback)", method)
            else:
                try:
                    previous = pyperclip.paste()
                except Exception:  # noqa: BLE001
                    previous = None

        last_err = ""
        for step in chain:
            try:
                if step == "type":
                    if _try_type(text):
                        _restore_clipboard(previous, text)
                        log.info("paste ok via digitar")
                        return PasteResult(ok=True, method="type")
                    last_err = "falha ao digitar"
                    continue

                chord = _PASTE_CHORD.get(step, "ctrl+v")
                if not _copy_to_clipboard(text):
                    last_err = "clipboard bloqueado"
                    continue
                if _try_chord(chord):
                    _restore_clipboard(previous, text)
                    log.info("paste ok via %s", step)
                    return PasteResult(ok=True, method=step)
                last_err = f"atalho {step} não pegou"
            except Exception as exc:  # noqa: BLE001
                last_err = repr(exc)
                log.debug("passo paste %s falhou: %s", step, exc)

        # falhou tudo
        if last_err == "clipboard bloqueado":
            msg = "clipboard bloqueado por outro app"
        else:
            msg = "não consegui colar — tente modo Digitar nos Ajustes"
        log.error("paste falhou: %s", msg)
        return PasteResult(ok=False, method=method, message=msg)


# Compat: chamadas antigas que ignoram o retorno continuam ok
def paste_text_legacy(text: str, method: str = "ctrl+v",
                      restore_clipboard: bool = True) -> None:
    paste_text(text, method=method, restore_clipboard=restore_clipboard)
