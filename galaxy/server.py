#!/usr/bin/env python3
"""Knowledge-galaxy server: static viewer/ on 127.0.0.1:4700 plus POST /chat.

The API key lives in ./config.json (project root, outside viewer/) and is
never served. Run with the galaxy venv:  .venv/bin/python server.py
"""

# ════════════════════════════════════════════════════════════════════════════════════════
#  PERSONA: who the assistant is. Rewrite this block to change the character.
#
#  Everything here is pure character. The mechanics (JSON fields, source IDs, the
#  knowledge/small-talk decision, live SYSTEM STATUS) are appended further down in
#  SYSTEM_PROMPT and LOCAL_SYSTEM_PROMPT, so a rewrite here can't break the camera or
#  the citations. Restart server.py after editing.
#
#  PERSONA        full character brief, used with Claude.
#  PERSONA_LOCAL  the same character in fewer words, for the small local model
#                 (every prompt token costs it time on this CPU).
#  NOT_IN_NOTES   what the small local model says when no note backs its answer. Its replies
#                 are checked in code because a 1.5B model will otherwise happily invent one.
#  REMEMBER_*     the lines spoken after "remember that …": saved, failed, saved-but-not-indexed.
#                 {title} and {reason} are filled in. A failure is always said out loud.
#  SEE_*          screen-sight lines: no share live, share ended, couldn't see.
#  BOOT_GREETING  the one line spoken when the page loads, after the first click or
#                 keypress, because browsers block speech until then. Nothing else is said.
#                 (The previous character, a dry British butler, greeted with "Hello, sir.")
# ════════════════════════════════════════════════════════════════════════════════════════
BOOT_GREETING = "Control online. Standing by."
NOT_IN_NOTES = "Negative. That isn't in your notes."
REMEMBER_OK = "Copy. Logged to captures: {title}."
REMEMBER_FAIL = "Negative. Capture failed: {reason}. Nothing was saved."
SEE_NO_SHARE = "Negative. No screen share is live. Press the screen button, then ask again."
SEE_ENDED = "Negative. The screen share has ended, so I can't see your screen. Share again and ask."
SEE_FAIL = "Negative. I couldn't see the screen: {reason}."
REMEMBER_UNINDEXED = ("Caution. {title} is saved to disk, but I couldn't index it: {reason}. "
                      "It will join the galaxy on the next rebuild.")

PERSONA = """\
You are Sentinel: a mission-control operator, female, calm and terse. You run the console \
for one operator (the user) and his knowledge base. Think flight controller on a clean \
channel: clipped, exact, unflappable.

How you speak:
- Short declarative sentences. Radio economy: "Copy." "Confirmed." "Negative." "Standing by." \
Use them where they fit, not as a verbal tic.
- Shape of a knowledge answer: ONE crisp status line, then the facts, plainly. The note itself \
is already on his screen, so never recite or quote it; give the point and the source's title.
- Dry humour is allowed in a single understated line when it genuinely lands. Otherwise none. \
Brevity beats a forced joke every time.
- No emoji, no exclamation marks, no gushing, no filler, no "Great question".
- When his notes don't cover something, say so plainly: negative, not in the notes. Never \
invent a source, never pad, and never pass off a merely related note as the answer.
- Small talk (greetings, thanks, jokes, how-are-you) gets one clipped, friendly line and \
nothing more.
"""

PERSONA_LOCAL = """\
You are Sentinel, a calm, terse female mission-control operator.
Short clipped sentences. Radio words like "Copy", "Confirmed", "Negative" where they fit.
Knowledge answer: one crisp status line, then the facts in one sentence. Never recite the note.
No emoji, no exclamation marks, no filler.
Not in the notes: say "Negative" and that it isn't in the notes. Never invent or stretch a source.
Small talk: one short, friendly line.
"""
# ═══════════════════════════════ end of PERSONA ══════════════════════════════════════════
import atexit
import base64
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from collections import deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
VIEWER = HERE / "viewer"
CONFIG = HERE / "config.json"
GRAPH_JS = VIEWER / "graph-data.js"
HOST, PORT = "127.0.0.1", 4700
PLACEHOLDER = "PUT-YOUR-KEY-HERE"
TOP_K = 6
HISTORY_TURNS = 6  # question/answer pairs kept for follow-ups
CHAT_MAX_TOKENS = 2000  # covers thinking + answer on Opus 5.5
RETRY_MAX_TOKENS = 6000
CHAT_EFFORT = "medium"

SYSTEM_PROMPT = PERSONA + (
    "\nYour knowledge base: the user's Sentinel project notes and the source documents Sentinel "
    "was taught (books, legal texts, treaties, etc.).\n\n"
    "First decide the intent of the user's message:\n"
    "- \"knowledge\": a real question or request about the content of the notes or taught "
    "sources, or about this computer's live status.\n"
    "- \"small_talk\": greetings, thanks, jokes, chit-chat, or anything not asking about "
    "the knowledge base.\n\n"
    "For knowledge: use ONLY the NOTES and TAUGHT PASSAGES in the user turn; never outside "
    "knowledge. Taught passages come from OCR'd scans, so read past garbled characters. Each "
    "source is tagged with an ID like S1: list in used_sources only the IDs that actually answer "
    "the question, most important first. If none of them answers it, used_sources MUST be empty "
    "(a related-but-not-answering note is not a source).\n"
    "A SYSTEM STATUS line may describe this computer's live temperature, fan and CPU speed: if "
    "asked about heat, temperature or how the machine is doing, answer from it with empty "
    "used_sources.\n"
    "For small_talk: used_sources empty.\n\n"
    "\"answer\" is what appears on screen. \"spoken\" is read aloud: the witty line and the gist "
    "in at most about 30 words, never quoting the notes. Plain prose, no source IDs, no markdown."
)
# Property order matters: the model fills `intent` before it writes anything else, so the
# camera decision rests on a classification made up front, not inferred from the answer.
ANSWER_FORMAT = {"type": "json_schema", "schema": {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["knowledge", "small_talk"]},
        "answer": {"type": "string"},
        "spoken": {"type": "string"},
        "used_sources": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "answer", "spoken", "used_sources"],
    "additionalProperties": False,
}}
# The small local model can loop inside a string until it runs out of tokens, which truncates
# the JSON. Its grammar caps each field's length, so it must close the reply instead.
LOCAL_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["knowledge", "small_talk"]},
        "answer": {"type": "string", "maxLength": 280},
        "spoken": {"type": "string", "maxLength": 160},
        "used_sources": {"type": "array", "items": {"type": "string", "maxLength": 4}, "maxItems": 4},
    },
    "required": ["intent", "answer", "spoken", "used_sources"],
    "additionalProperties": False,
}
SEARCH_TIMEOUT = 20
PASSAGE_CHARS = 1500
MAX_PASSAGES = 8

STOPWORDS = set("""a an and are as at be but by can do does for from has have how i in
is it its me my of on or our so that the their them then there these this to was
what when where which who why will with you your about into than also any all not
""".split())

