# ==========================================
# ✅ LINE Bot 重構完整版（強化提示詞 + 穩定版）
# ==========================================

from fastapi import FastAPI, Request
import requests
import logging
import random

app = FastAPI()

# ==========================================
# ✅ Logging（正式環境必備）
# ==========================================
logging.basicConfig(level=logging.INFO)

# ==========================================
# ✅ Token（自動去空格）
# ==========================================
LINE_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU=".replace(" ", "")

LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

HEADERS = {
    "Authorization": f"Bearer {LINE_TOKEN}",
    "Content-Type": "application/json"
}

# ==========================================
# ✅ ✅ 罐頭回應池（核心升級🔥）
# ==========================================
RESPONSES = {
    "roll_call": [
        "來報到 👇 請打：到 ✅",
        "集合時間到囉！請輸入「到」✅",
        "點名開始！請回覆：到 🙌"
    ],
    "arrived": [
        "✅ 收到",
        "👌 到齊！",
        "👍 已記錄"
    ],
    "prayer": [
        """我們一起禱告 🙏

主啊，
求祢看顧，賜下平安與力量。

奉主耶穌的名，阿們。""",

        """讓我們安靜禱告 🙏

願主的平安臨到你心中，
帶來安穩與盼望。

阿們。"""
    ],
    "care": [
        "辛苦了 🙏 神與你同在 💛",
        "給你一點溫暖 💛 若需要我可以陪你禱告 🙏",
        "別忘了，你不是一個人 🙌"
    ],
    "test": [
        "測試成功 ✅",
        "系統運作正常 👍",
        "OK ✅ 一切正常"
    ],
    "fallback": [
        None,  # ✅ 保持「不亂回」策略
        None,
    ]
}

# ==========================================
# ✅ 工具：隨機回應（增加自然感）
# ==========================================
def pick(category):
    return random.choice(RESPONSES.get(category, [None]))

# ==========================================
# ✅ LINE 回覆函式（強化版）
# ==========================================
def reply_to_line(reply_token: str, text: str):

    if not reply_token or not text:
        return

    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }

    try:
        res = requests.post(
            LINE_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=5
        )

        if res.status_code != 200:
            logging.error(f"LINE API錯誤: {res.text}")

    except Exception as e:
        logging.error(f"發送失敗: {e}")

# ==========================================
# ✅ ✅ 提示詞風格（可接AI🔥）
# ==========================================
SYSTEM_HINT = """
你是一個溫暖、簡潔、有信仰關懷的 LINE 助手：
- 回覆簡短
- 帶溫度與關懷
- 適合教會或團體互動
"""

# ==========================================
# ✅ 關鍵字處理（核心邏輯保留）
# ==========================================
def handle_message(user_msg: str):

    if not user_msg:
        return None

    msg = user_msg.strip()

    # ✅ 1️⃣ 點名
    if any(k in msg for k in ["點名", "報到", "簽到", "集合", "點到"]):
        return pick("roll_call")

    # ✅ 2️⃣ 到（精準）
    elif msg == "到":
        return pick("arrived")

    # ✅ 3️⃣ 禱告
    elif any(k in msg for k in ["禱告", "代禱", "祈禱", "求神", "主啊"]):
        return pick("prayer")

    # ✅ 4️⃣ 情緒關懷
    elif any(k in msg for k in ["累", "壓力", "難過", "低落"]):
        return pick("care")

    # ✅ 5️⃣ 測試
    elif "測試" in msg:
        return pick("test")

    # ✅ ❗不亂回（關鍵）
    return None

# ==========================================
# ✅ Webhook 入口（完整防呆版）
# ==========================================
@app.post("/reply")
async def reply(request: Request):

    reply_token = None

    try:
        body = await request.json()
        logging.info(f"📩 LINE資料: {body}")

        events = body.get("events", [])

        if not events:
            return {"status": "ok"}

        # ✅ 支援多事件（升級🔥）
        for event in events:

            if event.get("type") != "message":
                continue

            message = event.get("message", {})

            if message.get("type") != "text":
                continue

            user_msg = message.get("text", "")
            reply_token = event.get("replyToken")

            logging.info(f"👤 使用者: {user_msg}")

            reply_text = handle_message(user_msg)

            # ✅ 核心：有內容才回
            if reply_text:
                reply_to_line(reply_token, reply_text)

    except Exception as e:
        logging.error(f"❌ 系統錯誤: {e}")

        if reply_token:
            reply_to_line(reply_token, "系統忙碌中 🙏 請稍後再試")

    return {"status": "ok"}
