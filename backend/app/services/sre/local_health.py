"""Local process-callable signal mirrors /health semantics; no HTTP or dependencies."""


def sentinel_process_liveness():
    return {"status": "healthy", "service": "SentinelAI"}
