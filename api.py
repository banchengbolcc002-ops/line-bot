# ==========================================
# 【第1部分】載入套件
# ==========================================

# FastAPI：建立網站 API
from fastapi import FastAPI, Request

# requests：連接 LINE API
import requests

# Google Sheet
import gspread

# 系統工具
import os
import json

# 日期時間
from datetime import datetime, timedelta

# Google 驗證
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ChatGPT
from openai import OpenAI


# ==========================================
# 【第2部分】建立 FastAPI
# ==========================================

app = FastAPI()


# ==========================================
# 【第3部分】讀取 Render 環境變數
# ==========================================

# LINE Token
CHANNEL_ACCESS_TOKEN = os.environ[
    "LINE_CHANNEL_ACCESS_TOKEN"
]

# OpenAI
client_ai = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


# ==========================================
# 【第4部分】連接 Google Sheet
# ==========================================

scope = [

    "https://www.googleapis.com/auth/spreadsheets",

    "https://www.googleapis.com/auth/drive"

]

google_key = json.loads(
    os.environ["GOOGLE_KEY"]
)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_key,
    scope
)

client = gspread.authorize(creds)

sheet = client.open(
    "linebot-log"
).worksheet(
    "linebot-care"
)


# ==========================================
# 【第5部分】ChatGPT回答
# ==========================================

def ask_chatgpt(question):

    try:

        response = client_ai.chat.completions.create(

            model="gpt-4o-mini",

            messages=[

                {
                    "role": "system",
                    "content":
                    """
                    你是靈糧堂AI數位執事。

                    使用繁體中文回答。

                    態度溫和。

                    回答：
                    1. 聖經問題
                    2. 禱告問題
                    3. 職場問題
                    4. AI問題
                    5. 一般生活問題
                    """
                },

                {
                    "role": "user",
                    "content": question
                }

            ]

        )

        return response.choices[0].message.content

    except Exception as e:

        print("OpenAI錯誤")

        print(e)

        return "目前AI服務忙碌中，請稍後再試。"


# ==========================================
# 【第6部分】寫入 Google Sheet
# ==========================================

def log_to_sheet(

    user_name,
    user_message,
    bot_reply,
    intent

):

    try:

        sheet.append_row([

            str(
                datetime.now()
                + timedelta(hours=8)
            ),

            user_name,

            user_message,

            bot_reply,

            intent

        ])

    except Exception as e:

        print("Google Sheet錯誤")

        print(e)


# ==========================================
# 【第7部分】回覆LINE
# ==========================================

def reply_to_line(

    reply_token,

    text

):

    try:

        response = requests.post(

            "https://api.line.me/v2/bot/message/reply",

            headers={

                "Authorization":
                f"Bearer {CHANNEL_ACCESS_TOKEN}",

                "Content-Type":
                "application/json"

            },

            json={

                "replyToken":
                reply_token,

                "messages": [

                    {

                        "type": "text",

                        "text": text[:1000]

                    }

                ]

            }

        )

        print(
            "LINE STATUS:",
            response.status_code
        )

    except Exception as e:

        print("LINE錯誤")

        print(e)


# ==========================================
# 【第8部分】取得LINE名稱
# ==========================================

def get_user_name(user_id):

    try:

        response = requests.get(

            f"https://api.line.me/v2/bot/profile/{user_id}",

            headers={

                "Authorization":
                f"Bearer {CHANNEL_ACCESS_TOKEN}"

            }

        )

        if response.status_code == 200:

            return response.json().get(
                "displayName",
                user_id
            )

        return user_id

    except:

        return user_id


# ==========================================
# 【第9部分】固定指令
# ==========================================

def handle_message(msg):

    msg = msg.strip()

    commands = {

        "你好":
        (
            "🌿 平安！",
            "greet"
        ),

        "報到":
        (
            "✅ 已記錄報到",
            "checkin"
        ),

        "點名":
        (
            "📢 點名開始，請回覆：報到",
            "rollcall"
        ),

        "禱告":
        (
            "🙏 願神祝福你。",
            "prayer"
        )

    }

    if msg in commands:

        return commands[msg]

    # 不是固定指令
    return None, "chatgpt"


# ==========================================
# 【第10部分】首頁測試
# ==========================================

@app.get("/")

def home():

    return {

        "status": "ok",

        "message": "LINE BOT RUNNING"

    }


# ==========================================
# 【第11部分】LINE Webhook
# ==========================================

@app.post("/reply")

async def reply(request: Request):

    try:

        body = await request.json()

        events = body.get(
            "events",
            []
        )

        if len(events) == 0:

            return {

                "ok": True

            }

        event = events[0]

        # 非訊息事件直接略過

        if event.get("type") != "message":

            return {

                "ok": True

            }

        # 非文字訊息略過

        if event["message"]["type"] != "text":

            return {

                "ok": True

            }

        user_message = (
            event["message"]["text"]
        )

        user_id = (
            event["source"].get(
                "userId",
                ""
            )
        )

        reply_token = (
            event["replyToken"]
        )

        user_name = (
            get_user_name(user_id)
        )

        reply_text, intent = (
            handle_message(user_message)
        )

        # ChatGPT模式

        if intent == "chatgpt":

            reply_text = ask_chatgpt(
                user_message
            )

        # 回LINE

        reply_to_line(

            reply_token,

            reply_text

        )

        # 存Google Sheet

        log_to_sheet(

            user_name,

            user_message,

            reply_text,

            intent

        )

        return {

            "ok": True

        }

    except Exception as e:

        print("Webhook錯誤")

        print(e)

        return {

            "ok": False,

            "error": str(e)

        }
