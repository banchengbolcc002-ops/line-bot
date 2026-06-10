from fastapi import FastAPI, Request
import requests
import os, json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = FastAPI()

# ✅ LINE TOKEN（換你的）
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# ✅ Google Sheets（固定寫法，不要改）
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_key = json.loads(os.environ["GOOGLE_KEY"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

sheet = client.open("linebot-log").sheet1

# ✅ 寫入（加強DEBUG）
def log_to_sheet(msg):
    try:
        print("✅ 準備寫入:", msg)

        sheet.append_row([
            str(datetime.now()),
            msg
        ])

        print("✅ 寫入成功")

    except Exception as e:
        print("❌ 寫入失敗:", e)

# ✅ 回LINE
def reply_to_line(token, text):
    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "replyToken": token,
        "messages": [{"type": "text", "text": text}]
    }

    requests.post(url, headers=headers, json=body)

# ✅ 關鍵字邏輯（你要的保留版）
def handle(msg):

    msg = msg.lower()

    if "點名" in msg:
        return "📢 點名開始", "rollcall"

    if "累" in msg:
        return "💛 辛苦了", "emotion"

    if "禱告" in msg:
        return "🙏 為你禱告", "prayer"

    if "你好" in msg:
        return "🌿 平安", "greet"

    return "✅ 收到", "none"

# ✅ Webhook（最重要）
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    events = body.get("events", [])

    if not events:
        return {"ok": True}

    event = events[0]

    msg = event["message"]["text"]
    reply_token = event["replyToken"]

    # ✅ 關鍵字回應
    reply_text, intent = handle(msg)

    # ✅ 回LINE
    reply_to_line(reply_token, reply_text)

    # ✅ ✅ ✅ 一定寫入（最重要）
    log_to_sheet(msg + " | " + intent)

    return {"ok": True}
