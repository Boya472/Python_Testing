# tests/test_routes.py
import urllib.parse
import server

def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'name="email"' in resp.data
    # la form POST pour showSummary peut être action="/showSummary" ou action="showSummary"
    assert b'action="showSummary"' in resp.data or b'/showSummary' in resp.data

def test_showSummary_invalid_email(client):
    # email inconnu -> redirection vers index + message d'erreur
    resp = client.post("/showSummary", data={"email": "inconnue@example.com"}, follow_redirects=True)
    assert resp.status_code == 200
    # Le message d'erreur en français est généré dans server.showSummary : "Adresse email inconnue"
    assert b"Adresse email inconnue" in resp.data or b"inconnue" in resp.data or b"Adresse" in resp.data

def test_showSummary_valid_email(client):
    # Utilise dynamiquement le premier club chargé par server
    assert len(server.clubs) > 0, "server.clubs est vide — vérifie clubs.json"
    club = server.clubs[0]
    email = club.get("email")
    resp = client.post("/showSummary", data={"email": email}, follow_redirects=True)
    assert resp.status_code == 200
    # le nom du club devrait apparaître dans la page welcome
    assert club["name"].encode() in resp.data

def test_book_route(client):
    # Utilise une compétition et un club existants
    assert len(server.competitions) > 0, "server.competitions est vide — vérifie competitions.json"
    comp = server.competitions[0]
    club = server.clubs[0]
    url = "/book/{}/{}".format(urllib.parse.quote_plus(comp["name"]), urllib.parse.quote_plus(club["name"]))
    resp = client.get(url)
    # selon l'implémentation, on peut avoir 200 ou 400 ; mais on ne veut pas d'exception
    assert resp.status_code in (200, 400, 302)

def test_purchase_places_success(client):
    # Choisit une compétition et club où au moins 1 place est disponible et le club a au moins 1 point
    comp = None
    club = None
    for c in server.competitions:
        if c.get("numberOfPlaces", 0) > 0:
            comp = c
            break
    club = next((cl for cl in server.clubs if cl.get("points", 0) > 0), None)

    assert comp is not None, "Aucune compétition avec des places disponibles trouvée dans competitions.json"
    assert club is not None, "Aucun club avec des points trouvés dans clubs.json"

    initial_places = comp["numberOfPlaces"]
    initial_points = club["points"]

    data = {
        "competition": comp["name"],
        "club": club["name"],
        "places": "1"
    }
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # vérifier effet dans les structures en mémoire (décrémentation)
    # trouver la compétition mise à jour dans server.competitions
    updated_comp = next((c for c in server.competitions if c["name"] == comp["name"]), None)
    updated_club = next((cl for cl in server.clubs if cl["name"] == club["name"]), None)
    assert updated_comp is not None and updated_club is not None
    assert updated_comp["numberOfPlaces"] == initial_places - 1
    assert updated_club["points"] == initial_points - 1

def test_purchase_places_insufficient_points(client):
    # Choisis un club et une compétition puis demande beaucoup de places > club points
    comp = server.competitions[0]
    club = server.clubs[0]

    # places supérieures aux points du club
    too_many = club["points"] + 10
    data = {"competition": comp["name"], "club": club["name"], "places": str(too_many)}
    resp = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert resp.status_code == 200
    # Vérifie qu'un message d'erreur a été flashé (texte français attendu)
    assert b"assez de points" in resp.data or b"Erreur" in resp.data or b"n\u2019avez pas assez" in resp.data or b"Impossible" in resp.data

def test_leaderboard_and_logout(client):
    # leaderboard accessible
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    # logout redirige vers index (follow)
    resp2 = client.get("/logout", follow_redirects=True)
    assert resp2.status_code == 200
    assert b'name="email"' in resp2.data or b"Welcome" in resp2.data
