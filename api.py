# =====================================
# LINE AI 關懷助理
# 作者：葉堠祿版
# FastAPI + LINE + Gemini + Google Sheet
# =====================================

# ---------------------------
# 載入套件
# ---------------------------

from fastapi import FastAPI, Request

import requests

import os
import json
import random

import gspread

from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime, timedelta

import google.generativeai as genai


# ---------------------------
# 建立 FastAPI
# ---------------------------

app = FastAPI()


# ---------------------------
# LINE TOKEN
# 從 Render 讀取
# ---------------------------

CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)


# ---------------------------
# Gemini 設定
# ---------------------------

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)


# ---------------------------
# Google Sheet 設定
# ---------------------------

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


# ---------------------------
# 使用者聊天記憶
# ---------------------------

user_memory = {}


# ---------------------------
# 寫入 Google Sheet
# ---------------------------

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
            e
        )


# ---------------------------
# 回覆 LINE
# ---------------------------

def reply_to_line(
    reply_token,
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
                reply_token,

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
            e
        )


# ---------------------------
# 抓 LINE 使用者名稱
# ---------------------------

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

        else:

            return user_id

    except:

        return user_id


# ---------------------------
# 危機關懷判斷
# ---------------------------

def is_danger_message(msg):

    keywords = [

        "自殺",
        "想死",
        "不想活",
        "活不下去",
        "結束生命",
        "沒人要我",
        "不如死一死"

    ]

    return any(
        k in msg
        for k in keywords
    )


# ---------------------------
# Gemini AI
# ---------------------------

def ask_gemini(
    user_name,
    question
):

    try:

        if user_name not in user_memory:

            user_memory[user_name] = []

        history = user_memory[user_name][-6:]

        conversation = "\n".join(
            history
        )

        prompt = f"""

你是一位基督徒 AI 關懷助理。

規則：

1. 使用繁體中文
2. 態度溫暖友善
3. 回答簡潔
4. 若對方低落請鼓勵
5. 若對方需要禱告請提供禱告內容
6. 不要使用簡體字

聊天紀錄：

{conversation}

使用者問題：

{question}

"""

        response = model.generate_content(
            prompt
        )

        answer = response.text

        user_memory[user_name].append(
            f"使用者：{question}"
        )

        user_memory[user_name].append(
            f"AI：{answer}"
        )

        return answer

    except Exception as e:

        print(
            "Gemini錯誤:",
            e
        )

        return "AI服務暫時無法使用"


# ---------------------------
# 核心訊息處理
# ---------------------------

def handle_message(
    msg,
    user_name
):

    msg = msg.strip()

    # ==================
    # 危機關懷
    # ==================

    if is_danger_message(msg):

        return (

            "💛 你是寶貴的。\n\n"
            "請立即與家人、朋友、牧者聯絡。\n\n"
            "📞 安心專線 1925\n"
            "📞 生命線 1995\n\n"
            "不要一個人承擔。"

        ), "danger"

    # ==================
    # 固定指令
    # ==================

    exact = {

        "點名": (
            "📢 點名開始，請回覆：到",
            "rollcall"
        ),

        "到": (
            "✅ 已記錄出席",
            "attendance"
        ),

        "禱告": (
            "🙏 願神賜福你，帶領你今天的一切。",
            "prayer"
        ),

        "經文": (
            "📖 詩篇23:1\n耶和華是我的牧者，我必不致缺乏。",
            "bible"
        )

    }

    if msg in exact:

        return exact[msg]

    # ==================
    # Gemini AI
    # ==================

    ai_reply = ask_gemini(
        user_name,
        msg
    )

    return ai_reply, "gemini"


# ---------------------------
# LINE Webhook
# ---------------------------

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

        # 非訊息事件

        if event.get("type") != "message":

            return {
                "ok": True
            }

        # 非文字訊息

        if event["message"].get("type") != "text":

            return {
                "ok": True
            }

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

        reply_text, intent = handle_message(
            msg,
            user_name
        )

        reply_to_line(
            reply_token,
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
            e
        )

        return {

            "ok": False

        }
