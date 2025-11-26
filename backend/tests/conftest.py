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


@pytest.fixture(autouse=True)
def fake_email_client(monkeypatch):
    class FakeEmailClient:
        def __init__(self):
            self.sent = []
            self.should_fail = False

        def send_temporary_password_email(self, to_email, password, parent_name=None):
            self.sent.append({
                'to_email': to_email,
                'password': password,
                'parent_name': parent_name,
            })
            if self.should_fail:
                raise RuntimeError('simulated email failure')

    client = FakeEmailClient()
    monkeypatch.setattr('app.api.parents.gmail_client', client)
    yield client
