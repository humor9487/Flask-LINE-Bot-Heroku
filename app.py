import os
from datetime import datetime

from flask import Flask, abort, request

import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

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
    reply = TextSendMessage(text=f"紀錄成功{text}")
    #reply = TextSendMessage(text=f"成功記錄 : {m}月{d}日在{item}項目花費了{cost}元")
    line_bot_api.reply_message(event.reply_token, reply)
    
    
    # ascess Google Sheet
    Json = 'liquid-streamer-343612-20f96166f6a8.json'  # Json 的單引號內容請改成妳剛剛下載的那個金鑰
    Url = ['https://spreadsheets.google.com/feeds']
    # 連結至資料表
    Connect = SAC.from_json_keyfile_name(Json, Url)
    GoogleSheets = gspread.authorize(Connect)
    # 開啟資料表及工作表
    Sheet = GoogleSheets.open_by_key('15z2LDV9Rr1c7QueeeKQZSWaylEieKo9YJA-vmHLVKNE')  # 這裡請輸入妳自己的試算表代號
    Sheets = Sheet.sheet1
    Sheets.append_row([1,2,3,4])

