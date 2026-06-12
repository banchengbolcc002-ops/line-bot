# =====================================
# ✅ 1️⃣ 匯入套件
# =====================================
from fastapi import FastAPI, Request   # API服務（LINE會呼叫）
import requests                        # 發送LINE回覆

import gspread                         # Google Sheet操作
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

import os, json, random                # 系統工具


# =====================================
# ✅ 2️⃣ 建立服務
# =====================================
app = FastAPI()


# =====================================
# ✅ 3️⃣ LINE TOKEN（❗不能有空格）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="


# =====================================
# ✅ 4️⃣ Google Sheets連線
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_key = json.loads(os.environ["GOOGLE_KEY"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# ✅ 開整個試算表
spreadsheet = client.open("linebot-log")

# ✅ 分頁
sheet = spreadsheet.worksheet("linebot-log")
care_sheet = spreadsheet.worksheet("linebot-care")


# =====================================
# ✅ 5️⃣ 記錄聊天
# =====================================
def log_to_sheet(user_name, msg, reply, intent):
    sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),  # 台灣時間
        user_name,
        msg,
        reply if reply else "None",
        intent
    ])


# =====================================
# ✅ 6️⃣ 關懷追蹤
# =====================================
def log_care(user_name, msg, level):
    care_sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),
        user_name,
        msg,
        level,
        "未處理"
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
# ✅ 8️⃣ 抓使用者名稱
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
# ✅ 9️⃣ AI判斷（🔥已修正完整）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # ✅ 固定回應
    EXACT = {
        "你好": ("🌿 平安！很高興見到你", "greet"),
        "謝謝": ("🙏 感謝主，也謝謝你", "thanks"),
        "test": ("✅ 系統正常運作中", "system")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 關鍵字分類（🔥完整結構）
    MAP = {

        # 💛 情緒
        "emotion": {
            "keywords": [
                "累","好累","很累","壓力","崩潰","很煩","難過",
                "低落","沒力","疲憊","孤單","寂寞"
            ],
            "reply": [
                "💛 辛苦了，你真的撐很久了",
                "🌿 願神給你平安與力量",
                "🙏 你不是一個人，我們在這裡",
                "💫 先休息一下，你已經很努力了"
            ]
        },

        # 🚨 危機
        "danger": {
            "keywords": [
                "想死","自殺","不想活","撐不住","活不下去","痛苦"
            ],
            "reply": [
                "💛 你很重要，請不要放棄自己",
                "🙏 我們在這裡陪著你",
                "🌿 神沒有離開你"
            ]
        },

        # 🙏 禱告
        "prayer": {
            "keywords": ["幫我禱告","為我禱告","需要禱告"],
            "reply": [
                "🙏 願主親自帶領你",
                "✨ 神的恩典夠你用"
            ]
        },

        # 💪 鼓勵
        "encourage": {
            "keywords": ["加油","好難","放棄","不行了"],
            "reply": [
                "🔥 你比想像更堅強",
                "💪 再撐一下就好"
            ]
        }
    }

    # ✅ 關鍵字掃描
    for intent, data in MAP.items():
        if any(k in msg for k in data["keywords"]):
            return random.choice(data["reply"]), intent

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

    reply_text, intent = handle_message(msg)

    # ✅ 回覆
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 關懷追蹤
    if intent == "danger":
        log_care(user_name, msg, "🔴 高風險")

    elif intent == "emotion":
        log_care(user_name, msg, "🟡 中風險")

    # ✅ 記錄聊天
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
