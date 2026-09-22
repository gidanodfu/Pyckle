import pytest

from app.core.config import Settings

VALID = {
    "environment": "production",
    "secret_key": "a" * 48,
    "cors_origins": "https://pyckle.com,https://www.pyckle.com",
    "trusted_hosts": "pyckle.com,*.pyckle.com",
    "frontend_url": "https://pyckle.com",
    "domain": "pyckle.com",
    "database_url": "postgresql+asyncpg://user:pass@db:5432/pyckle",
    "redis_url": "redis://redis:6379/0",
    "storage_backend": "s3",
    "supabase_s3_endpoint": "https://project.storage.supabase.co/storage/v1/s3",
    "supabase_s3_region": "us-east-1",
    "supabase_s3_access_key_id": "key",
    "supabase_s3_secret_access_key": "secret",
    "supabase_s3_bucket": "pyckle",
    "allowed_image_types": "image/jpeg,image/png",
    "admin_password": "clave-admin-larga-y-fuerte",
}


def _prod(**overrides) -> Settings:
    return Settings(**{**VALID, **overrides})


def test_production_rejects_default_secret():
    settings = _prod(secret_key="dev-insecure-secret-change-me")
    with pytest.raises(RuntimeError):
        settings.ensure_production_ready()


def test_production_rejects_empty_and_short_secret():
    for secret in ("", "short-secret"):
        with pytest.raises(RuntimeError):
            _prod(secret_key=secret).ensure_production_ready()


def test_production_accepts_valid_configuration():
    _prod().ensure_production_ready()


def test_development_allows_insecure_defaults():
    Settings(
        environment="development", secret_key="dev-insecure-secret-change-me"
    ).ensure_production_ready()


def test_production_rejects_public_env_example_placeholder_secret():
    settings = _prod(secret_key="replace-with-openssl-rand-hex-32")
    with pytest.raises(RuntimeError):
        settings.ensure_production_ready()


def test_production_accepts_generated_secret():
    _prod(secret_key="a" * 64).ensure_production_ready()


def test_production_requires_admin_password():
    for value in (None, "", "corta"):
        with pytest.raises(RuntimeError):
            _prod(admin_password=value).ensure_production_ready()


@pytest.mark.parametrize(
    "value",
    ["replace-strong-admin-password", "replace-demo-password", "changeme", "password123"],
)
def test_production_rejects_known_admin_placeholders(value):
    with pytest.raises(RuntimeError):
        _prod(admin_password=value).ensure_production_ready()


def test_production_accepts_strong_admin_password():
    _prod(admin_password="clave-admin-larga-y-fuerte").ensure_production_ready()


def test_production_rejects_weak_demo_password_when_set():
    with pytest.raises(RuntimeError):
        _prod(demo_password="replace-demo-password").ensure_production_ready()


def test_development_allows_missing_admin_password():
    Settings(environment="development").ensure_production_ready()


@pytest.mark.parametrize("algorithm", ["none", "RS256", "HS512-bad", ""])
def test_production_rejects_non_hmac_jwt_algorithm(algorithm):
    with pytest.raises(RuntimeError):
        _prod(jwt_algorithm=algorithm).ensure_production_ready()


def test_production_rejects_demo_seed_enabled():
    with pytest.raises(RuntimeError):
        _prod(seed_demo_data=True).ensure_production_ready()


def test_development_allows_demo_seed_enabled():
    Settings(environment="development", seed_demo_data=True).ensure_production_ready()


def test_production_rejects_invalid_trusted_proxies():
    with pytest.raises(RuntimeError):
        _prod(trusted_proxies="not-a-network").ensure_production_ready()
    _prod(trusted_proxies="172.16.0.0/12,127.0.0.1/32").ensure_production_ready()


def test_oauth_onboarding_ttl_default_is_120():
    assert Settings().oauth_onboarding_ttl_seconds == 120


def test_production_rejects_non_positive_onboarding_ttl():
    with pytest.raises(RuntimeError):
        _prod(oauth_onboarding_ttl_seconds=0).ensure_production_ready()
    with pytest.raises(RuntimeError):
        _prod(oauth_onboarding_ttl_seconds=-1).ensure_production_ready()


@pytest.mark.parametrize(
    "overrides",
    [
        {"cors_origins": ""},
        {"cors_origins": "   "},
        {"cors_origins": "https://a.com,*"},
        {"cors_origins": "pyckle.com"},
        {"cors_origins": "https://a.com/path"},
    ],
)
def test_production_rejects_invalid_cors(overrides):
    with pytest.raises(RuntimeError):
        _prod(**overrides).ensure_production_ready()


@pytest.mark.parametrize(
    "overrides",
    [
        {"trusted_hosts": ""},
        {"trusted_hosts": "   "},
        {"trusted_hosts": "*"},
        {"trusted_hosts": "http://pyckle.com"},
        {"trusted_hosts": "pyckle.com/evil"},
    ],
)
def test_production_rejects_invalid_trusted_hosts(overrides):
    with pytest.raises(RuntimeError):
        _prod(**overrides).ensure_production_ready()


@pytest.mark.parametrize(
    "overrides",
    [
        {"frontend_url": "not-a-url"},
        {"frontend_url": ""},
        {"domain": "fix.example.com"},
        {"domain": ""},
        {"database_url": "postgresql://user:pass@db:5432/pyckle"},
        {"database_url": ""},
        {"redis_url": "http://localhost:6379"},
        {"redis_url": ""},
        {"storage_backend": "ftp"},
        {"allowed_image_types": ""},
    ],
)
def test_production_rejects_invalid_scalars(overrides):
    with pytest.raises(RuntimeError):
        _prod(**overrides).ensure_production_ready()


def test_production_rejects_local_storage():
    """El almacenamiento local no es válido para múltiples instancias."""
    with pytest.raises(RuntimeError):
        _prod(storage_backend="local").ensure_production_ready()


def test_development_allows_local_storage():
    Settings(environment="development", storage_backend="local").ensure_production_ready()


def test_development_allows_s3_storage():
    Settings(environment="development", storage_backend="s3").ensure_production_ready()


def test_production_s3_requires_all_params():
    with pytest.raises(RuntimeError):
        _prod(
            storage_backend="s3",
            supabase_s3_endpoint=None,
            supabase_s3_access_key_id=None,
            supabase_s3_secret_access_key=None,
        ).ensure_production_ready()

    _prod(
        storage_backend="s3",
        supabase_s3_endpoint="https://project.storage.supabase.co/storage/v1/s3",
        supabase_s3_access_key_id="key",
        supabase_s3_secret_access_key="secret",
        supabase_s3_bucket="pyckle",
    ).ensure_production_ready()
