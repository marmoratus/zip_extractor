"""File hashing and differential copy utilities.

Provides SHA256-based hashing of files/bytes and a ``diff_copy`` helper
that only writes a file to its destination when the content differs from
what is already there (determined by comparing hashes). This avoids
unnecessary disk writes when re-extracting a ZIP archive whose contents
have not changed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from enum import Enum

DEFAULT_CHUNK_SIZE = 65536


class CopyStatus(str, Enum):
    """Outcome of a diff-copy operation."""

    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CopyResult:
    """Result of copying a single file."""

    filename: str
    status: CopyStatus
    size: int = 0
    error: str | None = None


def compute_sha256(filepath: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str | None:
    """Compute the SHA256 hex digest of a file.

    Returns ``None`` if the file does not exist.
    """
    if not os.path.isfile(filepath):
        return None

    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Compute the SHA256 hex digest of an in-memory bytes object."""
    return hashlib.sha256(data).hexdigest()


def diff_copy_bytes(data: bytes, dst_path: str, filename: str = "") -> CopyResult:
    """Write ``data`` to ``dst_path`` unless an identical file already exists.

    Compares the SHA256 hash of ``data`` against the existing destination
    file (if any) and skips the write when they match.
    """
    filename = filename or os.path.basename(dst_path)
    try:
        dst_exists = os.path.isfile(dst_path)
        if dst_exists:
            existing_hash = compute_sha256(dst_path)
            new_hash = compute_bytes_sha256(data)
            if existing_hash == new_hash:
                return CopyResult(filename=filename, status=CopyStatus.SKIPPED, size=len(data))

        dst_dir = os.path.dirname(dst_path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)

        tmp_path = f"{dst_path}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(data)
        os.replace(tmp_path, dst_path)

        status = CopyStatus.UPDATED if dst_exists else CopyStatus.CREATED
        return CopyResult(filename=filename, status=status, size=len(data))
    except OSError as exc:
        return CopyResult(filename=filename, status=CopyStatus.ERROR, error=str(exc))


def diff_copy_file(src_path: str, dst_path: str, filename: str = "") -> CopyResult:
    """Copy ``src_path`` to ``dst_path`` unless they already have the same content."""
    filename = filename or os.path.basename(dst_path)
    try:
        dst_exists = os.path.isfile(dst_path)
        if dst_exists:
            src_hash = compute_sha256(src_path)
            dst_hash = compute_sha256(dst_path)
            if src_hash == dst_hash:
                size = os.path.getsize(dst_path)
                return CopyResult(filename=filename, status=CopyStatus.SKIPPED, size=size)

        dst_dir = os.path.dirname(dst_path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)

        tmp_path = f"{dst_path}.tmp"
        shutil.copyfile(src_path, tmp_path)
        os.replace(tmp_path, dst_path)

        size = os.path.getsize(dst_path)
        status = CopyStatus.UPDATED if dst_exists else CopyStatus.CREATED
        return CopyResult(filename=filename, status=status, size=size)
    except OSError as exc:
        return CopyResult(filename=filename, status=CopyStatus.ERROR, error=str(exc))
