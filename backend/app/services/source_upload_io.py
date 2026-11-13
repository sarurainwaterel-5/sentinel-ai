"""Bounded local source intake; folder paths are metadata, never storage paths."""
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException

READABLE_FORMATS = ('pdf', 'png', 'jpg', 'jpeg', 'txt', 'md', 'csv', 'json', 'mp4', 'mov', 'webm')
IMAGE_FORMATS = {'png', 'jpg', 'jpeg'}
TEXT_FORMATS = {'txt', 'md', 'csv', 'json'}
VIDEO_FORMATS = {'mp4', 'mov', 'webm'}


def validate_relative_path(value, filename):
    if not value:
        return None
    if (len(value) > 1024 or value.startswith('/') or '\\' in value
            or any(ord(c) < 32 for c in value) or ':' in value):
        raise HTTPException(422, 'Folder paths must be relative source labels.')
    parts = value.split('/')
    if len(parts) > 32 or any(p in ('', '.', '..') for p in parts) or parts[-1] != filename:
        raise HTTPException(422, 'Folder paths must match the source filename without traversal.')
    return value


def source_limit(filename, max_bytes):
    extension = Path(filename).suffix.lower().lstrip('.')
    cap = 32 * 1024**2 if extension in IMAGE_FORMATS else 16 * 1024**2 if extension in TEXT_FORMATS else max_bytes
    return min(max_bytes, cap)


async def save_source_upload(file, directory, max_bytes):
    filename = file.filename or ''
    if (not filename or len(filename) > 255 or filename in ('.', '..')
            or '/' in filename or '\\' in filename or any(ord(c) < 32 for c in filename)):
        raise HTTPException(400, 'A plain source filename is required.')
    extension = Path(filename).suffix.lower().lstrip('.')
    suffix = '.' + extension if extension in READABLE_FORMATS else '.bin'
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (str(uuid4()) + suffix)
    header = bytearray()
    size = 0
    try:
        with path.open('xb') as output:
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > source_limit(filename, max_bytes):
                    raise HTTPException(413, 'Source exceeds its upload size limit.')
                if len(header) < 32:
                    header.extend(chunk[:32-len(header)])
                output.write(chunk)
        if not size:
            raise HTTPException(422, 'Empty sources cannot be uploaded.')
        signature = bytes(header)
        valid = (extension != 'pdf' or signature.startswith(b'%PDF-'))
        valid &= extension != 'png' or signature.startswith(b'\x89PNG\r\n\x1a\n')
        valid &= extension not in ('jpg', 'jpeg') or signature.startswith(b'\xff\xd8\xff')
        valid &= extension not in ('mp4', 'mov') or signature[4:8] == b'ftyp'
        valid &= extension != 'webm' or signature.startswith(b'\x1aE\xdf\xa3')
        if not valid:
            raise HTTPException(415, 'The source content does not match its file extension.')
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path, filename
