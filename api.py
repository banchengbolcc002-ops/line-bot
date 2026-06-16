# =====================================
# ✅ 1️⃣ 匯入套件
# =====================================
from fastapi import FastAPI, Request   # 建立API服務（LINE會打這裡）
import requests                        # 傳送LINE訊息

import gspread                         # 操作Google Sheet
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

import os, json, random                # 系統工具（隨機、讀設定）

# =====================================
# ✅ 2️⃣ 建立服務
# =====================================
app = FastAPI()

# =====================================
# ✅ 3️⃣ LINE TOKEN（⚠️不能有空格）
# =====================================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# =====================================
# ✅ 4️⃣ Google Sheets連線
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ✅ 從Render取得金鑰
google_key = json.loads(os.environ["GOOGLE_KEY"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

# ✅ 開整個試算表
spreadsheet = client.open("linebot-log")

# ✅ 分頁（兩張表）
sheet = spreadsheet.worksheet("linebot-log")
care_sheet = spreadsheet.worksheet("linebot-care")

# =====================================
# ✅ 5️⃣ 記錄聊天
# =====================================
def log_to_sheet(user_name, msg, reply, intent):
    sheet.append_row([
        str(datetime.now() + timedelta(hours=8)),  # ✅ 台灣時間
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
# ✅ 8️⃣ 抓使用者名字
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
# ✅ 9️⃣ AI判斷（🔥PPT整合版）
# =====================================
def handle_message(msg):

    msg = msg.strip().lower()

    # ✅ 專題介紹（展示用🔥）
    if "專題" in msg or "介紹" in msg:
        return (
            "📊【教會數位服事機器人】\n"
            "✅ 結合LINE與關懷系統\n"
            "✅ 關鍵字觸發減少人力負擔\n"
            "✅ 自動回應與關懷提醒\n"
            "✅ 提升教會服事效率",
            "project"
        )

    # ✅ 功能介紹
    if "功能" in msg:
        return (
            "🧩【系統功能】\n"
            "✅ 點名（輸入：點名）\n"
            "✅ 禱告（輸入：禱告）\n"
            "✅ 情緒關懷\n"
            "✅ 危機關懷\n"
            "✅ Google Sheet記錄",
            "feature"
        )

    # ✅ 設計理念
    if "理念" in msg:
        return (
            "💡【設計理念】\n"
            "✔ 關鍵字觸發\n"
            "✔ 不干擾聊天\n"
            "✔ 降低人力負擔\n"
            "✔ 可擴充設計",
            "concept"
        )

    # ✅ 聖經
    if "經文" in msg:
        return (
            "✝️ 傳道書10:10\n"
            "鐵器鈍了要磨利\n\n"
            "💡 科技提升效率\n"
            "💛 信仰決定方向",
            "bible"
        )

    # ✅ 基本指令
    EXACT = {
        "你好": ("🌿 平安！很高興見到你", "greet"),
        "謝謝": ("🙏 感謝主", "thanks"),
        "test": ("✅ 系統正常運作中", "system"),
        "點名": ("📢 點名開始，請回：到", "rollcall"),
        "到": ("✅ 已記錄出席", "arrived"),
        "禱告": ("🙏 願主親自與你同在", "prayer")
    }

    if msg in EXACT:
        return EXACT[msg]

    # ✅ 情緒
    if any(k in msg for k in ["累","壓力","煩","難過"]):
        return random.choice([
            "💛 辛苦了，你真的撐很久了",
            "🌿 願神給你平安與力量",
            "🙏 我們陪你"
        ]), "emotion"

    # ✅ 危機（🔥正確縮排）
    if any(k in msg for k in ["想死","自殺","不想活","撐不住"]):
        return random.choice([
            "💛 你很重要，請不要放棄自己",
            "🙏 我們在這裡陪著你",
            "🌿 神沒有離開你"
        ]), "danger"

    # ✅ fallback
    return None, "none"

# =====================================
# ✅ 🔟 Webhook入口（LINE打這裡🔥）
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

    # ✅ 取得姓名
    user_name = get_user_name(user_id)

    token = event["replyToken"]

    # ✅ 判斷語意
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
