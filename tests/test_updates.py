from __future__ import annotations

from types import SimpleNamespace

import httpx

from sussurro import updates


def test_parse_version() -> None:
    assert updates.parse_version("v0.1.3") == (0, 1, 3)
    assert updates.parse_version("0.10.0") == (0, 10, 0)
    assert updates.parse_version("v0.2.0-beta") is None
    assert updates.parse_version(None) is None


def test_is_newer_compares_numbers_not_text() -> None:
    assert updates.is_newer("v0.1.10", "0.1.9")
    assert not updates.is_newer("v0.1.2", "0.1.2")
    assert not updates.is_newer("v0.1.1", "0.1.2")
    assert not updates.is_newer("nightly", "0.1.2")


def _fake_get(tag: str):
    def get(url, **kwargs):
        assert url == updates.LATEST_RELEASE_API
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"tag_name": tag, "html_url": f"https://example/{tag}"},
        )
    return get


def test_check_for_update_finds_a_newer_release(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "get", _fake_get("v0.2.0"))
    assert updates.check_for_update("0.1.3") == ("v0.2.0", "https://example/v0.2.0")


def test_check_for_update_skips_current_and_already_notified(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "get", _fake_get("v0.2.0"))
    assert updates.check_for_update("0.2.0") is None
    assert updates.check_for_update("0.1.3", already_notified="v0.2.0") is None


def test_check_for_update_without_internet(monkeypatch) -> None:
    def boom(url, **kwargs):
        raise httpx.ConnectError("sem rede")
    monkeypatch.setattr(httpx, "get", boom)
    assert updates.check_for_update("0.1.3") is None
