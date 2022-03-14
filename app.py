import os
from datetime import datetime


import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC


from flask import Flask, abort, request

# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))


@app.route("/", methods=["GET", "POST"])
def callback():

    if request.method == "GET":
        return "Hello Heroku"
    if request.method == "POST":
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)

        return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    get_message = event.message.text

    # Send To Line
    reply = TextSendMessage(text=f"{get_message}喵~")
    line_bot_api.reply_message(event.reply_token, reply)
    
    # google sheet

    Json = 'liquid-streamer-343612-20f96166f6a8.json' # Json 的單引號內容請改成妳剛剛下載的那個金鑰
    Url = ['https://spreadsheets.google.com/feeds']
    # 連結至資料表
    Connect = SAC.from_json_keyfile_name(Json, Url)
    GoogleSheets = gspread.authorize(Connect)
    # 開啟資料表及工作表
    Sheet = GoogleSheets.open_by_key('15z2LDV9Rr1c7QueeeKQZSWaylEieKo9YJA-vmHLVKNE') # 這裡請輸入妳自己的試算表代號
    Sheets = Sheet.sheet1
    # 寫入
    if Sheets.get_all_values() == []:
        dataTitle = ["消費日期", "消費項目", "消費金額"]
        Sheets.append_row(dataTitle)
    Sheets.append_row(get_message)
@handler.add(FollowEvent)
def Welcome(event):
    get_ID = event.source.userId
    
    # Send Welcome Message
    welcome = TextSendMessage(text=f"Welcome come on!!!")
    line_bot_api.push_message(get_ID, welcome)