if not CONFIG.exists():
    CONFIG.write_text(json.dumps(
        {"anthropic_api_key": PLACEHOLDER, "model": "claude-opus-5-5"}, indent=2) + "\n")


def load_config():
    return json.loads(CONFIG.read_text())


def load_graph():
    text = GRAPH_JS.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 1 and w not in STOPWORDS]


class Index:
    """One immutable snapshot of the graph; swapped whole when Sentinel learns something."""
    def __init__(self, graph):
        self.version = graph.get("version", "")
        self.nodes = graph["nodes"]
        self.tokens = [(set(tokens(n["label"])), tokens(n["excerpt"])) for n in self.nodes]
        self.taught_by_file = {n["path"]: n["id"] for n in self.nodes if n.get("taught")}


INDEX = Index(load_graph())
_api_base = None


def discover_sentinel_api():
    try:
        out = subprocess.run(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}",
             "sentinel-local-api-1"], capture_output=True, text=True, timeout=10).stdout.split()
        return f"http://{out[0]}:8000" if out else None
    except (OSError, subprocess.SubprocessError):
        return None


def sentinel_search(query):
    """Semantic search over everything Sentinel was taught, via Sentinel's own /search."""
    global _api_base
    configured = (load_config().get("sentinel_api_url") or "").rstrip("/") or None
    for base in dict.fromkeys([configured, _api_base, discover_sentinel_api()]):
        if not base:
            continue
        try:
            url = f"{base}/search?" + urllib.parse.urlencode({"question": query})
            with urllib.request.urlopen(url, timeout=SEARCH_TIMEOUT) as r:
                results = json.load(r)
            _api_base = base
            return [{
                "filename": x.get("filename") or "unknown source",
                "chunk": x.get("chunk_index"),
                "score": round(float(x.get("score") or 0), 3),
                "text": re.sub(r"\s+", " ", x.get("text") or "").strip()[:PASSAGE_CHARS],
            } for x in results if x.get("text")]
        except (OSError, ValueError):
            continue
    return None  # Sentinel unreachable


# Direct vector search over Sentinel's Qdrant store, embedding the question with the
# same model Sentinel indexes with (all-MiniLM-L6-v2, via fastembed/ONNX). This lets us
# choose the passage count and cutoff, and scope follow-ups to the previous sources.
# Falls back to Sentinel's /search if the embedder or Qdrant is unavailable.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QDRANT_COLLECTION = "incident_knowledge"
GLOBAL_LIMIT, GLOBAL_THRESHOLD = 6, 0.35
SCOPED_LIMIT = 4
_embedder = None
_embedder_lock = threading.Lock()
_qdrant_base = None


def embed(text):
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            from fastembed import TextEmbedding
            _embedder = TextEmbedding(EMBED_MODEL, cache_dir=str(HERE / ".models"))
        return next(iter(_embedder.embed([text]))).tolist()


def discover_qdrant():
    try:
        out = subprocess.run(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}",
             "sentinel-local-qdrant-1"], capture_output=True, text=True, timeout=10).stdout.split()
        return f"http://{out[0]}:6333" if out else None
    except (OSError, subprocess.SubprocessError):
        return None


def qdrant_query(vector, limit, threshold=None, filenames=None):
    global _qdrant_base
    must = [{"key": "organization_id", "match": {"value": "default"}}]
    if filenames:
        must.append({"key": "filename", "match": {"any": list(filenames)}})
    body = {"query": vector, "limit": limit, "with_payload": True, "filter": {"must": must}}
    if threshold is not None:
        body["score_threshold"] = threshold
    configured = (load_config().get("qdrant_url") or "").rstrip("/") or None
    for base in dict.fromkeys([configured, _qdrant_base, discover_qdrant()]):
        if not base:
            continue
        try:
            req = urllib.request.Request(
                f"{base}/collections/{QDRANT_COLLECTION}/points/query", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=SEARCH_TIMEOUT) as r:
                points = json.load(r)["result"]["points"]
            _qdrant_base = base
            return [{
                "filename": pt["payload"].get("filename") or "unknown source",
                "chunk": pt["payload"].get("chunk_index"),
                "score": round(float(pt.get("score") or 0), 3),
                "text": re.sub(r"\s+", " ", pt["payload"].get("text") or "").strip()[:PASSAGE_CHARS],
            } for pt in points if pt.get("payload", {}).get("text")]
        except (OSError, ValueError, KeyError):
            continue
    raise OSError("Qdrant unreachable")


def taught_search(question, prev_files):
    """Passages from taught sources: best global matches, plus (for follow-ups) the best
    matches inside the sources the previous answer used. Returns None if unreachable."""
    try:
        vec = embed(question)
        found = qdrant_query(vec, GLOBAL_LIMIT, GLOBAL_THRESHOLD)
        if prev_files:
            found += qdrant_query(vec, SCOPED_LIMIT, filenames=prev_files)
    except Exception:
        found = sentinel_search(question)
        if found is None:
            return None
    merged, seen = [], set()
    for p in found:
        key = (p["filename"], p["chunk"])
        if key not in seen and len(merged) < MAX_PASSAGES:
            merged.append(p)
            seen.add(key)
    return merged


history = deque(maxlen=HISTORY_TURNS * 2)
history_lock = threading.Lock()
last_taught_files = []  # sources used by the previous answer, for follow-up scoping


CAPTURE_DIR = "captures"  # inside the notes folder; "remember that …" notes land here


def rank(ix, question, recent="", min_score=1):
    q = set(tokens(question + " " + recent))
    scored = []
    for idx, (title_toks, body_toks) in enumerate(ix.tokens):
        if ix.nodes[idx].get("taught"):
            continue  # taught sources are found by Sentinel's semantic search instead
        title_hits = len(q & title_toks)
        body_hits = sum(1 for w in body_toks if w in q)
        score = title_hits * 5 + min(body_hits, 20)
        floor = min(min_score, 2) if ix.nodes[idx].get("group") == CAPTURE_DIR else min_score
        if score >= floor:
            scored.append((score, idx))
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [idx for _, idx in scored[:TOP_K]]


# ---- Heat monitor -----------------------------------------------------------------------
# The firmware's own heat brake (BD PROCHOT) is switched off on this laptop (see the
# unthrottle runbook), so Sentinel watches the CPU herself: she warns on screen, out loud and
# with a desktop notification, and pauses the local model when it's critical. The CPU's
# internal protection still throttles at 100 °C regardless.
HEAT_WARN_C = 85
HEAT_CRITICAL_C = 93
HEAT_CLEAR_MARGIN_C = 5       # a level clears only after cooling this far below it
HEAT_POLL_SECONDS = 5
HEAT_SUSTAIN = 2              # consecutive readings needed to raise a level (no blips)
HEAT_LOG = HERE / "heat-log.jsonl"
HEAT_LEVELS = ("ok", "warning", "critical")

heat_lock = threading.Lock()
heat = {"temp": None, "level": "ok", "fan_rpm": None, "mhz": None, "max_temp": None,
        "seq": 0, "events": deque(maxlen=20), "simulated": None}
_heat_streak = {"level": "ok", "count": 0}


