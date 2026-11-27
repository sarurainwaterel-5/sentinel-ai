#!/usr/bin/env python3
"""Preflight: run every LIVE chain of the knowledge galaxy end to end and print a verdict.

Not unit tests, not mocks: real HTTP calls against the running server and real calls to the
Anthropic API, because the failures that hurt are the ones where every unit test passes and a
real chain is dead.

    .venv/bin/python preflight.py [--url http://127.0.0.1:4700]

Exit status is non-zero if any check fails. Side effects, all cleaned up: one probe note is
written through /remember (and deleted afterwards), and the probe questions join the server's
in-memory chat history.

RULE: every time something breaks, add a check here that would have caught it, and a line below.

INCIDENT LOG (date: what broke -> check that now catches it)
  2026-11-25: viewer labelled every screen answer "Seen by Claude", even when the local
              SmolVLM answered -> "Viewer names who actually answered a screen question"
  2026-11-25: /see went to the local vision model while Claude was healthy, because the text
              brain toggle was "local" -> "/see answers a real JPEG" fails if Claude was skipped
  2026-11-25: GET /config.json%00.js crashed the request thread (NUL byte, ValueError in the
              stdlib) instead of a 400 -> "config.json is NOT reachable from the browser"
  2026-11-25: a /remember after a restart, with Sentinel down, rebuilt the galaxy without its
              70 taught sources -> "/remember ..." fails if the taught count drops
  2026-11-25: Sentinel API crash-looped (Postgres password auth failed after a setup script
              regenerated .env.local) -> "Taught sources are live" names the container's error
  2026-11-25: edits to server.py had no effect until a restart -> "Running server code matches"
  2026-11-26: (from the brief) a loose matcher hears "opus 5.5", keeps only the 5, loads Opus 5 and
              says it did as asked -> "/model swaps only to real models"
"""
import argparse
import base64
import hashlib
import http.client
import io
import json
import os
import random
import re
import secrets
import string
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE / "viewer"
CONFIG = HERE / "config.json"
DEFAULT_NOTES = HERE.parent / "docs"        # build.py's DEFAULT_NOTES
CHAT_TIMEOUT = 300                          # the local brain can take minutes on this CPU
SEE_TIMEOUT = 180

TTY = sys.stdout.isatty()
C = {"pass": "\033[32m", "fail": "\033[1;31m", "warn": "\033[33m", "dim": "\033[2m", "end": "\033[0m"} if TTY \
    else {"pass": "", "fail": "", "warn": "", "dim": "", "end": ""}
MARK = {"pass": "✓", "fail": "✗", "warn": "!"}


class Fail(Exception):
    pass


class Warn(Exception):
    pass


# ---- HTTP helpers ---------------------------------------------------------------------------
BASE = None


def request(method, path, body=None, timeout=30, raw_path=False):
    """Return (status, headers, bytes). raw_path sends the path byte-for-byte, unnormalised."""
    u = urllib.parse.urlsplit(BASE)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    try:
        conn.putrequest(method, path, skip_accept_encoding=True)
        for k, v in headers.items():
            conn.putheader(k, v)
        if data is not None:
            conn.putheader("Content-Length", str(len(data)))
        conn.endheaders(data)
        r = conn.getresponse()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
    finally:
        conn.close()


def get_json(method, path, body=None, timeout=30):
    status, headers, data = request(method, path, body, timeout)
    try:
        return status, json.loads(data)
    except json.JSONDecodeError:
        raise Fail(f"{method} {path} returned HTTP {status} with a body that isn't JSON: {data[:120]!r}")


def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except FileNotFoundError:
        raise Fail(f"{CONFIG} doesn't exist")
    except json.JSONDecodeError as e:
        raise Fail(f"{CONFIG} isn't valid JSON ({e})")


