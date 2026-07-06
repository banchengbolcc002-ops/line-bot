# =====================================
# LINE Bot + Google Sheet
# 穩定教學版
# 作者：資管系教授版
# =====================================

from fastapi import FastAPI, Request

import requests
import gspread
import json
import os

from random import choice
from datetime import datetime, timedelta

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# =====================================
# 建立 FastAPI
# =====================================

app = FastAPI()

# =====================================
# LINE Token
# =====================================
# 請貼上 LINE Developers 最新 Token
# 不可有空白

CHANNEL_ACCESS_TOKEN = "請貼上你的LINE Token"

# =====================================
# Google Sheet 權限設定
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
# 寫入試算表
# =====================================

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

        print("Google Sheet 寫入成功")

    except Exception as e:

        print("Google Sheet 錯誤")

        print(e)

# =====================================
# LINE回覆
# =====================================

def reply_to_line(
    reply_token,
    message
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

                        "text": message

                    }

                ]

            }

        )

        print(
            "LINE STATUS :",
            response.status_code
        )

        print(
            "LINE RESPONSE :",
            response.text
        )

    except Exception as e:

        print("LINE回覆失敗")

        print(e)

# =====================================
# 取得LINE名稱
# =====================================

def get_user_name(user_id):

    try:

        url = (
            f"https://api.line.me/v2/bot/profile/"
            f"{user_id}"
        )

        headers = {

            "Authorization":
            f"Bearer {CHANNEL_ACCESS_TOKEN}"

        }

        response = requests.get(
            url,
            headers=headers
        )

        if response.status_code == 200:

            return response.json().get(
                "displayName",
                user_id
            )

        return user_id

    except:

        return user_id

# =====================================
# 關鍵字判斷
# =====================================

def handle_message(msg):

    msg = msg.strip().lower()

    exact = {

        "你好":
        (
            "🌿 平安，很高興見到你",
            "greet"
        ),

        "謝謝":
        (
            "🙏 願神祝福你",
            "thanks"
        ),

        "報到":
        (
            "✅ 已記錄報到",
            "checkin"
        ),

        "點名":
        (
            "📢 點名開始，請回覆 報到",
            "rollcall"
        ),

        "禱告":
        (
            "🙏 我願意為你禱告",
            "prayer"
        )

    }

    if msg in exact:

        return exact[msg]

    if "累" in msg:

        return (
            "💛 辛苦了，願主加添力量",
            "emotion"
        )

    if "壓力" in msg:

        return (
            "🌿 願神賜你平安與智慧",
