# =====================================
# LINE AI 關懷助理
# FastAPI + LINE + Gemini + Google Sheet
# =====================================

from fastapi import FastAPI, Request
import requests
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime, timedelta

import google.generativeai as genai

import os
import json

# =====================================
# 建立 FastAPI
# =====================================

app = FastAPI()

# =====================================
# LINE Access Token
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

# =====================================
# Gemini 設定
# =====================================

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

# 修正模型名稱

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# =====================================
# Google Sheet
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
# 記憶功能
# =====================================

user_memory = {}

# =====================================
# Google Sheet紀錄
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
            "Google Sheet 錯誤:",
            str(e)
        )

# =====================================
# 回覆LINE
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
            "LINE回覆錯誤:",
            str(e)
        )

# =====================================
# 取得使用者名稱
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
# Gemini聊天
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
你是一位教會AI關懷助理。

規則：

1. 使用繁體中文
2. 口氣溫暖
3. 提供鼓勵
4. 回答簡潔

聊天紀錄：

{chr(10).join(history)}

使用者問題：

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

        return (
            "AI服務暫時無法使用\n\n"
            + str(e)
        )

# =====================================
# 高風險關懷
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
# 訊息處理
# =====================================

def handle_message(
    msg,
    user_name
):

    msg = msg.strip()

    if is_danger_message(msg):

        return (

            "💛 你很重要。\n\n"
            "請立即聯絡家人、朋友或牧者。\n\n"
            "1925安心專線\n"
            "1995生命線",

            "danger"

        )

    commands = {

        "你好": (
            "🌿 平安！",
            "hello"
        ),

        "經文": (
            "📖 詩篇23:1\n耶和華是我的牧者，我必不致缺乏。",
            "bible"
        ),

        "禱告": (
            "🙏 願神賜福你。",
            "prayer"
        )

    }

    if msg in commands:

        return commands[msg]

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

# 群組模式

if event["source"]["type"] == "group":

    # 沒有提到機器人就不回覆
    if "@靈糧堂-數位執事" not in msg:
        return {"ok": True}

    # 移除標記文字
    msg = msg.replace(
        "@靈糧堂-數位執事",
        ""
    ).strip()
