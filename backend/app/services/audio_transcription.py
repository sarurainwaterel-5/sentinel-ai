"""Local, bounded video speech transcription with timestamped provenance."""
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile

from fastapi import HTTPException

MAX_SECONDS = 7200
MAX_TRANSCRIPT_BYTES = 8 * 1024 * 1024
MAX_PCM_BYTES = 16000 * 2 * MAX_SECONDS + 1024 * 1024


def model_directory():
    return Path(os.getenv('SENTINEL_WHISPER_MODEL_DIR', '/opt/sentinel-models/whisper-base'))


def available():
    directory = model_directory()
    return (all(shutil.which(tool) for tool in ('ffmpeg', 'ffprobe', 'prlimit'))
            and importlib.util.find_spec('faster_whisper') is not None
            and all((directory / name).is_file() for name in ('config.json', 'model.bin', 'tokenizer.json')))


def transcribe_video(path, duration, progress=None):
    if not math.isfinite(duration) or not 0 < duration <= MAX_SECONDS:
        raise HTTPException(422, 'Video audio exceeds the transcription duration limit.')
    if not available():
        raise HTTPException(503, 'Local speech transcription is unavailable; the recording is preserved.')
    from app.services.media_extraction import _run
    if progress:
        progress({'phase': 'audio_transcription'})
    with tempfile.TemporaryDirectory(prefix='sentinel-speech-') as directory:
        audio = Path(directory) / 'audio.wav'
        _run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '1',
              '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm',
              '-i', str(path), '-map', '0:a:0', '-vn', '-sn', '-t', str(duration),
              '-ar', '16000', '-ac', '1', '-af', 'aresample=async=1:first_pts=0',
              '-c:a', 'pcm_s16le', '-y', str(audio)], timeout=300,
             output_limit=MAX_PCM_BYTES, cpu_seconds=300)
        if not audio.is_file() or not 44 <= audio.stat().st_size <= MAX_PCM_BYTES:
            raise HTTPException(422, 'The video audio could not be decoded within transcription limits.')
        raw = _run([sys.executable, '-I', str(Path(__file__).with_name('audio_worker.py')),
                    str(audio), str(model_directory()), str(MAX_TRANSCRIPT_BYTES)],
                   timeout=7200, output_limit=MAX_TRANSCRIPT_BYTES,
                   cpu_seconds=7200, memory_bytes=4 * 1024**3)
    return parse_transcript(raw, duration)


def parse_transcript(raw, duration):
    """Reject malformed/partial worker output rather than indexing invented timing."""
    parts, languages = [], set()
    previous = 0.0
    try:
        if len(raw) > MAX_TRANSCRIPT_BYTES:
            raise ValueError('transcript_limit')
        for line in raw.decode('utf-8', errors='strict').splitlines():
            row = json.loads(line)
            start, end, text = row['start'], row['end'], row['text']
            if (type(start) not in (int, float) or type(end) not in (int, float)
                    or not math.isfinite(start) or not math.isfinite(end)
                    or start < previous or start >= duration or not 0 <= start < end <= duration + 1
                    or not isinstance(text, str) or not text.strip() or '\x00' in text):
                raise ValueError('invalid_segment')
            previous = start
            parts.append(f'[Speech {start:.3f}–{min(end, duration):.3f} seconds]\n{text.strip()}')
            language = row.get('language')
            if language is not None:
                if not isinstance(language, str) or not 1 <= len(language) <= 12 or not language.isalpha():
                    raise ValueError('invalid_language')
                languages.add(language)
        text = '\n\n'.join(parts)
        if len(text.encode('utf-8')) > MAX_TRANSCRIPT_BYTES:
            raise ValueError('transcript_limit')
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeError):
        raise HTTPException(422, 'Local speech transcription returned invalid or oversized output.') from None
    return text, {'status': 'completed', 'engine': 'faster_whisper', 'model': model_directory().name, 'segments': len(parts),
                  'languages': sorted(languages), 'timestamps': 'seconds_from_recording_start'}
