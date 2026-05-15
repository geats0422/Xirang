from app.core.config import Settings


def test_creem_and_region_settings_have_defaults() -> None:
    settings = Settings()

    assert settings.creem_api_base_url == "https://api.creem.io"
    assert settings.creem_checkout_success_url
    assert settings.creem_checkout_cancel_url
    assert "US" in settings.premium_regions
    assert "IN" in settings.developing_regions


def test_region_settings_parse_csv() -> None:
    settings = Settings(premium_regions="us, gb", developing_regions="in,th")

    assert settings.premium_regions == ["US", "GB"]
    assert settings.developing_regions == ["IN", "TH"]
