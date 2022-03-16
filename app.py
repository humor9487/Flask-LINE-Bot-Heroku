import os
from datetime import datetime
# google sheet使用套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from flask import Flask, abort, request

# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, TemplateSendMessage, URIAction, PostbackAction, ButtonsTemplate, PostbackEvent

# 試算表金鑰與網址
Json = 'informatics-and-social-service-4075fdd59a29.json'  # Json 的單引號內容請改成妳剛剛下載的那個金鑰
Url = ['https://spreadsheets.google.com/feeds']
# 連結至資料表
Connect = SAC.from_json_keyfile_name(Json, Url)
GoogleSheets = gspread.authorize(Connect)
# 開啟資料表及工作表
Sheet = GoogleSheets.open_by_key('1sXOLCHiH0n-HnmdiJzLVVDE5TjhoAPI3yN4Ku-4JUM4')  # 這裡請輸入妳自己的試算表代號
Sheets = Sheet.sheet1
# 寫入
if Sheets.get_all_values() == []:
    dataTitle = ["消費日期", "消費項目", "消費金額"]
    Sheets.append_row(dataTitle)

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))


def inquire_certain_day(day):
    datas = Sheets.get_all_values()
    re = []
    for data in datas:
        if data[0] == day:
            re.append(data)
    return re
def date_valid(m, d):
    if m % 2:
        if m > 7:
            return d <= 30
        else:
            return d <=31
    else:
        if m == 2:
            return d <= 29
        elif m > 6:
            return d <= 31
        else:
            return d <= 30



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
    if get_message == '功能選項':
        buttons_template_message = TemplateSendMessage(
            alt_text='功能選項',
            template=ButtonsTemplate(
                thumbnail_image_url='https://example.com/image.jpg',
                title='功能選項',
                text='請選擇要使用的功能',
                actions=[
                    PostbackAction(
                        label='記帳',
                        display_text='我要記帳',
                        data='record'
                    ),
                    PostbackAction(
                        label='查詢',
                        display_text='我要查詢',
                        data='inquire'
                    ),
                    PostbackAction(
                        label='重置',
                        display_text='我要重置',
                        data='reset'
                    ),
                    URIAction(
                        label='查看表單',
                        uri='https://docs.google.com/spreadsheets/d/1sXOLCHiH0n-HnmdiJzLVVDE5TjhoAPI3yN4Ku-4JUM4/edit?usp=sharing')
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    else:
        try:
            m, d = get_message.split("/")
            valid = date_valid(m, d)
            if valid:
                out = inquire_certain_day(get_message)
                if out == []:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到資料"))
                else:
                    reply = []
                    s = 0
                    for o in out:
                        s += int(o[2])
                        if o[2] > 0:
                            reply.append(TextSendMessage(text=f"{get_message}在{o[1]}項目中花費了{-o[2]}元"))
                        else:
                            reply.append(TextSendMessage(text=f"{get_message}在{o[1]}項目中得到了{o[2]}元"))
                    reply.append(TextSendMessage(text=f"結算:{s}"))
                    line_bot_api.reply_message(event.reply_token, reply)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="錯誤的日期格式"))
        except ValueError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="不明的指令"))

    # Send To Line
    line_bot_api.reply_message(event.reply_token, buttons_template_message)


# 新增功能1:歡迎訊息
@handler.add(FollowEvent)
def Welcome(event):
    get_ID = event.source.userId

    # Send Welcome Message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Got follow event'))

@handler.add(PostbackEvent)
def Postback01(event):
    get_data = event.postback.data
    if get_data == 'record':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='紀錄成功'))
    elif get_data == 'inquire':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='輸入您想查詢的日期(格式month/day):'))
    elif get_data == 'reset':
        Sheets.clear()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='重置成功'))
    else:
        print("error")
        pass
