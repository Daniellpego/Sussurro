"""Historico de transcricoes em JSON.

Lista append-only com timestamp, mode, texto, duracao audio + inferencia.
Mantem ate `MAX_ENTRIES` (rotaciona FIFO).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, fields

from sussurro.storage.paths import backup_corrupt, history_path, write_text_atomic

MAX_ENTRIES = 500


@dataclass
class HistoryEntry:
    timestamp: float
    mode: str
    text: str
    duration_audio: float
    duration_infer: float
    language: str = "pt"

    @property
    def when_label(self) -> str:
        return time.strftime("%H:%M", time.localtime(self.timestamp))

    @property
    def date_label(self) -> str:
        return time.strftime("%d/%m/%Y", time.localtime(self.timestamp))


class History:
    def __init__(self) -> None:
        self._entries: list[HistoryEntry] = []
        self.load()

    def load(self) -> None:
        path = history_path()
        if not path.exists():
            self._entries = []
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError:
            self._entries = []
            return
        except json.JSONDecodeError:
            raw = None
        if not isinstance(raw, list):
            backup_corrupt(path)
            self._entries = []
            return

        valid = {f.name for f in fields(HistoryEntry)}
        required = {"timestamp", "mode", "text", "duration_audio", "duration_infer"}
        entries: list[HistoryEntry] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            data = {k: v for k, v in item.items() if k in valid}
            if not required.issubset(data):
                continue
            try:
                entries.append(HistoryEntry(**data))
            except (TypeError, ValueError):
                # Histórico é dado do usuário: uma linha ruim não invalida as demais.
                continue
        self._entries = entries

    def save(self) -> None:
        path = history_path()
        data = [asdict(e) for e in self._entries[-MAX_ENTRIES:]]
        write_text_atomic(
            path, json.dumps(data, ensure_ascii=False, indent=2))

    def append(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > MAX_ENTRIES:
            self._entries = self._entries[-MAX_ENTRIES:]
        self.save()

    def all(self) -> list[HistoryEntry]:
        """Mais recente primeiro."""
        return list(reversed(self._entries))

    def clear(self) -> None:
        self._entries = []
        self.save()

    def count(self) -> int:
        return len(self._entries)

    def delete_at(self, timestamp: float) -> None:
        """Remove a entrada com o timestamp dado (delete individual)."""
        self._entries = [e for e in self._entries if e.timestamp != timestamp]
        self.save()

    def count_today(self) -> int:
        today_start = time.mktime(time.strptime(
            time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
        return sum(1 for e in self._entries if e.timestamp >= today_start)
