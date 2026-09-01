"""Thread-safe progress tracking for long-running batch operations."""

from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass


@dataclass
class ProgressSummary:
    """Snapshot of progress counters."""

    total: int
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    elapsed: float = 0.0


class ProgressTracker:
    """Tracks and reports progress across multiple worker threads.

    All public methods are safe to call concurrently from multiple
    threads.
    """

    def __init__(self, total: int, show_progress: bool = True, stream=None):
        self._lock = threading.Lock()
        self.total = total
        self.processed = 0
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.errors = 0
        self.show_progress = show_progress
        self._stream = stream if stream is not None else sys.stdout
        self._start_time = time.monotonic()

    def update(self, status: str) -> ProgressSummary:
        """Record completion of one item with the given ``status``.

        ``status`` is expected to be one of ``created``, ``updated``,
        ``skipped`` or ``error`` (matching ``diff_copy.CopyStatus``
        values), but any unrecognized status is still counted towards
        ``processed``.
        """
        with self._lock:
            self.processed += 1
            if status == "created":
                self.created += 1
            elif status == "updated":
                self.updated += 1
            elif status == "skipped":
                self.skipped += 1
            elif status == "error":
                self.errors += 1

            summary = self._summary_locked()

        if self.show_progress:
            self._render(summary)

        return summary

    def _summary_locked(self) -> ProgressSummary:
        return ProgressSummary(
            total=self.total,
            processed=self.processed,
            created=self.created,
            updated=self.updated,
            skipped=self.skipped,
            errors=self.errors,
            elapsed=time.monotonic() - self._start_time,
        )

    def summary(self) -> ProgressSummary:
        with self._lock:
            return self._summary_locked()

    def _render(self, summary: ProgressSummary) -> None:
        pct = (summary.processed / summary.total * 100) if summary.total else 100.0
        line = (
            f"\r[{pct:6.2f}%] {summary.processed}/{summary.total} "
            f"created={summary.created} updated={summary.updated} "
            f"skipped={summary.skipped} errors={summary.errors}"
        )
        self._stream.write(line)
        if summary.processed >= summary.total:
            self._stream.write("\n")
        self._stream.flush()
