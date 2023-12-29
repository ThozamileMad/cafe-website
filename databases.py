from flask_sqlalchemy import SQLAlchemy
from cafes import cafe_data
from sqlalchemy.exc import IntegrityError


def sqlalchemy_object(app):
    return SQLAlchemy(app)


def sqlalchemy_databases(app, db, UserMixin):
    with app.app_context():
        class Cafe(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            map_url = db.Column(db.String)
            img_url = db.Column(db.String)
            location = db.Column(db.String)
            has_sockets = db.Column(db.Boolean)
            has_toilet = db.Column(db.Boolean)
            has_wifi = db.Column(db.Boolean)
            can_take_calls = db.Column(db.Boolean)
            seats = db.Column(db.String)
            coffee_price = db.Column(db.String)
            
        class User(UserMixin, db.Model):
            __bind_key__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String, unique=False, nullable=False)
            email = db.Column(db.String, unique=True, nullable=False)
            password = db.Column(db.String, unique=False, nullable=False)
            change_password_pin = db.Column(db.String, nullable=True)
            pin_date_and_time = db.Column(db.String, nullable=True)
            pin_page_accessed = db.Column(db.Boolean)

        db.create_all()

        data = db.session.query(Cafe).all()
        if data == []:
            for dictionary in cafe_data:
                cafe = Cafe(id=dictionary["id"],
                            name=dictionary["name"],
                            img_url=dictionary["img_url"],
                            map_url=dictionary["map_url"],
                            location=dictionary["location"],
                            has_sockets=dictionary["has_sockets"],
                            has_toilet=dictionary["has_toilet"],
                            has_wifi=dictionary["has_wifi"],
                            can_take_calls=dictionary["can_take_calls"],
                            seats=dictionary["seats"],
                            coffee_price=dictionary["coffee_price"],
                            )
                db.session.add(cafe)
                db.session.commit()


        
    return [User, Cafe] 
    
