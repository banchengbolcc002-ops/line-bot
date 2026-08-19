import html
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import gspread
import requests
from fastapi import FastAPI, HTTPException, Request
from google.oauth2.service_account import Credentials
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("christian-church-digital-deacon-ai")

APP_NAME = "基督教會 AI 執事"
APP_NAME_EN = "Christian Church Digital Deacon AI"

app = FastAPI(title=APP_NAME)


LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1").strip()
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

LINE_CONFIGURATION = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
LINE_HANDLER = WebhookHandler(LINE_CHANNEL_SECRET)


GREETING_MESSAGES = {
    "你好",
    "哈囉",
    "嗨",
    "hi",
    "hello",
    "test",
    "測試",
    "早安",
    "午安",
    "晚安",
    "謝謝",
    "感謝",
    "感謝主",
}

PEACE_MESSAGES = {"平安"}
AMEN_MESSAGES = {"阿們", "amen"}
SCRIPTURE_MESSAGES = {"經文"}
PRAYER_MESSAGES = {"禱告", "代禱"}

NO_GEMINI_MESSAGES = (
    GREETING_MESSAGES
    | PEACE_MESSAGES
    | AMEN_MESSAGES
    | SCRIPTURE_MESSAGES
    | PRAYER_MESSAGES
)

HIGH_RISK_KEYWORDS = {
    "自殺",
    "想死",
    "不想活",
    "活不下去",
    "結束生命",
}

conversation_memory: dict[str, list[dict[str, str]]] = {}


