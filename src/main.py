"""Command-line entry point for the multithreaded ZIP extractor."""

from __future__ import annotations

import argparse
import sys
import time

try:
    from .zip_extractor import extract_zip
except ImportError:  # pragma: no cover - allows running as a script
    from zip_extractor import extract_zip


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zip_extractor",
        description=(
            "Extract a ZIP archive using multiple worker threads, "
            "skipping files whose SHA256 hash already matches the destination."
        ),
    )
    parser.add_argument("zip_path", help="Path to the ZIP archive to extract")
    parser.add_argument("dest_dir", help="Directory to extract the archive into")
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help="Number of worker threads to use (default: CPU count x 4)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress output",
    )
    return parser


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    start = time.monotonic()
    try:
        summary = extract_zip(
            args.zip_path,
            args.dest_dir,
            num_workers=args.workers,
            show_progress=not args.no_progress,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    elapsed = time.monotonic() - start
    print(
        f"Done in {elapsed:.2f}s | total={summary.total} "
        f"created={summary.created} updated={summary.updated} "
        f"skipped={summary.skipped} errors={summary.errors}"
    )

    return 1 if summary.errors else 0


if __name__ == "__main__":
    sys.exit(main())
