"""Bounded local extraction; video samples represent visible text, not audio."""
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import warnings as warning_control

from fastapi import HTTPException

MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_PDF_TEXT_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_VIDEO_SECONDS = 7200
MAX_VIDEO_FRAMES = 24
# Import only the installed parser in an isolated interpreter. Stream page text
# rather than building the full document in either application or child memory.
_PDF_EXTRACT_SCRIPT = '''
import sys
from pypdf import PdfReader
limit = int(sys.argv[2])
total = 0
with open(sys.argv[1], 'rb') as source:
    if source.read(5) != b'%PDF-':
        raise ValueError('invalid_pdf')
    source.seek(0)
    reader = PdfReader(source)
    if len(reader.pages) > 1000000:
        raise ValueError('page_limit')
    for page in reader.pages:
        text = page.extract_text()
        if text:
            data = (text + '\\n').encode('utf-8')
            total += len(data)
            if total > limit:
                raise ValueError('text_limit')
            sys.stdout.buffer.write(data)
'''
FORMATS = {'.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg',
           '.jpeg': 'image/jpeg', '.txt': 'text/plain', '.md': 'text/markdown',
           '.csv': 'text/csv', '.json': 'application/json', '.mp4': 'video/mp4',
           '.mov': 'video/quicktime', '.webm': 'video/webm'}


def capabilities():
    ocr = bool(shutil.which('tesseract') and shutil.which('prlimit') and importlib.util.find_spec('PIL'))
    video = ocr and bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))
    return {'formats': [{'extension': extension, 'media_type': media,
                         'available': video if media.startswith('video/') else
                         ocr if media.startswith('image/') else True}
                        for extension, media in FORMATS.items()],
            'image_ocr_available': ocr, 'video_visual_text_available': video,
            'audio_transcription_available': False, 'max_video_seconds': MAX_VIDEO_SECONDS,
            'max_video_frames': MAX_VIDEO_FRAMES}


def _require(*tools):
    if any(not shutil.which(tool) for tool in (*tools, 'prlimit')):
        raise HTTPException(503, 'Local media extraction tools are unavailable.')


def _run(arguments, *, timeout=60, output_limit=MAX_TEXT_BYTES):
    """No shell, bounded process CPU/address space/file writes and wall time."""
    _require(arguments[0])
    command = ['prlimit', '--cpu=60', '--as=2147483648',
               f'--fsize={output_limit}', '--', *arguments]
    with tempfile.TemporaryFile() as output:
        try:
            subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output,
                           stderr=subprocess.DEVNULL, timeout=timeout, check=True,
                           start_new_session=True)
            output.seek(0)
            data = output.read(output_limit + 1)
            if len(data) > output_limit:
                raise ValueError('output_limit')
            return data
        except (OSError, subprocess.SubprocessError, ValueError):
            raise HTTPException(422, 'Local media extraction failed or exceeded its limits.') from None


def _ocr(path):
    _require('tesseract')
    try:
        from PIL import Image
    except ImportError:
        raise HTTPException(503, 'Local image decoding is unavailable.') from None
    try:
        with warning_control.catch_warnings():
            warning_control.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(path) as image:
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                    raise ValueError('image_limit')
                if image.format not in ('PNG', 'JPEG'):
                    raise ValueError('image_format')
                image.load()
                with tempfile.TemporaryDirectory(prefix='sentinel-ocr-') as directory:
                    normalized = Path(directory) / 'image.png'
                    rgb = image.convert('RGB')
                    rgb.thumbnail((4096, 4096))
                    rgb.save(normalized)
                    text = _run(['tesseract', str(normalized), 'stdout', '-l', 'eng', '--psm', '3'])
        return text.decode('utf-8', errors='strict').strip(), {'width': width, 'height': height}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'The image could not be decoded within extraction limits.') from None