def load_graph_from(text):
    m = re.search(r"const GRAPH = (\{.*\});\s*$", text, re.S)
    if not m:
        raise Fail("graph-data.js doesn't contain `const GRAPH = {...};`")
    return json.loads(m.group(1))


STATE = {}   # values earlier checks hand to later ones


# ---- The checks, in order -------------------------------------------------------------------
def check_server():
    try:
        status, headers, body = request("GET", "/", timeout=5)
    except OSError as e:
        STATE["down"] = True
        raise Fail(f"nothing answering at {BASE} ({e.__class__.__name__}: {e}). "
                   "Start it: cd galaxy && .venv/bin/python server.py")
    if status != 200:
        raise Fail(f"GET / returned HTTP {status}")
    if "text/html" not in headers.get("content-type", ""):
        raise Fail(f"GET / served {headers.get('content-type')!r}, not HTML")
    page = body.decode("utf-8", "replace")
    missing = [s for s in ('src="graph-data.js"', 'id="ask"', 'id="screen"') if s not in page]
    if missing:
        raise Fail(f"GET / served HTML, but not the galaxy viewer (missing {', '.join(missing)})")
    return f"{BASE}/ serves the viewer ({len(body) // 1024} KB)"


def check_graph():
    status, _, body = request("GET", "/graph-data.js")
    if status != 200:
        raise Fail(f"GET /graph-data.js returned HTTP {status}")
    try:
        graph = load_graph_from(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise Fail(f"graph-data.js is served but its GRAPH isn't valid JSON ({e})")
    nodes, links = graph.get("nodes") or [], graph.get("links") or []
    if not nodes:
        raise Fail("graph-data.js loads but has 0 nodes")
    n = len(nodes)
    bad = [l for l in links if not (0 <= l["source"] < n and 0 <= l["target"] < n)]
    if bad:
        raise Fail(f"{len(bad)} links point at nodes that don't exist (first: {bad[0]})")
    if [x["id"] for x in nodes] != list(range(n)):
        raise Fail("node ids aren't 0..N-1, so link indices and node ids disagree")
    STATE["graph"] = graph
    _, v = get_json("GET", "/graph-version")
    detail = f"{n} nodes, {len(links)} links, version {graph.get('version')}"
    if v.get("notes", 0) + v.get("taught", 0) != n or v.get("version") != graph.get("version"):
        raise Warn(detail + f"; but the server's live index says {v} (a rebuild may be mid-flight)")
    return detail


def ask_chat(question):
    t0 = time.time()
    status, d = get_json("POST", "/chat", {"question": question}, timeout=CHAT_TIMEOUT)
    return status, d, time.time() - t0


def check_chat():
    graph = STATE.get("graph")
    if not graph:
        raise Fail("skipped: no graph loaded, so there's no real note to ask about")
    # A real question about a real note: the first non-taught note with a multi-word title.
    note = next((x for x in graph["nodes"] if not x.get("taught") and len(x["label"].split()) >= 2),
                graph["nodes"][0])
    q = f"What does my note on {note['label']} say?"
    status, d, dt = ask_chat(q)
    if status != 200 or d.get("error"):
        raise Fail(f"/chat returned HTTP {status}: {d.get('error') or d}")
    answer, nodes = d.get("answer"), d.get("nodes")
    if not isinstance(answer, str) or not answer.strip():
        raise Fail(f"/chat returned no answer text: {d}")
    if not isinstance(nodes, list) or not all(isinstance(i, int) and 0 <= i < len(graph["nodes"]) for i in nodes):
        raise Fail(f"/chat 'nodes' isn't a list of valid node ids: {nodes!r}")
    detail = f"{d.get('brain', '?')} brain, {dt:.1f}s, {len(nodes)} node(s) for {q!r}: {answer[:90]!r}"
    if d.get("brain_note"):
        raise Warn(detail + f" (fell back: {d['brain_note']})")
    return detail


def sentinel_diagnosis(container="sentinel-local-api-1"):
    """Name the actual cause when Sentinel is down: container state plus its last error line."""
    def run(*cmd):
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        state = run("docker", "inspect", "-f", "{{.State.Status}} (restarts: {{.RestartCount}})", container)
    except (OSError, subprocess.SubprocessError):
        return f"Couldn't run docker to inspect {container}."
    if state.returncode != 0:
        return f"Container {container} doesn't exist."
    logs = run("docker", "logs", "--tail", "60", container)
    errors = [l.strip() for l in (logs.stdout + logs.stderr).splitlines()
              if re.search(r"(Error|FATAL|Exception)\b", l) and not l.lstrip().startswith(("File ", "^", "~"))]
    cause = errors[-1][:240] if errors else "no error line in its last 60 log lines"
    return f"{container} is {state.stdout.strip()}; last error: {cause}"


def check_taught():
    _, v = get_json("GET", "/graph-version")
    status, d, dt = ask_chat("What do the taught sources say about governance?")
    if status != 200 or d.get("error"):
        raise Fail(f"/chat returned HTTP {status}: {d.get('error') or d}")
    problems = []
    if not v.get("taught"):
        problems.append("the galaxy has 0 taught sources")
    if d.get("taught_checked") is False:
        problems.append("/chat couldn't reach Sentinel's /search, so answers ignore everything it was taught")
    if problems:
        raise Fail("; ".join(problems) + ". " + sentinel_diagnosis())
    return f"{v['taught']} taught sources in the galaxy; /chat searched them ({len(d.get('passages') or [])} passage(s) used)"


def anthropic_client():
    import anthropic
    key = (load_config().get("anthropic_api_key") or "").strip()
    if not key or key == "PUT-YOUR-KEY-HERE":
        raise Fail("config.json has no anthropic_api_key")
    STATE["key"] = key
    return anthropic, anthropic.Anthropic(api_key=key, max_retries=0, timeout=60)


def check_key():
    anthropic, client = anthropic_client()
    model = load_config().get("model", "claude-opus-5-5")
    try:
        client.messages.create(model=model, max_tokens=16, messages=[{"role": "user", "content": "Reply OK."}])
    except anthropic.AuthenticationError:
        raise Fail("Anthropic rejected the API key in config.json (401 authentication_error)")
    except anthropic.PermissionDeniedError as e:
        raise Fail(f"the key authenticated but isn't permitted: {e.message}")
    except anthropic.NotFoundError:
        return "key authenticated (the model id itself is reported by the next check)"
    except anthropic.BadRequestError as e:
        if re.search(r"credit|billing", str(e.message), re.I):
            raise Fail("the key is valid but the Anthropic account is out of API credits")
        raise Fail(f"Anthropic rejected the minimal call: {e.message}")
    except anthropic.APIConnectionError as e:
        raise Fail(f"couldn't reach the Anthropic API ({e})")
    except anthropic.APIStatusError as e:
        raise Fail(f"Anthropic API error {e.status_code}: {e.message}")
    STATE["claude_ok"] = True
    return f"one real messages call to {model} succeeded"


def check_model():
    anthropic, client = anthropic_client()
    model = load_config().get("model")
    if not model:
        raise Fail("config.json has no \"model\"")
    try:
        m = client.models.retrieve(model)
    except anthropic.NotFoundError:
        raise Fail(f"the Models API has no model with id {model!r} for this key; fix \"model\" in config.json")
    except anthropic.AuthenticationError:
        raise Fail(f"couldn't look up model {model!r}: the key was rejected")
    except anthropic.APIError as e:
        raise Fail(f"couldn't look up model {model!r}: {e}")
    return f"Models API knows {m.id!r} ({getattr(m, 'display_name', '') or 'no display name'})"


def check_model_set():
    """Every Anthropic id the voice swap can load must be real for this key, per the Models API."""
    anthropic, client = anthropic_client()
    _, st = get_json("GET", "/model")
    ids = st.get("models") or []
    if not ids:
        raise Fail("GET /model listed no models")
    missing, resolved = [], 0
    for mid in ids:
        if "/" in mid:                    # OpenRouter ids are checked against its catalog below
            continue
        try:
            client.models.retrieve(mid)
            resolved += 1
        except anthropic.NotFoundError:
            missing.append(mid)
    if missing:
        raise Fail(f"in the server's MODELS set but unknown to the Models API for this key: {', '.join(missing)}")
    others = [m for m in ids if "/" in m]
    detail = f"all {resolved} Anthropic ids in MODELS are real for this key"
    if others:
        try:
            with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=20) as r:
                catalog = {m["id"] for m in json.load(r)["data"]}
        except (OSError, ValueError, KeyError) as e:
            raise Warn(detail + f"; couldn't fetch the OpenRouter catalog to check {', '.join(others)} ({e})")
        gone = [m for m in others if m not in catalog]
        if gone:
            raise Fail(detail + f"; but not in OpenRouter's catalog: {', '.join(gone)}")
        detail += f"; {', '.join(others)} in OpenRouter's catalog"
        if not (load_config().get("openrouter_api_key") or "").strip():
            raise Warn(detail + " (no openrouter_api_key in config.json, so those swaps are refused)")
    return detail


