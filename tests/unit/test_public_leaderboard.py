# tests/unit/test_public_leaderboard.py

def test_leaderboard_is_public(client):
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert b"Tableau public des points" in resp.data
    # Un club connu doit apparaître
    assert b"Simply Lift" in resp.data or b"Iron Temple" in resp.data
