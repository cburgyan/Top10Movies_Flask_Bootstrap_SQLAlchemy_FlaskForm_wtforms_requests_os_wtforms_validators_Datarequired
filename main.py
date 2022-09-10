from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


# Constants and Initializations
API_KEY = os.environ.get('TMDB_KEY')
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
search_movie_list = []


# Create Flask Object
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)

# Create Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///movies-collection.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define Table/Record
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(400), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


# Form For Rating and Reviewing A Movie
class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


# Form For Searching For A Movie Title In The Movie Database (TMDB)
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# Create Table
db.create_all()


# Rank Movies In movies_list In Order That They Are Listed
def rank_ordered_movies(movies_list):
    rank = 1
    for movie in movies_list:
        movie.ranking = rank
        rank += 1


# Home Page and Primary Display Page
@app.route("/")
def home():
    # Check If Deletion Was Made
    movie_to_delete_id = request.args.get('id')
    if movie_to_delete_id is not None:
        delete_movie(movie_to_delete_id)

    # Order Movies By Rating
    movie_list = Movie.query.order_by(Movie.rating).all()[::-1]
    full_page = request.args.get('full_page')
    if not full_page:
        movie_list = movie_list[:10]

    # Rank Movies By Order
    rank_ordered_movies(movie_list)
    return render_template("index.html", movies=movie_list, full_page=full_page)


# Pivoting Page For Deleting That Quickly Redirects To Home Page
def delete_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    db.session.delete(movie)
    db.session.commit()


# Page For Editing Or Adding A Rating And Review
@app.route("/edit/<id>", methods=['POST', 'GET'])
def edit_page(id):
    rating = request.args.get('rating')
    review = request.args.get('review')
    if rating or review:
        form = RateMovieForm(rating=rating, review=review)
    else:
        form = RateMovieForm()
    movie = Movie.query.filter_by(id=id).first()
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


# Page For Searching For A Movie
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
        return render_template('select.html', movies_list=search_movie_list, TMDB_IMG_URL=TMDB_IMG_URL)

    return render_template('add.html', form=form)


# Page For Selecting A Movie From Search Results Of /add Page
@app.route('/select')
def select_movie():
    movie = {}
    movie_id = request.args.get('id')
    for movie_element in search_movie_list:
        if str(movie_element['id']) == str(movie_id):
            movie = movie_element

    new_movie = Movie(
        id=movie_id,
        title=movie['title'],
        year=movie['release_date'][:4],
        description=movie['overview'],
        rating=0.0,
        ranking=0,
        review="",
        img_url=f'{TMDB_IMG_URL}{movie["poster_path"]}'
    )
    movie_already_in_database = Movie.query.get(int(movie_id))
    if not movie_already_in_database:
        db.session.add(new_movie)
        db.session.commit()
    else:
        rating = movie_already_in_database.rating
        review = movie_already_in_database.review
    return redirect(url_for('edit_page', id=movie_id, rating=rating, review=review))


# Run Flask Server
if __name__ == '__main__':
    app.run(debug=True)
