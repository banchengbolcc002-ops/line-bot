# =====================================
# ✅ 1️⃣ 匯入套件
# =====================================
from fastapi import FastAPI, Request
import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import os, json, random


# =====================================
# ✅ 2️⃣ 建立服務
# =====================================
app = FastAPI()


# =====================================
# ✅ 3️⃣ LINE TOKEN（⚠️不能有空格）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="


# =====================================
# ✅ 4️⃣ Google Sheets
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_key = json.loads(os.environ["GOOGLE_KEY"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# ✅ 原本聊天紀錄
sheet = client.open("linebot-log").sheet1

# ✅ ✅ 新增：關懷追蹤表（要自己建立）
care_sheet = client.open("linebot-care").sheet1


# =====================================
# ✅ 5️⃣ 聊天紀錄
# =====================================
def log_to_sheet(user_name, msg, reply, intent):

    sheet.append_row([
        str(datetime.now()),
        user_name,
        msg,
        reply if reply else "None",
        intent
    ])


# =====================================
# ✅ 6️⃣ ✅ 關懷追蹤（新功能🔥）
# =====================================
def log_care(user_name, msg, level):

    care_sheet.append_row([
        str(datetime.now()),  # 時間
        user_name,            # 誰
        msg,                  # 說了什麼
        level,                # 風險等級
        "未處理"               # 狀態（預設）
    ])


# =====================================
# ✅ 7️⃣ 回LINE
# =====================================
def reply_to_line(token, text):

    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "replyToken": token,
            "messages": [{"type": "text", "text": text}]
        }
    )


# =====================================
# ✅ 8️⃣ user_id → 名字
# =====================================
def get_user_name(user_id):

    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"
        headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res.json().get("displayName")
        else:
            return user_id

    except:
        return user_id


# =====================================
# ✅ 9️⃣ AI判斷
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    EXACT = {
        "你好": ("🌿 平安！很高興見到你", "greet"),
        "謝謝": ("🙏 感謝主", "thanks"),
        "test": ("✅ 系統正常運作中", "system")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 情緒
    if any(k in msg for k in [
        "好累","很累","壓力","崩潰","很煩","難過"
    ]):
        return random.choice([
            "💛 辛苦了，你真的撐很久了",
            "🌿 願神給你平安",
            "🙏 我們陪你"
        ]), "emotion"

    # ✅ 危機
    if any(k in msg for k in [
        "想死","自殺","不想活","撐不住"
    ]):
        return random.choice([
            "💛 你很重要",
            "🙏 我們陪你",
            "🌿 神沒有離開你"
        ]), "danger"

    return None, "none"


# =====================================
# ✅ 🔟 Webhook
# =====================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"].strip()
    user_id = event["source"].get("userId")

    user_name = get_user_name(user_id)

    token = event["replyToken"]

    # ✅ 判斷
    reply_text, intent = handle_message(msg)

    # ✅ 回覆
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ ✅ ✅ 關懷追蹤啟動（核心🔥）
    if intent == "danger":
        log_care(user_name, msg, "🔴 高風險")

    elif intent == "emotion":
        log_care(user_name, msg, "🟡 中風險")

    # ✅ 原本記錄（保留）
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
