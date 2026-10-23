from flask import Flask, request, abort

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

import supabase

app = Flask(__name__)

if os.path.exists(".env.local"):
    from dotenv import load_dotenv
    load_dotenv(".env.local")

configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
cron_token = os.getenv("CRON_JOB_TOKEN")
github_token = os.getenv("GITHUB_DISPATCH_TOKEN")

# TODO: Create an endpoint for cron requests
# TODO: Make database for user & group ids
# TODO: Notify the ids when news data change
# TODO: Have retries for OpenVPN connection
# TODO (optional): Make a system (like a cache) for read operations

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


@app.route("/cron", methods=['GET'])
def cron():
    cron_secret_header = request.headers['X-Cron-Secret']

    if cron_secret_header != cron_token:
        abort(403)

    data = {"event_type": "cron_trigger"}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + github_token,
        "X-GitHub-Api-Version": "2026-03-10",
    }
    response = requests.post("https://api.github.com/repos/tigerboss101/line-tun-bot/dispatches", json=data, headers=headers)

    if response.status_code != 204:
        abort(response.status_code)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    if event.message.text != "!tun":
        return

    db_url = os.environ.get("SUPABASE_URL")
    db_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    db = supabase.create_client(db_url, db_key)

    response = db.table("latest_news").select("title, link").execute()
    message = "\n\n".join(row["title"] + "\n" + row["link"] for row in response.data)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=message)]
            )
        )

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
