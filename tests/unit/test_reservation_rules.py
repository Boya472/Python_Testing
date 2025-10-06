# tests/unit/test_reservation_rules.py

def _pick_club_and_comp():
    # utilitaire simple pour trouver un club et une compétition
    from server import clubs, competitions
    club = next(c for c in clubs if c["name"] == "Simply Lift")
    comp = next(c for c in competitions if c["name"] in ("Spring Festival", "Fall Classic"))
    return club, comp

def test_reservation_success(client):
    club, comp = _pick_club_and_comp()
    starting_points = club["points"]
    starting_places = comp["numberOfPlaces"]

    resp = client.post(
        "/purchasePlaces",
        data={"club": club["name"], "competition": comp["name"], "places": "2"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Reservation" in resp.data or b"R" in resp.data  # tolérant à l'encodage
    # Vérifie décrémentations
    assert club["points"] == starting_points - 2
    assert comp["numberOfPlaces"] == starting_places - 2
    # Trace par club
    assert comp["reservations"].get(club["name"], 0) >= 2

def test_reservation_more_than_available_places(client):
    club, comp = _pick_club_and_comp()
    too_many = comp["numberOfPlaces"] + 1
    resp = client.post(
        "/purchasePlaces",
        data={"club": club["name"], "competition": comp["name"], "places": str(too_many)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"pas assez de places disponibles" in resp.data or b"Erreur" in resp.data


def test_reservation_more_than_points(client):
    from server import clubs
    club = next(c for c in clubs if c["name"] == "Iron Temple")  # 4 points dans ton JSON
    comp_name = "Spring Festival"

    resp = client.post(
        "/purchasePlaces",
        data={"club": club["name"], "competition": comp_name, "places": "5"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"pas assez de points" in resp.data

def test_reservation_more_than_12(client):
    club, comp = _pick_club_and_comp()
    resp = client.post(
        "/purchasePlaces",
        data={"club": club["name"], "competition": comp["name"], "places": "13"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"pas r" in resp.data or b"12" in resp.data  # "vous ne pouvez pas r\u00e9server plus de 12"

def test_reservation_invalid_quantity(client):
    club, comp = _pick_club_and_comp()
    for bad in ("0", "-1", "abc"):
        resp = client.post(
            "/purchasePlaces",
            data={"club": club["name"], "competition": comp["name"], "places": bad},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"sup" in resp.data or b"zero" in resp.data  # "sup\u00e9rieur \u00e0 z\u00e9ro"