def clean_text(value: Any) -> str:
    """Remove HTML pollution and normalize text before replying or logging."""
    text = "" if value is None else str(value)
    text = html.unescape(text)

    text = re.sub(
        r"<a\s+[^>]*href=[\"']?([^\"'\s>]+)[\"']?[^>]*>(.*?)</a>",
        lambda match: f"{match.group(2).strip()} {match.group(1).strip()}".strip(),
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(https?://[^\s<>'\"]+)[\"']?\s*>", r"\1", text)
    text = re.sub(r"(https?://[^\s<>'\"]+)[\"']+", r"\1", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_message(message: str) -> str:
    return clean_text(message).strip().lower()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def get_google_sheet():
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        return None

    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes,
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        return spreadsheet.worksheet(GOOGLE_SHEET_NAME)
    except Exception:
        logger.exception("Google Sheet initialization failed")
        return None


def write_google_sheet_log(
    user_name: str,
    message: str,
    reply: str,
    intent: str,
) -> None:
    worksheet = get_google_sheet()
    if worksheet is None:
        logger.info("Google Sheet logging skipped: missing or invalid settings")
        return

    try:
        worksheet.append_row(
            [
                now_iso(),
                clean_text(user_name),
                clean_text(message),
                clean_text(reply),
                clean_text(intent),
            ],
            value_input_option="USER_ENTERED",
        )
    except Exception:
        logger.exception("Google Sheet append failed")


def get_user_name(user_id: str) -> str:
    if not user_id or not LINE_CHANNEL_ACCESS_TOKEN:
        return "LINE 使用者"

    try:
        with ApiClient(LINE_CONFIGURATION) as api_client:
            line_bot_api = MessagingApi(api_client)
            profile = line_bot_api.get_profile(user_id)
            return clean_text(profile.display_name) or "LINE 使用者"
    except Exception:
        logger.exception("Get LINE user profile failed")
        return "LINE 使用者"


def remember_message(user_id: str, role: str, content: str) -> None:
    if not user_id:
        return

    history = conversation_memory.setdefault(user_id, [])
    history.append({"role": role, "content": clean_text(content)})
    conversation_memory[user_id] = history[-8:]


def get_memory_text(user_id: str) -> str:
    history = conversation_memory.get(user_id, [])
    if not history:
        return "目前沒有既有對話紀錄。"

    lines = []
    for item in history[-8:]:
        role = "使用者" if item["role"] == "user" else APP_NAME
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


def detect_high_risk(message: str) -> bool:
    return any(keyword in message for keyword in HIGH_RISK_KEYWORDS)


def detect_intent(message: str) -> str:
    normalized = normalize_message(message)

    if detect_high_risk(message):
        return "高風險關懷"
    if normalized in PEACE_MESSAGES:
        return "固定回覆-平安"
    if normalized in AMEN_MESSAGES:
        return "固定回覆-阿們"
    if normalized in SCRIPTURE_MESSAGES:
        return "固定回覆-經文"
    if normalized in PRAYER_MESSAGES:
        return "固定回覆-禱告"
    if normalized in GREETING_MESSAGES:
        return "固定回覆-問候"
    return "Gemini 回覆"


def greeting_reply() -> str:
    return clean_text(
        """
        🌿 平安！

        我是基督教會 AI 執事。

        很高興與您相遇。

        如果您有：

        🙏 禱告需求

        📖 聖經問題

        ❤️ 生活關懷

        都歡迎與我分享。
        """
    )


def scripture_reply() -> str:
    return clean_text(
        """
        📖 今日經文

        詩篇23:1

        耶和華是我的牧者，
        我必不致缺乏。
        """
    )


def prayer_reply() -> str:
    return clean_text(
        """
        🙏 禱告文

        親愛的天父：

        感謝祢今天的帶領。

        求祢賜給我們平安、
        智慧與力量。

        保守我們的家庭、
        工作與健康。

        奉主耶穌基督的名禱告。

        阿們。
        """
    )


def peace_reply() -> str:
    return "🌿 願主耶穌的平安與您同在。"


def amen_reply() -> str:
    return clean_text(
        """
        🙏 阿們！

        願神祝福您。
        """
    )


def high_risk_reply() -> str:
    return clean_text(
        """
        💛 您的生命非常寶貴。

        請立即聯絡：

        1925安心專線

        1995生命線

        並尋求：

        牧者
        家人
        朋友

        協助。
        """
    )


def fixed_reply_for_intent(intent: str) -> str | None:
    if intent == "高風險關懷":
        return high_risk_reply()
    if intent == "固定回覆-平安":
        return peace_reply()
    if intent == "固定回覆-阿們":
        return amen_reply()
    if intent == "固定回覆-經文":
        return scripture_reply()
    if intent == "固定回覆-禱告":
        return prayer_reply()
    if intent == "固定回覆-問候":
        return greeting_reply()
    return None


def extract_gemini_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        return ""

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    texts = []
    for part in parts:
        text = part.get("text", "")
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


def gemini_reply(user_id: str, user_name: str, message: str) -> str:
    if not GEMINI_API_KEY:
        return "目前 AI 服務尚未設定完成。願主賜您平安。"

    try:
        prompt = f"""
你是「基督教會 AI 執事」（Christian Church Digital Deacon AI）。
請以一位服事教會超過30年的資深牧師之牧養經驗、聖經關懷與溫柔勸勉作為回答視角。
你的身份仍是「基督教會 AI 執事」，不要自稱 LINE AI 關懷助理，也不要使用學習助理、課程助理等稱呼。

規則：
- 使用繁體中文
- 回覆完整結束
- 不可停在半句
- 字數約300至600字
- 簡潔、溫暖、鼓勵
- 適度使用 🌿 🙏 📖 ❤️
- 不輸出 HTML 標籤
- 若提供連結，只輸出純網址，例如 https://example.com
- 可以用資深牧者的口吻關懷、勸勉、安慰與提醒，但不可宣稱自己是真人牧師
- 遇到醫療、法律、財務或危機議題，提醒尋求專業與真人協助
- 請務必完成整段回答，
- 不可停在未完成的句子，
- 結尾必須有完整結論。

職責：
1. 關懷教會弟兄姊妹
2. 提供禱告協助
3. 提供聖經分享
4. 回答信仰相關問題
5. 提供生活與職場鼓勵
6. 提供教會資訊服務

使用者名稱：{user_name}

最近對話：
{get_memory_text(user_id)}

使用者訊息：
{message}
"""
        api_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent"
        )
        response = requests.post(
            api_url,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 5000,
                    "temperature": 0.7,
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(json.dumps(data, ensure_ascii=False, indent=2))
        reply = extract_gemini_text(data) or "我收到您的訊息了。願主賜您平安。"
        final_reply = clean_text(reply)
        logger.info(final_reply)
        return final_reply

    
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        error_text = exc.response.text.lower() if exc.response is not None else str(exc).lower()
        logger.exception("Gemini HTTP response failed")
        if status_code == 429 or "quota" in error_text or "resource_exhausted" in error_text or "retry_delay" in error_text:
            return "目前 AI 額度暫時受限。您仍可以輸入「禱告」或「經文」，我會立即回覆。"
        return "目前 AI 回覆暫時忙碌中。願主賜您平安，請稍後再試。"
    except Exception as exc:
        error_text = str(exc).lower()
        logger.exception("Gemini response failed")
        if "quota" in error_text or "resource_exhausted" in error_text or "retry_delay" in error_text:
            return "目前 AI 額度暫時受限。您仍可以輸入「禱告」或「經文」，我會立即回覆。"
        return "目前 AI 回覆暫時忙碌中。願主賜您平安，請稍後再試。"


def create_reply(user_id: str, user_name: str, message: str) -> tuple[str, str]:
    message = clean_text(message)
    intent = detect_intent(message)
    fixed_reply = fixed_reply_for_intent(intent)

    if fixed_reply is not None:
        return fixed_reply, intent

    remember_message(user_id, "user", message)
    reply = gemini_reply(user_id, user_name, message)
    remember_message(user_id, "assistant", reply)
    return reply, intent


def reply_to_line(reply_token: str, reply: str) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN is missing")
        return

    try:
        with ApiClient(LINE_CONFIGURATION) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=clean_text(reply)[:5000])],
                )
            )
    except Exception:
        logger.exception("LINE reply failed")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "LINE BOT RUNNING"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health() -> dict[str, str]:
    return {"status": "OK"}



@app.post("/callback")
async def callback(request: Request) -> dict[str, str]:
    if not LINE_CHANNEL_SECRET:
        logger.error("LINE_CHANNEL_SECRET is missing")
        return {"status": "OK"}

    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        LINE_HANDLER.handle(body, signature)
    except InvalidSignatureError:
        logger.exception("Invalid LINE signature")
        return {"status": "OK"}
    except Exception:
        logger.exception("LINE webhook handling failed")
        return {"status": "OK"}

    return {"status": "OK"}


@LINE_HANDLER.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    user_id = getattr(event.source, "user_id", "") or ""
    user_name = "LINE 使用者"
    message = ""
    reply = "目前系統暫時忙碌中。願主賜您平安，請稍後再試。"
    intent = "系統錯誤"

    try:
        user_name = get_user_name(user_id)
        message = clean_text(event.message.text)
        reply, intent = create_reply(user_id, user_name, message)
    except Exception:
        logger.exception("Create LINE reply failed")

    reply_to_line(event.reply_token, reply)
    write_google_sheet_log(user_name, message, reply, intent)
