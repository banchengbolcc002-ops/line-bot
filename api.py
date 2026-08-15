# =====================================
# 基督教會數位執事 AI
# 板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學號：18
# =====================================

from fastapi import FastAPI, Request
import requests
import os

# =====================================
# 建立 FastAPI 應用程式
# =====================================

app = FastAPI()

# =====================================
# Render 首頁
# =====================================

@app.get("/")
def home():

    return {

        "status": "LINE BOT RUNNING",

        "class_name": "板橋-iPAS AI應用與雙程式設計實務班",

        "student_name": "葉堠祿",

        "student_id": "18"

    }

# =====================================
# Render 健康檢查
# =====================================

@app.get("/health")
def health():

    return {

        "status": "OK"

    }

# =====================================
# LINE TOKEN
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="
)

# =====================================
# 快速回覆字典
# =====================================

quick_reply = {

    "你好": "🌿 平安！願主賜福您。",

    "哈囉": "😊 哈囉！很高興見到您。",

    "嗨": "👋 嗨！願神與您同在。",

    "hi": "👋 Hi！平安。",

    "hello": "👋 Hello！很高興為您服務。",

    "測試": "✅ 機器人運作正常。",

    "test": "✅ 機器人運作正常。",

    "ping": "🏓 Pong！系統在線中。",

    "早安": "☀️ 早安！願主祝福您今天。",

    "午安": "🌤️ 午安！願您平安喜樂。",

    "晚安": "🌙 晚安！願主保守您。",

    "謝謝": "❤️ 不客氣，很高興能幫助您。"

}

# =====================================
# LINE 回覆函式
# =====================================

def reply_to_line(reply_token, text):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {

        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}",

        "Content-Type":
        "application/json"

    }

    body = {

        "replyToken": reply_token,

        "messages": [

            {

                "type": "text",

                "text": text

            }

        ]

    }

    requests.post(
        url,
        headers=headers,
        json=body,
        timeout=10
    )

# =====================================
# LINE Webhook
# =====================================

@app.post("/callback")
async def callback(request: Request):

    body = await request.json()

    events = body.get(
        "events",
        []
    )

    for event in events:

        if event.get("type") == "message":

            if event["message"].get("type") == "text":

                user_msg = event["message"]["text"]

                reply_token = event["replyToken"]

                msg = user_msg.strip().lower()

                # =========================
                # 快速回覆
                # =========================

                if msg in quick_reply:

                    ai_reply = quick_reply[msg]

                else:

                    ai_reply = (

                        "🙏 您好，我是基督教會數位執事 AI。\n\n"

                        f"您剛剛說的是：\n"

                        f"{user_msg}\n\n"

                        "目前為教學版範例，未啟用 Gemini。"

                    )

                reply_to_line(
                    reply_token,
                    ai_reply
                )

    return {

        "status": "OK"

    }
