# ===============================
# ✅ 1️⃣ 基本套件（網站 + API用）
# ===============================
from fastapi import FastAPI, Request
import requests
import random

# ===============================
# ✅ 2️⃣ Google Sheets 套件（寫Excel）
# ===============================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===============================
# ✅ 3️⃣ 讀 Render 環境變數（安全金鑰）
# ===============================
import os
import json

# ===============================
# ✅ 4️⃣ 建立 Web App（LINE會打進來）
# ===============================
app = FastAPI()

# ===============================
# ✅ 5️⃣ LINE 憑證（自己換）
# ⚠️ 不可以有空格！！
# ===============================
CHANNEL_ACCESS_TOKEN = "你的LINE_CHANNEL_ACCESS_TOKEN"

# ===============================
# ✅ 6️⃣ Google Sheets 設定
# ===============================

# 👉 允許操作 Google API 的權限
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 👉 從 Render 讀 GOOGLE_KEY（JSON格式）
google_key = json.loads(os.environ["GOOGLE_KEY"])

# 👉 產生登入憑證
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)

# 👉 連線 Google
client = gspread.authorize(creds)

# 👉 打開你的 sheet（名字要完全一樣）
sheet = client.open("linebot-log").sheet1


# ===============================
# ✅ 7️⃣ 存資料到 Google Sheet（核心🔥）
# ===============================
def log_to_sheet(user_id, msg, reply, intent):
    try:
        print("✅ 準備寫入:", user_id, msg)

        sheet.append_row([
            str(datetime.now()),           # 時間
            user_id,                       # 使用者ID
            msg,                           # 使用者輸入
            reply if reply else "None",    # 回應內容
            intent                         # 分類（emotion/prayer）
        ])

        print("✅ 寫入成功")

    except Exception as e:
        print("❌ 寫入失敗:", e)


# ===============================
# ✅ 8️⃣ LINE 回覆功能
# ===============================
def reply_to_line(reply_token, text):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
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

    # 👉 傳送回LINE
    requests.post(url, headers=headers, json=body)


# ===============================
# ✅ 9️⃣ 智慧邏輯（Bot大腦🔥）
# ===============================
seen_users = set()
attendance = set()

def handle_message(user_msg, user_id):

    msg = user_msg.strip().lower()

    # ✅ 新人歡迎（只一次）
    if user_id not in seen_users:
        seen_users.add(user_id)
        return "👋 歡迎！試試：點名 / 禱告 / 經文", "greet"

    # ✅ 點名
    if msg in ["到", "到了", "已到"]:
        attendance.add(user_id)
        return f"✅ 已記錄，目前 {len(attendance)} 人到", "arrived"

    # ✅ 危機關懷
    if any(w in msg for w in ["想死","自殺"]):
        return "💛 你不是一個人，我們一起禱告", "danger"

    # ✅ 功能
    if "點名" in msg:
        attendance.clear()
        return "📢 點名開始，請回：到", "rollcall"

    if "累" in msg:
        return "💛 辛苦了，神與你同在", "emotion"

    if "禱告" in msg:
        return "🙏 願主看顧你", "prayer"

    if "你好" in msg:
        return "🌿 平安！", "greet"

    # ✅ fallback
    if random.random() < 0.05:
        return "😊 試試：點名 / 禱告 / 經文", "hint"

    return None, "none"


# ===============================
# ✅ 🔟 Webhook（LINE入口🔥🔥🔥）
# ===============================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"status": "ok"}

    event = events[0]

    reply_token = event.get("replyToken")
    message = event.get("message", {})

    # ✅ 只處理文字
    if message.get("type") != "text":
        return {"status": "ok"}

    user_msg = message.get("text")
    user_id = event.get("source", {}).get("userId")

    # ✅ 呼叫邏輯
    reply_text, intent = handle_message(user_msg, user_id)

    # ✅ 回應
    if reply_text:
        reply_to_line(reply_token, reply_text)

    # ✅ ✅ ✅ 強制寫入（關鍵🔥）
    log_to_sheet(user_id, user_msg, reply_text, intent)

    return {"status": "ok"}
