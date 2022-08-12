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


# # Merge Helper Function To The Mergesort Function
# def merge(movies_list, l, m, r):
#     n1 = m - l + 1
#     n2 = r - m
#
#     L = [0] * n1
#     R = [0] * n2
#
#     for i in range(0, n1):
#         L[i] = movies_list[l + i]
#
#     for j in range(0, n2):
#         R[j] = movies_list[m + 1 + j]
#
#     i = 0
#     j = 0
#     k = l
#
#     while i < n1 and j < n2:
#         if L[i].rating >= R[j].rating:
#             movies_list[k] = L[i]
#             i += 1
#         else:
#             movies_list[k] = R[j]
#             j += 1
#         k += 1
#
#     while i < n1:
#         movies_list[k] = L[i]
#         i += 1
#         k += 1
#
#     while j < n2:
#         movies_list[k] = R[j]
#         j += 1
#         k += 2
#
#
# # Mergesort Function For Sorting By Moving Rating
# def mergesort(movies_list, l, r):
#     if l < r:
#         m = l + (r-l)//2
#
#         mergesort(movies_list, l, m)
#         mergesort(movies_list, m + 1, r)
#         merge(movies_list, l, m, r)


# Rank Movies In movies_list In Order That They Are Listed
def rank_ordered_movies(movies_list):
    rank = 1
    for movie in movies_list:
        movie.ranking = rank
        rank += 1


# Home Page and Primary Display Page
@app.route("/")
def home():
    movie_to_delete_id = request.args.get('id')
    if movie_to_delete_id is not None:
        delete_movie(movie_to_delete_id)

    movie_list = Movie.query.order_by(Movie.rating).all()[::-1]
    print(movie_list)

    # movie_list = Movie.query.all()
    # num_of_movies = len(movie_list)
    # mergesort(movie_list, 0, num_of_movies - 1)
    rank_ordered_movies(movie_list)
    return render_template("index.html", movies=movie_list)


# Page For Editing Or Adding A Rating And Review
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


# Pivoting Page For Deleting That Quickly Redirects To Home Page
# @app.route('/<id>')
def delete_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    db.session.delete(movie)
    db.session.commit()
    # return redirect(url_for('home'))


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
        return render_template('select.html', movies_list=search_movie_list)

    return render_template('add.html', form=form)


# Page For Selecting A Movie From Search Results Of /add Page
@app.route('/select<id>')
def select_movie(id):
    # print("HELLO")
    # print(id)
    movie = {}
    for movie_element in search_movie_list:
        # print(movie_element['id'])
        if str(movie_element['id']) == str(id):
            movie = movie_element
    # print("Movie: ")
    # print(movie)
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


# Run Flask Server
if __name__ == '__main__':
    app.run(debug=True)