def _video(path, progress):
    _require('ffprobe', 'ffmpeg', 'tesseract')
    probe = _run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe',
                  '-format_whitelist', 'mov,matroska,webm', '-show_entries',
                  'format=duration:stream=codec_type,width,height', '-of', 'json', str(path)],
                 timeout=30, output_limit=65536)
    try:
        info = json.loads(probe)
        duration = float(info['format']['duration'])
        streams = info['streams']
        if (not math.isfinite(duration) or not 0 < duration <= MAX_VIDEO_SECONDS
                or type(streams) is not list or len(streams) > 128
                or not any(s.get('codec_type') == 'video' for s in streams)):
            raise ValueError('invalid_video')
        for stream in streams:
            if stream.get('codec_type') == 'video':
                width, height = stream.get('width', 0), stream.get('height', 0)
                if (type(width) is not int or type(height) is not int
                        or width <= 0 or height <= 0 or width * height > MAX_PIXELS):
                    raise ValueError('video_dimensions')
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(422, 'The video is invalid or exceeds extraction limits.') from None
    count = min(MAX_VIDEO_FRAMES, max(1, math.ceil(duration / 30)))
    text_parts = []
    extracted_bytes = 0
    with tempfile.TemporaryDirectory(prefix='sentinel-video-') as directory:
        frame = Path(directory) / 'frame.png'
        for index in range(count):
            timestamp = duration * index / count
            # A successful ffmpeg seek can produce no frame. Never OCR a prior
            # sample under the current timestamp in that case.
            frame.unlink(missing_ok=True)
            _run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '1',
                  '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm',
                  '-ss', f'{timestamp:.3f}', '-i', str(path), '-map', '0:v:0', '-an', '-sn',
                  '-frames:v', '1', '-vf', "scale=1280:1280:force_original_aspect_ratio=decrease",
                  '-threads', '1', '-y', str(frame)], timeout=45)
            text, _ = _ocr(frame)
            if text:
                part = f'[Video frame at {timestamp:.3f} seconds]\n{text}'
                extracted_bytes += len(part.encode('utf-8')) + 2
                if extracted_bytes > MAX_TEXT_BYTES:
                    raise HTTPException(422, 'Extracted video text exceeds the extraction limit.')
                text_parts.append(part)
            if progress:
                progress({'phase': 'video_ocr', 'completed_frames': index + 1, 'total_frames': count})
    return '\n\n'.join(text_parts), {'duration_seconds': duration, 'sampled_frames': count}


def extract_source_text(path, filename, progress=None):
    """Extract retained local bytes; never infer full video or audio understanding."""
    extension = Path(filename).suffix.lower()
    media_type = FORMATS.get(extension)
    if media_type is None:
        raise HTTPException(415, 'This source format is not supported.')
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 ** 3:
        raise HTTPException(422, 'The source is unavailable or exceeds extraction limits.')
    notices, metadata = [], {}
    if extension == '.pdf':
        try:
            text = _run([sys.executable, '-I', '-c', _PDF_EXTRACT_SCRIPT,
                         str(path), str(MAX_PDF_TEXT_BYTES)], timeout=60,
                        output_limit=MAX_PDF_TEXT_BYTES).decode('utf-8', errors='strict')
        except UnicodeError:
            raise HTTPException(422, 'The PDF could not be read within extraction limits.') from None
        method = 'pdf_text'
        if not text.strip():
            notices.append('pdf_has_no_extractable_text_ocr_not_applied')
    elif media_type.startswith('image/'):
        text, metadata = _ocr(path)
        method = 'tesseract_english_ocr'
        if not text:
            notices.append('image_has_no_readable_text')
    elif media_type.startswith('video/'):
        text, metadata = _video(path, progress)
        method = 'sampled_video_frame_ocr'
        notices.extend(['audio_not_transcribed', 'video_sampling_incomplete', 'embedded_subtitles_not_extracted'])
        if not text:
            notices.append('video_has_no_readable_sampled_text')
    else:
        try:
            with path.open('rb') as source:
                data = source.read(MAX_TEXT_BYTES + 1)
            if len(data) > MAX_TEXT_BYTES:
                raise ValueError('text_limit')
            text = data.decode('utf-8-sig')
            if '\x00' in text:
                raise ValueError('binary_text')
            if extension == '.json':
                json.loads(text)
        except (OSError, ValueError, UnicodeError, RecursionError):
            raise HTTPException(422, 'The text source must contain bounded valid UTF-8 content.') from None
        method = 'utf8_text'
    if len(text.encode('utf-8')) > (MAX_PDF_TEXT_BYTES if extension == '.pdf' else MAX_TEXT_BYTES):
        raise HTTPException(422, 'Extracted text exceeds the extraction limit.')
    return {'text': text, 'media_type': media_type, 'extraction_method': method,
            'warnings': notices, 'metadata': metadata}
