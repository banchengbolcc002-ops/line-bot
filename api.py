# ===============================
# ✅ 基本套件（讓Web服務可以跑）
# ===============================
from fastapi import FastAPI, Request
import requests
import random

# ===============================
# ✅ Google Sheets 套件（寫入Excel用）
# ===============================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===============================
# ✅ 這兩個是「讀環境變數」必備（你剛剛設定的 GOOGLE_KEY）
# ===============================
import os
import json

# ===============================
# ✅ 建立 Web App（LINE會打進來）
# ===============================
app = FastAPI()

# ===============================
# ✅ LINE Token（記得你的不能有空格）
# ===============================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# ===============================
# ✅ Google Sheets 設定（關鍵🔥）
# ===============================

# 👉 告訴Google你要用哪些權限
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 👉 ✅ 從 Render 讀環境變數 GOOGLE_KEY（你剛剛做的）
google_key = json.loads(os.environ["GOOGLE_KEY"])

# 👉 ✅ 用 key 產生登入憑證
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)

# 👉 ✅ 登入 Google Sheets
client = gspread.authorize(creds)

# 👉 ✅ 打開你的表（名稱一定要一樣）
sheet = client.open("linebot-log").sheet1

# ===============================
# ✅ 存資料到 Google Sheet（後台分析用）
# ===============================
def log_to_sheet(user_id, msg, reply, intent):

    # 👉 append_row = 新增一列
    sheet.append_row([
        str(datetime.now()),        # 現在時間
        user_id,                    # 使用者ID
        msg,                        # 使用者訊息
        reply if reply else "None", # 回覆內容（沒有就寫None）
        intent                      # 判斷結果（emotion / prayer 等）
    ])

# ===============================
# ✅ LINE 回覆（把訊息傳回去）
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
            {
                "type": "text",
                "text": text
            }
        ]
    }

    # 👉 送出回覆
    requests.post(url, headers=headers, json=data)

# ===============================
# ✅ 智慧回應邏輯（你Bot的腦）
# ===============================
seen_users = set()   # 記錄誰第一次來
attendance = set()   # 記錄點名

def handle_message(user_msg, user_id):

    msg = user_msg.strip().lower()

    # ✅ 新使用者
    if user_id not in seen_users:
        seen_users.add(user_id)
        return "👋 歡迎！試試：點名 / 禱告 / 經文", "greet"

    # ✅ 點名
    if msg in ["到", "到了", "已到", "我到了"]:
        attendance.add(user_id)
        return f"✅ 已記錄，目前 {len(attendance)} 人到", "arrived"

    # ✅ 強情緒
    if any(w in msg for w in ["想死","自殺","活不下去"]):
        return "💛 你不是一個人，我們一起禱告", "danger"

    # ✅ 功能判斷
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

    # ✅ 隨機提示（避免干擾）
    if random.random() < 0.03:
        return "😊 試試：點名 / 禱告 / 經文", "hint"

    # ✅ 都沒命中
    return None, "none"

# ===============================
# ✅ Webhook（LINE入口🔥）
# ===============================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()

    events = body.get("events", [])

    # ✅ LINE測試用
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

    # ✅ 呼叫AI邏輯
    reply_text, intent = handle_message(user_msg, user_id)

    # ✅ 有內容才回
    if reply_text:
        reply_to_line(reply_token, reply_text)

    # ✅ ✅ ✅ 「一定寫入Google Sheet」（關鍵🔥）
    log_to_sheet(user_id, user_msg, reply_text, intent)

    return {"status": "ok"}
