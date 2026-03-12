import re
from statistics import mean


def normalize_name(name):
    """
    Normalize product names to improve matching across stores
    """
    if not name:
        return ""

    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()


def calculate_score(price, shipping, rating):
    """
    Scoring system combining price, shipping and seller rating
    Lower final price and higher rating = better score
    """

    final_price = price + shipping

    score = (rating * 2) - (final_price / 1000)

    return round(score, 2)


def compare_prices(price_results):
    """
    Core price comparison engine
    """

    offers = []

    for item in price_results:

        price_str = item.get("price", "0")
        price_str = price_str.replace("₹", "").replace(",", "").strip()

        try:
            price = float(price_str)
        except:
            continue

        shipping_value = item.get("shipping", 0)

        if isinstance(shipping_value, str):
            shipping = 0
        else:
            shipping = float(shipping_value)

        rating = float(item.get("rating", 4.0) or 4.0)

        availability = item.get("availability", "Unknown")

        final_price = price + shipping

        score = calculate_score(price, shipping, rating)

        offers.append({

            "store": item.get("store"),

            "product_name": item.get("name"),

            "normalized_name": normalize_name(item.get("name")),

            "price": price,

            "shipping": shipping,

            "rating": rating,

            "availability": availability,

            "final_price": final_price,

            "score": score,

            "url": item.get("url")

        })

    if not offers:
        return {
            "offers": [],
            "lowest_price": None,
            "highest_price": None,
            "average_price": None
        }

    prices = [o["final_price"] for o in offers]

    lowest_price = min(prices)

    highest_price = max(prices)

    average_price = round(mean(prices), 2)

    # Sort by score (best offer first)
    offers = sorted(offers, key=lambda x: x["score"], reverse=True)

    return {

        "offers": offers,

        "lowest_price": lowest_price,

        "highest_price": highest_price,

        "average_price": average_price

    }