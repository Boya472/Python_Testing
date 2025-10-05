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
        flash("Adresse email inconnue. Vérifiez et réessayez.", "error")
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

    flash(f"Connexion réussie pour {club['name']}.", "success")
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


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    competition['numberOfPlaces'] = int(competition['numberOfPlaces'])-placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    """
    Déconnecte le secrétaire et retourne à la page d'accueil.
    """
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('index'))
