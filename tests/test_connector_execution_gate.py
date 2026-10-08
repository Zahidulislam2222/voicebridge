import pytest
from fastapi import FastAPI
from voicebridge.connectors import RemoteTransport
from voicebridge.contracts import DomainError


def test_vapi_owner_block_precedes_network_even_if_other_connectors_enabled(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(
                update={"enabled": True, "vapi_owner_resolved": False}
            )
        }
    )

    def unexpected_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Blocked Vapi transport must never create a client")

    monkeypatch.setattr(httpx, "Client", unexpected_network)
    with pytest.raises(DomainError, match="vapi_owner_resolution_required"):
        RemoteTransport(settings).request(
            "GET", settings.provider.vapi_base_url.rstrip("/") + "/assistant", {}
        )
