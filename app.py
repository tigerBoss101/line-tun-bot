from bs4 import BeautifulSoup

from dotenv import load_dotenv

from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os

import requests

load_dotenv()


class Base(DeclarativeBase):
    pass


app = Flask(__name__)

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db.init_app(app)

configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]


with app.app_context():
    db.create_all()


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def get_tun_news():
    response = requests.get("https://tun.ac.th/mainpage", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"})
    soup = BeautifulSoup(response.text, "html.parser")
    anchors = soup.find("table", class_="news_index").find_all("a", class_="link")
    return [
        anchor["title"] + "\n" + "https://tun.ac.th/" + anchor["href"]
        for anchor in anchors
    ]


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if event.message.text == "!tun":
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="\n\n".join(get_tun_news()))]
                )
            )

if __name__ == "__main__":
    app.run()
