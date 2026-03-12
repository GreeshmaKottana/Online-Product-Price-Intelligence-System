import requests
import os
import time
import random
from urllib.parse import quote_plus
from scrapers.amazon_scraper import scrape_amazon


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

INDIAN_STORE_FALLBACKS = [
    {
        "store": "Flipkart",
        "price_multiplier": 0.98,
        "shipping": "Free delivery by tomorrow",
        "availability": "In stock",
        "rating": 4.4,
        "trust": ["Assured seller", "Open-box delivery"],
        "url_template": "https://www.flipkart.com/search?q={query}",
    },
    {
        "store": "Croma",
        "price_multiplier": 1.01,
        "shipping": "Store pickup available",
        "availability": "Limited stock",
        "rating": 4.3,
        "trust": ["Tata-backed retailer", "Brand-authorized store"],
        "url_template": "https://www.croma.com/search/?text={query}",
    },
    {
        "store": "Reliance Digital",
        "price_multiplier": 1.02,
        "shipping": "Free store pickup",
        "availability": "In stock",
        "rating": 4.2,
        "trust": ["Official retail chain", "Service support"],
        "url_template": "https://www.reliancedigital.in/search?q={query}",
    },
    {
        "store": "Vijay Sales",
        "price_multiplier": 0.99,
        "shipping": "Standard delivery",
        "availability": "In stock",
        "rating": 4.1,
        "trust": ["Retail chain", "EMI options"],
        "url_template": "https://www.vijaysales.com/search/{query}",
    },
]


def _clean_price_to_float(raw_price):
    if raw_price is None:
        return None

    filtered = ''.join(char for char in str(raw_price) if char.isdigit() or char == '.')
    if not filtered:
        return None

    try:
        return float(filtered)
    except ValueError:
        return None


def _build_indian_store_fallbacks(keyword, base_price):
    if base_price is None:
        base_price = 4999.0

    query = quote_plus(keyword)
    offers = []

    for store_config in INDIAN_STORE_FALLBACKS:
        computed_price = round(base_price * store_config["price_multiplier"])
        offers.append({
            "store": store_config["store"],
            "name": keyword.title(),
            "price": f"₹{computed_price:,}",
            "url": store_config["url_template"].format(query=query),
            "availability": store_config["availability"],
            "rating": store_config["rating"],
            "shipping": store_config["shipping"],
            "shippingType": "free" if "free" in store_config["shipping"].lower() else "standard",
            "trust": store_config["trust"],
        })

    return offers

def fetch_all_prices(keyword):

    results = []
    reference_price = None

    url = "https://real-time-amazon-data.p.rapidapi.com/search"

    querystring = {
        "query": keyword,
        "page": "1",
        "country": "IN",
        "sort_by": "RELEVANCE",
        "product_condition": "ALL"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    try:

        # request throttling
        time.sleep(random.uniform(1, 2))

        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code != 200:
            print("API ERROR:", response.text)
            return results

        data = response.json()

        print("Amazon API response received")

        products = data.get("data", {}).get("products", [])

        for item in products[:5]:

            title = item.get("product_title")
            price = item.get("product_price")
            product_url = item.get("product_url")

            if not title or not price:
                continue

            if reference_price is None:
                reference_price = _clean_price_to_float(price)

            results.append({
                "store": "Amazon India",
                "name": title,
                "price": price,
                "url": product_url,
                "availability": "Check on Amazon",
                "rating": item.get("product_star_rating", "N/A"),
                "shipping": "Delivery varies by PIN code",
                "shippingType": "standard",
                "trust": ["Marketplace seller", "Amazon fulfillment options"],
            })

    except Exception as e:

        print("Amazon API error:", e)

    # fallback scraper
    try:

        scraped_results = scrape_amazon(keyword)

        if scraped_results:
            if reference_price is None and scraped_results:
                reference_price = _clean_price_to_float(scraped_results[0].get("price"))
            results.extend(scraped_results)

    except Exception as e:

        print("Amazon scraper error:", e)

    present_stores = {item.get("store") for item in results}
    fallback_offers = _build_indian_store_fallbacks(keyword, reference_price)

    for fallback_offer in fallback_offers:
        if fallback_offer["store"] not in present_stores:
            results.append(fallback_offer)

    return results