def check_model_swap():
    _, st = get_json("GET", "/model")
    before, default = st["model"], st["default"]
    cfg_before = CONFIG.read_bytes()
    if default != load_config().get("model"):
        raise Fail(f"server's default model {default!r} isn't config.json's {load_config().get('model')!r}")
    say = lambda text: get_json("POST", "/model", {"say": text})
    try:
        status, d = say("try on opus 5.5")
        if status != 200 or d.get("model") != "claude-opus-5-5":
            raise Fail(f"'try on opus 5.5' loaded {d.get('model')!r} (HTTP {status}), not claude-opus-5-5")
        if d.get("label") != "OPUS 5.5":
            raise Fail(f"chip label for claude-opus-5-5 is {d.get('label')!r}, not 'OPUS 5.5'")
        for bad in ("switch to opus 6", "switch to opus 5 5", "switch to opus"):
            status, d = say(bad)
            if status == 200 or d.get("ok") or d.get("model") != "claude-opus-5-5":
                raise Fail(f"{bad!r} wasn't refused cleanly: HTTP {status}, now on {d.get('model')!r}")
        refusal = d.get("spoken", "")
        status, d = say("switch to haiku 4.5")
        if status != 200 or d.get("model") != "claude-haiku-4-5":
            raise Fail(f"'switch to haiku 4.5' gave HTTP {status}: {d.get('error') or d.get('model')}")
        if CONFIG.read_bytes() != cfg_before:
            raise Fail("a runtime swap wrote config.json; swaps must be runtime-only")
        detail = "opus 5.5 -> claude-opus-5-5 (OPUS 5.5); opus 6, 'opus 5 5', bare opus refused"
        if d.get("mode") == "local":
            raise Warn(detail + "; brain switch is Local, so a swapped model can't be asked a real question")
        status, c, dt = ask_chat("Say hello in five words.")
        if status != 200 or c.get("error"):
            raise Fail(detail + f"; but /chat on Haiku 4.5 failed: HTTP {status} {c.get('error') or c}")
        if c.get("model") != "claude-haiku-4-5":
            raise Fail(detail + f"; but /chat after the swap was answered by {c.get('model') or c.get('brain')!r}")
        return detail + f"; /chat answered on HAIKU 4.5 (no effort setting) in {dt:.1f}s; config.json untouched"
    finally:                               # put back exactly what was loaded before the check
        get_json("POST", "/model", {"reset": True} if before == default else {"model": before})


