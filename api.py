# ==========================================
# ✅ LINE 智慧回應機器人（完整版）
# ==========================================

# ✅ FastAPI：建立 API 服務（讓 LINE 可以連進來）
from fastapi import FastAPI, Request

# ✅ requests：用來回傳訊息給 LINE
import requests

# ✅ random：用來讓回覆有變化（避免機器人感）
import random

# ✅ 建立 Web API 服務
app = FastAPI()

# ==========================================
# ✅ ⚠️ 請放你的 LINE Channel Access Token
# ==========================================
LINE_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# ==========================================
# ✅ 點名記錄（記錄誰回「到」）
# ==========================================
attendance = set()

# ==========================================
# ✅ ✅ 回覆 LINE 訊息（固定格式）
# ==========================================
def reply_to_line(reply_token, text):
    """
    把訊息回傳給 LINE 使用者
    reply_token = LINE給你的回覆金鑰
    text = 要回覆的內容
    """

    headers = {
        "Authorization": "Bearer " + LINE_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    # 發送回 LINE 平台
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=data
    )


# ==========================================
# ✅ ✅ ✅ 核心邏輯（智慧判斷🔥）
# ==========================================
def handle_message(user_msg, user_id):

    # ✅ 將訊息整理（去空白 + 轉小寫）
    msg = user_msg.strip().lower()

    # ==========================================
    # ✅ ✅ 關鍵字資料庫（已優化）
    # ==========================================
    keyword_map = {

        "rollcall": {
            "keywords": ["點名","報到","集合","在嗎","集合一下","都到了嗎"]
        },

        "arrived": {
            "exact": ["到","到了","到✅","我到了","已到"]
        },

        "emotion": {
            "keywords": [
                "累","好累","崩潰","壓力","難過","低落",
                "想放棄","沒動力","孤單","寂寞",
                "撐不住","煩","心累","沒有希望"
            ]
        },

        "prayer": {
            "keywords": [
                "禱告","代禱","主啊","阿們","求主",
                "祝福","神啊","幫我禱告"
            ]
        },

        "encourage": {
            "keywords": [
                "加油","努力","撐住","不要放棄",
                "可以嗎","會成功嗎"
            ]
        },

        "greet": {
            "keywords": ["早安","你好","嗨","hello","hi"]
        },

        "thank": {
            "keywords": ["謝謝","感謝","3q"]
        },

        "bible": {
            "keywords": ["聖經","經文","靈修"]
        }
    }

    # ==========================================
    # ✅ ✅ ✅ 1️⃣ 精準比對（最高優先）
    # ==========================================
    if msg in keyword_map["arrived"]["exact"]:
        attendance.add(user_id)
        return f"✅ 已記錄，目前 {len(attendance)} 人到"

    # ==========================================
    # ✅ ✅ ✅ 2️⃣ 情緒強度判斷
    # ==========================================
    strong_emotion = ["想死","自殺","活不下去","撐不下去"]

    for w in strong_emotion:
        if w in msg:
            return random.choice([
                "💛 你不是一個人，神真的很愛你",
                "🙏 我們一起禱告，主現在就與你同在",
                "🌿 再難的時候，神也沒有離開你"
            ])

    # ==========================================
    # ✅ ✅ ✅ 3️⃣ 一般關鍵字判斷
    # ==========================================
    for intent, data in keyword_map.items():

        # ✅ 模糊搜尋（只要包含關鍵字就算）
        if any(k in msg for k in data.get("keywords", [])):

            # ✅ 不同類型給不同回覆
            if intent == "emotion":
                return random.choice([
                    "💛 辛苦了，神與你同在",
                    "🌿 願神給你平安與力量",
                    "🙏 主知道你的需要"
                ])

            elif intent == "prayer":
                return random.choice([
                    "🙏 我們一起禱告，願主帶領你",
                    "🌿 主會親自安慰你",
                    "✨ 願神賜你平安"
                ])

            elif intent == "encourage":
                return random.choice([
                    "🔥 不要放棄，神與你同在！",
                    "💪 你可以的，加油！",
                    "🌟 主會為你開路"
                ])

            elif intent == "greet":
                return random.choice([
                    "🌿 平安！願神祝福你",
                    "😊 哈囉！今天也要喜樂喔"
                ])

            elif intent == "thank":
                return random.choice([
                    "🙏 感謝主！",
                    "🌿 願神祝福你"
                ])

            elif intent == "rollcall":
                attendance.clear()
                return "📢 點名開始，請回：到 ✅"

            elif intent == "bible":
                return random.choice([
                    "📖 詩篇23:1 耶和華是我的牧者，我必不致缺乏",
                    "📖 腓立比書4:13 我靠著那加給我力量的，凡事都能做"
                ])

    # ==========================================
    # ✅ ✅ ✅ 4️⃣ 沒命中 → 不回（重要）
    # ==========================================
    return None


# ==========================================
# ✅ ✅ ✅ Webhook（LINE入口）
# ==========================================
@app.post("/reply")
async def reply(request: Request):

    try:
        # ✅ 取得 LINE 傳來的資料
        body = await request.json()

        print("📩 收到:", body)

        events = body.get("events", [])

        # ✅ 驗證用（LINE會傳空）
        if not events:
            return {"status": "ok"}

        event = events[0]

        reply_token = event.get("replyToken")

        message = event.get("message", {})

        # ✅ 只處理文字
        if message.get("type") != "text":
            return {"status": "ok"}

        user_msg = message.get("text")
        user_id = event.get("source", {}).get("userId")

        print("👤 使用者:", user_msg)

        # ✅ 呼叫智慧邏輯
        reply_text = handle_message(user_msg, user_id)

        # ✅ 有內容才回（不亂回）
        if reply_text:
            reply_to_line(reply_token, reply_text)

    except Exception as e:
        print("❌ 錯誤:", e)

    return {"status": "ok"}
