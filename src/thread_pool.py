"""Thread pool for running worker tasks in parallel.

A thin wrapper around :class:`concurrent.futures.ThreadPoolExecutor` that
provides a simple ``map``-style API for submitting a batch of tasks and
collecting their results as they complete. Kept as its own module so the
rest of the codebase does not need to depend on ``concurrent.futures``
directly and so the pool sizing/behaviour can be tuned in one place.
"""

from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, Iterator, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ThreadPool:
    """A simple thread pool for executing tasks concurrently.

    Parameters
    ----------
    num_workers:
        Number of worker threads to use. If ``None`` or less than 1, the
        number of CPUs on the machine (plus a small multiplier suitable for
        I/O bound work) is used instead.
    """

    def __init__(self, num_workers: int | None = None):
        if num_workers is None or num_workers < 1:
            num_workers = (os.cpu_count() or 1) * 4
        self.num_workers = num_workers
        self._executor: ThreadPoolExecutor | None = None

    def __enter__(self) -> "ThreadPool":
        self._executor = ThreadPoolExecutor(max_workers=self.num_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None

    def submit(self, fn: Callable[..., R], *args, **kwargs) -> Future:
        """Submit a single task to the pool and return its Future."""
        if self._executor is None:
            raise RuntimeError("ThreadPool must be used as a context manager")
        return self._executor.submit(fn, *args, **kwargs)

    def map_unordered(
        self, fn: Callable[[T], R], items: Iterable[T]
    ) -> Iterator[R]:
        """Run ``fn`` on every item in ``items`` concurrently.

        Results are yielded as soon as they are available, which is not
        necessarily the same order as ``items``. This is useful for
        progress reporting where completion order matters more than
        input order.
        """
        if self._executor is None:
            raise RuntimeError("ThreadPool must be used as a context manager")

        futures = [self._executor.submit(fn, item) for item in items]
        for future in as_completed(futures):
            yield future.result()
