"""Multithreaded ZIP extraction with differential copy.

Extracts the contents of a ZIP archive into a destination directory,
processing multiple archive members in parallel worker threads. Each
file is only written to disk if its content (compared via SHA256 hash)
differs from what already exists at the destination, which makes
repeated extractions of the same archive fast and avoids needless
writes. Backups of overwritten files are intentionally not created.
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional

from .diff_copy import CopyResult, CopyStatus, diff_copy_bytes
from .progress import ProgressTracker
from .thread_pool import ThreadPool


@dataclass
class ExtractionSummary:
    """Aggregate result of extracting a ZIP archive."""

    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    results: List[CopyResult] = field(default_factory=list)

    @property
    def error_results(self) -> List[CopyResult]:
        return [r for r in self.results if r.status == CopyStatus.ERROR]


def _extract_member(zip_path: str, member: str, dest_path: str) -> CopyResult:
    """Read a single member from the ZIP archive and diff-copy it to disk.

    Opens the archive independently for each call so that this function
    can safely be run concurrently from multiple worker threads
    (``zipfile.ZipFile`` objects are not guaranteed to be thread-safe for
    concurrent reads).
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        data = zf.read(member)
    return diff_copy_bytes(data, dest_path, filename=member)


class ZipExtractor:
    """Extracts a ZIP archive using a pool of worker threads."""

    def __init__(
        self,
        zip_path: str,
        dest_dir: str,
        num_workers: Optional[int] = None,
        show_progress: bool = True,
    ):
        self.zip_path = zip_path
        self.dest_dir = dest_dir
        self.num_workers = num_workers
        self.show_progress = show_progress

    def extract(self) -> ExtractionSummary:
        """Extract the archive, returning an :class:`ExtractionSummary`."""
        if not os.path.isfile(self.zip_path):
            raise FileNotFoundError(f"ZIP file not found: {self.zip_path}")

        os.makedirs(self.dest_dir, exist_ok=True)

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            infos = zf.infolist()

        # Directories are created up-front; only files are diff-copied.
        file_members = []
        for info in infos:
            dest_path = os.path.join(self.dest_dir, info.filename)
            if info.is_dir():
                os.makedirs(dest_path, exist_ok=True)
                continue
            file_members.append(info.filename)

        summary = ExtractionSummary(total=len(file_members))
        tracker = ProgressTracker(total=len(file_members), show_progress=self.show_progress)

        if not file_members:
            return summary

        def worker(member: str) -> CopyResult:
            dest_path = os.path.join(self.dest_dir, member)
            return _extract_member(self.zip_path, member, dest_path)

        with ThreadPool(self.num_workers) as pool:
            for result in pool.map_unordered(worker, file_members):
                summary.results.append(result)
                tracker.update(result.status.value if isinstance(result.status, CopyStatus) else result.status)
                if result.status == CopyStatus.CREATED:
                    summary.created += 1
                elif result.status == CopyStatus.UPDATED:
                    summary.updated += 1
                elif result.status == CopyStatus.SKIPPED:
                    summary.skipped += 1
                elif result.status == CopyStatus.ERROR:
                    summary.errors += 1

        return summary


def extract_zip(
    zip_path: str,
    dest_dir: str,
    num_workers: Optional[int] = None,
    show_progress: bool = True,
) -> ExtractionSummary:
    """Convenience function to extract a ZIP archive with diff copy."""
    return ZipExtractor(
        zip_path,
        dest_dir,
        num_workers=num_workers,
        show_progress=show_progress,
    ).extract()
