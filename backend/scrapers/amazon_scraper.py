import requests
from bs4 import BeautifulSoup
import random
import time

# rotate user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def scrape_amazon(keyword):

    url = f"https://www.amazon.in/s?k={keyword}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9"
    }

    try:
        # request throttling
        time.sleep(random.uniform(1.5, 3))

        response = requests.get(url, headers=headers)

        soup = BeautifulSoup(response.text, "lxml")

        products = []

        items = soup.select("div.s-result-item")

        for item in items[:5]:

            title = item.select_one("h2 span")
            price = item.select_one(".a-price-whole")
            link = item.select_one("h2 a")
            rating = item.select_one(".a-icon-alt")

            if title and price and link:

                products.append({
                    "store": "Amazon Scraper",
                    "name": title.text.strip(),
                    "price": price.text.strip(),
                    "url": "https://amazon.in" + link.get("href"),
                    "rating": rating.text if rating else "N/A",
                    "availability": "Check on Amazon",
                    "shipping": "Varies"
                })

        return products

    except Exception as e:

        print("Amazon scraper error:", e)

        return []