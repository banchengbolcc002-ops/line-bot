# ==========================================
# ✅ LINE Bot（AI升級版🔥）
# ==========================================

from fastapi import FastAPI, Request
import requests
import random
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ✅ Token
LINE_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU=".replace(" ", "")

LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

HEADERS = {
    "Authorization": f"Bearer {LINE_TOKEN}",
    "Content-Type": "application/json"
}

# ==========================================
# ✅ AI風格回應模板（核心🔥）
# ==========================================

AI_TEMPLATES = {
    "emotion": [
        "聽起來你有點辛苦 🙏 要不要我陪你聊聊？",
        "💛 我在這裡，你不需要一個人承受",
        "或許現在不容易，但你真的很努力了",
        "需要我幫你禱告嗎？🙏"
    ],
    "faith": [
        "🙏 願主現在就給你平安與力量",
        "神知道你的需要，祂一直都在 💛",
        "讓我們一起禱告，交託給神 🙏"
    ],
    "general": [
        "我收到你的訊息了 👌",
        "這是一個不錯的問題 😊",
        "我在，請繼續說 🙌"
    ],
    "encourage": [
        "💪 你可以的！",
        "🔥 不要放棄，繼續前進",
        "🌟 每一步都很重要"
    ]
}

# ==========================================
# ✅ AI模擬邏輯（關鍵🔥）
# ==========================================
def ai_reply(msg):

    msg = msg.lower()

    # ✅ 情緒判斷
    if any(k in msg for k in ["累", "壓力", "難過", "煩", "悶"]):
        return random.choice(AI_TEMPLATES["emotion"])

