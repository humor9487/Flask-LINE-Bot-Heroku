import os
from datetime import datetime
# google sheet使用套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from flask import Flask, abort, request
import time

# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, TemplateSendMessage\
    , URIAction, PostbackAction, ButtonsTemplate, PostbackEvent, DatetimePickerTemplateAction, ConfirmTemplate

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
    dataTitle = ["日期", "項目", "金額"]
    Sheets.append_row(dataTitle)

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
onaction = False

ini_y, ini_m, ini_d = '2022', '06', '30'
def get_now_time():
    global ini_y, ini_m, ini_d
    now_time = time.localtime(time.time())
    ini_m = str(now_time.tm_mon)
    ini_d = str(now_time.tm_mday)
    ini_y = str(now_time.tm_year)
    if len(ini_m) == 1:
        ini_m = "0"+str(ini_m)
    if len(ini_d) == 1:
        ini_d = "0"+str(ini_d)




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
            item, money = str(get_message).split('=')
            money = int(money)
            datas = Sheets.get_all_values()
            if money <= 0:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入有效的金額"))
            elif Sheets.cell(len(datas), 2).value == '*待輸入支出':
                Sheets.update_cell(len(datas), 2, item)
                Sheets.update_cell(len(datas), 3, str(-money))
                data = Sheets.get_all_values()[-1]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"成功紀錄:\n{data[0]}在{data[1]}項目中花費了{-int(data[2])}元"))
            elif Sheets.cell(len(datas), 2).value == '*待輸入收入':
                Sheets.update_cell(len(datas), 2, item)
                Sheets.update_cell(len(datas), 3, str(money))
                data = Sheets.get_all_values()[-1]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"成功紀錄:\n{data[0]}在{data[1]}項目中花費了{-int(data[2])}元"))
            elif Sheets.cell(len(datas), 2).value == '*待輸入':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇 收入/支出"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先使用記帳功能選擇時間"))
        except ValueError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="不明的指令\n請輸入'功能選項'呼叫功能表"))

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
    get_now_time()
    get_data = event.postback.data
    if get_data == 'record':
        picker = TemplateSendMessage(
            alt_text='紀錄中...',
            template=ButtonsTemplate(
                text='請選擇日期',
                title='YYYY-MM-dd',
                actions=[
                    DatetimePickerTemplateAction(
                        label='Setting',
                        data='record_date',
                        mode='date',
                        initial=f'{ini_y}-{ini_m}-{ini_d}',
                        min='2020-01-01',
                        max='2099-12-31'
                    )
                ]
            )
        )

        line_bot_api.reply_message(event.reply_token, picker)



        #line_bot_api.reply_message(event.reply_token, TextSendMessage(text='紀錄成功'))
    elif get_data == 'inquire':
        picker = TemplateSendMessage(
            alt_text='查詢中...',
            template=ButtonsTemplate(
                text='請選擇',
                title='請選擇收入/支出',
                actions=[
                    DatetimePickerTemplateAction(
                        label='選擇日期',
                        data='inquire_date',
                        mode='date',
                        initial=f'{ini_y}-{ini_m}-{ini_d}',
                        min='2020-01-01',
                        max='2099-12-31'
                    )
                ]
            )
        )

        line_bot_api.reply_message(event.reply_token, picker)
    elif get_data == 'reset':
        onaction = True
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='您真的要重置所有紀錄嗎?'))
        picker = TemplateSendMessage(
            alt_text='選擇中...',
            template=ConfirmTemplate(
                text='之前的資料都會不見喔!!',
                title='確定要重置所有紀錄嗎?',
                actions=[
                    PostbackAction(
                        label='是',
                        display_text='是',
                        data='reset_true'
                    ),
                    PostbackAction(
                        label='否',
                        display_text='否',
                        data='record_false'
                    )
                ]
            )
        )

        line_bot_api.reply_message(event.reply_token, picker)

    elif get_data == 'reset_true':
        if onaction:
            Sheets.clear()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='重置成功'))
    elif get_data == 'reset_false':
        onaction = False
    elif get_data == 'record_date':
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        datas = Sheets.get_all_values()
        if datas[-1][1][0] != '*':
            Sheets.append_row([date, '*待輸入', '0'])
        else:
            Sheets.update_cell(len(datas), 1, date)
            Sheets.update_cell(len(datas), 2, '*待輸入')

        picker = TemplateSendMessage(
            alt_text='選擇中...',
            template=ConfirmTemplate(
                text='收入/支出',
                title='請選擇收入或支出',
                actions=[
                    PostbackAction(
                        label='收入',
                        display_text='輸入中...',
                        data='record_income'
                    ),
                    PostbackAction(
                        label='支出',
                        display_text='輸入中...',
                        data='record_expense'
                    )
                ]
            )
        )

        line_bot_api.reply_message(event.reply_token, picker)

    elif get_data == 'record_income':
        datas = Sheets.get_all_values()
        if datas[-1][1] == '*待輸入' or datas[-1][1] == '*待輸入收入' or datas[-1][1] == '*待輸入支出':
            Sheets.update_cell(len(datas), 2, '*待輸入收入')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請輸入收入項目與金額。\n(ex:撿到一百塊=100)'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請重新選擇日期'))
    elif get_data == 'record_expense':
        datas = Sheets.get_all_values()
        if datas[-1][1] == '*待輸入' or datas[-1][1] == '*待輸入收入' or datas[-1][1] == '*待輸入支出':
            Sheets.update_cell(len(datas), 2, '*待輸入支出')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請輸入支出項目與金額。\n(ex:我的豆花=30)'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請重新選擇日期'))
    elif get_data == 'inquire_date':
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        datas = Sheets.get_all_values()
        result = []
        for data in datas:
            if data[0] == date:
                result.append(data)
        if result == []:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到資料"))
        else:
            reply = []
            s = 0
            for re in result:
                s += int(re[2])
                if re[1] == '待輸入':
                    continue
                if int(re[2]) < 0:
                    reply.append(TextSendMessage(text=f"{re[0]}在{re[1]}項目中花費了{-int(re[2])}元"))
                else:
                    reply.append(TextSendMessage(text=f"{re[0]}在{re[1]}項目中存到了{re[2]}元"))
            reply.append(TextSendMessage(text=f"{re[0]}的收支結算:{s}"))
            line_bot_api.reply_message(event.reply_token, reply)

    else:
        print("Unexpect PostbackEvent!!!")
