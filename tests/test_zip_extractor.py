import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.diff_copy import CopyStatus
from src.zip_extractor import ZipExtractor, extract_zip


def _make_zip(zip_path, files):
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


class ZipExtractorTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.zip_path = os.path.join(self.tmp_dir.name, "archive.zip")
        self.dest_dir = os.path.join(self.tmp_dir.name, "out")

    def test_extract_missing_zip_raises(self):
        extractor = ZipExtractor(
            os.path.join(self.tmp_dir.name, "missing.zip"), self.dest_dir
        )
        with self.assertRaises(FileNotFoundError):
            extractor.extract()

    def test_extract_creates_all_files(self):
        files = {f"file{i}.txt": f"content-{i}".encode() for i in range(20)}
        files["dir/nested.txt"] = b"nested-content"
        _make_zip(self.zip_path, files)

        summary = extract_zip(
            self.zip_path, self.dest_dir, num_workers=4, show_progress=False
        )

        self.assertEqual(summary.total, len(files))
        self.assertEqual(summary.created, len(files))
        self.assertEqual(summary.updated, 0)
        self.assertEqual(summary.skipped, 0)
        self.assertEqual(summary.errors, 0)

        for name, content in files.items():
            path = os.path.join(self.dest_dir, name)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), content)

    def test_second_extract_skips_unchanged_files(self):
        files = {f"file{i}.txt": f"content-{i}".encode() for i in range(10)}
        _make_zip(self.zip_path, files)

        extract_zip(self.zip_path, self.dest_dir, num_workers=4, show_progress=False)
        summary = extract_zip(
            self.zip_path, self.dest_dir, num_workers=4, show_progress=False
        )

        self.assertEqual(summary.created, 0)
        self.assertEqual(summary.skipped, len(files))
        self.assertEqual(summary.updated, 0)
        self.assertEqual(summary.errors, 0)

    def test_extract_updates_changed_files(self):
        files = {"file.txt": b"original"}
        _make_zip(self.zip_path, files)
        extract_zip(self.zip_path, self.dest_dir, num_workers=2, show_progress=False)

        _make_zip(self.zip_path, {"file.txt": b"changed"})
        summary = extract_zip(
            self.zip_path, self.dest_dir, num_workers=2, show_progress=False
        )

        self.assertEqual(summary.updated, 1)
        with open(os.path.join(self.dest_dir, "file.txt"), "rb") as f:
            self.assertEqual(f.read(), b"changed")

    def test_extract_empty_zip(self):
        _make_zip(self.zip_path, {})

        summary = extract_zip(self.zip_path, self.dest_dir, show_progress=False)

        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.errors, 0)


if __name__ == "__main__":
    unittest.main()
