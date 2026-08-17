# ==========================================
# 基督教會 AI 執事
# 板橋-iPAS AI應用與雙程式設計實務班
# 學生姓名：葉堠祿
# 學號：18
# ==========================================

from fastapi import FastAPI, Request
import requests
import os

# ==========================================
# 建立 FastAPI
# ==========================================

app = FastAPI()

# ==========================================
# LINE TOKEN
# ==========================================

LINE_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

# ==========================================
# 首頁
# ==========================================

@app.get("/")
def home():

    return {

        "status": "LINE BOT RUNNING",

        "project": "基督教會AI執事",

        "student": "葉堠祿"

    }

# ==========================================
# 健康檢查
# ==========================================

@app.get("/health")
def health():

    return {

        "status": "OK"

    }

# ==========================================
# 回覆 LINE
# ==========================================

def reply_to_line(
    reply_token,
    text
):

    headers = {

        "Authorization":
        "Bearer " + LINE_TOKEN,

        "Content-Type":
        "application/json"

    }

    data = {

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

        "https://api.line.me/v2/bot/message/reply",

        headers=headers,

        json=data,

        timeout=10

    )

# ==========================================
# 高風險關懷
# ==========================================

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

# ==========================================
# 訊息處理
# ==========================================

def handle_message(msg):

    msg = msg.strip()

    if is_danger_message(msg):

        return """

💛 您的生命非常寶貴。

請立即聯絡：

1925 安心專線

1995 生命線

並尋求牧者、
家人或朋友的協助。

🙏 願神保守您。

"""

    commands = {

        "你好": """

🌿 平安！

我是基督教會 AI 執事。

很高興與您相遇。

如果您有：

🙏 禱告需求

📖 聖經問題

❤️ 生活困擾

都歡迎與我分享。

""",

        "平安": """

🌿 願主耶穌基督的平安與您同在。

願神保守您與您的家人。

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

感謝祢今天的帶領。

求祢賜給我們平安、
智慧與力量。

願祢保守我們的家庭、
工作與健康。

奉主耶穌基督的名禱告。

阿們。

""",

        "測試": """

✅ 系統運作正常

基督教會 AI 執事

在線服務中

""",

        "test": """

✅ 系統運作正常

基督教會 AI 執事

在線服務中

""",

        "hi": "👋 Hi！願神祝福您。",

        "hello": "👋 Hello！願神與您同在。",

        "哈囉": "😊 哈囉！很高興見到您。",

        "嗨": "👋 嗨！願主賜福您。",

        "早安": "☀️ 早安！願神祝福您今天。",

        "午安": "🌤️ 午安！願您平安喜樂。",

        "晚安": "🌙 晚安！願主保守您。",

        "謝謝": "❤️ 不客氣，很高興能幫助您。",

        "感謝": "🙏 願神祝福您。"

    }

    if msg in commands:

        return commands[msg]

    return """

🌿 基督教會 AI 執事

已收到您的訊息。

目前為穩定版執事系統。

若您需要：

🙏 禱告

📖 經文

❤️ 關懷

歡迎直接輸入關鍵字。

"""

# ==========================================
# LINE WEBHOOK
# ==========================================

@app.post("/callback")
async def callback(request: Request):

    body = await request.json()

    events = body.get(
        "events",
        []
    )

    for event in events:

        if event.get("type") != "message":

            continue

        if event["message"].get("type") != "text":

            continue

        user_msg = event["message"]["text"]

        reply_token = event["replyToken"]

        reply_text = handle_message(
            user_msg
        )

        reply_to_line(
            reply_token,
            reply_text
        )

    return {

        "status": "OK"

    }
