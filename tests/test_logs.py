import logging
import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path

from throttle.logs import BACKUPS, MAX_BYTES, setup_logging


class LogTests(unittest.TestCase):
    def tearDown(self):
        logging.basicConfig(force=True, handlers=[logging.NullHandler()])

    def test_file_log_rotates(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "throttle.log"
            setup_logging(log_file)
            handler = next(h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler))
            self.assertEqual((handler.maxBytes, handler.backupCount), (MAX_BYTES, BACKUPS))

            handler.maxBytes = 200
            for i in range(50):
                logging.getLogger("throttle.test").info("line %d", i)
            handler.close()
            rotated = sorted(p.name for p in log_file.parent.iterdir())
            self.assertIn("throttle.log.1", rotated)
            self.assertLessEqual(len(rotated), BACKUPS + 1)

    def test_no_file_without_path(self):
        setup_logging(None)
        self.assertFalse(any(isinstance(h, RotatingFileHandler) for h in logging.getLogger().handlers))


if __name__ == "__main__":
    unittest.main()
