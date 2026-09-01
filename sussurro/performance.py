"""Métricas locais de latência do pipeline de ditado."""
from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from sussurro.storage.paths import app_data_dir

_PAIRS = {
    "hotkey_to_capture_ready_ms": ("hotkey_down", "audio_capture_ready"),
    "hotkey_to_first_frame_ms": ("hotkey_down", "first_frame_received"),
    "release_to_audio_final_ms": ("hotkey_up", "audio_finalized"),
    "release_to_first_partial_ms": ("hotkey_up", "first_partial"),
    "hotkey_to_first_partial_ms": ("hotkey_down", "first_partial"),
    "release_to_transcript_final_ms": ("hotkey_up", "transcript_final"),
    "transcript_to_llm_start_ms": ("transcript_final", "llm_start"),
    "llm_duration_ms": ("llm_start", "llm_final"),
    "text_to_paste_start_ms": ("text_final", "paste_start"),
    "paste_duration_ms": ("paste_start", "paste_final"),
}


@dataclass
class LatencyTrace:
    """Marcos monotônicos de uma única interação de push-to-talk."""

    request_id: int
    started_at: float = field(default_factory=time.time)
    marks: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def mark(self, name: str, at: float | None = None) -> float:
        value = time.perf_counter() if at is None else at
        with self._lock:
            self.marks.setdefault(name, value)
        return value

    def as_record(self) -> dict[str, object]:
        with self._lock:
            marks = dict(self.marks)
            metadata = dict(self.metadata)
        durations: dict[str, float] = {}
        for name, (start, end) in _PAIRS.items():
            if start in marks and end in marks and marks[end] >= marks[start]:
                durations[name] = round((marks[end] - marks[start]) * 1000, 3)
        return {
            "request_id": self.request_id,
            "started_at": self.started_at,
            "marks": marks,
            "durations_ms": durations,
            "metadata": metadata,
        }


class LatencyStore:
    """Grava JSONL em background, sem I/O no caminho de colagem."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "latency.jsonl"
        self._queue: queue.Queue[dict[str, object] | None] = queue.Queue()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="latency-writer"
        )
        self._thread.start()

    def submit(self, trace: LatencyTrace) -> None:
        self._queue.put(trace.as_record())

    def close(self, timeout: float = 1.0) -> None:
        self._queue.put(None)
        self._thread.join(timeout)

    def _run(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            record = self._queue.get()
            if record is None:
                return
            try:
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            finally:
                self._queue.task_done()
