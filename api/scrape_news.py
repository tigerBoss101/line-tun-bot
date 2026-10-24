from bs4 import BeautifulSoup
from curl_cffi import requests
import os
import supabase
import time

def scrape_news():

    # Connect to TUN site

    url = "https://www.tun.ac.th/"

    for _ in range(10):
        response = requests.get(url + "mainpage", impersonate="chrome120", timeout=10)
        if response.status_code != 403:
            break
        time.sleep(1)
    else:
        raise ValueError("All forbidden")

    # Scrape News

    soup = BeautifulSoup(response.text, "html.parser")
    news_anchors = soup.find(class_="news_index").find_all("a")
    news_titles = [str(news_anchor.string) for news_anchor in news_anchors]
    news_links = [url + news_anchor["href"] for news_anchor in news_anchors]

    # DB init

    if os.path.exists(".env.local"):
        from dotenv import load_dotenv
        load_dotenv(".env.local")

    db_url = os.environ.get("SUPABASE_URL")
    db_key = os.environ.get("SUPABASE_SECRET_KEY")
    db = supabase.create_client(db_url, db_key)

    # Check if news changed

    latest_link = db.table("latest_news").select("link").limit(1).execute().data[0]["link"]
    changed = latest_link != news_links[0]

    # Update news

    news_data = [{"id": i, "title": title, "link": link} for i, (title, link) in enumerate(zip(news_titles, news_links))]
    response = db.table("latest_news").upsert(news_data).execute()

    # Notify users if news changed
    if changed:
        requests.get("https://line-tun-bot.vercel.app/notify")

    return response

if __name__ == "__main__":
    print(scrape_news())
