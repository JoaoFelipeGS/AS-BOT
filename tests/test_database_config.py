import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.config import settings
from backend.database import get_engine


class DatabaseConfigurationTests(unittest.TestCase):
    def test_sqlite_file_url_uses_absolute_path_and_creates_parent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "persistent" / "client.db"
            with patch.object(settings, "database_url", f"sqlite:///{db_path}"):
                engine = get_engine()
            try:
                self.assertEqual(Path(engine.url.database), db_path.resolve())
                with engine.connect() as connection:
                    self.assertEqual(connection.exec_driver_sql("SELECT 1").scalar_one(), 1)
                self.assertTrue(db_path.parent.is_dir())
            finally:
                engine.dispose()

    def test_sqlite_memory_url_is_not_rewritten_to_a_file_path(self):
        with patch.object(settings, "database_url", "sqlite:///:memory:"):
            engine = get_engine()
        try:
            self.assertEqual(engine.url.database, ":memory:")
            with engine.connect() as connection:
                self.assertEqual(connection.exec_driver_sql("SELECT 1").scalar_one(), 1)
        finally:
            engine.dispose()

    def test_sqlite_memory_url_without_database_stays_in_memory(self):
        with patch.object(settings, "database_url", "sqlite://"):
            engine = get_engine()
        try:
            self.assertIsNone(engine.url.database)
            with engine.connect() as connection:
                self.assertEqual(connection.exec_driver_sql("SELECT 1").scalar_one(), 1)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
