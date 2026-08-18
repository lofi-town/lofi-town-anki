from addon.security import (
    is_allowed_app_url,
    is_safe_external_url,
    is_safe_oauth_authorization_url,
)


def test_allows_public_https_external_links() -> None:
    assert is_safe_external_url("https://lofi.town/about")
    assert is_safe_external_url("https://198.51.1.1/")


def test_rejects_unsafe_external_links() -> None:
    for value in (
        "http://lofi.town/about",
        "https://user:secret@lofi.town",
        "https://localhost/admin",
        "https://127.0.0.1/admin",
        "https://192.168.1.1/admin",
        "https://[::1]/admin",
        "https://router.local/admin",
        "https://printer/admin",
        "file:///etc/passwd",
        "lofitown://auth/callback",
    ):
        assert not is_safe_external_url(value), value


def test_restricts_oauth_authorization_urls() -> None:
    assert is_safe_oauth_authorization_url(
        "https://project.supabase.co/auth/v1/authorize?provider=discord"
    )
    assert is_safe_oauth_authorization_url(
        "https://project.supabase.in/auth/v1/authorize?provider=google"
    )
    assert not is_safe_oauth_authorization_url(
        "https://evil.example/auth/v1/authorize"
    )
    assert not is_safe_oauth_authorization_url(
        "https://project.supabase.co/auth/v1/token"
    )
    assert not is_safe_oauth_authorization_url(
        "https://supabase.co/auth/v1/authorize"
    )


def test_allows_only_the_configured_app_origin() -> None:
    origin = "https://app.lofi.town"
    assert is_allowed_app_url("https://app.lofi.town/", origin)
    assert is_allowed_app_url("https://app.lofi.town/productivity", origin)
    assert not is_allowed_app_url("https://lofi.town/", origin)
    assert not is_allowed_app_url("https://user:secret@app.lofi.town/", origin)
    assert not is_allowed_app_url("http://app.lofi.town/", origin)
