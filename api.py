# =====================================
# LINE AI 關懷助理
# 板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學號：18
# FastAPI + LINE + Gemini + Google Sheet
# =====================================

from fastapi import FastAPI, Request
import requests
import gspread
import traceback

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
# LINE Token
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

# =====================================
# Gemini API
# =====================================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
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

client = gspread.authorize(creds)

# 試算表名稱
SPREADSHEET_NAME = "linebot-log"

# 工作表名稱
WORKSHEET_NAME = "linebot-care"

sheet = client.open(
    SPREADSHEET_NAME
).worksheet(
    WORKSHEET_NAME
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

        taiwan_time = (
            datetime.utcnow()
            + timedelta(hours=8)
        )

        sheet.append_row([
            str(taiwan_time),
            user_name,
            msg,
            reply,
            intent
        ])

        print("✅ Google Sheet寫入成功")

    except Exception as e:

        print("❌ Google Sheet錯誤")

        print(str(e))

        traceback.print_exc()

# =====================================
# LINE 回覆
# =====================================

def reply_to_line(
    token,
    text
):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type":
        "application/json"
    }

    body = {
        "replyToken": token,
        "messages": [
            {
                "type": "text",
                "text": str(text)[:5000]
            }
        ]
    }

    requests.post(
        url,
        headers=headers,
        json=body
    )

# =====================================
# 取得LINE名稱
# =====================================

def get_user_name(user_id):

    try:

        url = (
            f"https://api.line.me/v2/bot/profile/{user_id}"
        )

        headers = 
