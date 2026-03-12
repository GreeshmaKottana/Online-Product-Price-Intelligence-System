import requests
import os
import time
import random
from scrapers.amazon_scraper import scrape_amazon


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def fetch_all_prices(keyword):

    results = []

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

            results.append({
                "store": "Amazon API",
                "name": title,
                "price": price,
                "url": product_url,
                "availability": "Check on Amazon",
                "rating": item.get("product_star_rating", "N/A"),
                "shipping": "Varies"
            })

    except Exception as e:

        print("Amazon API error:", e)

    # fallback scraper
    try:

        scraped_results = scrape_amazon(keyword)

        if scraped_results:
            results.extend(scraped_results)

    except Exception as e:

        print("Amazon scraper error:", e)

    return results