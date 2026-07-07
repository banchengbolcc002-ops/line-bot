# =====================================
# LINE AI 關懷助理
# FastAPI + LINE + Gemini + Google Sheet
# =====================================

# =====================================
# 載入套件
# =====================================

from fastapi import FastAPI, Request
import requests
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime
from datetime import timedelta

import google.generativeai as genai

import os
import json
import random

# =====================================
# 建立 FastAPI
# =====================================

app = FastAPI()

# =====================================
# LINE Access Token
# 從 Render 讀取
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

# =====================================
# Gemini API 設定
# =====================================

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# =====================================
# Google Sheet 設定
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

client = gspread.authorize(
    creds
)

sheet = client.open(
    "linebot-log"
).worksheet(
    "linebot-care"
)

# =====================================
# 使用者記憶
# =====================================

user_memory = {}

# =====================================
# 紀錄到 Google Sheet
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

            reply,

            intent

        ])

    except Exception as e:

        print(
            "Google Sheet錯誤:",
            str(e)
        )

# =====================================
# 回覆 LINE
# =====================================

def reply_to_line(
    token,
    text
):

    try:

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
                token,

                "messages": [

                    {
                        "type": "text",
                        "text": str(text)[:5000]
                    }

                ]

            }

        )

    except Exception as e:

        print(
            "LINE回覆失敗:",
            str(e)
        )

# =====================================
# 取得 LINE 使用者名稱
# =====================================

def get_user_name(
    user_id
):

    try:

        url = (
            f"https://api.line.me/v2/bot/profile/{user_id}"
        )

        headers = {

            "Authorization":
            f"Bearer {CHANNEL_ACCESS_TOKEN}"

        }

        res = requests.get(
            url,
            headers=headers
        )

        if res.status_code == 200:

            data = res.json()

            return data.get(
                "displayName",
                user_id
            )

        return user_id

    except:

        return user_id

# =====================================
# Gemini AI
# =====================================

def ask_gemini(
    user_name,
    question
):

    try:

        if user_name not in user_memory:

            user_memory[user_name] = []

        history = user_memory[user_name][-6:]

        prompt = f"""
你是一位教會 AI 關懷助理。

規則：

1. 使用繁體中文
2. 語氣溫暖
3. 回答簡潔
4. 具有鼓勵性
5. 適合教會關懷

聊天記錄：

{chr(10).join(history)}

使用者：

{question}
"""

        response = model.generate_content(
            prompt
        )

        answer = response.text

        user_memory[user_name].append(
            f"使用者:{question}"
        )

        user_memory[user_name].append(
            f"AI:{answer}"
        )

        return answer

    except Exception as e:

        error_msg = str(e)

        print(
            "Gemini錯誤:",
            error_msg
        )

        return (
            "AI服務暫時無法使用\n\n"
            + error_msg
        )

# =====================================
# 危機關懷判斷
# =====================================

def is_danger_message(msg):

    keywords = [

        "自殺",
        "想死",
        "不想活",
        "活不下去",
        "結束生命"

    ]

    return any(
        k in msg
        for k in keywords
    )

# =====================================
# 核心處理
# =====================================

def handle_message(
    msg,
    user_name
):

    msg = msg.strip()

    # 危機關懷

    if is_danger_message(msg):

        return (

            "💛 你很重要。\n\n"
            "請立即聯絡家人、朋友或牧者。\n\n"
            "1925 安心專線\n"
            "1995 生命線",

            "danger"

        )

    # 固定指令

    exact = {

        "點名": (
            "📢 點名開始，請回：到",
            "rollcall"
        ),

        "到": (
            "✅ 已記錄出席",
            "arrived"
        ),

        "你好": (
            "🌿 平安！",
            "greet"
        ),

        "謝謝": (
            "🙏 感謝主",
            "thanks"
        ),

        "禱告": (
            "🙏 願神賜福你",
            "prayer"
        ),

        "經文": (
            "📖 詩篇23:1\n耶和華是我的牧者，我必不致缺乏。",
            "bible"
        )

    }

    if msg in exact:

        return exact[msg]

    # Gemini AI

    ai_reply = ask_gemini(
        user_name,
        msg
    )

    return (
        ai_reply,
        "gemini"
    )

# =====================================
# LINE Webhook
# =====================================

@app.post("/reply")
async def reply(
    request: Request
):

    try:

        body = await request.json()

        events = body.get(
            "events",
            []
        )

        if not events:

            return {
                "ok": True
            }

        event = events[0]

        if event.get("type") != "message":

            return {
                "ok": True
            }

        if event["message"].get("type") != "text":

            return {
                "ok": True
            }

        msg = event["message"]["text"]

        user_id = event["source"].get(
            "userId",
            ""
        )

        token = event["replyToken"]

        user_name = get_user_name(
            user_id
        )

        reply_text, intent = handle_message(
            msg,
            user_name
        )

        reply_to_line(
            token,
            reply_text
        )

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

        print(
            "Webhook錯誤:",
            str(e)
        )

        return {
            "ok": False
        }
