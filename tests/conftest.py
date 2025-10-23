import copy
import pytest
import server  

@pytest.fixture
def app():
    server.app.config.update(TESTING=True)
    return server.app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_state():
    """Restaure clubs/competitions après chaque test (server les charge en mémoire)."""
    clubs_backup = copy.deepcopy(server.clubs)
    comps_backup = copy.deepcopy(server.competitions)
    yield
    server.clubs[:] = clubs_backup
    server.competitions[:] = comps_backup
