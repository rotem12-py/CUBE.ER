from flask import Flask, render_template, flash, request, redirect, url_for
from scramble import scramble
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user


# create the app and init necessary things for the app
app = Flask(__name__)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)


# the db tables
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    solves = relationship("NewSolve", back_populates="owner")


class NewSolve(db.Model):
    __tablename__ = "solves"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[str] = mapped_column(String, nullable=False)
    solve_num: Mapped[int] = mapped_column(Integer, nullable=False)
    scramble: Mapped[str] = mapped_column(String, nullable=False)

    owner_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    owner = relationship("User", back_populates="solves")



# load login manager
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# home route
@app.route("/", methods=["POST", "GET"])
def home():
    # if user is not logged in redirect them to register page and tell them they need to be logged in
    if not current_user.is_authenticated:
        flash("To use The Website You Need To register Or Log In.")
        return redirect(url_for("register"))

    # if they are logged in and the request methods is post(meaning they added a new solve) handle it and add to the db
    if request.method == "POST":

        # check if its from timer mode or input mode and behave accordingly
        if request.is_json:
            data = request.get_json()

            new_solve = NewSolve(
                time = float(data["time"]),
                owner = current_user,
                solve_num = len(current_user.solves) + 1,
                scramble = data["scramble"]
            )

        else:
            new_solve = NewSolve(
                time=float(request.form["time"]) ,
                owner=current_user,
                solve_num=len(current_user.solves) + 1,
                scramble=request.form["scramble"]
            )
        # add solves to db and commit
        db.session.add(new_solve)
        db.session.commit()

        # at the end, return to the same page request came from
        return redirect(request.referrer)
    # if logged in but didn't post(meaning they are loading the page but didn't do anything yet) load the page and pass everything needed to it
    else:
        mode = request.args.get("mode", "input")
        return render_template("index.html", scramble=scramble("3x3"), all_solves=list(reversed(current_user.solves)), mode=mode)

# register route
@app.route("/register", methods=["POST", "GET"])
def register():

    # if the request method is post(meaning user filled the form)
    if request.method == "POST":

        # if there is already an existing user with the wanted username tell the user there is already a user with that username
        req_user = db.session.execute(db.select(User).where(User.username == request.form['username'])).scalar()
        if req_user:
            flash("There Is Already A User With This Username")
            return redirect(url_for("register"))
        # if not, register the user and add it to the db with a hashed password then redirect to home
        else:
            new_user = User(
                username = request.form["username"],
                password = generate_password_hash(request.form["password"], method="scrypt", salt_length=8)
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))
        # if it's not a post request(meaning they load the page) load the page
    else:
        return render_template("register.html")


# login route
@app.route("/login", methods=["POST", "GET"])
def login():
    # if the request method is post(meaning user filled the form)
    if request.method == "POST":
        # get the user that the user tried to log into by the username
        req_user = db.session.execute(db.select(User).where(User.username == request.form['username'])).scalar()

        # if there is no user with this username tell the user that
        if not req_user:
            flash("There Is No User With This Username")
            return redirect(url_for("login"))
        # if the requested user is existing but the password is wrong, tell the user that
        elif not check_password_hash(req_user.password, request.form['password']):
            flash("Wrong Password")
            return redirect(url_for("login"))
        # but if both the user is existing and the password is correct log them in
        else:
            login_user(req_user)
            return redirect(url_for("home"))
    # if it's not a post, show the page
    else:
        return render_template("login.html")


# simple logout
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
