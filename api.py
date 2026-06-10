# ===============================
# ✅ 基本套件
# ===============================
from fastapi import FastAPI, Request
import requests
import random

# ===============================
# ✅ Google Sheets 套件
# ===============================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===============================
# ✅ 初始化 APP
# ===============================
app = FastAPI()

# ===============================
# ✅ LINE 設定（請確認你有放token）
# ===============================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# ===============================
# ✅ Google Sheets 設定
# ===============================

# 👉 允許Google存取的範圍
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 👉 用 key.json 登入（剛剛你上傳的）
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)

# 👉 建立連線
client = gspread.authorize(creds)

# 👉 開啟你的表（名字要一樣）
sheet = client.open("linebot-log").sheet1


# ===============================
# ✅ 存資料到 Google Sheet
# ===============================
def log_to_sheet(user_id, msg, reply, intent):
    sheet.append_row([
        str(datetime.now()),      # 時間
        user_id,                  # 使用者ID
        msg,                      # 使用者說什麼
        reply if reply else "None", # 回覆內容
        intent                   # 判斷類型
    ])


# ===============================
# ✅ LINE 回覆
# ===============================
def reply_to_line(reply_token, text):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }

    requests.post(url, headers=headers, json=data)


# ===============================
# ✅ 智慧回應核心
# ===============================

seen_users = set()
attendance = set()

def handle_message(user_msg, user_id):

    msg = user_msg.strip().lower()

    # ✅ 新使用者（只出現一次）
    if user_id not in seen_users:
        seen_users.add(user_id)
        return "👋 歡迎！試試：點名 / 禱告 / 經文", "greet"

    # ✅ 點名
    if msg in ["到", "到了", "已到", "我到了"]:
        attendance.add(user_id)
        return f"✅ 已記錄，目前 {len(attendance)} 人到", "arrived"

    # ✅ 危急情緒
    if any(w in msg for w in ["想死","自殺","活不下去"]):
        return "💛 你不是一個人，我們一起禱告", "danger"

    # ✅ 關鍵字
    if "點名" in msg:
        attendance.clear()
        return "📢 點名開始，請回：到", "rollcall"

    if "累" in msg or "壓力" in msg:
        return "💛 辛苦了，神與你同在", "emotion"

    if "禱告" in msg:
        return "🙏 願主看顧你", "prayer"

    if "加油" in msg:
        return "🔥 你可以的！", "encourage"

    if "你好" in msg or "hi" in msg:
        return "🌿 平安！", "greet"

    if "謝謝" in msg:
        return "🙏 感謝主", "thank"

    if "經文" in msg:
        return "📖 詩篇23:1 耶和華是我的牧者", "bible"

    # ✅ fallback（偶爾提示）
    if random.random() < 0.03:
        return "😊 試試：點名 / 禱告 / 經文", "hint"

    return None, "none"


# ===============================
# ✅ LINE Webhook
# ===============================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()

    events = body.get("events", [])

    # ✅ LINE測試用（沒事件）
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

    # ✅ 呼叫智慧邏輯
    reply_text, intent = handle_message(user_msg, user_id)

    # ✅ 有回才回LINE
    if reply_text:
        reply_to_line(reply_token, reply_text)

    # ✅ 一定寫進Google Sheet
    log_to_sheet(user_id, user_msg, reply_text, intent)

    return {"status": "ok"}
