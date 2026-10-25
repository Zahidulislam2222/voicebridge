import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from voicebridge.settings import ProviderSettings, Settings


@pytest.mark.parametrize(
    "url",
    [
        "http://provider.invalid",
        "file:///tmp/test-only-file",
        "https://test-user:test-key@provider.invalid",
        "https://provider.invalid?token=test-key",
        "https://provider.invalid#unexpected-fragment",
        "https://provider.invalid/contacts;unexpected",
        "",
    ],
)
def test_provider_endpoints_reject_unsafe_configuration(app: FastAPI, url: str) -> None:
    value = app.state.service.settings.provider.model_dump()
    value["vapi_base_url"] = url
    with pytest.raises(ValidationError):
        ProviderSettings.model_validate(value)


@pytest.mark.parametrize("key", ["retell_key", "vapi_key", "hubspot_key", "google_client_secret"])
def test_provider_credentials_reject_empty_values(app: FastAPI, key: str) -> None:
    value = app.state.service.settings.provider.model_dump()
    value[key] = ""
    with pytest.raises(ValidationError):
        ProviderSettings.model_validate(value)


@pytest.mark.parametrize(
    ("field", "accepted", "rejected"),
    [("native_max_seconds", 180, 181), ("native_entitlement_ttl_seconds", 7200, 7201)],
)
def test_native_call_bounds_stay_capped(
    app: FastAPI, field: str, accepted: int, rejected: int
) -> None:
    value = app.state.service.settings.model_dump()
    value[field] = accepted
    assert getattr(Settings.model_validate(value), field) == accepted
    value[field] = rejected
    with pytest.raises(ValidationError):
        Settings.model_validate(value)
