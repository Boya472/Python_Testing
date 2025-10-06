import os
import sys

# Ajout du dossier parent (là où se trouve server.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import server  # ✅ pas .py ici !
import pytest
import copy




@pytest.fixture
def app():
    server.app.config["TESTING"] = True
    return server.app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_state():
    """
    Sauvegarde et restaure l'état global (clubs/competitions) pour isoler les tests.
    """
    clubs_backup = copy.deepcopy(server.clubs)
    comps_backup = copy.deepcopy(server.competitions)
    yield
    server.clubs[:] = clubs_backup  # restaure in-place
    server.competitions[:] = comps_backup
