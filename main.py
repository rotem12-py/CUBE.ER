from flask import Flask, render_template, flash, request, redirect, url_for
from scramble import scramble
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from datetime import date
from functools import wraps
from avgs import get_best_solve, calc_small_ao, best_ao, calc_mo3


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
    sessions = relationship("Session", back_populates="owner")


class NewSolve(db.Model):
    __tablename__ = "solves"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[float] = mapped_column(Float, nullable=False)
    solve_num: Mapped[int] = mapped_column(Integer, nullable=False)
    scramble: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    p2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="OK")

    owner_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    owner = relationship("User", back_populates="solves")

    session_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("sessions.id"))
    session_owned_by = relationship("Session", back_populates="solves")


class Session(db.Model):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    session_type: Mapped[str] = mapped_column(String, nullable=False)

    owner_id = mapped_column(Integer, db.ForeignKey("users.id"))
    owner = relationship("User", back_populates="sessions")

    solves = relationship("NewSolve", back_populates="session_owned_by")



# load login manager
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def session_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the session_id from the request args
        session_id = request.args.get("session_id")
        if session_id:
            # Retrieve the session from the database
            session = db.get_or_404(Session, session_id)

            # Check if the current user is the owner of the session
            if session.owner_id != current_user.id:
                return redirect(url_for("home"))  # Redirect to home or an error page

        return f(*args, **kwargs)
    return decorated_function


def solve_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the session_id from the request args
        solve_id = request.args.get("solve_id")
        if solve_id:
            # Retrieve the session from the database
            solve = db.get_or_404(NewSolve, solve_id)

            # Check if the current user is the owner of the session
            if solve.owner_id != current_user.id:
                return redirect(url_for("home"))  # Redirect to home or an error page

        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if user is not logged in redirect them to register page and tell them they need to be logged in
        if not current_user.is_authenticated:
            flash("To use The Website You Need To register Or Log In.")
            return redirect(url_for("register"))

        return f(*args, **kwargs)

    return decorated_function

red_url = ""

# home route
@app.route("/", methods=["POST", "GET"])
@session_owner_required
@login_required
def home():
    # get the current session using the session_id parameter from the url
    session_id = request.args.get("session_id", current_user.sessions[0].id)
    current_session = db.get_or_404(Session, session_id)

    # if they are logged in and the request methods is post(meaning they added a new solve) handle it and add to the db
    if request.method == "POST":
        # check if its from timer mode or input mode and behave accordingly
        if request.is_json:
            data = request.get_json()

            new_solve = NewSolve(
                time = float(data["time"]),
                owner = current_user,
                solve_num = len(current_session.solves) + 1,
                scramble = data["scramble"],
                date = str(date.today()),
                session_owned_by=current_session
            )

        else:
            new_solve = NewSolve(
                time=float(request.form["time"]) ,
                owner=current_user,
                solve_num=len(current_session.solves) + 1,
                scramble=request.form["scramble"],
                date=str(date.today()),
                session_owned_by = current_session
            )
        # add solves to db and commit
        db.session.add(new_solve)
        db.session.commit()

        # at the end, return to the same page request came from
        return redirect(request.referrer)
    # if logged in but didn't post(meaning they are loading the page but didn't do anything yet) load the page and pass everything needed to it
    else:
        mode = request.args.get("mode", "input")
        return render_template("index.html", scramble=scramble(current_session.session_type), all_solves=list(reversed(current_session.solves)), mode=mode, current_session=current_session, best_solve=get_best_solve(current_session), ao5=calc_small_ao(current_session.solves[-5:], ao_length=5), ao12=calc_small_ao(current_session.solves[-12:], ao_length=12), best_ao5=best_ao(ao_length=5, solves=current_session.solves), best_ao12=best_ao(ao_length=12, solves=current_session.solves), mo3=calc_mo3(current_session.solves[-3:]), best_mo3=best_ao(solves=current_session.solves, ao_length=3))

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

            # also create a new session for the user
            new_session = Session(
                name = "1",
                session_type = "3x3",
                owner = new_user
            )

            # add the user and the session to db and login the user
            db.session.add(new_user)
            db.session.add(new_session)
            db.session.commit()
            login_user(new_user)

            # redirect to the home page with the new session after registering
            return redirect(url_for("home", session_id=new_session.id))
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