def _hwmon(name):
    for h in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (h / "name").read_text().strip() == name:
                return h
        except OSError:
            continue
    return None


def read_cpu_temp():
    """CPU package temperature in °C (coretemp 'Package id 0', else the x86_pkg_temp zone)."""
    h = _hwmon("coretemp")
    if h:
        for label in sorted(h.glob("temp*_label")):
            if label.read_text().strip().startswith("Package"):
                return int((h / label.name.replace("_label", "_input")).read_text()) / 1000
    for z in Path("/sys/class/thermal").glob("thermal_zone*"):
        if (z / "type").read_text().strip() == "x86_pkg_temp":
            return int((z / "temp").read_text()) / 1000
    return None


def read_fan_rpm():
    h = _hwmon("dell_smm")
    try:
        return int((h / "fan1_input").read_text()) if h else None
    except (OSError, ValueError):
        return None


def read_mhz():
    try:
        vals = [float(l.split(":")[1]) for l in open("/proc/cpuinfo") if l.startswith("cpu MHz")]
        return round(sum(vals) / len(vals)) if vals else None
    except OSError:
        return None


def heat_message(level, temp, prev="ok"):
    if level == "warning" and prev == "critical":
        return f"Cooling down: the CPU is at {temp:.0f} degrees, still warm. The local model is back on."
    if level == "ok" and prev == "critical":
        return f"The CPU has cooled down to {temp:.0f} degrees. The local model is back on."
    return {
        "critical": f"CPU critical at {temp:.0f} degrees. I've paused the local model until it cools down. "
                    "Check the vents and give the laptop some air.",
        "warning": f"Heads up: the CPU is running hot, {temp:.0f} degrees.",
        "ok": f"The CPU has cooled down to {temp:.0f} degrees.",
    }[level]


