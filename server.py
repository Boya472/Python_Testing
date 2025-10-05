import json
from flask import Flask,render_template,request,redirect,flash,url_for
from datetime import datetime


def loadClubs():
    with open('clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
        # Convertir points en entier pour permettre les calculs
        for club in listOfClubs:
            club['points'] = int(club['points'])
        return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        for competition in listOfCompetitions:
            # Convertir numberOfPlaces en entier
            
            competition['numberOfPlaces'] = int(competition['numberOfPlaces'])
            # Ajouter la clé reservations si elle n'existe pas
            if 'reservations' not in competition:
                competition['reservations'] = {}
        return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def showSummary():
    """
    Connexion du secrétaire via son email + affichage des compétitions à venir.
    """
    email = request.form.get('email', '').strip().lower()
    matches = [club for club in clubs if club['email'].lower() == email]

    if not matches:
        err("Adresse email inconnue. Vérifiez et réessayez.")
        return redirect(url_for('index'))

    club = matches[0]

    # Filtrer uniquement les compétitions à venir
    today = datetime.now()
    upcoming_competitions = []
    for comp in competitions:
        try:
            comp_date = datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
            if comp_date >= today:
                upcoming_competitions.append(comp)
        except Exception:
            # Si la date est invalide, on garde la compétition pour éviter de la perdre
            upcoming_competitions.append(comp)

    ok(f"Connexion réussie pour {club['name']}.")
    return render_template('welcome.html', club=club, competitions=upcoming_competitions)

@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition_name = request.form['competition']
    club_name = request.form['club']
    try:
        places_required = int(request.form['places'])
    except ValueError:
        places_required = 0

    # Trouver le club et la compétition correspondants
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
        # Tout est OK → on réserve
        competition['numberOfPlaces'] -= places_required
        club['points'] -= places_required

        # Enregistrer dans reservations
        if 'reservations' not in competition:
            competition['reservations'] = {}

        already = competition['reservations'].get(club_name, 0)
        competition['reservations'][club_name] = already + places_required

        ok(f"✅ Réservation réussie : {places_required} place(s) réservée(s) pour {competition_name}.")

    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    """
    Déconnecte le secrétaire et retourne à la page d'accueil.
    """
    ok("Déconnexion réussie.")
    return redirect(url_for('index'))


def ok(msg: str):
    from flask import flash
    flash(msg, "success")

def err(msg: str):
    from flask import flash
    flash(msg, "error")

def info(msg: str):
    from flask import flash
    flash(msg, "info")

