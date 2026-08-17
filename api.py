# ==========================================
# 基督教會 AI 助理
# 姓名：葉堠祿
# ==========================================

from fastapi import FastAPI, Request
import requests
import os

# ==========================================
# FastAPI
# ==========================================

app = FastAPI()

# ==========================================
# LINE TOKEN
# Render 環境變數名稱：
# LINE_CHANNEL_ACCESS_TOKEN
# ==========================================

LINE_TOKEN = os.getenv(
    "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="
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

    msg = msg.strip().lower()

    # ==========================
    # 高風險關懷
    # ==========================

    if is_danger_message(msg):

        return """

💛 您的生命非常寶貴。

請立即聯絡：

1925 安心專線

1995 生命線

並聯絡牧者、
家人或朋友。

🙏 願神保守您。

"""

    # ==========================
    # 固定回覆
    # 不耗 AI 額度
    # ==========================

    commands = {

        "你好": """

🌿 平安！

我是基督教會 AI 執事。

很高興與您相遇。

🙏 有代禱需要

📖 有聖經問題

❤️ 有生活困擾

都歡迎與我分享。

""",

        "hi": """
👋 Hi！
願神祝福您。
""",

        "hello": """
👋 Hello！
願主與您同在。
""",

        "哈囉": """
😊 哈囉！
很高興見到您。
""",

        "嗨": """
👋 嗨！
願主賜福您。
""",

        "平安": """

🌿 願主耶穌的平安與您同在。

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

保守我們的家庭、
工作與健康。

奉主耶穌基督的名禱告。

阿們。

""",

        "阿
