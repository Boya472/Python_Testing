# tests/unit/test_auth.py
from flask import url_for

def test_login_success(client):
    resp = client.post("/showSummary", data={"email": "john@simplylift.co"}, follow_redirects=True)
    assert resp.status_code == 200
    # Message de succès et présence du nom/points
    assert b"Connexion r" in resp.data  # "Connexion r\u00e9ussie..." (on évite l'accent strict)
    assert b"Welcome" in resp.data

def test_login_unknown_email(client):
    resp = client.post("/showSummary", data={"email": "foo@bar.com"}, follow_redirects=True)
    assert resp.status_code == 200
    # Devrait revenir à l'accueil avec message d'erreur
    assert b"Adresse email inconnue" in resp.data
    assert b"Registration Portal" in resp.data  # index.html
