# =====================================
# ✅ 1️⃣ 基本套件（LINE Bot運作）
# =====================================
from fastapi import FastAPI, Request
import requests

# =====================================
# ✅ 2️⃣ Google Sheets（資料庫）
# =====================================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# =====================================
# ✅ 3️⃣ 系統工具
# =====================================
import os, json, random

# =====================================
# ✅ 4️⃣ 建立服務
# =====================================
app = FastAPI()

# =====================================
# ✅ 5️⃣ LINE TOKEN（請替換）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# =====================================
# ✅ 6️⃣ Google Sheets 連線
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_key = json.loads(os.environ["GOOGLE_KEY"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

sheet = client.open("linebot-log").sheet1

# =====================================
# ✅ 7️⃣ 寫入資料
# =====================================
def log_to_sheet(user_id, msg, reply, intent):
    sheet.append_row([
        str(datetime.now()),   # 時間
        user_id,               # 誰
        msg,                   # 訊息
        reply if reply else "None",
        intent
    ])

# =====================================
# ✅ 8️⃣ 回LINE
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
# ✅ 9️⃣ 精準判斷系統（防亂回🔥）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # ✅ 1️⃣ 完全匹配（最準）
    EXACT = {
        "點名": ("📢 點名開始，請回：到", "rollcall"),
        "到": ("✅ 已記錄出席", "arrived"),
        "你好": ("🌿 平安！", "greet"),
        "禱告": ("🙏 為你禱告", "prayer"),
        "謝謝": ("🙏 感謝主", "thanks")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 2️⃣ 強語意關鍵字（不易誤判）
    MAP = {
        "emotion": {
            "keywords": ["好累","很累","壓力大","真的很煩","好崩潰"],
            "reply": ["💛 辛苦了，你不是一個人","🌿 神與你同在"]
        },

        "danger": {
            "keywords": ["想死","活不下去","撐不住","不想活"],
            "reply": ["💛 你很重要，我們陪你","🙏 一起禱告"]
        },

        "prayer": {
            "keywords": ["幫我禱告","需要禱告"],
            "reply": ["🙏 願主幫助你","✨ 神與你同在"]
        },

        "encourage": {
            "keywords": ["鼓勵我","幫我加油"],
            "reply": ["🔥 你可以的","💪 不要放棄"]
        }
    }

    for intent, data in MAP.items():
        if any(k in msg for k in data["keywords"]):
            return random.choice(data["reply"]), intent

    # ✅ 3️⃣ fallback（關鍵：不亂回）
    return None, "none"


# =====================================
# ✅ 🔟 LINE Webhook
# =====================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"]
    user_id = event["source"].get("userId")
    token = event["replyToken"]

    # ✅ 判斷
    reply_text, intent = handle_message(msg)

    # ✅ ✅ 只有有意義才回（重點🔥）
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 一定記錄（分析用）
    log_to_sheet(user_id, msg, reply_text, intent)

    return {"ok": True}
