# ==========================================================
# 班級名稱：板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學生學號：18
#
# 專題名稱：
# LINE Bot + Google Sheet + Gemini AI 智慧助理系統
#
# 功能：
# 1. LINE訊息接收
# 2. 關鍵字回覆
# 3. 點名功能
# 4. 出席紀錄
# 5. Google Sheet 紀錄
# 6. Gemini AI 問答
# ==========================================================

# ==========================================================
# 載入套件
# ==========================================================

from fastapi import FastAPI, Request

import requests
import gspread
import json
import os

from datetime import datetime, timedelta

from oauth2client.service_account import (
    ServiceAccountCredentials
)

from google import genai


# ==========================================================
# 建立 FastAPI
# ==========================================================

app = FastAPI()


# ==========================================================
# 讀取 Render 環境變數
# ==========================================================

CHANNEL_ACCESS_TOKEN = os.environ[
   "LINE_CHANNEL_ACCESS_TOKEN"
]

GEMINI_API_KEY = os.environ[
    "GEMINI_API_KEY"
]


# Gemini Client
client_ai = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==========================================================
# Google Sheet 連線
# ==========================================================

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


# ==========================================================
# Gemini AI 問答
# ==========================================================

def ask_ai(question):

    try:

        print("===== Gemini Start =====")

        response = client_ai.models.generate_content(

            model="gemini-2.0-flash",

            contents=question

        )

        print("===== Gemini Success =====")

        if hasattr(response, "text"):

            return response.text[:1000]

        return "目前無法取得回答"

    except Exception as e:

        print("===== Gemini Error =====")

        print(str(e))

        print("========================")

        return """
AI服務暫時無法使用

請稍後再試
"""


# ==========================================================
# 寫入 Google Sheet
# ==========================================================

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

        print("Google Sheet 錯誤")

        print(str(e))


# ==========================================================
# 回覆 LINE
# ==========================================================

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

                        "text": str(text)[:1000]

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

        print(str(e))


# ==========================================================
# 取得 LINE 顯示名稱
# ==========================================================

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


# ==========================================================
# 固定指令
# ==========================================================

def handle_message(msg):

    msg = msg.strip()

    commands = {

        "你好":
        (
            "🌿 平安！",
            "greet"
        ),

        "謝謝":
        (
            "🙏 感謝主",
            "thanks"
        ),

        "禱告":
        (
            "🙏 願神祝福你。",
            "prayer"
        ),

        "點名":
        (
            "📢 點名開始，請回：到",
            "rollcall"
        ),

        "到":
        (
            "✅ 已記錄出席",
            "arrived"
        ),

        "自我介紹":
        (
            """
我是靈糧堂數位執事。

功能：

1. AI問答
2. 點名
3. 出席紀錄
4. Google Sheet紀錄
5. 教會關懷服務
            """,
            "intro"
        )

    }

    if msg in commands:

        return commands[msg]

    return None, "gemini"


# ==========================================================
# 首頁
# ==========================================================

@app.get("/")
def home():

    return {

        "班級名稱":
        "板橋-iPAS AI應用與雙程式設計實務班",

        "學生姓名":
        "葉堠祿",

        "學生學號":
        "18",

        "專題名稱":
        "LINE Bot + Google Sheet + Gemini AI 智慧助理系統",

        "系統狀態":
        "正常運作"

    }


# ==========================================================
# LINE Webhook
# ==========================================================

@app.post("/reply")
async def reply(request: Request):

    try:

        body = await request.json()

        events = body.get(
            "events",
            []
        )

        if len(events) == 0:

            return {"ok": True}

        event = events[0]

        if event.get("type") != "message":

            return {"ok": True}

        if event["message"]["type"] != "text":

            return {"ok": True}

        msg = event["message"]["text"]

        user_id = event["source"].get(
            "userId",
            ""
        )

        user_name = get_user_name(
            user_id
        )

        reply_token = event[
            "replyToken"
        ]

        reply_text, intent = (
            handle_message(msg)
        )

        # AI回答

        if intent == "gemini":

            reply_text = ask_ai(msg)

        # LINE回覆

        reply_to_line(

            reply_token,

            reply_text

        )

        # Google Sheet紀錄

        log_to_sheet(

            user_name,

            msg,

            reply_text,

            intent

        )

        return {

            "ok": True

        }

    except Exception as e:

        print("Webhook錯誤")

        print(str(e))

        return {

            "ok": False,

            "error": str(e)

        }
