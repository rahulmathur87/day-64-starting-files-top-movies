from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
bootstrap = Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movielist.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()

# Adding Entry
# with app.app_context():
#     new_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#     db.session.add(new_movie)
#     db.session.commit()


class UpdateForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


API_READ_ACCESS_TOKEN = os.environ.get('API_READ_ACCESS_TOKEN')

headers = {
    "accept": "application/json",
    "Authorization": API_READ_ACCESS_TOKEN
}


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movie).order_by(Movie.rating))
        all_movies = result.scalars().all()

        for i in range(len(all_movies)):
            with app.app_context():
                all_movies[i].ranking = int(len(all_movies) - i)
                db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route("/update", methods=['GET', 'POST'])
def update():
    form = UpdateForm()
    movie_id = request.args.get("id")
    if form.validate_on_submit():
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
            movie_to_update.rating = form.rating.data
            movie_to_update.review = form.review.data
            db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_id = request.args.get("id")
    with app.app_context():
        movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        endpoint = "https://api.themoviedb.org/3/search/movie"
        params = {
            "query": form.title.data
        }
        response = requests.get(url=endpoint, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()['results']
        return render_template('select.html', results=results)
    return render_template("add.html", form=form)


@app.route("/find", methods=['GET', 'POST'])
def find_movie():
    tmdb_id = request.args.get("tmdb_id")
    # 1100782 - Smile 2
    endpoint = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    response = requests.get(url=endpoint, headers=headers)
    response.raise_for_status()
    results = response.json()
    with app.app_context():
        new_movie = Movie(title=f"{results["title"]}",
                          year=f"{results["release_date"][:4]}",
                          description=f"{results["overview"]}",
                          img_url=f"https://image.tmdb.org/t/p/w500{results["poster_path"]}")
        db.session.add(new_movie)
        db.session.commit()
        movie_id = new_movie.id
    return redirect(url_for('update', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)


'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:


On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