def notes_root():
    custom = load_config().get("notes_dir")
    return Path(custom).expanduser() if custom else DEFAULT_NOTES


def check_remember():
    token = "pf" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    word = random.choice(["ORCHID", "GRANITE", "LANTERN", "HARBOR", "COBALT", "MERIDIAN"])
    path = None
    _, before = get_json("GET", "/graph-version")
    try:
        status, d = get_json("POST", "/remember",
                             {"text": f"remember that preflight probe {token} codeword is {word}", "via": "typed"},
                             timeout=120)
        if d.get("path"):
            path = notes_root() / d["path"]
        if status != 200 or not d.get("ok"):
            raise Fail(f"/remember returned HTTP {status}: {d.get('error') or d}")
        if not path.is_file():
            raise Fail(f"/remember said it saved {d['path']}, but {path} isn't on disk")
        text = path.read_text(encoding="utf-8")
        if token not in text or word not in text:
            raise Fail(f"{path} exists but doesn't contain the probe text")
        node_id = d["node"]["id"]
        _, after = get_json("GET", "/graph-version")
        if after.get("taught", 0) < before.get("taught", 0):
            raise Fail(f"the capture indexed, but the galaxy lost taught sources "
                       f"({before.get('taught')} -> {after.get('taught')})")
        status, c, dt = ask_chat(f"What is the preflight probe {token} codeword?")
        if status != 200 or c.get("error"):
            raise Fail(f"note saved as node {node_id}, but /chat then failed: HTTP {status} {c.get('error') or c}")
        cited, said = node_id in (c.get("nodes") or []), word.lower() in (c.get("answer") or "").lower()
        if not (cited or said):
            raise Fail(f"note saved as node {node_id} ({d['path']}), but /chat didn't retrieve it: "
                       f"nodes={c.get('nodes')} answer={c.get('answer', '')[:100]!r}")
        detail = (f"wrote {d['path']} (node {node_id}); /chat ({c.get('brain', '?')}, {dt:.1f}s) "
                  + ("cited it and said the codeword" if cited and said else
                     "cited it" if cited else "said the codeword"))
        if not cited:
            raise Warn(detail + ", but didn't cite the node, so the camera wouldn't fly to it")
        return detail
    finally:
        if path is not None and path.is_file():
            path.unlink()                          # the watcher drops it from the graph within a minute


