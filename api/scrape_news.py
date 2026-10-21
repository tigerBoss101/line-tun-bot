from curl_cffi import requests
from bs4 import BeautifulSoup
import time

def scrape_news():

    url = "https://www.tun.ac.th/"

    for _ in range(10):
        response = requests.get(url + "mainpage", impersonate="chrome120", timeout=10)
        if response.status_code != 403:
            break
        time.sleep(1)
    else:
        raise ValueError("All forbidden")

    soup = BeautifulSoup(response.text, "html.parser")
    news_anchors = soup.find(class_="news_index").find_all("a")
    news_texts = [str(news_anchor.string) for news_anchor in news_anchors]
    news_links = [url + news_anchor["href"] for news_anchor in news_anchors]
    return news_texts, news_links

if __name__ == "__main__":
    print(scrape_news())
