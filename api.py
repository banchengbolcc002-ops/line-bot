# =====================================
# 基督教會數位執事 AI
# =====================================

# 載入 FastAPI 套件
from fastapi import FastAPI, Request

# 載入 requests 套件
import requests

# 載入作業系統環境變數
import os

# =====================================
# 建立 FastAPI 網站
# =====================================

app = FastAPI()

# =====================================
# 首頁
# 測試 Render 是否正常
# =====================================

@app.get("/")
def home():

    return {

        "status": "LINE BOT RUNNING",

        "class_name":
        "基督教會數位執事 AI",

        "student_name":
        "Linus",

        "student_id":
        "18"

    }

# =====================================
# 健康檢查
# 給 UptimeRobot 使用
# =====================================

@app.get("/health")
def health():

    return {

        "status": "OK"

    }

# =====================================
# LINE Access Token
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="
)

# =====================================
# 教會執事固定回覆
# =====================================

commands = {

    "你好": """

🌿 平安！

我是基督教會數位執事 AI。

很高興與您相遇。

願上帝賜福您今天滿有平安與喜樂。

如果您有：

🙏 禱告需要

📖 聖經問題

❤️ 生活關懷

💼 職場困擾

都歡迎與我分享。

""",

    "平安": """

🌿 願主耶穌基督的平安與您同在。

願神祝福您與您的家人。

🙏 阿們。

""",

    "經文": """

📖 今日經文

詩篇23:1

耶和華是我的牧者，
我必不致缺乏。

""",

    "禱告": """

🙏 禱告文

親愛的天父：

感謝祢今天的保守與看顧。

求祢賜給我們平安、
智慧與力量。

幫助我們面對工作、
家庭與人生中的挑戰。

奉主耶穌基督的名禱告。

阿們。

""",

    "test": """

✅ 系統運作正常

基督教會數位執事 AI

目前在線服務中。

""",

    "測試": """

✅ 系統運作正常

基督教會數位執事 AI

目前在線服務中。

"""
}

# =====================================
# 回覆 LINE
# =====================================

def reply_to_line(
    reply_token,
    text
):

    url = (
        "https://api.line.me/v2/bot/message/reply"
    )

    headers = {

        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}",

        "Content-Type":
        "application/json"

    }

    body = {

        "replyToken":
        reply_token,

        "messages": [

            {

                "type": "text",

                "text": text

            }

        ]

    }

    requests.post(
        url,
        headers=headers,
        json=body,
        timeout=10
    )

# =====================================
# LINE Webhook
# =====================================

@app.post("/callback")
async def callback(
    request: Request
):

    body = await request.json()

    events = body.get(
        "events",
        []
    )

    for event in events:

        if event.get("type") != "message":

            continue

        if (
            event["message"].get("type")
            != "text"
        ):

            continue

        # 使用者輸入內容

        user_message = (
            event["message"]["text"]
        ).strip()

        # LINE 回覆代碼

        reply_token = (
            event["replyToken"]
        )

        # 固定回覆

        if user_message in commands:

            reply_text = commands[
                user_message
            ]

        else:

            reply_text = f"""

🌿 基督教會數位執事 AI

您剛剛輸入：

{user_message}

目前為教學範例版本。

未來可擴充：

📖 聖經查詢

🙏 禱告助手

❤️ 關懷陪伴

💼 職場諮詢

"""

        # 回覆 LINE

        reply_to_line(
            reply_token,
            reply_text
        )

    return {

        "status": "OK"

    }
