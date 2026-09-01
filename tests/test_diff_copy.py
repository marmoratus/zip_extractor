import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.diff_copy import (
    CopyStatus,
    compute_bytes_sha256,
    compute_sha256,
    diff_copy_bytes,
    diff_copy_file,
)


class ComputeHashTests(unittest.TestCase):
    def test_compute_sha256_missing_file_returns_none(self):
        self.assertIsNone(compute_sha256("/nonexistent/path/does/not/exist"))

    def test_compute_sha256_matches_bytes_hash(self, tmp_path=None):
        import tempfile

        data = b"hello world" * 100
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "file.bin")
            with open(path, "wb") as f:
                f.write(data)
            self.assertEqual(compute_sha256(path), compute_bytes_sha256(data))


class DiffCopyBytesTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.dst_path = os.path.join(self.tmp_dir.name, "sub", "file.txt")

    def test_creates_new_file(self):
        result = diff_copy_bytes(b"content-1", self.dst_path)
        self.assertEqual(result.status, CopyStatus.CREATED)
        self.assertTrue(os.path.isfile(self.dst_path))
        with open(self.dst_path, "rb") as f:
            self.assertEqual(f.read(), b"content-1")

    def test_skips_when_content_unchanged(self):
        diff_copy_bytes(b"content-1", self.dst_path)
        mtime_before = os.path.getmtime(self.dst_path)

        result = diff_copy_bytes(b"content-1", self.dst_path)

        self.assertEqual(result.status, CopyStatus.SKIPPED)
        self.assertEqual(os.path.getmtime(self.dst_path), mtime_before)

    def test_updates_when_content_changed(self):
        diff_copy_bytes(b"content-1", self.dst_path)

        result = diff_copy_bytes(b"content-2", self.dst_path)

        self.assertEqual(result.status, CopyStatus.UPDATED)
        with open(self.dst_path, "rb") as f:
            self.assertEqual(f.read(), b"content-2")

    def test_error_status_on_failure(self):
        # Point destination at a directory to force an OSError.
        result = diff_copy_bytes(b"content", self.tmp_dir.name)
        self.assertEqual(result.status, CopyStatus.ERROR)
        self.assertIsNotNone(result.error)


class DiffCopyFileTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.src_path = os.path.join(self.tmp_dir.name, "src.txt")
        self.dst_path = os.path.join(self.tmp_dir.name, "dst.txt")
        with open(self.src_path, "wb") as f:
            f.write(b"payload")

    def test_creates_new_file(self):
        result = diff_copy_file(self.src_path, self.dst_path)
        self.assertEqual(result.status, CopyStatus.CREATED)
        with open(self.dst_path, "rb") as f:
            self.assertEqual(f.read(), b"payload")

    def test_skips_when_identical(self):
        diff_copy_file(self.src_path, self.dst_path)
        result = diff_copy_file(self.src_path, self.dst_path)
        self.assertEqual(result.status, CopyStatus.SKIPPED)


if __name__ == "__main__":
    unittest.main()
