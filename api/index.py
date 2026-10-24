import os
import requests
import supabase

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
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    LeaveEvent,
    TextMessageContent,
)

app = Flask(__name__)

if os.path.exists(".env.local"):
    from dotenv import load_dotenv
    load_dotenv(".env.local")

configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
cron_token = os.getenv("CRON_JOB_TOKEN")
github_token = os.getenv("GITHUB_DISPATCH_TOKEN")

db = supabase.create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SECRET_KEY")
)

# TODO: Add functionality for groups too
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


@handler.add(FollowEvent)
def handle_follow(event: FollowEvent):
    user_id = event.source.user_id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        name = line_bot_api.get_profile(user_id).display_name

    db.table("users").insert({"user_id": user_id, "name": name}).execute()


@handler.add(UnfollowEvent)
def handle_unfollow(event: UnfollowEvent):
    user_id = event.source.user_id

    db.table("users").delete().eq("user_id", user_id).execute()


@handler.add(JoinEvent)
def handle_join(event: JoinEvent):
    group_id = event.source.group_id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        name = line_bot_api.get_group_summary(group_id).group_name

    db.table("users").insert({"user_id": group_id, "name": name}).execute()


@handler.add(LeaveEvent)
def handle_unfollow(event: LeaveEvent):
    group_id = event.source.group_id

    db.table("users").delete().eq("user_id", group_id).execute()


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
