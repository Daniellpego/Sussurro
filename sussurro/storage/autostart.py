"""Helper de autostart no Windows via HKCU\\...\\Run.

Le/escreve a chave do registro responsavel por iniciar apps no logon.
"""
from __future__ import annotations

import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Sussurro"


def _winreg():
    try:
        import winreg
        return winreg
    except ImportError:
        return None


def is_enabled() -> bool:
    winreg = _winreg()
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_enabled(enabled: bool, exe_path: str | None = None) -> bool:
    """Habilita/desabilita autostart. Retorna True se aplicou."""
    winreg = _winreg()
    if winreg is None:
        return False

    if not enabled:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                 winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return True

    target = exe_path or _detect_exe_path()
    if target is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                             winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{target}"')
        return True
    except OSError:
        return False


def _detect_exe_path() -> str | None:
    """Caminho do exe quando frozen (PyInstaller); None em venv."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return None
