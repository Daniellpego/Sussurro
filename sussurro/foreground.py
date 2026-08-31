"""Detecção do app em foco (Windows) — pra escolher o modo automaticamente.

Reusa a ideia do GetForegroundWindow (já usada pra posicionar o HUD), mas pega
o NOME DO EXECUTÁVEL da janela ativa (ex.: 'code.exe', 'outlook.exe') pra mapear
em um modo. É o que deixa o Sussurro "consciente de contexto" — algo que os
concorrentes locais não fazem.
"""
from __future__ import annotations

import os


def foreground_app() -> str | None:
    """Nome do executável da janela em foco (minúsculo), ou None."""
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
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            ok = kernel32.QueryFullProcessImageNameW(
                handle, 0, buf, ctypes.byref(size))
            if ok:
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(handle)
    except Exception:  # noqa: BLE001
        return None
    return None


# Mapa padrão exe (minúsculo) -> id de modo built-in. Editável depois pela UI.
DEFAULT_APP_MODES: dict[str, str] = {
    # terminais / editores de código -> Code
    "code.exe": "code",
    "cursor.exe": "code",
    "windowsterminal.exe": "code",
    "wt.exe": "code",
    "cmd.exe": "code",
    "powershell.exe": "code",
    "pwsh.exe": "code",
    "alacritty.exe": "code",
    "mintty.exe": "code",
    # e-mail -> Email
    "outlook.exe": "email",
    "thunderbird.exe": "email",
    "hmailserver.exe": "email",
    # chat / mensageria -> Clean
    "slack.exe": "clean",
    "discord.exe": "clean",
    "teams.exe": "clean",
    "ms-teams.exe": "clean",
    "whatsapp.exe": "clean",
    "telegram.exe": "clean",
}


def mode_for_app(exe: str | None) -> str | None:
    """Modo sugerido pro executável, ou None se não houver regra."""
    if not exe:
        return None
    return DEFAULT_APP_MODES.get(exe)
