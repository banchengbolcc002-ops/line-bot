# ==========================================
# ✅ LINE 機器人（穩定優化版 ✅）
# ==========================================

from fastapi import FastAPI, Request
import requests

app = FastAPI()

# ✅ ⚠️ Token不能有空格（你原本有一個空格❗）
LINE_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="


# ==========================================
# ✅ 回LINE函式
# ==========================================
def reply_to_line(reply_token, text):

    headers = {
        "Authorization": "Bearer " + LINE_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "replyToken": str(reply_token),
        "messages": [
            {
                "type": "text",
                "text": str(text)
            }
        ]
    }

    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=data
    )


# ==========================================
# ✅ 關鍵字邏輯（精準版🔥）
# ==========================================
def handle_message(user_msg):

    msg = user_msg.strip()

    # ✅ 1️⃣ 點名（模糊匹配OK）
    if any(k in msg for k in [
        "點名", "報到", "簽到", "集合", "點到"
    ]):
        return "來報到 👇 請打：到 ✅"


    # ✅ 2️⃣ 到（❗只允許完全匹配，避免亂回）
    elif msg == "到":
        return "✅ 收到"

    # ✅ ✅ 如果你要保留幾種「到」可改這樣（安全版）
    # elif msg in ["到", "到✅", "到了"]:
    #     return "✅ 收到"


    # ✅ 3️⃣ 禱告
    elif any(k in msg for k in [
        "禱告", "代禱", "祈禱", "求神", "主啊"
    ]):
        return """我們一起禱告 🙏

主啊，
求祢看顧，賜下平安與力量。

奉主耶穌的名，阿們。"""


    # ✅ 4️⃣ 情緒關懷
    elif any(k in msg for k in [
        "累", "壓力", "難過", "低落"
    ]):
        return "辛苦了 🙏 若需要可以一起禱告 💛"


    # ✅ 5️⃣ 測試
    elif "測試" in msg:
        return "測試成功 ✅"


    # ✅ ❗沒有觸發 → 不回（核心）
    return None


# ==========================================
# ✅ Webhook入口
# ==========================================
@app.post("/reply")
async def reply(request: Request):

    body = await request.json()
    print("📩 LINE資料:", body)

    try:
        events = body.get("events", [])

        if not events:
            return {"status": "ok"}

        event = events[0]
        reply_token = event.get("replyToken")

        # ✅ 只處理訊息
        if event.get("type") != "message":
            return {"status": "ok"}

        msg = event.get("message", {})

        # ✅ 只處理文字
        if msg.get("type") != "text":
            return {"status": "ok"}

        user_msg = msg.get("text", "")
        print("👤 使用者:", user_msg)

        reply_text = handle_message(user_msg)

        # ✅ ❗只有有內容才回（非常重要）
        if reply_text:
            reply_to_line(reply_token, reply_text)

    except Exception as e:
        print("❌ 錯誤:", e)
        reply_to_line(reply_token, "系統忙碌中 🙏")

    return {"status": "ok"}
