import pytest

import app.db.database as db_module
from app.services.chat_session import clear_sessions


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db_path = tmp_path / "pytest.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    db_module._db_path = str(db_path)
    db_module._initialized = False
    db_module.init_db(force=True)
    clear_sessions()
    yield
    clear_sessions()
