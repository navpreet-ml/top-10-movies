from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
TMDB_API_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
TMDB_API_KEY = "381828cb0aef5db97ca4a0e434430062"
TMDB_API_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzODE4MjhjYjBhZWY1ZGI5N2NhNGEwZTQzNDQzMDA2MiIsInN1YiI6IjYxNWMzYTNkYmIxMDU3MDA4OWU3ZDFmZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.2sEIqOOXUgeboxAbqcZZ0Duxc8jpsFav3dWs7XTvOi8"

#SQL Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(1000), nullable=True)
    img_url = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return f'<Movie: {self.title}>'


db.create_all()

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)

# db.session.add(new_movie)
# db.session.commit()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating out of 10.0")
    review = StringField("Your review")
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Search for a movie name")
    submit = SubmitField("Search")


@app.route("/", methods = ["GET", "POST"])
def home():
    if os.path.isfile("movies.db"):
        all_movies = db.session.query(Movie).all()
        # This line loops through all the movies
        for i in range(len(all_movies)):
            # This line gives each movie a new ranking reversed from their order in all_movies
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        return render_template("index.html", movies=all_movies)
    else:
        return render_template("index.html", movies=[''])

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_param = {"api_key": TMDB_API_KEY,  "language": "en-US"}
        response = requests.get(url = f"https://api.themoviedb.org/3/movie/{movie_api_id}", params=movie_param)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
            description=data["overview"],
            rating = data['popularity'],
            ranking = 0,
            review = ""

        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("home"))

@app.route("/edit", methods = ["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete", methods = ["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods = ["GET", "POST"])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        movie_to_search = form.title.data
        movie_params = {
            "api_key": TMDB_API_KEY,
            "query": movie_to_search
        }
        response = requests.get(url=TMDB_API_ENDPOINT, params=movie_params)
        response.raise_for_status()
        data = response.json()["results"]
        return render_template("select.html", options = data)
    return render_template("add.html", form = form)












if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
