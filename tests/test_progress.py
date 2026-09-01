import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.progress import ProgressTracker


class ProgressTrackerTests(unittest.TestCase):
    def test_update_counts_by_status(self):
        tracker = ProgressTracker(total=4, show_progress=False)

        tracker.update("created")
        tracker.update("updated")
        tracker.update("skipped")
        summary = tracker.update("error")

        self.assertEqual(summary.total, 4)
        self.assertEqual(summary.processed, 4)
        self.assertEqual(summary.created, 1)
        self.assertEqual(summary.updated, 1)
        self.assertEqual(summary.skipped, 1)
        self.assertEqual(summary.errors, 1)

    def test_concurrent_updates_are_thread_safe(self):
        import threading

        total = 200
        tracker = ProgressTracker(total=total, show_progress=False)

        def worker():
            for _ in range(total // 10):
                tracker.update("created")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = tracker.summary()
        self.assertEqual(summary.processed, total)
        self.assertEqual(summary.created, total)


if __name__ == "__main__":
    unittest.main()
