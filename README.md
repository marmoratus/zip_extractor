# zip_extractor
Multithreaded ZIP extraction with diff copy functionality in Python

## Features

- Extracts ZIP archives using a pool of worker threads for faster I/O-bound processing
- SHA256-based diff copy: files whose content already matches the destination are skipped, avoiding unnecessary writes
- Live progress reporting (processed / created / updated / skipped / errors)
- No backup files are created; this tool only extracts and diff-copies

## Project Layout

```
zip_extractor/
├── src/
│   ├── __init__.py
│   ├── thread_pool.py    # Worker thread pool
│   ├── diff_copy.py      # File hashing and differential copy
│   ├── zip_extractor.py  # ZIP extraction orchestration
│   ├── progress.py       # Thread-safe progress tracking
│   └── main.py           # CLI entry point
├── tests/                 # Unit tests
├── requirements.txt
├── setup.py
└── README.md
```

## Usage

### Command line

```bash
python -m src.main path/to/archive.zip path/to/destination --workers 8
```

Options:

- `-w`, `--workers`: number of worker threads (default: `CPU count x 4`)
- `--no-progress`: disable the live progress output

### As a library

```python
from src.zip_extractor import extract_zip

summary = extract_zip("archive.zip", "destination/", num_workers=8)
print(summary.total, summary.created, summary.updated, summary.skipped, summary.errors)
```

Re-running `extract_zip` against the same destination will skip any files whose
SHA256 hash already matches what's on disk, only writing files that are new or
have changed.

## Running tests

```bash
python -m unittest discover -s tests -v
```
