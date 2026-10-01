"""Aviso de nova versão: consulta a última release publicada no GitHub.

Só lê a API pública de releases (nenhum dado do usuário é enviado) e nunca
baixa nada sozinho: o app só avisa e abre a página da versão.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger("sussurro")

LATEST_RELEASE_API = "https://api.github.com/repos/Daniellpego/Sussurro/releases/latest"

_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    """'v0.1.3' ou '0.1.3' -> (0, 1, 3); pré-releases e lixo -> None."""
    m = _VERSION.match((text or "").strip())
    return tuple(int(g) for g in m.groups()) if m else None  # type: ignore[return-value]


def is_newer(tag: str | None, current: str) -> bool:
    new, cur = parse_version(tag), parse_version(current)
    return bool(new and cur and new > cur)


def fetch_latest_release(timeout: float = 8.0) -> tuple[str, str] | None:
    """(tag, url da página) da última release, ou None se não deu pra saber."""
    try:
        import httpx

        resp = httpx.get(
            LATEST_RELEASE_API, timeout=timeout, follow_redirects=True,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        data = resp.json()
        tag, url = data.get("tag_name"), data.get("html_url")
        if isinstance(tag, str) and isinstance(url, str):
            return tag, url
    except Exception as exc:  # noqa: BLE001 - sem internet não é erro
        log.info("não foi possível verificar atualizações: %s", exc)
    return None


def check_for_update(current: str, already_notified: str = "") -> tuple[str, str] | None:
    """Release mais nova que `current` e ainda não avisada, ou None."""
    latest = fetch_latest_release()
    if latest is None:
        return None
    tag, url = latest
    if tag == already_notified or not is_newer(tag, current):
        return None
    return tag, url
