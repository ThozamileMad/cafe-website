from flask import Flask, render_template, flash, redirect, url_for, abort
from flask_bootstrap import Bootstrap
from databases import sqlalchemy_object, sqlalchemy_databases
from forms import RegisterForm, LoginForm, AddForm, ForgotPasswordForm, RecoveryCodeForm, ChangePasswordForm, searchform
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from functools import wraps
from datetime import datetime
from smtplib import SMTP
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "SSSHHHHHHHHH It's a secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
app.config["SQLALCHEMY_BINDS"] = {"users": "sqlite:///users.db"}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = sqlalchemy_object(app)
database_lst = sqlalchemy_databases(app, db, UserMixin)

Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

User = database_lst[0]
Cafe = database_lst[1]

icons = ["https://cdn-icons-png.flaticon.com/512/9620/9620771.png",
         "https://cdn-icons-png.flaticon.com/512/1095/1095198.png",
         "https://cdn-icons-png.flaticon.com/512/1926/1926476.png",
         "https://cdn-icons-png.flaticon.com/512/2848/2848762.png",
         "https://cdn-icons-png.flaticon.com/512/2891/2891529.png",
         "https://cdn-icons-png.flaticon.com/512/6785/6785822.png"]


def make_pin_expire(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        user = User.query.filter_by(id=kwargs["user_id"]).first()

        try:
            if user.change_password_pin is not None:
                date_time = ["year", "month", "day", "hour"]

                current_date_time = str(datetime.now()).replace("-", " ").replace(":", " ").split()[:-2]
                pin_date_and_time = user.pin_date_and_time.replace("-", " ").replace(":", " ").split()[:-2]
                pin_date_and_time[-1] = str(int(pin_date_and_time[-1]) + 1)

                dict_current_date_time = {date_time[num]: int(current_date_time[num]) for num in range(len(date_time))}
                dict_pin_date_and_time = {date_time[num]: int(pin_date_and_time[num]) for num in range(len(date_time))}

                no_abort = False
                for date_type in date_time:
                    if dict_current_date_time[date_type] > dict_pin_date_and_time[date_type]:
                        return abort(403, description="Error pin expired: access denied until user requests a new pin.")
                    else:
                        no_abort = True
                if no_abort:
                    return function(*args, **kwargs)
            else:
                return abort(403,
                             description="Error pin has not been generated: access denied until the user generates a pin")
        except AttributeError:
            return abort(404, description="Error user does not exist.")
    return inner_function


def restrict_register_login(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        if current_user.is_authenticated:
            return abort(403, description="Unauthorised, access denied until user has logged out of server.")
        else:
            return function(*args, **kwargs)

    return inner_function


def restrict_delete_add_cafe(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        if current_user.is_authenticated:
            return function(*args, **kwargs)
        else:
            return abort(403, description="Unauthorised, access denied until user is logged in.")

    return inner_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def ret_cafe_data(c_data):
    cafe_data = [{"id": data.id, "name": data.name, "img_url": data.img_url,
                  "display_data": [{"Map": [data.map_url,
                                            "https://cdn-icons-png.flaticon.com/512/1072/1072566.png"],
                                    "Location": [data.location,
                                                 "https://cdn-icons-png.flaticon.com/512/447/447031.png"],
                                    "Sockets": [data.has_sockets,
                                                "https://cdn-icons-png.flaticon.com/512/8793/8793193.png"],
                                    "Toilet": [data.has_toilet,
                                               "https://cdn-icons-png.flaticon.com/512/566/566279.png"],
                                    "Wifi": [data.has_wifi,
                                             "https://cdn-icons-png.flaticon.com/512/93/93158.png"],
                                    "Can make calls": [data.can_take_calls,
                                                       "https://cdn-icons-png.flaticon.com/512/126/126341.png"],
                                    "Seats": [data.seats,
                                              "https://cdn-icons-png.flaticon.com/512/6013/6013596.png"],
                                    "Coffee Price": [data.coffee_price,
                                                     "https://cdn-icons-png.flaticon.com/512/991/991952.png"]
                                    }
                                   ]
                  }
                 for data in c_data]

    return cafe_data

@app.route("/", methods=["GET", "POST"])
def home():
    cafes = db.session.query(Cafe).all()[::-1]
    cafe_data = ret_cafe_data(cafes)

    last_cafe_in_database = cafes[-1]
    last_cafe_name = last_cafe_in_database.name
    year = datetime.now().year

    form_func = searchform(random.choice(cafe_data)["name"])
    form = form_func()

    if form.validate_on_submit():
        cafe_names = [dictionary["name"] for dictionary in cafe_data]
        if form.search.data not in cafe_names:
            flash("Cafe not found.")
        else:
            return redirect(url_for("search_cafe", cafe_name=form.search.data))

    return render_template("home.html",
                           cafe_data=cafe_data,
                           logged_in=current_user.is_authenticated,
                           last_cafe_name=last_cafe_name,
                           current_year=year,
                           form=form)


@app.route("/register", methods=["GET", "POST"])
@restrict_register_login
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        emails = [data.email for data in db.session.query(User).all()]
        username = form.username.data
        email = form.email.data
        password = form.password.data

        if email in emails:
            flash("Account exists in MadCafe's database log in instead.")
        else:
            hashed_password = generate_password_hash(password)

            user = User(
                username=username,
                email=email,
                password=hashed_password,
                pin_page_accessed=False
            )
            db.session.add(user)
            db.session.commit()
            user = User.query.filter_by(password=hashed_password).first()
            login_user(user)

            return redirect(url_for("home"))

    return render_template("register_login.html",
                           form=form,
                           icon=random.choice(icons),
                           header="Register",
                           url=url_for('login'),
                           anchor_text="Login",
                           include_forgot_pass=False,
                           add_paragraph=False
                           )


@app.route("/login", methods=["GET", "POST"])
@restrict_register_login
def login():
    form = LoginForm()
    if form.validate_on_submit():
        emails = [data.email for data in db.session.query(User).all()]
        email = form.email.data
        if email in emails:
            user = User.query.filter_by(email=email).first()
            password = form.password.data
            hashed_password = user.password
            if check_password_hash(pwhash=hashed_password, password=password):
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash(
                    f"Invalid Password: Please ensure that you have provided the correct password. {check_password_hash(pwhash=hashed_password, password=password)}")
        else:
            flash(
                "Invalid Email: Please ensure that the email provided is correctly spelt and that you have registered an account in MadCafe's database.")

    return render_template("register_login.html",
                           form=form,
                           icon=random.choice(icons),
                           header="Login",
                           url=url_for('register'),
                           anchor_text="Register",
                           include_forgot_pass=True,
                           add_paragraph=False
                           )


@app.route("/add-cafe", methods=["GET", "POST"])
@restrict_delete_add_cafe
def add_cafe():
    form = AddForm()
    if form.validate_on_submit():
        cafe_names = [data.name for data in db.session.query(Cafe).all()]
        map_urls = [data.map_url for data in db.session.query(Cafe).all()]
        img_urls = [data.img_url for data in db.session.query(Cafe).all()]
        currency_symbols = "¢ $ € £ ¥ ₮ ৲ ৳ ௹ ฿ ៛ ₠ ₡ ₢ ₣ ₤ ₥ ₦ ₧ ₨ ₩ ₪ ₫ ₭ ₯ ₰ ₱ ₲ ₳ ₴ ₵ ￥ R".split()

        cafe_name = form.name.data
        map_url = form.map_url.data
        img_url = form.img_url.data
        location = form.location.data
        has_sockets = form.sockets.data
        has_toilet = form.toilet.data
        has_wifi = form.wifi.data
        can_call = form.call.data
        number_of_seats = form.seats.data
        coffee_price = form.coffee_price.data

        if cafe_name in cafe_names or map_url in map_urls or img_url in img_urls:
            flash("Data already exists in MadCafe's database.")
        elif coffee_price[0] not in currency_symbols:
            flash("Please include the currency in the coffee price field.")
        else:
            try:
                int(number_of_seats)
                float(coffee_price[1:])

                cafe = Cafe(
                    name=cafe_name,
                    map_url=map_url,
                    img_url=img_url,
                    location=location,
                    has_sockets=has_sockets,
                    has_wifi=has_wifi,
                    has_toilet=has_toilet,
                    can_take_calls=can_call,
                    seats=number_of_seats,
                    coffee_price=coffee_price
                )
                db.session.add(cafe)
                db.session.commit()

                return redirect(url_for("home"))
            except ValueError:
                flash("Invalid number of seats or coffee price entered.")

    return render_template("add_cafe.html",
                           form=form,
                           header="Add Cafe",
                           add_paragraph=False)


@app.route("/delete-cafe/<int:cafe_id>")
@restrict_delete_add_cafe
def delete_cafe(cafe_id):
    cafe = Cafe.query.filter_by(id=cafe_id).first()
    db.session.delete(cafe)
    db.session.commit()
    return redirect(url_for("home"))


def send_pin(email, user):
    recovery_pin = random.randint(100, 999)
    with SMTP("smtp.office365.com") as message:
        message.starttls()
        message.login(
            user="madbaudick@outlook.com",
            password="jjbefkaukdnxutaj"
        )
        message.sendmail(
            from_addr="madbaudick@outlook.com",
            to_addrs=f"{email}",
            msg=f'Subject: MadCafes password recovery code\n\nEnter the following pin to change your password: {recovery_pin}'
        )
    user.change_password_pin = recovery_pin
    date_and_time = str(datetime.now())
    user.pin_date_and_time = date_and_time
    db.session.commit()


@app.route("/forgot-password", methods=["GET", "POST"])
@restrict_register_login
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        emails = [data.email for data in db.session.query(User).all()]
        email = form.email.data
        if email not in emails:
            flash(
                "Invalid Email: Please ensure that the email provided is correctly spelt and that you have registered an account in MadCafe's database.")
        else:
            user = User.query.filter_by(email=email).first()
            send_pin(email=email, user=user)

            return redirect(url_for("enter_pin", user_id=user.id))

    return render_template("forgot-password.html",
                           form=form,
                           header="Enter User Email",
                           url=url_for('login'),
                           anchor_text="Login",
                           paragraph="Enter the email you registered with and a three digit pin will be sent to it, the user will be expected to provide that three digit pin to make changes to their password.",
                           add_paragraph=True
                           )


@app.route("/resend_mail/<int:user_id>")
@restrict_register_login
@make_pin_expire
def resend_mail(user_id):
    user = User.query.filter_by(id=user_id).first()
    send_pin(email=user.email, user=user)
    return redirect(url_for("enter_pin", user_id=user.id))


@app.route("/pin-entry/<int:user_id>", methods=["GET", "POST"])
@restrict_register_login
@make_pin_expire
def enter_pin(user_id):
    user = User.query.filter_by(id=user_id).first()

    if user.pin_page_accessed is False:
        email = user.email
        form = RecoveryCodeForm()
        if form.validate_on_submit():
            pin = form.pin.data
            if pin != user.change_password_pin:
                flash("Error: Pin does not match the pin in the database.")
            else:
                try:
                    int(pin)
                    user = User.query.filter_by(email=email).first()
                    user.pin_page_accessed = True
                    db.session.commit()
                    return redirect(url_for('change_password', user_id=user_id))
                except ValueError:
                    flash("Invalid Pin!")
                    pass
    else:
        return abort(403,
                     description="Error pin has already been submitted, page inaccessible until the user requests a new pin.")

    return render_template("forgot-password.html",
                           form=form,
                           header="Enter Pin",
                           url=url_for('resend_mail', user_id=user.id),
                           anchor_text="Resend Pin",
                           paragraph="Enter the pin that was sent to your email. If you have trouble receiving the email check your spam or click the button in the top right corner.",
                           add_paragraph=True
                           )


@app.route("/change-password/<int:user_id>", methods=["GET", "POST"])
@restrict_register_login
@make_pin_expire
def change_password(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user.pin_page_accessed:
        form = ChangePasswordForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            user.password = hashed_password
            user.pin_page_accessed = False
            user.change_password_pin = None
            db.session.commit()
            return redirect(url_for("login"))

        return render_template("forgot-password.html",
                               form=form,
                               header="Change Password",
                               url=url_for('login'),
                               anchor_text="Login",
                               paragraph="Make changes to your password below.",
                               add_paragraph=True
                               )
    else:
        return abort(403,
                     description="Error pin has not been submitted: access denied until the user submits a valid pin")


@app.route("/search/<cafe_name>", methods=["GET", "POST"])
def search_cafe(cafe_name):
    cafes = db.session.query(Cafe).all()
    cafe_data = ret_cafe_data(cafes)

    searched_cafe = [data for data in cafe_data if data["name"] == cafe_name]

    form_func = searchform(random.choice(cafe_data)["name"])
    form = form_func()

    if form.validate_on_submit():
        cafe_names = [dictionary["name"] for dictionary in cafe_data]
        if form.search.data not in cafe_names:
            flash("Cafe not found.")
        else:
            return redirect(url_for("search_cafe", cafe_name=form.search.data))

    return render_template("search_cafe.html",
                           form=form,
                           last_cafe_name=searched_cafe[0]["name"],
                           cafe_data=searched_cafe,
                           logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