def probe_jpeg(number):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (960, 540), "white")
    draw = ImageDraw.Draw(img)
    draw.text((480, 210), "PREFLIGHT", fill="black", anchor="mm", font=ImageFont.load_default(size=64))
    draw.text((480, 330), str(number), fill="black", anchor="mm", font=ImageFont.load_default(size=120))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)              # the browser's canvas.toBlob("image/jpeg", 0.85)
    return buf.getvalue(), img.size


def check_see():
    number = random.randint(1000, 9999)
    data, (w, h) = probe_jpeg(number)
    assert data[:3] == b"\xff\xd8\xff", "probe isn't a JPEG"
    body = {"question": "What number is written on this screen?",
            "image": base64.b64encode(data).decode(), "media_type": "image/jpeg",   # what the client sends
            "width": w, "height": h, "captured_at": time.time() * 1000}
    t0 = time.time()
    status, d = get_json("POST", "/see", body, timeout=SEE_TIMEOUT)
    dt = time.time() - t0
    if status != 200 or d.get("error"):
        raise Fail(f"/see returned HTTP {status}: {d.get('error') or d}")
    frame = d.get("frame") or {}
    if frame.get("media_type") != "image/jpeg":
        raise Fail(f"/see sent the frame onward as {frame.get('media_type')!r}, not image/jpeg")
    answer = d.get("answer") or ""
    if str(number) not in answer.replace(",", ""):
        raise Fail(f"/see answered but didn't read the probe's {number}: {answer[:120]!r}")
    detail = f"{d.get('brain')} read {number} off a {w}x{h} JPEG ({len(data) // 1024} KB) in {dt:.1f}s"
    _, st = get_json("GET", "/model")
    expected = "openrouter" if st.get("provider") == "openrouter" else "claude"
    if d.get("brain") != expected:
        why = d.get("brain_note") or "no reason given"
        if STATE.get("claude_ok"):   # Claude just answered the key check, so skipping it is a routing bug
            raise Fail(detail + f", but Claude is healthy and was skipped ({why}). Screen questions must go to Claude")
        raise Warn(detail + f": the local fallback answered because Claude is unavailable ({why})")
    return detail


