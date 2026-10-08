import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from voicebridge.settings import ProviderSettings


@pytest.mark.parametrize(
    "url",
    [
        "http://provider.invalid",
        "file:///tmp/test-only-file",
        "https://test-user:test-key@provider.invalid",
        "https://provider.invalid?token=test-key",
        "https://provider.invalid#unexpected-fragment",
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
