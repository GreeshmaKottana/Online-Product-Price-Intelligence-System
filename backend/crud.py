from database import db, Product, Price, SearchHistory
from datetime import datetime


def create_product(name, category, image_url=""):
    product = Product(
        name=name,
        category=category,
        image_url=image_url
    )

    db.session.add(product)
    db.session.commit()

    return product


def get_product(product_id):
    return db.session.get(Product, product_id)


def get_all_products():
    return Product.query.all()


def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if product:
        db.session.delete(product)
        db.session.commit()

    return product


def create_price(product_id, store_name, price, product_url):
    price_entry = Price(
        product_id=product_id,
        store_name=store_name,
        price=price,
        product_url=product_url,
        timestamp=datetime.utcnow()
    )

    db.session.add(price_entry)
    db.session.commit()

    return price_entry


def get_prices(product_id):
    return Price.query.filter_by(product_id=product_id).all()


def save_search(user_id, query):
    search = SearchHistory(
        user_id=user_id,
        query=query,
        timestamp=datetime.utcnow()
    )

    db.session.add(search)
    db.session.commit()

    return search