def check_sight_label():
    """The answer line under a screen answer must name who actually looked, never a fixed name."""
    status, _, body = request("GET", "/index.html")
    page = body.decode("utf-8", "replace")
    m = re.search(r"async function look\(.*?\n  \}\n", page, re.S)
    if status != 200 or not m:
        raise Fail("couldn't find look() in the served index.html, so the label can't be verified")
    code = m.group(0)
    if re.search(r"Seen by (Claude|the local)[^$]*?:", code) or "d.brain" not in code:
        raise Fail("the served viewer labels screen answers with a fixed name instead of d.brain, "
                   "so a local-model answer would claim Claude saw it")
    return "look() builds the 'Seen by …' label from d.brain (Claude vs local vision model)"


def check_served():
    files = sorted(p for p in VIEWER.rglob("*") if p.is_file())
    stale, missing, no_store = [], [], []
    for p in files:
        rel = p.relative_to(VIEWER).as_posix()
        for attempt in range(2):                   # graph-data.js may be rewritten mid-read: retry once
            status, headers, body = request("GET", "/" + urllib.parse.quote(rel))
            disk = p.read_bytes()
            if status == 200 and hashlib.sha256(body).digest() == hashlib.sha256(disk).digest():
                break
            time.sleep(0.5)
        else:
            (missing if status != 200 else stale).append(f"{rel} (HTTP {status})" if status != 200 else
                                                         f"{rel} (served {len(body)} B, disk {len(disk)} B)")
            continue
        if "no-store" not in headers.get("cache-control", ""):
            no_store.append(rel)
        STATE.setdefault("served_bodies", []).append(body)
    if stale or missing:
        raise Fail("served files differ from disk: " + "; ".join(stale + missing))
    detail = f"{len(files)} file(s) byte-identical to disk: {', '.join(p.name for p in files)}"
    if no_store:
        raise Warn(detail + f"; but no Cache-Control: no-store on {', '.join(no_store)}, so a browser may cache them")
    return detail


def server_pid():
    port = urllib.parse.urlsplit(BASE).port or 80
    try:
        out = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"pid=(\d+)", out)
    return int(m.group(1)) if m else None


def check_running_code():
    pid = server_pid()
    if pid is None:
        raise Warn("couldn't find the server's process (not on this machine, or ss unavailable)")
    try:
        ticks = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])
        boot = next(float(l.split()[1]) for l in Path("/proc/stat").read_text().splitlines() if l.startswith("btime"))
        started = boot + ticks / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError, StopIteration):
        raise Warn(f"couldn't read process {pid}'s start time")
    newer = [f.name for f in (HERE / "server.py", HERE / "build.py") if f.stat().st_mtime > started]
    when = time.strftime("%H:%M:%S", time.localtime(started))
    if newer:
        raise Fail(f"server (pid {pid}) started {when}, but {', '.join(newer)} changed after that: "
                   "it's running old code. Restart server.py")
    return f"server pid {pid} started {when}, after server.py and build.py last changed"


