import json
from flask import Flask, render_template, request, redirect, flash, url_for, has_request_context
from datetime import datetime
from urllib.parse import unquote_plus

# -----------------------------
# Chargement des données JSON
# -----------------------------
def loadClubs():
    with open('clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
        for club in listOfClubs:
            club['points'] = int(club['points'])
        return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        for competition in listOfCompetitions:
            competition['numberOfPlaces'] = int(competition['numberOfPlaces'])
            if 'reservations' not in competition:
                competition['reservations'] = {}
        return listOfCompetitions


# -----------------------------
# Initialisation Flask
# -----------------------------
app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()


# -----------------------------
# Page d'accueil
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')


# -----------------------------
# Connexion + affichage des compétitions à venir
# -----------------------------
@app.route('/showSummary', methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip().lower()
    matches = [club for club in clubs if club['email'].lower() == email]

    if not matches:
        err("Adresse email inconnue. Vérifiez et réessayez.")
        return redirect(url_for('index'))

    club = matches[0]

    today = datetime.now()
    upcoming_competitions = []
    for comp in competitions:
        try:
            comp_date = datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
            if comp_date >= today:
                upcoming_competitions.append(comp)
        except Exception:
            upcoming_competitions.append(comp)

    ok(f"Connexion réussie pour {club['name']}.")
    return render_template('welcome.html', club=club, competitions=upcoming_competitions)


# -----------------------------
# Réservation d'une compétition
# -----------------------------
@app.route('/book/<competition>/<club>')
def book(competition, club):
    competition = unquote_plus(competition)
    club = unquote_plus(club)

    foundClub = [c for c in clubs if c['name'] == club]
    foundCompetition = [c for c in competitions if c['name'] == competition]

    if foundClub and foundCompetition:
        return render_template('booking.html', club=foundClub[0], competition=foundCompetition[0])
    else:
        flash("Something went wrong - please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


# -----------------------------
# Achat de places
# -----------------------------
@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition_name = request.form.get('competition')
    club_name = request.form.get('club')

    try:
        places_required = int(request.form.get('places', 0))
    except (ValueError, TypeError):
        places_required = 0

    competition = next((c for c in competitions if c['name'] == competition_name), None)
    club = next((c for c in clubs if c['name'] == club_name), None)

    if not competition or not club:
        err("Erreur : club ou compétition introuvable.")
        return redirect(url_for('index'))

    # Vérifications des contraintes
    if places_required <= 0:
        err("Le nombre de places doit être supérieur à zéro.")
    elif places_required > 12:
        err("Erreur : vous ne pouvez pas réserver plus de 12 places par compétition.")
    elif competition['numberOfPlaces'] < places_required:
        err("Erreur : pas assez de places disponibles pour cette compétition.")
    elif club['points'] < places_required:
        err("Erreur : vous n’avez pas assez de points pour cette réservation.")
    else:
    # ✅ Réservation autorisée (même si le club dépense tous ses points)
     competition['numberOfPlaces'] -= places_required
    club['points'] -= places_required

    if 'reservations' not in competition:
        competition['reservations'] = {}

    already = competition['reservations'].get(club_name, 0)
    competition['reservations'][club_name] = already + places_required

    ok(f"✅ Réservation réussie : {places_required} place(s) réservée(s) pour {competition_name}.")
    return render_template('welcome.html', club=club, competitions=competitions)


# -----------------------------
# Tableau des scores
# -----------------------------
@app.route('/leaderboard')
def leaderboard():
    sorted_clubs = sorted(clubs, key=lambda c: (-int(c.get('points', 0)), c.get('name', '')))
    return render_template('leaderboard.html', clubs=sorted_clubs)


# -----------------------------
# Déconnexion
# -----------------------------
@app.route('/logout')
def logout():
    ok("Déconnexion réussie.")
    return redirect(url_for('index'))


# -----------------------------
# Fonctions de messages (flash)
# -----------------------------
def ok(msg: str):
    from flask import flash
    if has_request_context():
        flash(msg, "success")


def err(msg: str):
    from flask import flash
    if has_request_context():
        flash(msg, "error")


def info(msg: str):
    from flask import flash
    if has_request_context():
        flash(msg, "info")
