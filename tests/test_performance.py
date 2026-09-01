from __future__ import annotations

import json
import time

from sussurro.performance import LatencyStore, LatencyTrace


def test_trace_calculates_stage_durations() -> None:
    trace = LatencyTrace(7)
    trace.mark("hotkey_down", 10.0)
    trace.mark("audio_capture_ready", 10.012)
    trace.mark("first_frame_received", 10.020)
    record = trace.as_record()
    assert record["durations_ms"]["hotkey_to_capture_ready_ms"] == 12.0
    assert record["durations_ms"]["hotkey_to_first_frame_ms"] == 20.0


def test_store_writes_jsonl_off_the_calling_thread(tmp_path) -> None:
    path = tmp_path / "latency.jsonl"
    store = LatencyStore(path)
    trace = LatencyTrace(3)
    trace.mark("hotkey_down")
    store.submit(trace)
    store.close()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["request_id"] == 3
    assert payload["marks"]["hotkey_down"] <= time.perf_counter()
