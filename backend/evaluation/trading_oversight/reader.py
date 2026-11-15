"""Bounded local regular-file reads. No links, credentials, URLs or service clients."""
from __future__ import annotations

import os
import stat
from pathlib import Path

MAX_INPUT_BYTES = 1024 * 1024


def read_bounded_file(path: str | Path, *, max_bytes: int = MAX_INPUT_BYTES) -> bytes:
    return read_local(path, maximum=max_bytes)


def open_directory(path: str | Path) -> int:
    """Open each directory component without following a symbolic link."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in absolute.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_local(path: str | Path, *, maximum: int = MAX_INPUT_BYTES) -> bytes:
    path = Path(os.path.abspath(os.fspath(path)))
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise ValueError('input must be a bounded regular file')
            chunks = bytearray()
            while len(chunks) <= maximum:
                piece = os.read(fd, min(65536, maximum + 1 - len(chunks)))
                if not piece:
                    break
                chunks.extend(piece)
            after = os.fstat(fd)
            if len(chunks) > maximum or len(chunks) != before.st_size or (
                before.st_size, before.st_mtime_ns, before.st_ctime_ns
            ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError('input changed during bounded read')
            return bytes(chunks)
        finally:
            os.close(fd)
    finally:
        os.close(parent)
