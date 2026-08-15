# =====================================
# 基督教會 AI 執事
# 板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學號：18
# =====================================

from fastapi import FastAPI, Request
import requests
import os

# =====================================
# 建立 FastAPI
# =====================================

app = FastAPI()

# =====================================
# 首頁
# =====================================

@app.get("/")
def home():

    return {
        "status": "LINE BOT RUNNING",
        "project": "基督教會AI執事",
        "student_name": "葉堠祿",
        "student_id": "18"
    }

# =====================================
# 健康檢查
# =====================================

@app.get("/health")
def health():

    return {
        "status": "OK"
    }

# =====================================
# LINE Token
# Render 環境變數
# =====================================

CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

# =====================================
# 教會固定回覆
# 不消耗 AI 額度
# =====================================

COMMANDS = {

    "你好": """

🌿 平安！

我是基督教會 AI 執事。

很高興與您相遇。

若您需要：

🙏 禱告

📖 聖經分享

❤️ 生活關懷

都歡迎與我交流。

""",

    "平安": """

🌿 願主耶穌的平安與您同在。

願神祝福您與您的家人。

🙏 阿們

""",

    "經文": """

📖 今日經文

詩篇23:1

耶和華是我的牧者，

我必不致缺乏。

""",

    "禱告": """

🙏 禱告

親愛的天父：

感謝祢今天的保守與帶領。

求祢賜給我們智慧、

平安與力量。

奉主耶穌的名禱告。

阿們。

""",

    "test": """

✅ 系統運作正常

基督教會 AI 執事

在線服務中

""",

    "測試": """

✅ 系統運作正常

基督教會 AI 執事

在線服務中

""",

    "hi": "👋 Hi！願神祝福您。",

    "hello": "👋 Hello！平安。",

    "哈囉": "😊 哈囉！很高興見到您。",

    "早安": "☀️ 早安！願神祝福您今天。",

    "午安": "🌤️ 午安！願您平安喜樂。",

    "晚安": "🌙 晚安！願主保守您。",

    "謝謝": "❤️ 不客氣，很高興能幫助您。"

}

# =====================================
# 高風險訊息偵測
# =====================================

def is_danger_message(msg):

    keywords = [

        "自殺",
        "想死",
        "不想活",
        "活不下去",
        "結束生命"

    ]

    return any(
        word in msg
        for word in keywords
    )

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
                "text": str(text)[:5000]
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

        msg = (
            event["message"]["text"]
        ).strip()

        token = (
            event["replyToken"]
        )

        # =========================
        # 高風險關懷
        # =========================

        if is_danger_message(msg):

            reply_text = """

💛 您的生命非常寶貴。

請立即聯絡：

1925 安心專線

1995 生命線

或尋求牧者、
家人與朋友協助。

🙏 我們關心您。

"""

        # =========================
        # 固定回覆
        # =========================

        elif msg in COMMANDS:

            reply_text = COMMANDS[msg]

        # =========================
        # 未來可接 Gemini
        # =========================

        else:

            reply_text = f"""

🌿 基督教會 AI 執事

您剛剛輸入：

{msg}

目前此版本優先使用固定回覆。

未來可擴充：

📖 聖經查詢

🙏 禱告助手

❤️ 關懷陪伴

🤖 Gemini AI

"""

        reply_to_line(
            token,
            reply_text
        )

    return {
        "status": "OK"
    }
