# =====================================
# 1. 匯入套件
# =====================================

from fastapi import FastAPI, Request
import requests
import gspread
import os
import json
import random

from datetime import datetime, timedelta

from oauth2client.service_account import (
    ServiceAccountCredentials
)

from google import genai


# =====================================
# 2. 建立 FastAPI
# =====================================

app = FastAPI()


# =====================================
# 3. 讀取 Render 環境變數
# =====================================

# LINE Access Token
CHANNEL_ACCESS_TOKEN = os.environ[
    "LINE_CHANNEL_ACCESS_TOKEN"
]

# Gemini API
client_ai = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# =====================================
# 4. Google Sheet 連線
# =====================================

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


# =====================================
# 5. Gemini AI 問答
# =====================================

def ask_ai(question):

    try:

        response = client_ai.models.generate_content(

            model="gemini-2.5-flash",

            contents=f"""
你是教會 AI 數位執事。

請使用繁體中文回答。

回答風格：
1. 溫和
2. 友善
3. 清楚易懂
4. 不要太長

問題：

{question}
"""

        )

        return response.text[:1000]

    except Exception as e:

        print("Gemini錯誤")
        print(str(e))

        return "AI服務暫時無法使用"


# =====================================
# 6. 記錄到 Google Sheet
# =====================================

def log_to_sheet(

    user_name,
    msg,
    reply,
    intent

):

    try:

        sheet.append_row([

            str(
                datetime.now()
                + timedelta(hours=8)
            ),

            user_name,

            msg,

            reply if reply else "",

            intent

        ])

    except Exception as e:

        print("Google Sheet錯誤")
        print(e)


# =====================================
# 7. 回覆 LINE
# =====================================

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


# =====================================
# 8. 取得 LINE 名稱
# =====================================

def get_user_name(user_id):

    try:

        res = requests.get(

            f"https://api.line.me/v2/bot/profile/{user_id}",

            headers={

                "Authorization":
                f"Bearer {CHANNEL_ACCESS_TOKEN}"

            }

        )

        if res.status_code == 200:

            return res.json().get(
                "displayName",
                user_id
            )

        return user_id

    except:

        return user_id


# =====================================
# 9. 固定關鍵字
# =====================================

def handle_message(msg):

    msg = msg.strip()

    exact = {

        "你好":
        (
            "🌿 平安！",
            "greet"
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

        "謝謝":
        (
            "🙏 感謝主",
            "thanks"
        ),

        "禱告":
        (
            "🙏 為你禱告",
            "prayer"
        )

    }

    if msg in exact:

        return exact[msg]

    # 其它交給 Gemini

    return None, "gemini"


# =====================================
# 10. Render 測試頁
# =====================================

@app.get("/")
def home():

    return {

        "status": "ok",

        "message": "LINE BOT RUNNING"

    }


# =====================================
# 11. LINE Webhook
# =====================================

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

        # Gemini 回答

        if intent == "gemini":

            reply_text = ask_ai(msg)

        # 回覆 LINE

        reply_to_line(

            reply_token,

            reply_text

        )

        # 寫入 Google Sheet

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
