# ==========================================
# 第1部分：載入套件
# ==========================================

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


# ==========================================
# 第2部分：建立 FastAPI
# ==========================================

app = FastAPI()


# ==========================================
# 第3部分：讀取 Render 環境變數
# ==========================================

# LINE Bot Token

CHANNEL_ACCESS_TOKEN = os.environ[
    "LINE_CHANNEL_ACCESS_TOKEN"
]

# Gemini API

client_ai = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# ==========================================
# 第4部分：Google Sheet 設定
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
# 第5部分：Gemini AI
# ==========================================

def ask_ai(question):

    try:

        response = client_ai.models.generate_content(

            model="gemini-2.5-flash",

            contents=f"""
你是教會的 AI 數位執事。

請使用繁體中文回答。

請保持：
1. 友善
2. 禮貌
3. 簡明易懂
4. 適合教會使用

問題：

{question}
"""

        )

        return response.text[:1000]

    except Exception as e:

        print("Gemini錯誤")

        print(str(e))

        return "AI服務暫時無法使用。"


# ==========================================
# 第6部分：寫入 Google Sheet
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
                datetime.now() +
                timedelta(hours=8)
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
# 第7部分：LINE回覆
# ==========================================

def reply_to_line(

    reply_token,

    text

):

    try:

        response = requests.post(

            "https://api.line.me/v2/bot/message/reply",

            headers={

