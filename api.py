# =====================================
# ✅ 1️⃣ 匯入套件（讓系統能運作）
# =====================================
from fastapi import FastAPI, Request   # 建立API服務
import requests                        # 發送HTTP請求（LINE用）

# =====================================
# ✅ 2️⃣ Google Sheet 當資料庫
# =====================================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from datetime import timedelta

# =====================================
# ✅ 3️⃣ 系統工具
# =====================================
import os, json, random

# =====================================
# ✅ 4️⃣ 建立Web服務（LINE會打這裡）
# =====================================
app = FastAPI()

# =====================================
# ✅ 5️⃣ LINE TOKEN（⚠️不能有空格）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# =====================================
# ✅ 6️⃣ 連線 Google Sheets
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 👉 從 Render 環境讀 JSON 金鑰
google_key = json.loads(os.environ["GOOGLE_KEY"])

# 👉 登入
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# 👉 開啟試算表
sheet = client.open("linebot-log").sheet1


# =====================================
# ✅ 7️⃣ 寫資料（分析核心🔥）
# =====================================
def log_to_sheet(user_name, msg, reply, intent):

    sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),   # ⏰ 時間
        user_name,             # 👤 姓名（不是ID）
        msg,                   # 💬 訊息
        reply if reply else "None",
        intent                # 🧠 分類
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
# ✅ 9️⃣ 把 user_id 轉名字（關鍵🔥）
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
            return data.get("displayName")  # ✅ LINE顯示名稱
        else:
            return user_id  # ❗抓不到就回ID（避免當掉）

    except:
        return user_id


# =====================================
# ✅ 🔟 關鍵字判斷（智慧回應🔥）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # ✅ 精準指令
    EXACT = {
        "點名": ("📢 點名開始，請回：到", "rollcall"),
        "到": ("✅ 已記錄出席", "arrived"),
        "你好": ("🌿 平安！", "greet"),
        "謝謝": ("🙏 感謝主", "thanks"),
        "禱告": ("🙏 為你禱告", "prayer")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 擴增語意（大量關鍵字）
    MAP = {

        "emotion": {
            "keywords": [
                "累","好累","很累","超累","壓力",
                "壓力大","崩潰","很煩","不想做"
            ],
            "reply": [
                "💛 辛苦了，你不是一個人",
                "🌿 神與你同在",
                "🙏 願主給你平安"
            ]
        },

        "danger": {
            "keywords": [
                "想死","自殺","活不下去","不想活","撐不住"
            ],
            "reply": [
                "💛 你很重要，我們陪你",
                "🙏 一起禱告",
                "🌿 神沒有離開你"
            ]
        },

        "prayer": {
            "keywords": [
                "幫我禱告","為我禱告","需要禱告"
            ],
            "reply": [
                "🙏 願主幫助你",
                "✨ 神會帶領你"
            ]
        },

        "encourage": {
            "keywords": [
                "加油","鼓勵我","撐不住了"
            ],
            "reply": [
                "🔥 你可以的",
                "💪 不要放棄",
                "🌈 再撐一下就好"
            ]
        }
    }

    # ✅ 掃描關鍵字
    for intent, data in MAP.items():
        if any(k in msg for k in data["keywords"]):
            return random.choice(data["reply"]), intent

    # ✅ fallback
    return None, "none"


# =====================================
# ✅ 1️⃣1️⃣ LINE入口（最重要🔥）
# =====================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"]           # 使用者訊息
    user_id = event["source"].get("userId")  # 使用者ID

    # ✅ 轉姓名
    user_name = get_user_name(user_id)

    token = event["replyToken"]

    # ✅ 判斷語意
    reply_text, intent = handle_message(msg)

    # ✅ 不洗版
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 一定記錄（分析用）
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
