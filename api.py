# =====================================
# LINE AI 關懷助理
# 板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學號：18
# FastAPI + LINE + Gemini + Google Sheet
# =====================================

from fastapi import FastAPI, Request
import requests
import gspread
import traceback
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
import os
import json

# =====================================
# 建立 FastAPI
# =====================================

app = FastAPI()
# =====================================
# Render首頁
# =====================================

@app.get("/")
def home():

    return {
        "status": "LINE BOT RUNNING",
        "class_name": "板橋-iPAS AI應用與雙程式設計實務班",
        "student_name": "葉堠祿",
        "student_id": "18"
    }

# =====================================
# Render健康檢查
# =====================================

@app.get("/health")
def health():

    return {
        "status": "OK"
    }
# =====================================
# LINE Token
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# =====================================
# Gemini API
# =====================================

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# =====================================
# Google Sheet 設定
# =====================================

# 建議改用 gspread 原生支援的 service_account_from_dict（免去 oauth2client 依賴）
google_key = json.loads(os.environ["GOOGLE_KEY"])
client = gspread.service_account_from_dict(google_key)

SPREADSHEET_NAME = "linebot-log"
WORKSHEET_NAME = "linebot-care"

sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

# =====================================
# 記憶功能
# =====================================

user_memory = {}

# =====================================
# Google Sheet 紀錄
# =====================================

def log_to_sheet(user_name, msg, reply, intent):
    try:
        # 使用 timezone-aware 取得台灣時間 (UTC+8)
        taiwan_tz = timezone(timedelta(hours=8))
        taiwan_time = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")

        sheet.append_row([
            str(taiwan_time),
            user_name,
            msg,
            reply,
            intent
        ])

        print("✅ Google Sheet 寫入成功")

    except Exception as e:
        print("❌ Google Sheet 寫入錯誤")
        print(str(e))
        traceback.print_exc()

# =====================================
# LINE 回覆
# =====================================

def reply_to_line(token, text):
    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "replyToken": token,
        "messages": [
            {
                "type": "text",
                "text": str(text)[:5000]
            }
        ]
    }

    requests.post(url, headers=headers, json=body)

# =====================================
# 取得 LINE 使用者名稱
# =====================================

def get_user_name(user_id):
    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"
        headers = {
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        }
        res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            return res.json().get("displayName", "未知使用者")
        return "未知使用者"
    except Exception as e:
        print("❌ 取得 LINE 使用者名稱失敗:", str(e))
        return "未知使用者"

# =====================================
# LINE Webhook 接收與處理主邏輯
# =====================================

@app.post("/callback")
async def callback(request: Request):
    body = await request.json()
    events = body.get("events", [])

    for event in events:
        # 僅處理文字訊息事件
        if event.get("type") == "message" and event["message"].get("type") == "text":
            reply_token = event["replyToken"]
            user_id = event["source"].get("userId", "")
            user_msg = event["message"]["text"]

            # 1. 取得使用者名稱
            user_name = get_user_name(user_id) if user_id else "未知使用者"

            # 2. 獲取並維護對話記憶（保留最近 5 筆）
            history = user_memory.get(user_id, [])
            history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history])

            # 3. 組合 Prompt 並呼叫 Gemini API
            system_prompt = (
                f"你是『板橋-iPAS AI應用班』的 LINE AI 關懷助理。\n"
                f"當前對話使用者：{user_name}\n"
                f"請以親切、溫暖且富有同理心的語氣進行關懷與解答。\n\n"
                f"【過去對話紀錄】\n{history_text}\n\n"
                f"【使用者最新訊息】\n{user_msg}"
            )

            try:
                response = model.generate_content(system_prompt)
                ai_reply = response.text.strip()
                intent = "一般關懷與對話"
            except Exception as e:
                print("❌ Gemini API 處理錯誤:", str(e))
                ai_reply = "抱歉，我現在系統稍微忙碌中，請稍微等我一下再試試看喔！"
                intent = "系統異常"

            # 4. 更新對話記憶
            history.append({"user": user_msg, "ai": ai_reply})
            user_memory[user_id] = history[-5:]

            # 5. 發送回覆給 LINE 使用者
            reply_to_line(reply_token, ai_reply)

            # 6. 寫入 Google Sheet 紀錄
            log_to_sheet(user_name, user_msg, ai_reply, intent)

    return {"status": "OK"}
