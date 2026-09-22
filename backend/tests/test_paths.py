"""Rutas centralizadas: no debe haber /api/v1 hardcodeado fuera de config/paths."""

import uuid

import pytest

from app.core.paths import api_path, order_report_path

pytestmark = pytest.mark.asyncio


async def test_order_report_path_uses_api_prefix():
    order_id = uuid.uuid4()
    assert order_report_path(order_id) == f"/api/v1/orders/{order_id}/report"
    assert api_path("health") == "/api/v1/health"


async def test_root_hides_docs_when_disabled(client, monkeypatch):
    monkeypatch.setattr("app.main._docs_enabled", False)
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] is None


async def test_root_exposes_docs_in_dev(client):
    response = await client.get("/")
    assert response.json()["docs"] == "/docs"
