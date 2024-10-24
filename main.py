from scramble import generate_scramble
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from forms import EnterTimeForm, RegisterForm, LoginForm
from flask_login import LoginManager, logout_user, login_user, current_user, UserMixin
from sqlalchemy import String, Float, Integer
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re


app = Flask(__name__)
app.config['SECRET_KEY'] = '3747HHhshsdhdb38Sncshfownxs73hcHSJDnx1'

bootstrap = Bootstrap5(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solves.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    solves = relationship("New_Solve", back_populates="owner")

class New_Solve(db.Model):
    __tablename__ = "solves"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[float] = mapped_column(Float, nullable=False)
    date = str(date.today())

    owner_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    owner = relationship("User", back_populates="solves")

    solve_num: Mapped[str] = mapped_column(Integer, nullable=False)
    scramble: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    p2_count: Mapped[int] = mapped_column(Integer, default=0)





with app.app_context():
    db.create_all()


  
login_manager = LoginManager()
login_manager.init_app(app)


def solve_owner_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        solve_id = kwargs.get("solve_id")
        req_solve = db.get_or_404(New_Solve, solve_id)

        if req_solve.owner_id != current_user.id:
            return redirect(url_for('home'))

        return func(*args, **kwargs)
     
    return wrapper




@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:05.2f}"  

def convert_time_to_float(time_str):
    minutes, seconds = map(float, time_str.split(':'))
    return minutes * 60 + seconds


def calculate_ao5():
    last_5_solves = [solve for solve in current_user.solves][-5:]  if len(current_user.solves) > 4 else None

    ao5_list = []
    dnf_count = 0
    ao5_result = 0

    if last_5_solves != None:
        for i in last_5_solves:
            if i.status == "DNF":
                ao5_list.append(float('inf'))
                dnf_count += 1
            else:
                ao5_list.append(i.time)

        if dnf_count < 2:
            ao5_list.remove(min(ao5_list))
            ao5_list.remove(max(ao5_list))
            num = 0
            for i in ao5_list:
                num += i
            ao5_result = round(num / 3, 2)

            if ao5_result > 60:
                ao5_result = format_time(ao5_result)
        else:
            ao5_result = "DNF"

        return ao5_result
                
            


red_url = ""

@app.route("/", methods=["POST", "GET"])
def home():
    form = EnterTimeForm()
    scramble = generate_scramble()

    
    

    if form.validate_on_submit():
        if not form.time.data:
            flash("You Need To Enter A Time")
            return redirect(url_for("home"))
        else:
            try:
                if re.match(r'^\d{1,2}:\d{2}\.\d{2}$', form.time.data):
                    time_float = convert_time_to_float(form.time.data)


                    new_solve = New_Solve(
                        time = time_float,
                        owner = current_user,
                        solve_num = len(current_user.solves) + 1,
                        scramble = scramble,
                        status = "OK"
                    )

                else:
                    new_solve = New_Solve(
                        time = float(form.time.data),
                        owner = current_user,
                        solve_num = len(current_user.solves) + 1,
                        scramble = scramble,
                        status = "OK"
                    )

                db.session.add(new_solve)
                db.session.commit()


                form.time.data = ''
            except ValueError:
                flash("Please A Valid Time")
                return redirect(url_for("home"))



    if not current_user.is_authenticated:
        return render_template("login_msg.html")
    else:
        valid_solves = [solve.time for solve in current_user.solves if solve.status != "DNF"]
        min_time = min(valid_solves) if valid_solves else None

        if min_time is not None:
            if min_time > 60:
                min_time = format_time(min_time)

        

        solves = New_Solve.query.filter_by(owner=current_user).order_by(New_Solve.id.desc()).all()

        for solve in solves:
            if solve.time > 60:
                solve.formatted_time = format_time(solve.time)
            else:
                solve.formatted_time = solve.time



        return render_template("home-input.html", scramble=scramble, form=form, min_time=min_time, solves=solves, ao5=calculate_ao5())
        

@app.route("/timer", methods=["POST", "GET"])
def home_timer_page():

    scramble = generate_scramble()

    if request.method == "POST":
        data = request.get_json()

        new_solve = New_Solve(
            time = float(data['time']),
            owner = current_user,
            solve_num = len(current_user.solves) + 1,
            scramble = scramble,
            status = "OK"
        )

        db.session.add(new_solve)
        db.session.commit()

        

    if not current_user.is_authenticated:
        return render_template("login_msg.html")
    else:
        valid_solves = [solve.time for solve in current_user.solves if solve.status != "DNF"]
        min_time = min(valid_solves) if valid_solves else None

        if min_time is not None:
            if min_time > 60:
                min_time = format_time(min_time)




        solves = New_Solve.query.filter_by(owner=current_user).order_by(New_Solve.id.desc()).all()

        for solve in solves:
            if solve.time > 60:
                solve.formatted_time = format_time(solve.time)
            else:   
                solve.formatted_time = solve.time

        latest_solve_time = None
        if solves:
            latest_solve_time = solves[0].formatted_time  # Get the most recent solve's time




        return render_template("home-timer.html", scramble=scramble, solves=solves, min_time=min_time, ao5=calculate_ao5(), latest_solve_time=latest_solve_time)
       



@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User(
            username = form.username.data,
            password = generate_password_hash(form.password.data, salt_length=8, method="pbkdf2:sha256")
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        req_user = db.session.execute(db.select(User).where(User.username == username)).scalar()

        if req_user and check_password_hash(req_user.password, password):
            login_user(req_user)
            return redirect(url_for("home"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/delete/<int:solve_id>")
@solve_owner_only
def delete_solve(solve_id):
    req_solve = db.get_or_404(New_Solve, solve_id)

    db.session.delete(req_solve)
    db.session.commit()

    solves_to_change = [solve for solve in current_user.solves if solve.id > req_solve.id]
    
    for solve in solves_to_change:
        solve.solve_num = solve.solve_num - 1
        db.session.commit()


    return redirect(red_url)

@app.route("/edit-solve/<int:solve_id>")
@solve_owner_only
def edit_solve(solve_id):
    global red_url
    req_solve = db.get_or_404(New_Solve, solve_id)

    red_url = request.referrer or url_for("home")
    return render_template("edit-solve.html", solve=req_solve, red_url=red_url)


def reset_p2(req_solve):
    for i in range(req_solve.p2_count):
            req_solve.time -= 2
    req_solve.time = round(req_solve.time, 2)
    req_solve.p2_count = 0

@app.route("/<penalty>/<int:solve_id>")
@solve_owner_only
def penalty(penalty, solve_id):
    req_solve = db.get_or_404(New_Solve, solve_id)

    if penalty == "DNF":
        req_solve.status = "DNF"
        reset_p2(req_solve)
        db.session.commit()
    elif penalty == "+2":
        req_solve.p2_count += 1
        req_solve.status = "+2"
        req_solve.time += 2
        db.session.commit()

    return redirect(red_url)



@app.route("/reset-penalties/<int:solve_id>")
@solve_owner_only
def reset_penalties(solve_id):
    req_solve = db.get_or_404(New_Solve, solve_id)

    if req_solve.status == "DNF":
        req_solve.status = "OK"
        db.session.commit()
    elif req_solve.status == "+2":
        req_solve.status = "OK"
        reset_p2(req_solve)
        db.session.commit()

    return redirect(red_url)

if __name__ == "__main__":
    app.run(debug=True)