def check_config_hidden():
    key = STATE.get("key") or (load_config().get("anthropic_api_key") or "")
    paths = ["/config.json", "/config.tmp", "//config.json", "/../config.json", "/viewer/../config.json",
             "/%2e%2e/config.json", "/..%2fconfig.json", "/%2e%2e%2fconfig.json", "/..%5cconfig.json",
             "/./../config.json", "/config.json%00.js", "/server.py", "/../server.py"]
    leaks = []
    for p in paths:
        try:
            status, _, body = request("GET", p, raw_path=True, timeout=5)
        except OSError as e:
            leaks.append(f"{p} -> connection error {e.__class__.__name__} (couldn't prove it's hidden)")
            continue
        text = body.decode("utf-8", "replace")
        if status == 200 and ("anthropic_api_key" in text or (key and key in text) or "import anthropic" in text):
            leaks.append(f"{p} -> HTTP 200, served the file")
    if key:
        for body in STATE.get("served_bodies", []):
            if key.encode() in body:
                leaks.append("the API key appears inside a file the viewer serves")
                break
    if any("served" in x for x in leaks):
        raise Fail("\n".join(["", "!" * 72, "!!  CONFIG.JSON / API KEY IS REACHABLE FROM THE BROWSER",
                              *[f"!!    {x}" for x in leaks],
                              "!!  Anyone who can load this page can read your Anthropic key.",
                              "!!  Stop the server, rotate the key, fix the static file serving.", "!" * 72]))
    if leaks:   # nothing served, but a request crashed the server instead of being refused
        raise Fail("\n".join(["", "!" * 72, "!!  COULD NOT PROVE CONFIG.JSON IS HIDDEN",
                              *[f"!!    {x}" for x in leaks],
                              "!!  The server dropped these requests instead of refusing them.",
                              "!!  Check its log for the traceback and fix the static file handler.", "!" * 72]))
    return f"{len(paths)} paths tried (incl. traversal and encoding tricks): none served config.json or server.py"


CHECKS = [
    ("Server is up and serving the viewer", check_server, False),
    ("Graph data loads with nodes > 0", check_graph, False),
    ("/chat answers a real question with a nodes array", check_chat, False),
    ("Taught sources are live (Sentinel API reachable)", check_taught, False),
    ("API key in config.json is valid (one real call)", check_key, True),
    ("Model in config.json is reachable via the Models API", check_model, True),
    ("Every model in the swap set is real (Models API)", check_model_set, False),
    ("/model swaps only to real models, refuses the rest", check_model_swap, False),
    ("/remember writes a real note that /chat retrieves", check_remember, False),
    ("/see answers a real JPEG (image/jpeg)", check_see, False),
    ("Viewer names who actually answered a screen question", check_sight_label, False),
    ("Served files match the files on disk", check_served, False),
    ("Running server code matches server.py on disk", check_running_code, False),
    ("config.json is NOT reachable from the browser", check_config_hidden, False),
]


def main():
    global BASE
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default="http://127.0.0.1:4700")
    BASE = ap.parse_args().url.rstrip("/")
    print(f"Preflight against {BASE}  ({time.strftime('%Y-%m-%d %H:%M:%S')})\n")
    counts = {"pass": 0, "fail": 0, "warn": 0}
    for i, (name, fn, offline_ok) in enumerate(CHECKS, 1):
        t0 = time.time()
        if STATE.get("down") and not offline_ok:
            status, detail = "fail", "skipped: the server isn't up"
        else:
            try:
                status, detail = "pass", fn()
            except Fail as e:
                status, detail = "fail", str(e)
            except Warn as e:
                status, detail = "warn", str(e)
            except Exception as e:                 # a broken check is a failed check, never a silent one
                status, detail = "fail", f"check crashed: {e.__class__.__name__}: {e}"
        counts[status] += 1
        print(f"{C[status]}{MARK[status]}{C['end']} {i:>2}. {name}  {C['dim']}({time.time() - t0:.1f}s){C['end']}")
        for line in detail.split("\n"):
            print(f"       {C[status] if status == 'fail' else C['dim']}{line}{C['end']}")
    verdict = "FAIL" if counts["fail"] else "PASS"
    print(f"\n{C['fail' if counts['fail'] else 'pass']}{verdict}{C['end']}: "
          f"{counts['pass']} pass, {counts['fail']} fail, {counts['warn']} warn")
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
