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
# ✅ 4️⃣ 建立服務（LINE會打進來）
# =====================================
app = FastAPI()

# =====================================
# ✅ 5️⃣ LINE TOKEN（換成你自己的，不可以有空格）
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
# ✅ 7️⃣ 存資料（核心🔥）
# =====================================
def log_to_sheet(user_name, msg, reply, intent):

    sheet.append_row([
        str(datetime.now()),   # ⏰ 時間
        user_name,             # 👤 誰說的（名字）
        msg,                   # 💬 說什麼
        reply if reply else "None",
        intent                 # 🧠 判斷類型
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
# ✅ 9️⃣ 抓使用者名稱（最重要🔥）
# =====================================
def get_user_name(user_id):

    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"

        headers = {
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        }

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            data = res.json()
            return data.get("displayName")  # ✅ 顯示名稱
        else:
            return user_id  # ❗抓不到就用ID（避免當掉）

    except Exception as e:
        print("❌ 抓名字錯誤:", e)
        return user_id  # ✅ 保底


# =====================================
# ✅ 🔟 關鍵字判斷系統（不亂回🔥）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # ✅ 完全匹配（最準）
    EXACT = {
        "點名": ("📢 點名開始，請回：到", "rollcall"),
        "到": ("✅ 已記錄出席", "arrived"),
        "你好": ("🌿 平安！", "greet"),
        "禱告": ("🙏 為你禱告", "prayer"),
        "謝謝": ("🙏 感謝主", "thanks")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 擴增關鍵字（大量語意🔥）
    MAP = {
        "emotion": {
            "keywords": [
                "好累","很累","超累","壓力","壓力大",
                "崩潰","很煩","受不了","不想做"
            ],
            "reply": [
                "💛 辛苦了，你不是一個人",
                "🌿 神與你同在",
                "🙏 願主給你平安"
            ]
        },

        "danger": {
            "keywords": [
                "想死","自殺","活不下去","撐不住","不想活"
            ],
            "reply": [
                "💛 你很重要，我們陪你",
                "🙏 我們一起禱告",
                "🌿 神沒有離開你"
            ]
        },

        "prayer": {
            "keywords": [
                "幫我禱告","需要禱告","為我禱告"
            ],
            "reply": [
                "🙏 願主幫助你",
                "✨ 神會帶領你"
            ]
        },

        "encourage": {
            "keywords": [
                "幫我加油","鼓勵我","我不行了"
            ],
            "reply": [
                "🔥 你可以的",
                "💪 不要放棄"
            ]
        }
    }

    for intent, data in MAP.items():
        if any(k in msg for k in data["keywords"]):
            return random.choice(data["reply"]), intent

    # ✅ fallback（不亂回）
    return None, "none"


# =====================================
# ✅ 1️⃣1️⃣ LINE Webhook（入口🔥）
# =====================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    # ✅ 使用者說的話
    msg = event["message"]["text"]

    # ✅ 使用者ID
    user_id = event["source"].get("userId")

    # ✅ 👉 轉名字（關鍵🔥）
    user_name = get_user_name(user_id)

    # ✅ LINE回覆token
    token = event["replyToken"]

    # ✅ 判斷
    reply_text, intent = handle_message(msg)

    # ✅ ✅ 有需要才回（不洗版🔥）
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 一定存資料（分析用🔥）
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
