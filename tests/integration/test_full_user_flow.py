# tests/integration/test_full_user_flow.py
from server import clubs, competitions

def test_full_booking_flow(client):
    """
    Scénario complet : connexion + réservation + vérification des points.
    """

    # 1️⃣ Étape 1 : connexion du secrétaire
    resp = client.post("/showSummary", data={"email": "john@simplylift.co"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Connexion" in resp.data or b"Welcome" in resp.data

    # 2️⃣ Étape 2 : accéder à une compétition
    club = next(c for c in clubs if c["name"] == "Simply Lift")
    competition = next(c for c in competitions if c["name"] == "Spring Festival")

    starting_points = club["points"]
    starting_places = competition["numberOfPlaces"]

    # 3️⃣ Étape 3 : réserver 3 places
    resp = client.post(
        "/purchasePlaces",
        data={"club": club["name"], "competition": competition["name"], "places": "3"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"R" in resp.data or b"r" in resp.data  # message succès

    # 4️⃣ Étape 4 : vérifier la mise à jour des données
    assert club["points"] == starting_points - 3
    assert competition["numberOfPlaces"] == starting_places - 3
    assert competition["reservations"].get(club["name"], 0) >= 3

    # 5️⃣ Étape 5 : accéder au tableau public
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert b"Simply Lift" in resp.data
    assert str(club["points"]).encode() in resp.data
