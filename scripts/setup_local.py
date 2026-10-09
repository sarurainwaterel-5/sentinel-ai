"""Create private, local-only settings without overwriting existing credentials."""
import os
from pathlib import Path
import secrets
import subprocess

root = Path(__file__).resolve().parents[1]
env_path = root / ".env.local"
if env_path.exists():
    raise SystemExit("Local settings already exist; no passwords were replaced.")
password = secrets.token_urlsafe(24)
postgres_password = secrets.token_hex(24)
password_hash = subprocess.check_output(
    ["docker", "run", "--rm", "-i", "caddy:2-alpine", "caddy", "hash-password"],
    input=(password + "\n").encode(),
).decode().strip()

def private_write(path, content):
    with path.open("x") as file:
        os.chmod(path, 0o600)
        file.write(content)

private_write(env_path, (
    f"POSTGRES_PASSWORD={postgres_password}\n"
    "SENTINEL_ADMIN_USER=admin\n"
    f"SENTINEL_ADMIN_PASSWORD_HASH='{password_hash}'\n"
))
backend_env = root / "backend/.env"
if not backend_env.exists():
    private_write(backend_env, (
        f"DATABASE_URL=postgresql://sentinel:{postgres_password}@127.0.0.1:5432/sentinel_ai\n"
        "QDRANT_URL=http://127.0.0.1:6333\n"
        "OPENAI_API_KEY=\n"
        "CORS_ORIGINS=http://127.0.0.1:8080\n"
    ))
local = root / ".local"
local.mkdir(exist_ok=True)
private_write(local / "login.txt", f"Sentinel: http://127.0.0.1:8080\nUsername: admin\nPassword: {password}\n")
print("Local credentials created in .local/login.txt (mode 600).")
