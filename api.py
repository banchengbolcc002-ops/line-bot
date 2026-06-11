# =====================================
# ✅ 1️⃣ 匯入套件
# =====================================
from fastapi import FastAPI, Request
import requests

import gspread   # ✅ 修正：不能有亂文字
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import os, json, random

# =====================================
# ✅ 2️⃣ 建立服務
# =====================================
app = FastAPI()

# =====================================
# ✅ 3️⃣ TOKEN（⚠️不能有空格）
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

# ✅ 聊天表
sheet = client.open("linebot-log").sheet1

# ✅ 關懷表（一定要先建立）
care_sheet = client.open("linebot-care").sheet1

# =====================================
# ✅ 5️⃣ 聊天寫入
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
# ✅ 6️⃣ 關懷寫入
# =====================================
def log_care(name, phone, user_id):

    care_sheet.append_row([
        str(datetime.now()),
        name,
        phone,
        user_id
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
# ✅ 8️⃣ user_id → 姓名
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
# ✅ 9️⃣ 關懷流程（核心🔥）
# =====================================
user_sessions = {}

def handle_care(user_id, msg):

    if user_id not in user_sessions:

        if msg == "關懷申請"、 "關懷":
            user_sessions[user_id] = {"step": 1}
            return "📋 請輸入姓名（格式：姓名:王小明）", "care"

        return None, "none"

    session = user_sessions[user_id]

    # ✅ Step 1
    if session["step"] == 1:

        if msg.startswith("姓名:"):
            session["name"] = msg.replace("姓名:", "")
            session["step"] = 2
            return "📞 請輸入電話（電話:0912xxxxxx）", "care"

        return "⚠️ 格式錯誤：姓名:王小明", "care"

    # ✅ Step 2
    if session["step"] == 2:

        if msg.startswith("電話:"):
            session["phone"] = msg.replace("電話:", "")
            session["step"] = 3
            return "✅ 是否送出？YES / NO", "care"

        return "⚠️ 格式錯誤：電話:0912xxxxxx", "care"

    # ✅ Step 3
    if session["step"] == 3:

        if msg.upper() == "YES":

            log_care(
                session["name"],
                session["phone"],
                user_id
            )

            del user_sessions[user_id]

            return "🙏 已送出關懷申請", "care"

        if msg.upper() == "NO":
            del user_sessions[user_id]
            return "❌ 已取消", "care"

        return "⚠️ 請輸入 YES / NO", "care"

    return None, "none"

# =====================================
# ✅ 🔟 一般對話
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    EXACT = {
        "你好": ("🌿 平安！", "greet"),
        "謝謝": ("🙏 感謝主", "thanks"),
        "test": ("✅ 系統正常", "system")
    }

    if msg in EXACT:
        return EXACT[msg]

    if "累" in msg:
        return "💛 辛苦了", "emotion"

    if "想死" in msg:
        return "💛 我們陪你", "danger"

    return None, "none"

# =====================================
# ✅ 1️⃣1️⃣ LINE入口
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

    user_name = get_user_name(user_id)

    token = event["replyToken"]

    # ✅ 先關懷
    reply_text, intent = handle_care(user_id, msg)

    # ✅ 再AI
    if not reply_text:
        reply_text, intent = handle_message(msg)

    # ✅ 回覆
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 記錄
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
