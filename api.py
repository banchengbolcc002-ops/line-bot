# =====================================
# ✅ 1️⃣ 匯入套件（讓系統能運作）
# =====================================
from fastapi import FastAPI, Request   # 建立API服務（LINE會呼叫）
import requests                        # 發送HTTP請求（LINE API）

import gspread                         # Google Sheet操作
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

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
# ✅ 4️⃣ Google Sheets連線（🔥已修正）
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ✅ 從Render讀取金鑰
google_key = json.loads(os.environ["GOOGLE_KEY"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# ✅ ✅ ✅ 正確寫法（開整個試算表）
spreadsheet = client.open("linebot-log")

# ✅ 聊天紀錄分頁
sheet = spreadsheet.worksheet("linebot-log")

# ✅ ✅ 關懷追蹤分頁（🔥關鍵修正）
care_sheet = spreadsheet.worksheet("linebot-care")


# =====================================
# ✅ 5️⃣ 記錄聊天
# =====================================
def log_to_sheet(user_name, msg, reply, intent):

    sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),   # ⏰ 時間
        user_name,             # 👤 姓名
        msg,                   # 💬 訊息
        reply if reply else "None",
        intent                # 🧠 分類
    ])


# =====================================
# ✅ 6️⃣ 關懷追蹤（核心🔥）
# =====================================
def log_care(user_name, msg, level):

    care_sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),  # ⏰ 時間
        user_name,            # 👤 姓名
        msg,                  # 💬 訊息
        level,                # 🧠 等級
        "未處理"               # 📌 狀態
    ])


# =====================================
# ✅ 7️⃣ 回LINE訊息
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
        headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res.json().get("displayName")
        else:
            return user_id

    except:
        return user_id


# =====================================
# ✅ 9️⃣ AI判斷（超擴充版🔥）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # =====================================
    # ✅ 1️⃣ 精準指令
    # =====================================
    EXACT = {
        "你好": ("🌿 平安！很高興見到你", "greet"),
        "謝謝": ("🙏 感謝主，也謝謝你", "thanks"),
        "test": ("✅ 系統正常運作中", "system")
    }

    if msg in EXACT:
        return EXACT[msg]

    # =====================================
    # ✅ 2️⃣ 大量語意分類（可擴充1000+🔥）
    # =====================================
    MAP = {

        # 💛 情緒類（中風險）
        "emotion": {
            "keywords": [
                "累","好累","很累","超累","真的很累","累死","累翻",
                "壓力","壓力大","壓力很大","壓力爆表",
                "崩潰","快崩潰","要崩潰了","心累",
                "很煩","超煩","煩死","好煩",
                "難過","好難過","非常難過","心情不好",
                "低落","很低落","超低落","情緒不好",
                "沒力","沒動力","提不起勁","不想動",
                "疲憊","精神差","很空虛","孤單","寂寞"
            ],
            "reply": [
                "💛 辛苦了，你真的撐很久了",
                "🌿 願神給你平安與力量",
                "🙏 你不是一個人，我們在這裡",
                "💫 先休息一下，你已經很努力了",
                "✨ 願你在困難中找到力量",
                "🌈 黑夜再長也會過去",
                "🤍 願神的愛包圍你",
                "💛 每一步都不容易，你已經很棒了"
            ]
        },

        # 🚨 危機（高風險🔥）
        "danger": {
            "keywords": [
                "想死","我想死","好想死","不想活","我不想活",
                "自殺","想自殺","有點想自殺",
                "活不下去","撐不住","真的撐不住",
                "好痛苦","太痛苦","無法承受",
                "想結束","想消失","不想存在",
                "沒有意義","活著沒意義"
            ],
            "reply": [
                "💛 你很重要，請不要放棄自己",
                "🙏 我們在這裡陪著你",
                "🌿 神沒有離開你",


# =====================================
# ✅ 🔟 Webhook（主流程🔥）
# =====================================
@app.post("/reply")
async def reply(request: Request):

    # ✅ 取得LINE資料
    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"].strip()
    user_id = event["source"].get("userId")

    # ✅ 轉使用者名稱
    user_name = get_user_name(user_id)

    token = event["replyToken"]

    # ✅ 判斷語意
    reply_text, intent = handle_message(msg)

    # ✅ 回覆（只一次）
    if reply_text:
        reply_to_line(token, reply_text)

    # ✅ ✅ 關懷追蹤（🔥關鍵）
    if intent == "danger":
        log_care(user_name, msg, "🔴 高風險")

    elif intent == "emotion":
        log_care(user_name, msg, "🟡 中風險")

    # ✅ 記錄聊天
    log_to_sheet(user_name, msg, reply_text, intent)

    return {"ok": True}
