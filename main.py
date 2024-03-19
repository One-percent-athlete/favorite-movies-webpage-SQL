from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import dotenv
import os

dotenv.load_dotenv()                    
access_token = os.getenv('access_token')
api_key = os.getenv('api_key')

search_url = "https://api.themoviedb.org/3/search/movie?"
detail_url = "https://api.themoviedb.org/3/movie/"

headers = {
    "accept": "application/json",
    "Authorization": access_token
}

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
  pass
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///favorite-movie.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class Edit_form(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class Add_form(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")

@app.route("/")
def home():
        # result = db.session.query(Movie).order_by(Movie.ranking).all()
        # print(result)
    data = db.session.execute(db.select(Movie).order_by(Movie.rating))
    result = data.scalars().all()

    for i in range(len(result)):
        result[i].ranking = len(result) - i
    db.session.commit()

    return render_template("index.html", movies=result)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = Edit_form()
    id = request.args.get("id")
    movie = db.get_or_404(Movie, id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete")
def delete():
    id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["GET", "POST"])
def add():
    form = Add_form()
    if form.validate_on_submit():
        title = form.title.data
        response = requests.get(search_url, params={"api_key": api_key, "query": title})
        data = response.json()["results"]
        return render_template("select.html", movies=data)
    return render_template("add.html", form=form)

@app.route("/select", methods=["GET","POST"])
def select():
    id = request.args.get("id")
    if id:
        res = requests.get(f"{detail_url}/{id}", params={"api_key": api_key, "language": "en-US"})
        new_movie = Movie(
            title=res.json()["title"],
            year=res.json()["release_date"].split("-")[0],
            description=res.json()["overview"],
            rating= 0,
            ranking= 0,
            review="No reviews yet",
            img_url=f"https://image.tmdb.org/t/p/w500{res.json()['poster_path']}"
        )
        print(new_movie)
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
