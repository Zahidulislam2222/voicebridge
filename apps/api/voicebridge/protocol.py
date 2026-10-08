"""Immutable provider and tool protocol identities, never deployment defaults."""

RETELL_SIGNATURE_HEADER = "x-retell-signature"
VAPI_AUTHORIZATION_HEADER = "authorization"
CALL_CAPABILITY_HEADER = "x-call-capability"
CALL_CAPABILITY_METADATA_KEY = "voicebridge_capability"
CALL_INTENT_PREFIX = "intent-"
CALL_INTENT_KIND = "call_intent"
RETELL_TERMINAL = {"call_ended", "call_analyzed"}
VAPI_TERMINAL = {"end-of-call-report"}
TRANSCRIPT_SPEAKERS = {
    "retell": {"agent": "assistant", "user": "user"},
    "vapi": {"assistant": "assistant", "user": "user"},
}
BUSINESS_TOOLS = {
    "check_availability",
    "create_booking",
    "get_booking",
    "change_booking",
    "answer_question",
}
MANAGEMENT_TOOLS = {
    "get_state",
    "get_agent_draft",
    "save_agent_draft",
    "run_evaluations",
    "promote_agent",
}
BUSINESS_READ_TOOLS = {"check_availability", "get_booking", "answer_question"}
MANAGEMENT_READ_TOOLS = {"get_state", "get_agent_draft"}
MCP_VERSION = "2025-11-25"
MCP_COMPATIBLE_VERSIONS = {MCP_VERSION, "2025-03-26", "2025-06-18"}
LOCAL_CALENDAR_KIND = "calendar"
CORE_DISTRIBUTION = "voicebridge-core"
EVALUATION_CALENDAR_PREFIX = "E:"
EVALUATION_TENANT_PREFIX = "evaluation-"
SAFE_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}
OWNER_API_PREFIXES = ("/api/agent", "/api/evaluations", "/api/calls")

# A single ASCII mailbox; display names, lists and header controls are excluded.
SINGLE_EMAIL_PATTERN = (
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$"
)
