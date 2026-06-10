# =====================================
# ✅ 1️⃣ 基本套件（讓LINE Bot跑）
# =====================================
from fastapi import FastAPI, Request
import requests

# =====================================
# ✅ 2️⃣ Google Sheets（當資料庫）
# =====================================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# =====================================
# ✅ 3️⃣ 系統工具（讀KEY用）
# =====================================
import os, json, random

# =====================================
# ✅ 4️⃣ 建立Web服務
# =====================================
app = FastAPI()

# =====================================
# ✅ 5️⃣ LINE憑證（換成你的）
# =====================================
CHANNEL_ACCESS_TOKEN = "你的LINE_TOKEN"

# =====================================
# ✅ 6️⃣ 連線 Google Sheets
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 👉 從 Render 讀取 GOOGLE_KEY（JSON）
google_key = json.loads(os.environ["GOOGLE_KEY"])

# 👉 登入 Google
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)

# 👉 建立連線
client = gspread.authorize(creds)

# 👉 打開試算表（名字一定完全一樣）
sheet = client.open("linebot-log").sheet1


# =====================================
# ✅ 7️⃣ 存資料（核心🔥）
# =====================================
def log_to_sheet(user_id, msg, reply, intent):

    sheet.append_row([
        str(datetime.now()),  # 時間
        user_id,              # ✅ 誰傳的（分析用）
        msg,                  # ✅ 訊息
        reply if reply else "None", # 回覆
        intent                # ✅ 分類
    ])


# =====================================
# ✅ 8️⃣ 回LINE
# =====================================
def reply_to_line(token, text):j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU=

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
# ✅ 9️⃣ 關鍵字資料庫（重點🔥🔥🔥）
# =====================================

INTENT_MAP = {

    "greet": [
        "你好","嗨","hi","hello","早安","午安","晚安",
        "哈囉","yo","hey","安安","哈","你好嗎"
    ],

    "emotion": [
        "累","很累","超累","疲倦","壓力","煩","崩潰",
        "好累","不想做","受不了","很煩"
    ],

    "prayer": [
        "禱告","代禱","幫我禱告","求神","祝福我",
        "幫幫我","需要禱告"
    ],

    "encourage": [
        "加油","努力","撐住","不要放棄","可以嗎",
        "給我力量","撐不住"
    ],

    "rollcall": [
        "點名","集合","報到","出席","在嗎"
    ],

    "thanks": [
        "謝謝","感謝","3q","thanks","thx","感恩"
    ],

    "bible": [
        "經文","聖經","神的話","金句","主的話"
    ],

    "danger": [
        "想死","自殺","活不下去","撐不住","完蛋",
        "不想活","沒有希望"
    ]
}


# =====================================
# ✅ 🔟 回應資料（罐頭回應）
# =====================================
RESPONSE_MAP = {

    "greet": ["🌿 平安！","👋 歡迎你"],
    "emotion": ["💛 辛苦了，你不是一個人","🌿 神與你同在"],
    "prayer": ["🙏 我為你禱告","✨ 神會幫助你"],
    "encourage": ["🔥 你可以的","💪 不要放棄"],
    "rollcall": ["📢 點名開始，請回：到"],
    "thanks": ["🙏 感謝主","😊 不客氣"],
    "bible": ["📖 詩篇23:1 耶和華是我的牧者"],
    "danger": ["💛 你很重要，我們陪你","🙏 一起禱告"],
}


# =====================================
# ✅ 1️⃣1️⃣ 智慧判斷（核心🔥）
# =====================================
def handle_message(msg):

    msg = msg.lower()

    # 👉 掃描全部關鍵字
    for intent, keywords in INTENT_MAP.items():

        if any(k in msg for k in keywords):
            return random.choice(RESPONSE_MAP[intent]), intent

    # 👉 沒有命中
    return None, "none"


# =====================================
# ✅ 1️⃣2️⃣ Webhook（LINE入口🔥）
# =====================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"]

    # ✅ 這就是「誰」
    user_id = event["source"].get("userId")

    token = event["replyToken"]

    # ✅ 判斷回覆
    reply_text, intent = handle_message(msg)

    # ✅ ✅ 只有有意義才回（防洗版🔥）
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ ✅ 一定記錄（做分析）
    log_to_sheet(user_id, msg, reply_text, intent)

    return {"ok": True}
