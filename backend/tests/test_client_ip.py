"""Regresión: X-Real-IP solo se acepta desde un proxy de confianza."""

from types import SimpleNamespace

import pytest

from app.core import dependencies

pytestmark = pytest.mark.asyncio


class _Peer:
    def __init__(self, host: str) -> None:
        self.host = host


class _Request:
    def __init__(self, host: str, headers: dict[str, str] | None = None) -> None:
        self.client = _Peer(host)
        self.headers = headers or {}


def _settings(proxies: str):
    return SimpleNamespace(
        trusted_proxies_list=[p.strip() for p in proxies.split(",") if p.strip()],
    )


async def test_untrusted_peer_header_is_ignored(monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: _settings(""))
    request = _Request("203.0.113.9", {"x-real-ip": "10.0.0.1"})
    assert dependencies.client_ip(request) == "203.0.113.9"


async def test_untrusted_range_header_is_ignored(monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: _settings("172.16.0.0/12"))
    request = _Request("203.0.113.9", {"x-real-ip": "10.0.0.1"})
    assert dependencies.client_ip(request) == "203.0.113.9"


async def test_trusted_proxy_header_is_honored(monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: _settings("172.16.0.0/12"))
    request = _Request("172.18.0.5", {"x-real-ip": "198.51.100.7"})
    assert dependencies.client_ip(request) == "198.51.100.7"