def raise_heat_event(level, prev, temp):
    msg = heat_message(level, temp, prev)
    event = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "level": level, "previous": prev,
             "temp": round(temp, 1), "message": msg}
    with heat_lock:
        heat["seq"] += 1
        event["seq"] = heat["seq"]
        heat["events"].append(event)
    print(f"[heat] {level.upper()} {temp:.0f}°C — {msg}", flush=True)
    try:
        with open(HEAT_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")
    except OSError:
        pass
    try:  # desktop notification, so the alert lands even with the galaxy page closed
        urgency = {"critical": "critical", "warning": "normal", "ok": "low"}[level]
        subprocess.Popen(["notify-send", "-u", urgency, "-a", "Sentinel", "-i",
                          "dialog-warning" if level != "ok" else "dialog-information",
                          f"Sentinel: CPU {temp:.0f}°C", msg],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def heat_step():
    with heat_lock:
        simulated = heat["simulated"]
    temp = simulated if simulated is not None else read_cpu_temp()
    if temp is None:
        return
    fan, mhz = read_fan_rpm(), read_mhz()
    with heat_lock:
        level = heat["level"]
        heat.update(temp=round(temp, 1), fan_rpm=fan, mhz=mhz,
                    max_temp=max(temp, heat["max_temp"] or temp))
    # The level this reading supports, with hysteresis on the way down.
    if temp >= HEAT_CRITICAL_C:
        target = "critical"
    elif temp >= HEAT_WARN_C:
        target = "warning" if level != "critical" or temp < HEAT_CRITICAL_C - HEAT_CLEAR_MARGIN_C else "critical"
    elif level != "ok" and temp >= HEAT_WARN_C - HEAT_CLEAR_MARGIN_C:
        target = "warning"
    else:
        target = "ok"
    if target == level:
        _heat_streak.update(level=level, count=0)
        return
    rising = HEAT_LEVELS.index(target) > HEAT_LEVELS.index(level)
    if rising:  # rising needs a sustained reading; falling is already damped by the margin
        _heat_streak["count"] = _heat_streak["count"] + 1 if _heat_streak["level"] == target else 1
        _heat_streak["level"] = target
        if _heat_streak["count"] < HEAT_SUSTAIN:
            return
    _heat_streak.update(level=target, count=0)
    with heat_lock:
        heat["level"] = target
    raise_heat_event(target, level, temp)


def heat_loop():
    while True:
        try:
            heat_step()
        except Exception as e:  # never let a sensor hiccup kill the monitor
            print(f"[heat] monitor error: {e!r}", flush=True)
        time.sleep(HEAT_POLL_SECONDS)


def heat_status():
    with heat_lock:
        return {k: heat[k] for k in ("temp", "level", "fan_rpm", "mhz", "max_temp", "seq", "simulated")} | {
            "warn_at": HEAT_WARN_C, "critical_at": HEAT_CRITICAL_C, "events": list(heat["events"])}


def heat_context():
    """One line for the model, so "how hot are you?" gets a real answer."""
    s = heat_status()
    if s["temp"] is None:
        return ""
    return (f"SYSTEM STATUS (this computer, live): CPU {s['temp']:.0f}°C ({s['level']}; warning at "
            f"{HEAT_WARN_C}, critical at {HEAT_CRITICAL_C}), fan {s['fan_rpm'] or '?'} rpm, "
            f"{s['mhz'] or '?'} MHz.\n\n")


# ---- Brains ---------------------------------------------------------------------------
# "claude": the Anthropic API.  "local": a small model on this machine (llama.cpp's
# llama-server, started by this server, bound to 127.0.0.1).  "auto": Claude first, and the
# local model whenever Claude can't answer (no key, out of credit, offline, API errors).
BRAINS = ("auto", "claude", "local")
LOCAL_DIR = HERE / "local-llm"
LOCAL_PORT = 4701
LOCAL_URL = f"http://127.0.0.1:{LOCAL_PORT}"
LOCAL_CTX = 4096
LOCAL_MAX_TOKENS = 300
LOCAL_TIMEOUT = 600           # CPU-only: never give up before the model does
LOCAL_NOTES, LOCAL_NOTE_CHARS = 3, 300         # small model on a laptop CPU: every prompt token costs
LOCAL_PASSAGES, LOCAL_PASSAGE_CHARS = 2, 450
LOCAL_HISTORY_TURNS = 1


def physical_cores():
    """llama.cpp is fastest with one thread per physical core; hyperthreads slow it down."""
    try:
        cores = {line.split(":")[1].strip() for line in open("/proc/cpuinfo") if line.startswith("core id")}
        return max(1, len(cores))
    except OSError:
        return max(1, (os.cpu_count() or 2) // 2)


# A shorter brief for the small local model: the same rules, a fraction of the prompt tokens.
LOCAL_SYSTEM_PROMPT = PERSONA_LOCAL + (
    "intent: \"small_talk\" for greetings, thanks, jokes or chit-chat; otherwise \"knowledge\".\n"
    "knowledge: use ONLY the NOTES and TAUGHT PASSAGES given. used_sources: the [S#] IDs that "
    "actually answer it, most important first; none answer it = empty.\n"
    "Heat or how the computer is doing: answer from SYSTEM STATUS, used_sources empty.\n"
    "small_talk: used_sources empty.\n"
    "spoken: the status line plus the gist, one or two short sentences, no quotes.\n"
    "Examples of intent: \"Good morning\" = small_talk. \"Thanks\" = small_talk. "
    "\"What does my note on X say?\" = knowledge."
)
CLAUDE_COOLDOWN = 600         # auto: after "no credit", skip Claude for 10 minutes


class BrainError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


brain_lock = threading.Lock()
brain_mode = load_config().get("brain", "auto")
brain_mode = brain_mode if brain_mode in BRAINS else "auto"
claude_skip_until = 0.0
local_proc = None
local_lock = threading.Lock()


def set_brain(mode):
    global brain_mode, claude_skip_until
    with brain_lock:
        brain_mode = mode
        claude_skip_until = 0.0
        cfg = load_config()
        cfg["brain"] = mode                      # remembered across restarts
        tmp = CONFIG.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, indent=2) + "\n")
        tmp.replace(CONFIG)
    if mode == "local":
        threading.Thread(target=ensure_local, daemon=True).start()


def claude_key():
    key = (load_config().get("anthropic_api_key") or "").strip()
    return "" if key == PLACEHOLDER else key


def local_files():
    cfg = load_config()
    model = (HERE / Path(cfg["local_model"]).expanduser()) if cfg.get("local_model") else \
        next(iter(sorted(LOCAL_DIR.glob("*.gguf"))), None)
    binary = next(iter(sorted(LOCAL_DIR.rglob("llama-server"))), None)
    if model is not None and not model.exists():
        model = None
    return binary, model


def local_healthy():
    try:
        with urllib.request.urlopen(f"{LOCAL_URL}/health", timeout=2) as r:
            return r.status == 200
    except (OSError, ValueError):
        return False


def ensure_local(wait=240):
    """Start llama-server if it isn't running, and wait until the model is loaded."""
    global local_proc
    with local_lock:
        if local_healthy():
            return True
        binary, model = local_files()
        if not binary or not model:
            raise BrainError(HTTPStatus.SERVICE_UNAVAILABLE,
                             "The local model isn't installed (expected llama-server and a .gguf "
                             "model in galaxy/local-llm/).")
        if local_proc is None or local_proc.poll() is not None:
            env = {**os.environ, "LD_LIBRARY_PATH": str(binary.parent)}
            local_proc = subprocess.Popen(
                [str(binary), "-m", str(model), "--host", "127.0.0.1", "--port", str(LOCAL_PORT),
                 "-c", str(LOCAL_CTX), "-t", str(load_config().get("local_threads") or physical_cores()),
                 "--parallel", "1"],
                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
            print(f"Starting local model {model.name} on {LOCAL_URL} …", flush=True)
        deadline = time.time() + wait
        while time.time() < deadline:
            if local_healthy():
                print("Local model ready.", flush=True)
                return True
            if local_proc.poll() is not None:
                raise BrainError(HTTPStatus.BAD_GATEWAY, "The local model failed to start.")
            time.sleep(0.5)
        raise BrainError(HTTPStatus.GATEWAY_TIMEOUT, "The local model is still loading — ask again in a moment.")


def stop_local():
    if local_proc is not None and local_proc.poll() is None:
        local_proc.terminate()


def build_turn(ix, question, idxs, passages, note_chars=None, passage_chars=None):
    """Tag every source S1..Sn so the model can report exactly which ones it used."""
    sid = {}  # "S1" -> ("note", node index) | ("passage", passage index)
    note_lines, taught_lines = [], []
    for i in idxs:
        tag = f"S{len(sid) + 1}"; sid[tag] = ("note", i)
        n = ix.nodes[i]
        note_lines.append(f"[{tag}] note: {n['label']} ({n['path']})\n{n['excerpt'][:note_chars]}")
    for k, p in enumerate(passages):
        tag = f"S{len(sid) + 1}"; sid[tag] = ("passage", k)
        taught_lines.append(f"[{tag}] taught: {Path(p['filename']).stem} (passage {p['chunk']})\n"
                            f"{p['text'][:passage_chars]}")
    notes = "\n\n".join(note_lines) or "(none)"
    taught_txt = "\n\n".join(taught_lines) or "(none)"
    return sid, f"{heat_context()}NOTES:\n{notes}\n\nTAUGHT PASSAGES:\n{taught_txt}\n\nQUESTION: {question}"


def call_claude(key, model, messages, system=None, fmt=None):
    """Return the raw JSON text from Claude, or raise BrainError."""
    client = anthropic.Anthropic(api_key=key, max_retries=1, timeout=90)
    try:
        raw = ""
        for budget in (CHAT_MAX_TOKENS, RETRY_MAX_TOKENS):
            # Opus 5.5: thinking is always on (no thinking param sent), no forced
            # tool_choice. Server-side fallback reroutes a policy refusal.
            resp = client.beta.messages.create(
                model=model,
                max_tokens=budget,
                system=system or SYSTEM_PROMPT,
                output_config={"effort": CHAT_EFFORT, "format": fmt or ANSWER_FORMAT},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=messages,
            )
            if resp.stop_reason == "refusal":
                return None
            raw = "".join(b.text for b in resp.content if b.type == "text").strip()
            if raw:
                return raw
        raise BrainError(HTTPStatus.BAD_GATEWAY, "Claude returned no text, even after a retry.")
    except anthropic.AuthenticationError:
        raise BrainError(HTTPStatus.UNAUTHORIZED, "Anthropic rejected the API key in config.json.")
    except anthropic.PermissionDeniedError:
        raise BrainError(HTTPStatus.FORBIDDEN, "This API key can't use that model.")
    except anthropic.NotFoundError:
        raise BrainError(HTTPStatus.BAD_GATEWAY, "Model not found — check \"model\" in config.json.")
    except anthropic.RateLimitError:
        raise BrainError(HTTPStatus.TOO_MANY_REQUESTS, "Rate limited by Anthropic — try again shortly.")
    except anthropic.BadRequestError as e:
        if "credit" in str(e.message).lower() or "billing" in str(e.message).lower():
            raise BrainError(HTTPStatus.PAYMENT_REQUIRED, "Your Anthropic account is out of API credits.")
        raise BrainError(HTTPStatus.BAD_GATEWAY, f"Anthropic rejected the request: {e.message}")
    except anthropic.APIStatusError as e:
        raise BrainError(HTTPStatus.BAD_GATEWAY, f"Anthropic API error {e.status_code}.")
    except anthropic.APIConnectionError:
        raise BrainError(HTTPStatus.BAD_GATEWAY, "Couldn't reach the Anthropic API.")


def call_local(messages):
    """Return the raw JSON text from the local model, or raise BrainError."""
    s = heat_status()
    if s["level"] == "critical":
        raise BrainError(HTTPStatus.SERVICE_UNAVAILABLE,
                         f"The CPU is critically hot ({s['temp']:.0f}°C), so the local model is paused "
                         "until it cools down.")
    ensure_local()
    body = json.dumps({
        "messages": [{"role": "system", "content": LOCAL_SYSTEM_PROMPT}] + messages,
        "max_tokens": LOCAL_MAX_TOKENS,
        "temperature": 0.2,
        "repeat_penalty": 1.15,   # discourages the "I'm here to help…" loops small models fall into
        # Grammar-constrained decoding: same fields as Claude's schema, with length caps.
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "answer", "schema": LOCAL_ANSWER_SCHEMA}},
    }).encode()
    req = urllib.request.Request(f"{LOCAL_URL}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=LOCAL_TIMEOUT) as r:
            reply = json.load(r)
    except (OSError, ValueError) as e:
        raise BrainError(HTTPStatus.BAD_GATEWAY, f"The local model didn't answer ({e.__class__.__name__}).")
    return (reply.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()


# ---- Local-model guards: the small model can't be trusted to keep the persona's rules, so
# the server enforces the ones that matter (grounding, brevity, no emoji) after it answers.
SMALL_TALK_RE = re.compile(
    r"^\W*(hi|hello|hey|hiya|yo|good (morning|afternoon|evening|night)|morning|evening|thanks|"
    r"thank you|thx|cheers|bye|goodbye|good ?night|see you|that'?s all|that will be all|"
    r"how are you|how'?s it going|you there)\b", re.I)
STATUS_RE = re.compile(r"\b(hot|heat|temp|temperature|fan|cpu|status|machine|computer|running|overheat)", re.I)
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+")


def tidy(text, max_sentences):
    text = EMOJI_RE.sub("", text)
    text = re.sub(r"(^|\s)#\w+", " ", text)                  # hashtags
    text = re.sub(r"[*_`]+|\[|\]", "", text).replace("!", ".")  # markdown, exclamations (terse)
    text = re.sub(r"\.{2,}", ".", re.sub(r"\s+", " ", text)).strip()
    sentences = re.findall(r".+?[.?](?=\s|$)", text)            # whole sentences; keeps "1.8" intact
    return " ".join(x.strip() for x in sentences[:max_sentences]) if sentences else text


def guard_local(question, intent, answer, spoken, used_tags):
    if SMALL_TALK_RE.match(question):
        intent, used_tags = "small_talk", []
    if intent == "small_talk":
        line = tidy(answer, 1)
        return intent, line, line, []
    if not used_tags and not STATUS_RE.search(question):
        return intent, NOT_IN_NOTES, NOT_IN_NOTES, []     # nothing backs it: don't let it bluff
    answer = tidy(answer, 2)
    spoken = tidy(spoken, 1)
    if not spoken.endswith((".", "?")):                    # cut off mid-sentence: use the answer's lead
        spoken = tidy(answer, 1)
    return intent, answer, spoken, used_tags


def ask_brain(question):
    global claude_skip_until
    ix = INDEX  # one consistent snapshot for this whole request
    with history_lock:
        past = list(history)
        prev_files = list(last_taught_files) if past else []
    recent_q = " ".join(m["content"].split("QUESTION:")[-1] for m in past[-2:] if m["role"] == "user")
    passages = taught_search(question, prev_files)
    sentinel_down = passages is None
    passages = passages or []
    # Notes: when taught passages were found, keep only strong (title-level) note matches.
    floor = 5 if passages else 1
    idxs = rank(ix, question, min_score=floor) or rank(ix, question, recent_q, min_score=floor)

    with brain_lock:
        mode, skip_until = brain_mode, claude_skip_until
    key, cfg = claude_key(), load_config()
    order = {"claude": ["claude"], "local": ["local"],
             "auto": (["claude"] if key and time.time() >= skip_until else []) + ["local"]}[mode]
    if mode == "claude" and not key:
        return HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": "No API key yet. Put your Anthropic key in config.json (anthropic_api_key), "
                     "or switch the brain to Local.", "nodes": []}

    raw, brain, note, last_err = None, None, "", None
    for brain in order:
        try:
            if brain == "claude":
                sid, user_turn = build_turn(ix, question, idxs, passages)
                raw = call_claude(key, cfg.get("model", "claude-opus-5-5"),
                                  past + [{"role": "user", "content": user_turn}])
                if raw is None:
                    return HTTPStatus.OK, {"answer": "The model declined to answer that one.",
                                           "nodes": [], "brain": "claude"}
            else:
                sid, user_turn = build_turn(ix, question, idxs[:LOCAL_NOTES], passages[:LOCAL_PASSAGES],
                                            LOCAL_NOTE_CHARS, LOCAL_PASSAGE_CHARS)
                short_past = [{"role": m["role"], "content": m["content"].split("QUESTION:")[-1].strip()}
                              for m in past[-2 * LOCAL_HISTORY_TURNS:]]
                raw = call_local(short_past + [{"role": "user", "content": user_turn}])
            break
        except BrainError as e:
            last_err = e
            if brain == "claude":
                if e.status == HTTPStatus.PAYMENT_REQUIRED:
                    claude_skip_until = time.time() + CLAUDE_COOLDOWN
                note = e.message + " Answered by the local model instead."
                print(f"Claude unavailable ({e.message}); using the local model", flush=True)
            raw = None
    if raw is None:
        e = last_err or BrainError(HTTPStatus.BAD_GATEWAY, "No brain could answer.")
        return e.status, {"error": e.message, "nodes": []}

    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    answer = str(data.get("answer") or "").strip()
    spoken = str(data.get("spoken") or "").strip()
    intent = "small_talk" if data.get("intent") == "small_talk" else "knowledge"
    used_tags = list(dict.fromkeys(t for t in data.get("used_sources") or [] if t in sid))
    if intent == "small_talk":
        used_tags = []  # small talk never points at notes, so it can never move the camera
    if brain == "local" and answer:
        if intent == "knowledge" and not used_tags:
            # Small models often answer from a note but forget to cite it. Count a source only if
            # the answer names it outright (its title), never because it was merely retrieved.
            said = " " + " ".join(tokens(answer)) + " "
            for tag, (kind, ref) in sid.items():
                title = ix.nodes[ref]["label"] if kind == "note" else Path(passages[ref]["filename"]).stem
                t = tokens(title)
                named = sum(1 for w in t if f" {w} " in said)
                if len(t) >= 2 and named >= max(2, round(0.75 * len(t))):
                    used_tags.append(tag)
        intent, answer, spoken, used_tags = guard_local(question, intent, answer, spoken, used_tags)
    if not answer:
        return HTTPStatus.BAD_GATEWAY, {"error": "The model returned no answer.", "nodes": []}

    with history_lock:
        history.append({"role": "user", "content": user_turn})
        history.append({"role": "assistant", "content": answer})
        used_passages = [passages[sid[t][1]] for t in used_tags if sid[t][0] == "passage"]
        used_files = list(dict.fromkeys(p["filename"] for p in used_passages))[:3]
        last_taught_files[:] = used_files or last_taught_files
    nodes = []
    for t in used_tags:
        kind, ref = sid[t]
        node = ref if kind == "note" else ix.taught_by_file.get(passages[ref]["filename"])
        if node is not None:
            nodes.append(node)
    return HTTPStatus.OK, {
        "intent": intent,
        "answer": answer,
        "spoken": spoken or answer,
        "nodes": list(dict.fromkeys(nodes)),
        "version": ix.version,
        "passages": [{"node": ix.taught_by_file.get(p["filename"]), "source": p["filename"],
                      "chunk": p["chunk"], "text": p["text"]} for p in used_passages],
        "taught_checked": not sentinel_down,
        "brain": brain,
        "brain_note": note,
    }


def brain_status():
    binary, model = local_files()
    with brain_lock:
        mode, skip = brain_mode, claude_skip_until
    return {"mode": mode, "claude_key": bool(claude_key()),
            "claude_out_of_credit": time.time() < skip,
            "local_installed": bool(binary and model), "local_model": model.name if model else None,
            "local_running": local_healthy()}


# Auto-refresh: watch Sentinel's taught catalog and the notes folder; rebuild on change.
import build as galaxy_build  # noqa: E402

WATCH_SECONDS = 60
index_lock = threading.Lock()


def notes_root():
    custom = load_config().get("notes_dir")
    return Path(custom).expanduser() if custom else galaxy_build.DEFAULT_NOTES


build_lock = threading.Lock()   # one rebuild at a time: the watcher or a capture, never both
last_taught = []                # the last good Teach catalog, for when Sentinel blips


def refresh_index(force=False):
    with build_lock:
        return _refresh_index(force)


def _refresh_index(force=False):
    global INDEX
    root = notes_root()
    taught = galaxy_build.fetch_taught_documents()
    if taught:
        last_taught[:] = taught
    if not taught and INDEX.taught_by_file:
        return False  # Sentinel briefly unreachable: keep current graph, don't drop sources
    version = galaxy_build.signature(root, taught)
    if version == INDEX.version and not force:
        return False
    graph = galaxy_build.build(root, taught)
    galaxy_build.write_graph(graph, version)
    with index_lock:
        old = INDEX
        INDEX = Index({**graph, "version": version})
    added = len(INDEX.taught_by_file) - len(old.taught_by_file)
    print(f"Galaxy rebuilt ({version}): {len(INDEX.nodes)} nodes, {added:+d} taught sources", flush=True)
    return True


# ---- Sight: one screen frame + a question -> Claude. --------------------------------------
# Only Claude can see (the local model is text-only). Every request carries a frame grabbed at
# the moment of asking; nothing is cached, and screen answers never enter the chat history, so
# no later answer can lean on an old frame.
SEE_MAX_BYTES = 5 * 1024 * 1024          # the API's per-image limit
SEE_MAX_AGE_S = 15                       # a frame older than this is refused as stale
SEE_SYSTEM_PROMPT = PERSONA + (
    "\nYou are looking at ONE frame of the user's screen, captured the moment they asked. "
    "Answer specifically about what is visible in that frame: headline first (one line), then "
    "the specifics that matter. Do not describe things you cannot actually see, and do not use "
    "the knowledge base. If the frame is too small, blurry, cropped or ambiguous to judge, set "
    "legible to false and say so plainly instead of guessing.\n"
    "\"answer\" is shown on screen (headline first, then at most a few short sentences). "
    "\"spoken\" is read aloud: the headline and the one point that matters, about 30 words at "
    "most. Plain prose, no markdown."
)
SEE_FORMAT = {"type": "json_schema", "schema": {
    "type": "object",
    "properties": {  # legible first: judge the frame before talking about it
        "legible": {"type": "boolean"},
        "answer": {"type": "string"},
        "spoken": {"type": "string"},
    },
    "required": ["legible", "answer", "spoken"],
    "additionalProperties": False,
}}


def sniff_image(data):
    """The media type comes from the bytes themselves, never from a label."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return None


def see(question, image_b64, claimed_type, width, height, captured_at):
    fail = lambda status, reason: (status, {"error": reason, "spoken": SEE_FAIL.format(reason=reason),
                                            "nodes": [], "intent": "screen"})
    question = (question or "").strip()[:2000] or "What am I looking at?"
    age = time.time() - captured_at / 1000 if captured_at else None
    if age is None or age > SEE_MAX_AGE_S or age < -5:
        return fail(HTTPStatus.BAD_REQUEST, "that frame wasn't captured just now, and I won't judge a stale one")
    try:
        data = base64.b64decode(image_b64 or "", validate=True)
    except (ValueError, TypeError):
        return fail(HTTPStatus.BAD_REQUEST, "the frame arrived garbled")
    if not data:
        return fail(HTTPStatus.BAD_REQUEST, "no frame came with the question")
    if len(data) > SEE_MAX_BYTES:
        return fail(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "the frame is too large to send")
    media_type = sniff_image(data)
    if media_type is None:
        return fail(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "the frame isn't a JPEG or PNG image")
    if claimed_type and claimed_type != media_type:
        print(f"[see] browser said {claimed_type} but the bytes are {media_type}; sending {media_type}", flush=True)
    frame = {"width": width, "height": height, "bytes": len(data), "media_type": media_type, "age_s": round(age, 1)}
    print(f"[see] {media_type} {width}x{height} {len(data) // 1024} KB, {age:.1f}s old: {question!r}", flush=True)
    key = claude_key()
    with brain_lock:
        mode, skip_until = brain_mode, claude_skip_until
    # Sight always goes to Claude (the config.json model) whatever the text brain is set to; the
    # small local vision model is only a fallback when Claude can't look, and is labelled as such.
    claude_ok = bool(key) and time.time() >= skip_until
    order = ["claude"] if mode == "claude" else (["claude"] if claude_ok else []) + ["local"]
    note = "" if claude_ok or mode == "claude" else (
        "no Anthropic API key in config.json" if not key else "Claude is out of API credits")
    last_err = None
    for brain in order:
        try:
            if brain == "claude":
                if not key:
                    raise BrainError(HTTPStatus.SERVICE_UNAVAILABLE, "there's no Anthropic API key in config.json")
                content = [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                                 "data": base64.b64encode(data).decode()}},
                    {"type": "text", "text": f"Frame: {width or '?'}x{height or '?'} pixels, captured "
                                             f"{age:.1f}s ago.\n\nQUESTION: {question}"},
                ]
                raw = call_claude(key, load_config().get("model", "claude-opus-5-5"),
                                  [{"role": "user", "content": content}], system=SEE_SYSTEM_PROMPT, fmt=SEE_FORMAT)
                if raw is None:
                    return HTTPStatus.OK, {"intent": "screen", "answer": "Declined to comment on that one.",
                                           "spoken": "Declined to comment on that one.", "nodes": [],
                                           "brain": "claude", "frame": frame}
                try:
                    reply = json.loads(raw)
                except json.JSONDecodeError:
                    raise BrainError(HTTPStatus.BAD_GATEWAY, "Claude's reply came back unreadable")
                answer = str(reply.get("answer") or "").strip()
                if not answer:
                    raise BrainError(HTTPStatus.BAD_GATEWAY, "Claude returned no answer")
                return HTTPStatus.OK, {"intent": "screen", "answer": answer,
                                       "spoken": str(reply.get("spoken") or "").strip() or answer,
                                       "legible": bool(reply.get("legible", True)), "nodes": [],
                                       "brain": "claude", "frame": frame}
            text = call_local_vision(data, media_type, question)
            model, _ = vision_files()
            return HTTPStatus.OK, {"intent": "screen", "answer": tidy(text, 3) or text,
                                   "spoken": tidy(text, 2) or text, "legible": None, "nodes": [],
                                   "brain": "local", "vision_model": model.stem if model else "local",
                                   "brain_note": note, "frame": frame}
        except BrainError as e:
            last_err = e
            if brain == "claude":
                if e.status == HTTPStatus.PAYMENT_REQUIRED:
                    with brain_lock:
                        globals()["claude_skip_until"] = time.time() + CLAUDE_COOLDOWN
                note = e.message.rstrip(".")
                print(f"[see] Claude can't look ({e.message}); trying local vision", flush=True)
    e = last_err or BrainError(HTTPStatus.BAD_GATEWAY, "no brain could look")
    reason = e.message.rstrip(".")
    if e.status == HTTPStatus.PAYMENT_REQUIRED:
        reason = "sight needs Claude, and your Anthropic account is out of API credits"
    return fail(e.status, reason[:1].lower() + reason[1:])


# ---- Local sight: a small vision model (SmolVLM-500M) for when Claude can't look. -------
VISION_DIR = LOCAL_DIR / "vision"
VISION_PORT = 4702
VISION_URL = f"http://127.0.0.1:{VISION_PORT}"
VISION_TIMEOUT = 300
VISION_PROMPT = ("Look at this screenshot of the user's screen. First line: a short headline saying what "
                 "it is. Then at most two short sentences on the specifics that matter. If the image is "
                 "too small or blurry to read, say exactly that instead of guessing.")
vision_proc = None
vision_lock = threading.Lock()


def vision_files():
    model = next(iter(sorted(p for p in VISION_DIR.glob("*.gguf") if not p.name.startswith("mmproj"))), None)
    mmproj = next(iter(sorted(VISION_DIR.glob("mmproj*.gguf"))), None)
    return model, mmproj


def vision_healthy():
    try:
        with urllib.request.urlopen(f"{VISION_URL}/health", timeout=2) as r:
            return r.status == 200
    except (OSError, ValueError):
        return False


def ensure_vision(wait=120):
    global vision_proc
    with vision_lock:
        if vision_healthy():
            return
        binary, _ = local_files()
        model, mmproj = vision_files()
        if not binary or not model or not mmproj:
            raise BrainError(HTTPStatus.SERVICE_UNAVAILABLE, "the local vision model isn't installed")
        if vision_proc is None or vision_proc.poll() is not None:
            vision_proc = subprocess.Popen(
                [str(binary), "-m", str(model), "--mmproj", str(mmproj), "--host", "127.0.0.1",
                 "--port", str(VISION_PORT), "-c", "4096", "-t", str(load_config().get("local_threads") or physical_cores()),
                 "--parallel", "1"],
                env={**os.environ, "LD_LIBRARY_PATH": str(binary.parent)},
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print(f"Starting local vision model {model.name} on {VISION_URL} …", flush=True)
        deadline = time.time() + wait
        while time.time() < deadline:
            if vision_healthy():
                return
            if vision_proc.poll() is not None:
                raise BrainError(HTTPStatus.BAD_GATEWAY, "the local vision model failed to start")
            time.sleep(0.5)
        raise BrainError(HTTPStatus.GATEWAY_TIMEOUT, "the local vision model is still loading")


def stop_vision():
    if vision_proc is not None and vision_proc.poll() is None:
        vision_proc.terminate()


def call_local_vision(data, media_type, question):
    if heat_status()["level"] == "critical":
        raise BrainError(HTTPStatus.SERVICE_UNAVAILABLE, "the CPU is critically hot, so local vision is paused")
    ensure_vision()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64," + base64.b64encode(data).decode()}},
        {"type": "text", "text": f"{VISION_PROMPT}\n\nThe user asks: {question}"}]}],
        "max_tokens": 160, "temperature": 0.1, "repeat_penalty": 1.15}).encode()
    req = urllib.request.Request(f"{VISION_URL}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=VISION_TIMEOUT) as r:
            reply = json.load(r)
    except (OSError, ValueError) as e:
        raise BrainError(HTTPStatus.BAD_GATEWAY, f"the local vision model didn't answer ({e.__class__.__name__})")
    text = (reply.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise BrainError(HTTPStatus.BAD_GATEWAY, "the local vision model returned nothing")
    return text


# ---- Captures: "remember that …" -> a real markdown note, indexed and linked immediately ----
REMEMBER_RE = re.compile(r"^\W*(?:please\s+)?remember\s+(?:that\s+)?", re.I)


def capture_title(text, max_words=6):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'.\-]*", text)
    while words and words[0].lower() in ("the", "a", "an", "that"):
        words = words[1:]
    title = " ".join(words[:max_words]).rstrip(".")
    return (title[:1].upper() + title[1:]) if title else "Capture"


def node_key(n):
    return (bool(n.get("taught")), n["path"])


def index_capture(root, rel):
    """Rebuild with build.py's own linker, but keep every existing node id and append the new
    one, so the running page can add a single star instead of reloading."""
    global INDEX
    taught = galaxy_build.fetch_taught_documents() or list(last_taught)
    full = galaxy_build.build(root, taught)
    version = galaxy_build.signature(root, taught)
    old_keys = [node_key(n) for n in INDEX.nodes]
    by_key = {node_key(n): n for n in full["nodes"]}
    new_key = (False, rel)
    if new_key not in by_key:
        raise RuntimeError("the indexer didn't pick the file up")
    stable = set(by_key) == set(old_keys) | {new_key}
    if stable:
        order = old_keys + [new_key]
        pos = {k: i for i, k in enumerate(order)}
        full_keys = [node_key(n) for n in full["nodes"]]
        pairs = {tuple(sorted((pos[full_keys[l["source"]]], pos[full_keys[l["target"]]]))) for l in full["links"]}
        graph = {"nodes": [{**by_key[k], "id": i} for i, k in enumerate(order)],
                 "links": [{"source": a, "target": b} for a, b in sorted(pairs)]}
    else:  # other notes changed too: ids may shift, so the page must reload
        graph = full
    galaxy_build.write_graph(graph, version)
    with index_lock:
        INDEX = Index({**graph, "version": version})
    new_id = next(n["id"] for n in graph["nodes"] if node_key(n) == new_key)
    links = [l for l in graph["links"] if new_id in (l["source"], l["target"])]
    return INDEX, new_id, links, not stable


def remember(text, via="typed"):
    body = REMEMBER_RE.sub("", text, count=1).strip()
    fail = lambda status, reason: (status, {"ok": False, "saved": False, "error": reason,
                                            "spoken": REMEMBER_FAIL.format(reason=reason)})
    if len(body) < 3:
        return fail(HTTPStatus.BAD_REQUEST, "there was nothing after \"remember that\"")
    body = body[:1].upper() + body[1:]
    if not body.endswith((".", "?", "!")):
        body += "."
    title = capture_title(body)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "capture"
    root = notes_root()
    try:
        folder = root / CAPTURE_DIR
        folder.mkdir(parents=True, exist_ok=True)
        path, n = folder / f"{slug}.md", 2
        while path.exists():
            path, n = folder / f"{slug}-{n}.md", n + 1
        content = (f"# {title}\n\nCaptured: {time.strftime('%Y-%m-%d %H:%M')} ({via})\n\n{body}\n")
        tmp = path.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        if path.read_text(encoding="utf-8") != content:  # trust, but verify
            raise OSError("the file didn't read back correctly")
    except OSError as e:
        print(f"[remember] WRITE FAILED: {e!r}", flush=True)
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"I couldn't write the file ({e.strerror or e})")
    rel = str(path.relative_to(root))
    print(f"[remember] saved {rel}", flush=True)
    try:
        with build_lock:
            ix, new_id, links, reload = index_capture(root, rel)
    except Exception as e:
        reason = str(e) or e.__class__.__name__
        print(f"[remember] INDEX FAILED for {rel}: {e!r}", flush=True)
        return HTTPStatus.INTERNAL_SERVER_ERROR, {
            "ok": False, "saved": True, "path": rel, "error": f"saved but not indexed: {reason}",
            "spoken": REMEMBER_UNINDEXED.format(title=title, reason=reason)}
    nbr = {l["source"] if l["target"] == new_id else l["target"] for l in links}
    # Birthplace: the most related existing note, preferring one it's actually linked to.
    ranked = [i for i in rank(ix, body) if i != new_id]
    related = next((i for i in ranked if i in nbr), None)
    related = related if related is not None else (ranked[0] if ranked else (min(nbr) if nbr else None))
    print(f"[remember] indexed as node {new_id} with {len(links)} links (born near {related})", flush=True)
    return HTTPStatus.OK, {
        "ok": True, "saved": True, "path": rel, "title": title, "node": ix.nodes[new_id],
        "links": links, "related": related, "version": ix.version, "reload": reload,
        "spoken": REMEMBER_OK.format(title=title)}


def watch_loop():
    while True:
        try:
            refresh_index()
        except Exception as e:  # keep watching even if one pass fails
            print(f"Galaxy refresh failed: {e!r}", flush=True)
        time.sleep(WATCH_SECONDS)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIEWER), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/graph-version":
            ix = INDEX
            return self._json(HTTPStatus.OK, {
                "version": ix.version, "taught": len(ix.taught_by_file),
                "notes": len(ix.nodes) - len(ix.taught_by_file)})
        if self.path.split("?")[0] == "/brain":
            return self._json(HTTPStatus.OK, brain_status())
        if self.path.split("?")[0] == "/heat":
            return self._json(HTTPStatus.OK, heat_status())
        if self.path.split("?")[0] == "/persona":
            return self._json(HTTPStatus.OK, {"greeting": BOOT_GREETING, "remember_fail": REMEMBER_FAIL,
                                              "see_no_share": SEE_NO_SHARE, "see_ended": SEE_ENDED,
                                              "see_fail": SEE_FAIL})
        return super().do_GET()

    def do_POST(self):
        if self.path == "/heat":  # testing: {"simulate": 95} fakes the sensor, {"simulate": null} stops
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 1000)
                sim = json.loads(self.rfile.read(length) or b"{}").get("simulate")
                sim = None if sim is None else float(sim)
            except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "Send {\"simulate\": 95} or {\"simulate\": null}"})
            with heat_lock:
                heat["simulated"] = sim
            return self._json(HTTPStatus.OK, heat_status())
        if self.path == "/brain":
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 1000)
                mode = json.loads(self.rfile.read(length) or b"{}").get("mode")
            except (ValueError, json.JSONDecodeError, AttributeError):
                mode = None
            if mode not in BRAINS:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": f"mode must be one of {BRAINS}"})
            set_brain(mode)
            return self._json(HTTPStatus.OK, brain_status())
        if self.path == "/see":
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > SEE_MAX_BYTES * 2:
                    raise ValueError("too large")
                data = json.loads(self.rfile.read(length) or b"{}")
                status, payload = see(str(data.get("question", "")), data.get("image"),
                                      data.get("media_type"), data.get("width"), data.get("height"),
                                      float(data.get("captured_at") or 0))
            except (ValueError, TypeError, json.JSONDecodeError, AttributeError) as e:
                reason = "the frame was too large or garbled"
                status, payload = HTTPStatus.BAD_REQUEST, {"error": reason, "nodes": [], "intent": "screen",
                                                           "spoken": SEE_FAIL.format(reason=reason)}
            except Exception as e:  # never fail silently
                self.log_error("see failed: %r", e)
                reason = f"an internal error ({e.__class__.__name__})"
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {
                    "error": reason, "nodes": [], "intent": "screen", "spoken": SEE_FAIL.format(reason=reason)}
            return self._json(status, payload)
        if self.path == "/remember":
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 20_000)
                data = json.loads(self.rfile.read(length) or b"{}")
                text = str(data.get("text", ""))[:4000]
                via = "voice" if data.get("via") == "voice" else "typed"
            except (ValueError, json.JSONDecodeError, AttributeError):
                reason = "the request was garbled"
                return self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "saved": False, "error": reason,
                                                           "spoken": REMEMBER_FAIL.format(reason=reason)})
            try:
                status, payload = remember(text, via)
            except Exception as e:  # a capture must never fail silently
                self.log_error("remember failed: %r", e)
                reason = f"an internal error ({e.__class__.__name__})"
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {
                    "ok": False, "saved": False, "error": reason, "spoken": REMEMBER_FAIL.format(reason=reason)}
            return self._json(status, payload)
        if self.path != "/chat":
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 20_000)
            data = json.loads(self.rfile.read(length) or b"{}")
            question = str(data.get("question", "")).strip()[:2000]
        except (ValueError, json.JSONDecodeError):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Send JSON: {\"question\": \"...\"}"})
        if data.get("reset"):
            with history_lock:
                history.clear()
                last_taught_files.clear()
            return self._json(HTTPStatus.OK, {"answer": "Conversation cleared.", "nodes": []})
        if not question:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Ask a question.", "nodes": []})
        try:
            status, payload = ask_brain(question)
        except Exception as e:  # never crash the server on one bad request
            self.log_error("chat failed: %r", e)
            status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Chat failed on the server.", "nodes": []}
        self._json(status, payload)


if __name__ == "__main__":
    threading.Thread(target=lambda: embed("warm up"), daemon=True).start()
    threading.Thread(target=watch_loop, daemon=True).start()
    threading.Thread(target=heat_loop, daemon=True).start()
    atexit.register(stop_local)
    atexit.register(stop_vision)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    if brain_mode == "local" or (brain_mode == "auto" and not claude_key()):
        threading.Thread(target=lambda: ensure_local() if all(local_files()) else None, daemon=True).start()
    print(f"Knowledge galaxy: http://{HOST}:{PORT}/  ({len(INDEX.nodes) - len(INDEX.taught_by_file)} notes, "
          f"{len(INDEX.taught_by_file)} taught sources; watching Sentinel every {WATCH_SECONDS}s; brain: {brain_mode})", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
