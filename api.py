# =====================================
# LINE AI 關懷助理
# Debug版
# =====================================

from fastapi import FastAPI, Request
import requests
import os
import json
import random

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime, timedelta

import google.generativeai as genai

app = FastAPI()

# =====================================
# LINE Token
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

model = genai.GenerativeModel(
    "gemini-1.5-flash"
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
# 聊天記憶
# =====================================

user_memory = {}

# =====================================
# Sheet紀錄
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
# LINE回覆
# =====================================

def reply_to_line(
    token,
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
            token,

            "messages": [

                {
                    "type": "text",
                    "text": str(text)[:5000]
                }

            ]

        }

    )

# =====================================
# 使用者名稱
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
    message
):

    try:

        if user_name not in user_memory:

            user_memory[user_name] = []

        history = user_memory[user_name][-6:]

        prompt = f"""
你是一位教會AI關懷助理

請使用繁體中文

聊天紀錄：

{chr(10).join(history)}

使用者：

{message}
"""

        response = model.generate_content(
            prompt
        )

        answer = response.text

        user_memory[user_name].append(
            f"使用者:{message}"
        )

        user_memory[user_name].append(
