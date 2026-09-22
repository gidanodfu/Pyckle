"""Comprobaciones simples de arquitectura (sin herramientas externas)."""

import re
from pathlib import Path

import app.main  # noqa: F401  # importa la app y registra todos los modelos
from app.db.base import Base

BACKEND_APP = Path(__file__).resolve().parents[1] / "app"

EXPECTED_TABLES = {
    "conversations",
    "customer_profiles",
    "departments",
    "districts",
    "messages",
    "notifications",
    "oauth_accounts",
    "order_cost_items",
    "order_events",
    "order_price_changes",
    "orders",
    "permissions",
    "provinces",
    "quotation_items",
    "quotations",
    "repair_reports",
    "repair_request_images",
    "repair_requests",
    "reviews",
    "role_permissions",
    "roles",
    "specialties",
    "technician_specialties",
    "technicians",
    "user_roles",
    "users",
}

ADMIN_ROUTERS = ("reports.py", "users.py", "moderation.py", "technicians.py", "catalog.py")


def _router_files() -> list[Path]:
    files = sorted(BACKEND_APP.glob("domains/*/router.py"))
    files += sorted(BACKEND_APP.glob("domains/*/*_router.py"))
    files += [
        BACKEND_APP / "domains" / "admin" / name
        for name in ADMIN_ROUTERS
        if (BACKEND_APP / "domains" / "admin" / name).exists()
    ]
    return files


def _service_files() -> list[Path]:
    files = sorted(BACKEND_APP.glob("domains/*/service.py"))
    for extra in (
        "repair_requests/media.py",
        "repair_requests/privacy.py",
        "technicians/specialties.py",
        "admin/stats.py",
    ):
        path = BACKEND_APP / "domains" / extra
        if path.exists():
            files.append(path)
    return files


def test_domain_structure_is_in_place():
    assert (BACKEND_APP / "domains").is_dir()
    assert (BACKEND_APP / "api" / "router.py").is_file()
    assert not (BACKEND_APP / "services").exists()
    assert not (BACKEND_APP / "repositories").exists()
    assert not (BACKEND_APP / "api" / "v1").exists()


def test_metadata_contains_all_models():
    """Si un refactor pierde un modelo, Alembic dejaría de verlo."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_app_imports_and_uses_pyckle_name():
    from app.main import app

    assert app.title == "Pyckle"
    assert app.openapi_url == "/api/v1/openapi.json"


def test_no_hardcoded_api_prefix_outside_config():
    """El prefijo /api/v1 solo se declara como default en core/config.py."""
    allowed = {BACKEND_APP / "core" / "config.py"}
    violations = []
    for path in BACKEND_APP.rglob("*.py"):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"""["']/api/v1""", text):
            violations.append(str(path.relative_to(BACKEND_APP)))
    assert violations == []


def test_routers_do_not_touch_repositories_or_models():
    violations = []
    for path in _router_files():
        text = path.read_text(encoding="utf-8")
        if ".repository" in text:
            violations.append(f"{path.name}: importa repository")
        if re.search(r"from app\.models\.(?!enums)", text):
            violations.append(f"{path.name}: importa modelos")
    assert violations == []


def test_services_do_not_depend_on_fastapi():
    violations = [
        path.name for path in _service_files() if "fastapi" in path.read_text(encoding="utf-8")
    ]
    assert violations == []


def test_routers_do_not_embed_google_oauth_details():
    """El router solo delega; los detalles de Google viven en oauth/google.py."""
    forbidden = (
        "accounts.google.com",
        "oauth2.googleapis.com",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_CLIENT_ID",
        "app.domains.auth.oauth.google",
    )
    violations = []
    for path in _router_files():
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                violations.append(f"{path.name}: {needle}")
    assert violations == []


def test_user_model_is_provider_agnostic():
    user_model = (BACKEND_APP / "models" / "user.py").read_text(encoding="utf-8").lower()
    assert "google" not in user_model
    assert (BACKEND_APP / "domains" / "auth" / "oauth" / "google.py").is_file()


def test_repositories_only_access_data():
    violations = []
    for path in sorted(BACKEND_APP.glob("domains/*/repository.py")):
        text = path.read_text(encoding="utf-8")
        if "fastapi" in text or ".service" in text:
            violations.append(path.name)
    assert violations == []
