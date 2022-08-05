from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


API_KEY = os.environ.get('TMDB_KEY')
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
search_movie_list = []


# Create Flask Object
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Create Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define Table/Record
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(400), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# Create Table
db.create_all()


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
#
# db.session.add(new_movie)
# db.session.commit()


# new_movie2 = Movie(
#     title="Dune",
#     year=2021,
#     description="A noble family becomes embroiled in a war for control over the galaxy's most valuable asset while its heir becomes troubled by visions of a dark future.",
#     rating=8.0,
#     ranking=10,
#     review="This is a fantastic movie!",
#     img_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse1.mm.bing.net%2Fth%3Fid%3DOIP.fkw6e2qh_lrjTTJH8FT1FwHaK-%26pid%3DApi&f=1"
# )
#
# db.session.add(new_movie2)
# db.session.commit()


def merge(movies_list, l, m, r):
    n1 = m - l + 1
    n2 = r - m

    L = [0] * n1
    R = [0] * n2

    for i in range(0, n1):
        L[i] = movies_list[l + i]

    for j in range(0, n2):
        R[j] = movies_list[m + 1 + j]

    i = 0
    j = 0
    k = l

    while i < n1 and j < n2:
        if L[i].rating >= R[j].rating:
            movies_list[k] = L[i]
            i += 1
        else:
            movies_list[k] = R[j]
            j += 1
        k += 1

    while i < n1:
        movies_list[k] = L[i]
        i += 1
        k += 1

    while j < n2:
        movies_list[k] = R[j]
        j += 1
        k += 2


def mergesort(movies_list, l, r):
    if l < r:
        m = l + (r-l)//2

        mergesort(movies_list, l, m)
        mergesort(movies_list, m + 1, r)
        merge(movies_list, l, m, r)


def rank_ordered_movies(movies_list, length):
    for index in range(0, length):
        movies_list[index].ranking = index + 1


@app.route("/")
def home():
    movie_list = Movie.query.all()
    num_of_movies = len(movie_list)
    mergesort(movie_list, 0, num_of_movies - 1)
    rank_ordered_movies(movie_list, num_of_movies)
    return render_template("index.html", movies=movie_list)


@app.route("/edit/<id>", methods=['POST', 'GET'])
def edit_page(id):
    form = RateMovieForm()
    movie = Movie.query.filter_by(id=id).first()
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route('/<id>')
def delete_movie(id):
    movie = Movie.query.filter_by(id=id).first()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add_movie():
    global search_movie_list
    form = AddMovieForm()
    if form.validate_on_submit():
        title = form.title.data
        parameters = {
            "api_key": API_KEY,
            "query": title,
            "page": '1',
            "include_adult": 'false'
        }

        response = requests.get(TMDB_SEARCH_URL, params=parameters)
        search_movie_list = response.json()['results']
        return render_template('select.html', movies_list=search_movie_list)

    return render_template('add.html', form=form)


@app.route('/select<id>')
def select_movie(id):
    print("HELLO")
    print(id)
    movie = {}
    for movie_element in search_movie_list:
        print(movie_element['id'])
        if str(movie_element['id']) == str(id):
            movie = movie_element
    print("Movie: ")
    print(movie)
    new_movie = Movie(
        id=id,
        title=movie['title'],
        year=movie['release_date'][:4],
        description=movie['overview'],
        rating=0.0,
        ranking=0,
        review="",
        img_url=f'{TMDB_IMG_URL}{movie["poster_path"]}'
    )

    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit_page', id=id))

if __name__ == '__main__':
    app.run(debug=True)
