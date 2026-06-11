# =====================================
# ✅ 1️⃣ 匯入套件（讓程式可以使用功能）
# =====================================
from fastapi import FastAPI, Request   # 建立API服務（讓LINE連進來）
import requests                        # 用來呼叫LINE API

import gspread                         # 連接Google Sheet
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import os, json, random               # 系統工具


# =====================================
# ✅ 2️⃣ 建立Web服務
# =====================================
app = FastAPI()


# =====================================
# ✅ 3️⃣ LINE TOKEN（⚠️不能有空格）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="


# =====================================
# ✅ 4️⃣ 連線Google Sheets
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ✅ 從 Render 環境讀取金鑰
google_key = json.loads(os.environ["GOOGLE_KEY"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# ✅ 聊天紀錄 Sheet
sheet = client.open("linebot-log").sheet1

# ✅ 關懷資料 Sheet（需自己建立）
care_sheet = client.open("linebot-care").sheet1


# =====================================
# ✅ 5️⃣ 寫聊天紀錄
# =====================================
def log_to_sheet(user_name, msg, reply, intent):

    sheet.append_row([
        str(datetime.now()),   # 時間
        user_name,             # 使用者名稱
        msg,                   # 訊息內容
        reply if reply else "None",
        intent                 # 分類
    ])


# =====================================
# ✅ 6️⃣ 寫關懷資料（分開存）
# =====================================
def log_care(name, phone, user_id):

    care_sheet.append_row([
        str(datetime.now()),
        name,
        phone,
        user_id
    ])


# =====================================
# ✅ 7️⃣ 回 LINE 訊息
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
# ✅ 8️⃣ user_id → 使用者名稱
# =====================================
def get_user_name(user_id):

    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"

        headers = {
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        }

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res.json().get("displayName")
        else:
            return user_id   # 抓不到就用ID

    except:
        return user_id


# =====================================
# ✅ 9️⃣ 關懷流程（核心🔥）
# =====================================
user_sessions = {}  # 記錄每個人目前填到哪一步

def handle_care(user_id, msg):

    msg = msg.strip()

    # ✅ 還沒開始
    if user_id not in user_sessions:

        if msg in ["關懷申請", "關懷"]:
            user_sessions[user_id] = {"step": 1}
            return "📋 請輸入姓名（格式：姓名:王小明）", "care"

        return None, "none"

    session = user_sessions[user_id]

    # ✅ STEP 1：姓名
    if session["step"] == 1:

        if msg.startswith("姓名:"):
            session["name"] = msg.replace("姓名:", "")
            session["step"] = 2
            return "📞 請輸入電話（格式：電話:0912xxxxxx）", "care"

        return "⚠️ 請輸入：姓名:王小明", "care"

    # ✅ STEP 2：電話
    if session["step"] == 2:

        if msg.startswith("電話:"):
            session["phone"] = msg.replace("電話:", "")
            session["step"] = 3
            return "✅ 是否送出？（YES / NO）", "care"

        return "⚠️ 請輸入：電話:0912xxxxxx", "care"

    # ✅ STEP 3：確認
    if session["step"] == 3:

        if msg.upper() == "YES":

            # ✅ 寫入關懷資料
            log_care(
                session["name"],
                session["phone"],
                user_id
            )

            del user_sessions[user_id]

            return "🙏 已送出關懷申請，牧者會聯絡您", "care"

        if msg.upper() == "NO":
            del user_sessions[user_id]
            return "❌ 已取消申請", "care"

        return "⚠️ 請輸入 YES 或 NO", "care"

    return None, "none"


# =====================================
# ✅ 🔟 一般聊天
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    EXACT = {
        "你好": ("🌿 平安！", "greet"),
        "謝謝": ("🙏 感謝主", "thanks"),
        "test": ("✅ 系統正常運作", "system")
    }

    if msg in EXACT:
        return EXACT[msg]

    if "累" in msg or "壓力" in msg:
        return "💛 辛苦了，你不是一個人", "emotion"

    if "想死" in msg or "撐不住" in msg:
        return "💛 你很重要，我們陪你", "danger"

    return None, "none"


# =====================================
# ✅ 1️⃣1️⃣ LINE Webhook（入口）
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

    # ✅ 先跑關懷系統
    reply_text, intent = handle_care(user_id, msg)

    # ✅ 再跑一般聊天
    if not reply_text:
        reply_text, intent = handle_message(msg)

    # ✅ 回覆LINE
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ 記錄Google Sheet
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
