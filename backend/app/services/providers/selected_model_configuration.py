"""Explicit selected role configuration. No ambient credentials or model fallback."""
import hashlib
from pathlib import Path

from .openai_governed_transport import OpenAIGovernedTransport, RoleConfiguration, _bounded_json

SELECTION = Path(__file__).resolve().parents[4] / "docs/governance/sprint21-model-selection.json"
ROLES = {"generation": "gpt-6.1-sol", "semantic_judge": "gpt-6-astra", "relevance": "gpt-6.1-terra"}
EFFORTS = {"generation": "low", "semantic_judge": "low", "relevance": "none"}
KEY_NAMES = {"generation": "SEMANTIC_GENERATION_API_KEY", "semantic_judge": "SEMANTIC_JUDGE_API_KEY",
             "relevance": "SEMANTIC_RELEVANCE_API_KEY"}


def selected_configuration(path=SELECTION):
    """Return nonsecret, validated configuration and its exact artifact digest."""
    with Path(path).open("rb") as stream:
        raw = stream.read(32769)
    if len(raw) > 32768:
        raise ValueError("Model selection invalid.")
    try:
        record = _bounded_json(raw.decode("utf-8"))
    except (ValueError, TypeError, RecursionError):
        raise ValueError("Model selection invalid.") from None
    if (type(record) is not dict or record.get("version") != "sprint21-model-selection-v1"
            or record.get("model_selection_confirmed") is not True
            or record.get("roles") != ROLES or record.get("reasoning_efforts") != EFFORTS
            or record.get("credential_environment") != KEY_NAMES
            or record.get("production_enabled") is not False or record.get("release_authorized") is not False):
        raise ValueError("Model selection invalid.")
    return {"roles": dict(ROLES), "reasoning_efforts": dict(EFFORTS),
            "selection_sha256": hashlib.sha256(raw).hexdigest(),
            "production_enabled": False, "release_authorized": False}


class SelectedModelClients:
    """Own three independently constructed clients; configuration is not acceptance."""
    def __init__(self, clients, transport, configuration):
        self._clients, self.transport, self.configuration = tuple(clients), transport, configuration

    async def close(self):
        failed = False
        for client in self._clients:
            try:
                await client.close()
            except Exception:
                failed = True
        if failed:
            raise ValueError("Selected model client cleanup failed.") from None


async def create_selected_model_clients(*, credentials, selection_path=SELECTION, client_factory=None):
    """Explicit injected credential mapping; no dotenv/environment reads or inference.

    Missing role keys fail before constructing any client. The general application
    key is never a substitute. Client creation errors are sanitized and cleaned up.
    """
    configuration = selected_configuration(selection_path)
    if type(credentials) is not dict:
        raise ValueError("Explicit dedicated role credentials required.")
    keys = []
    for role, name in KEY_NAMES.items():
        value = credentials.get(name)
        if type(value) is not str or not value.strip() or "placeholder" in value.lower():
            raise ValueError("Dedicated credential missing for " + role + ".")
        keys.append(value)
    if client_factory is None:
        from openai import AsyncOpenAI
        client_factory = AsyncOpenAI
    clients = []
    try:
        for key in keys:
            clients.append(client_factory(api_key=key, timeout=30.0, max_retries=0))
        if len({id(client) for client in clients}) != 3:
            raise ValueError("Distinct clients required.")
        configs = [RoleConfiguration(client, ROLES[role], EFFORTS[role])
                   for client, role in zip(clients, ROLES)]
        transport = OpenAIGovernedTransport(generation=configs[0], statement=configs[1], relevance=configs[2])
        return SelectedModelClients(clients, transport, configuration)
    except Exception:
        for client in {id(c): c for c in clients}.values():
            try:
                await client.close()
            except Exception:
                pass
        raise ValueError("Selected model client initialization failed.") from None
