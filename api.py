# ==========================================
# ✅ LINE Bot 完整系統（教授教學 + 可同步Sheet）
# ==========================================

# =========================
# ✅ 1️⃣ 匯入套件
# =========================
from fastapi import FastAPI, Request   # 建立API
import requests                        # HTTP請求
import logging                         # 記錄log
import random                          # 隨機回應
import datetime                        # 時間（寫入Sheet用）

# =========================
# ✅ 2️⃣ 建立Web服務
# =========================
app = FastAPI()

# =========================
# ✅ 3️⃣ log設定
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# ✅ 4️⃣ LINE Token（已自動去空格）
# =========================
LINE_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU=".replace(" ", "")

# =========================
# ✅ 5️⃣ LINE API
# =========================
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

HEADERS = {
    "Authorization": f"Bearer {LINE_TOKEN}",
    "Content-Type": "application/json"
}

# =========================
# ✅ 6️⃣ Google Sheet Webhook（❗你要貼GAS網址）
# =========================
SHEET_WEBHOOK_URL = "你的GAS網址"

# =========================
# ✅ 7️⃣ 回應資料庫
# =========================
RESPONSES = {

    "roll_call": ["請回覆：到 ✅", "點名開始！輸入「到」"],
    "arrived": ["✅ 已記錄", "👌 收到"],
    "care": ["辛苦了 💛", "你不孤單 🙏"],
    "test": ["✅ 系統正常", "✅ 測試成功"],
    "hello": ["你好 👋", "平安 🙏"]
}

# =========================
# ✅ 8️⃣ 隨機選一句
# =========================
def pick(category):
    return random.choice(RESPONSES.get(category, [""]))

# =========================
# ✅ 9️⃣ 寫入 Google Sheet（🔥重點）
# =========================
def write_to_sheet(user, msg, reply):

    # 👉 要傳給 GAS 的資料
    data = {
        "time": str(datetime.datetime.now()),
        "user": user,
