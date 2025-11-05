import pytest


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    # use sqlite file in tmp path for isolation
    from sqlmodel import create_engine
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file}"
    new_engine = create_engine(url, echo=False)
    import app.db as dbmod
    # monkeypatch get_engine to return our temp engine
    monkeypatch.setattr(dbmod, "get_engine", lambda: new_engine)
    dbmod.init_db()
    yield
