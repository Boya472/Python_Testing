# tests/test_routes.py
import urllib.parse
import copy
import pytest
import server

# --- Tests initiaux (conservés) ---

def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'name="email"' in resp.data
    assert b'action="showSummary"' in resp.data or b'/showSummary' in resp.data

def test_showSummary_invalid_email(client):
    resp = client.post("/showSummary", data={"email": "inconnue@example.com"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Adresse email inconnue" in resp.data or b"inconnue" in resp.data or b"Adresse" in resp.data

def test_showSummary_valid_email(client):
    assert len(server.clubs) > 0, "server.clubs est vide — vérifie clubs.json"
    club = server.clubs[0]
    email = club.get("email")
    resp = client.post("/showSummary", data={"email": email}, follow_redirects=True)
    assert resp.status_code == 200
    assert club["name"].encode() in resp.data

def test_book_route(client):
    assert len(server.competitions) > 0, "server.competitions est vide — vérifie competitions.json"
    comp = server.competitions[0]
    club = server.clubs[0]
    url = "/book/{}/{}".format(urllib.parse.quote_plus(comp["name"]), urllib.parse.quote_plus(club["name"]))
    resp = client.get(url)
    assert resp.status_code in (200, 400, 302)

def test_purchase_places_success(client):
    comp = next((c for c in server.competitions if c.get("numberOfPlaces", 0) > 0), None)
    club = next((cl for cl in server.clubs if cl.get("points", 0) > 0), None)

    assert comp is not None, "Aucune compétition avec des places disponibles trouvée"
    assert club is not None, "Aucun club avec des points trouvés"

    initial_places = comp["numberOfPlaces"]
    initial_points = club["points"]

    data = {"competition": comp["name"], "club": club["name"], "places": "1"}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200

    updated_comp = next((c for c in server.competitions if c["name"] == comp["name"]), None)
    updated_club = next((cl for cl in server.clubs if cl["name"] == club["name"]), None)
    assert updated_comp is not None and updated_club is not None
    assert updated_comp["numberOfPlaces"] == initial_places - 1
    assert updated_club["points"] == initial_points - 1

def test_purchase_places_insufficient_points(client):
    comp = server.competitions[0]
    club = server.clubs[0]
    too_many = club["points"] + 10
    data = {"competition": comp["name"], "club": club["name"], "places": str(too_many)}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"assez de points" in resp.data or b"Erreur" in resp.data or b"n\u2019avez pas assez" in resp.data or b"Impossible" in resp.data

def test_leaderboard_and_logout(client):
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    resp2 = client.get("/logout", follow_redirects=True)
    assert resp2.status_code == 200
    assert b'name="email"' in resp2.data or b"Welcome" in resp2.data

# --- Tests complémentaires (basés sur le cahier des charges) ---

def test_purchase_places_exact_12_allowed_if_enough_points(client):
    comp = next((c for c in server.competitions if c.get("numberOfPlaces", 0) >= 12), None)
    club = next((cl for cl in server.clubs if cl.get("points", 0) >= 12), None)
    if not comp or not club:
        pytest.skip("Pas de competition ou de club avec >=12 places/points pour ce test")
    initial_places = comp["numberOfPlaces"]
    initial_points = club["points"]

    data = {"competition": comp["name"], "club": club["name"], "places": "12"}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200
    updated_comp = next(c for c in server.competitions if c["name"] == comp["name"])
    updated_club = next(cl for cl in server.clubs if cl["name"] == club["name"])
    assert updated_comp["numberOfPlaces"] == initial_places - 12
    assert updated_club["points"] == initial_points - 12

def test_purchase_places_exact_points_equal_to_places(client):
    comp = next((c for c in server.competitions if c.get("numberOfPlaces", 0) > 0), None)
    club = next((cl for cl in server.clubs if cl.get("points", 0) > 0), None)
    if not comp or not club:
        pytest.skip("Données insuffisantes pour ce test")
    original_points = club["points"]
    places_to_request = min(comp["numberOfPlaces"], original_points)
    if places_to_request <= 0:
        pytest.skip("Aucune place disponible ou points insuffisants")
    data = {"competition": comp["name"], "club": club["name"], "places": str(places_to_request)}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200
    updated_club = next(cl for cl in server.clubs if cl["name"] == club["name"])
    assert updated_club["points"] == original_points - places_to_request

def test_multiple_reservations_accumulate_in_reservations_field(client):
    comp = next((c for c in server.competitions if c.get("numberOfPlaces", 0) >= 2), None)
    club = next((cl for cl in server.clubs if cl.get("points", 0) >= 2), None)
    if not comp or not club:
        pytest.skip("Données insuffisantes pour test multiple reservations")
    comp_name = comp["name"]
    club_name = club["name"]
    prev = comp.get("reservations", {}).get(club_name, 0)
    for _ in range(2):
        data = {"competition": comp_name, "club": club_name, "places": "1"}
        resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
        assert resp.status_code == 200
    updated_comp = next(c for c in server.competitions if c["name"] == comp_name)
    assert updated_comp.get("reservations", {}).get(club_name, 0) == prev + 2

def test_book_route_handles_nonexistent_parameters_gracefully(client):
    url = "/book/competition_inexistante/club_inexistant"
    resp = client.get(url, follow_redirects=True)
    assert resp.status_code in (200, 302, 400)

def test_purchase_places_missing_fields(client):
    comp = server.competitions[0]
    club = server.clubs[0]
    # missing 'places'
    data = {"competition": comp["name"], "club": club["name"]}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert "doit être supérieur" in resp.get_data(as_text=True) or "Erreur" in resp.get_data(as_text=True) or "places" in resp.get_data(as_text=True)


def test_showSummary_handles_invalid_date_in_competition(client):
    bad_comp = {"name": "Comp Bad Date", "date": "invalid-date-format", "numberOfPlaces": 10, "reservations": {}}
    server.competitions.append(bad_comp)
    try:
        club_email = server.clubs[0]["email"]
        resp = client.post("/showSummary", data={"email": club_email}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Comp Bad Date" in resp.data or b"Comp Bad Date".encode() in resp.data
    finally:
        server.competitions.pop()

def test_ok_err_flash_functions(client, app):
    # Vérifie que les fonctions flash ne plantent pas
    with app.test_request_context('/'):
        server.ok("Test ok flash")
        server.err("Test err flash")
        server.info("Test info flash")
        assert True  # Si aucune exception n'est levée, c'est validé



   
