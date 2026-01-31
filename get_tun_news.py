import requests
from bs4 import BeautifulSoup


def get_tun_news():
    response = requests.get("https://tun.ac.th/mainpage", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"})
    soup = BeautifulSoup(response.text, "html.parser")
    anchors = soup.find("table", class_="news_index").find_all("a", class_="link")
    return [
        anchor["title"] + "\n" + "https://tun.ac.th/" + anchor["href"]
        for anchor in anchors
    ]

if __name__ == "__main__":
    print(get_tun_news())
