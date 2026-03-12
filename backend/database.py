from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    category = db.Column(db.String(100), index=True)
    image_url = db.Column(db.String(500))

    prices = db.relationship("Price", backref="product", lazy=True)


class Price(db.Model):
    __tablename__ = "prices"

    price_id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.product_id"),
        nullable=False
    )

    store_name = db.Column(db.String(100), index=True)
    price = db.Column(db.Float, nullable=False)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )

    product_url = db.Column(db.String(500))


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    search_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.String(100), index=True)
    query = db.Column(db.String(255), index=True)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )