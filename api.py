# ==========================================================
# 班級名稱：板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學生學號：18
#
# 專題名稱：
# LINE Bot + Google Sheet + Gemini AI 智慧助理系統
# ==========================================================

# ==========================================================
# 1. 載入套件
# ==========================================================

from fastapi import FastAPI, Request

import requests
import gspread
import os
import json

from datetime import datetime, timedelta

from oauth2client.service_account import (
    ServiceAccountCredentials
)

from google import genai


# ==========================================================
# 2. 建立 FastAPI
# ==========================================================

app = FastAPI()


# ==========================================================
# 3. 讀取 Render 環境變數
# ==========================================================

CHANNEL_ACCESS_TOKEN = os.environ[
    "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="
]

GEMINI_API_KEY = os.environ[
    "AQ.Ab8RN6I5qe1ZTl0UhhxFakpsE3x-Xf5vgPCUn3fEQUmLVYR3_A"
]

client_ai = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==========================================================
# 4. Google Sheet 設定
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
# 5. Gemini AI
# ==========================================================

def ask_ai(question):

    try:

        response = client_ai.models.generate_content(

            model="gemini-2.5-flash",

            contents=f"""
你是靈糧堂數位執事。

請使用繁體中文回答。

回答原則：

1. 溫和友善
2. 清楚易懂
3. 適合教會使用
4. 不要太長

問題：

{question}
"""

        )

        return response.text[:1000]

    except Exception as e:

        print(str(e))

        return "AI服務暫時無法使用。"


# ==========================================================
# 6. 寫入 Google Sheet
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

        print(e)


# ==========================================================
# 7. 回覆 LINE
# ==========================================================

def reply_to_line(

    reply_token,
    text

):

    requests.post(

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


# ==========================================================
# 8. 取得 LINE 名稱
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
# 9. 關鍵字處理
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
        )

    }

    if msg in commands:

        return commands[msg]

    # 其它問題交給 Gemini

    return None, "gemini"


# ==========================================================
# 10. Render 首頁
# ==========================================================

@app.get("/")
def home():

    return {

        "班級名稱": "板橋-iPAS AI應用與雙程式設計實務班",

        "學生姓名": "葉堠祿",

        "學生學號": "18",

        "專題名稱":
        "LINE Bot + Google Sheet + Gemini AI",

        "系統狀態":
        "正常運作"

    }


# ==========================================================
# 11. LINE Webhook
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

        if event["message"]["type"] != "text":

            return {"ok": True}

        msg = event["message"]["text"]

        user_id = event["source"].get(
            "userId",
            ""
        )

        reply_token = event[
            "replyToken"
        ]

        user_name = get_user_name(
            user_id
        )

        reply_text, intent = (
            handle_message(msg)
        )

        # Gemini 問答

        if intent == "gemini":

            reply_text = ask_ai(msg)

        # LINE 回覆

        reply_to_line(

            reply_token,

            reply_text

        )

        # Google Sheet 紀錄

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

        print(str(e))

        return {

            "ok": False,

            "error": str(e)

        }
