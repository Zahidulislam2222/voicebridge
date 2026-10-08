import pytest
from fastapi import FastAPI
from voicebridge.contracts import DomainError


@pytest.mark.parametrize("external", [{}, [], 42, None])
def test_malformed_call_identity_never_reaches_database(app: FastAPI, external: object) -> None:
    with pytest.raises(DomainError, match="call_binding_invalid"):
        app.state.providers.binding("retell", external, "test-agent", "test-call-capability")


def test_terminal_call_cannot_authorize_new_tools_but_accepts_later_analysis(app: FastAPI) -> None:
    providers = app.state.providers
    registered = providers.register("northline", "retell", "test-terminal-call", "test-agent")
    call = {"call_id": "test-terminal-call", "agent_id": "test-agent"}
    providers.event("retell", {"event": "call_ended", "call": call}, registered["capability"])
    with pytest.raises(DomainError, match="call_not_active"):
        providers.tools(
            "retell",
            {
                "call": call,
                "name": "answer_question",
                "args": {"query": "business hours"},
            },
            registered["capability"],
        )
    assert providers.event(
        "retell", {"event": "call_analyzed", "call": call}, registered["capability"]
    )["accepted"]