# render the edit-solve page
@app.route("/edit_solve")
@login_required
@solve_owner_required
def edit_solve():
    global red_url
    red_url = request.referrer
    req_solve = db.get_or_404(NewSolve, request.args.get("solve_id"))

    return render_template("edit-solve.html", req_solve=req_solve)


# reset all the solves penalties
@app.route("/reset_solve")
@login_required
@solve_owner_required
def reset_solve():
    # get the requested solve by the solve_id parameter
    req_solve = db.session.get(NewSolve, request.args.get("solve_id"))

    # if the solve status is "+2", remove 2 seconds from it for every p2_count and round at the end
    if req_solve.status == "+2":
        for i in range(req_solve.p2_count):
            req_solve.time -= 2

        req_solve.p2_count = 0
        req_solve.time = round(req_solve.time, 2)

    # at the end, if was a "+2" or not, change the solves status to ok and commit
    req_solve.status = "OK"
    db.session.commit()

    return redirect(red_url)


# add penalties to solves
@app.route("/penalty")
@login_required
@solve_owner_required
def penalty():
    # get the requested solve by the solve_id parameter
    req_solve = db.get_or_404(NewSolve, request.args.get("solve_id"))
    # get the penalty to add by the penalty_type parameter
    penalty_type = request.args.get("penalty_type")

    # if the penalty_type is "+2" add 2 seconds to the solve and 1 to the p2_count and change the status to "+2"
    if penalty_type == "+2":
        req_solve.time += 2
        req_solve.status = "+2"
        req_solve.p2_count += 1
        db.session.commit()
        return redirect(red_url)
    # if the penalty_type is dnf check if teh solves status is "+2" and if it is reset it. change the solves status to dnf and commit
    if penalty_type == "DNF":
        if req_solve.status == "+2":
            for i in range(req_solve.p2_count):
                req_solve.time -= 2

            req_solve.p2_count = 0
            req_solve.time = round(req_solve.time, 2)
        req_solve.status = "DNF"
        db.session.commit()
        return redirect(red_url)


# get solve using the solve_id parameter and delete it
@app.route("/delete_solve")
@login_required
@solve_owner_required
def delete_solve():
    req_solve = db.get_or_404(NewSolve, request.args.get("solve_id"))

    db.session.delete(req_solve)
    db.session.commit()
    return redirect(red_url)

# create new session
@app.route("/new_session", methods=["POST", "GET"])
@login_required
def create_session():
    # if it's a post request
    if request.method == "POST":
        # create the new session based on the form submitted
        new_session = Session(
            name = request.form["session_name"],
            session_type = request.form["session_type"],
            owner = current_user
        )

        # add it to the db and redirect to home with the new session id
        db.session.add(new_session)
        db.session.commit()

        return redirect(url_for("home", session_id=new_session.id))
    # if it's not a post, render the page
    return render_template("create-session.html")


# rename session
@app.route("/rename_session", methods=["POST", "GET"])
@login_required
@session_owner_required
def rename_session():
    # get the session form the session id parameter from the url
    session_id = request.args.get("session_id")
    current_session = db.get_or_404(Session, session_id)

    # if it's a post request
    if request.method == "POST":
        # get the new sessions name from the form and update the db with it. return to home with the sessions id
        current_session.name = request.form["new_session_name"]
        db.session.commit()
        return redirect(url_for("home", session_id=current_session.id))

    # if not a post render the page
    return render_template("rename-session.html", current_session=current_session)


# switch session
@app.route("/switch_session", methods=["POST", "GET"])
@login_required
def switch_session():
    # if it's a post request
    if request.method == "POST":
        # get the session ids from the form and redirect to home with it
        return redirect(url_for("home", session_id=request.form["session_to_switch"]))

    # if not a post render the page
    return render_template("switch-session.html")


# delete session
@app.route("/delete_session", methods=["POST", "GET"])
@login_required
@session_owner_required
def delete_session():
    # get the wanted session form the session_id url parameter
    session_id = request.args.get("session_id")
    current_session = db.get_or_404(Session, session_id)

    # if it's a post(meaning user pressed yes)
    if request.method == "POST":
        # delete every solve owned by this session and the session itself and commit. redirect to home
        for solve in current_session.solves:
            db.session.delete(solve)
        db.session.delete(current_session)
        db.session.commit()
        return redirect(url_for("home"))
# if not a post just render the page
    return render_template("delete-session.html", session_id=session_id, current_session=current_session)

if __name__ == "__main__":
    app.run(debug=True)
