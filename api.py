import html
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import gspread
from fastapi import FastAPI, HTTPException, Request
from google import genai
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
logger = logging.getLogger("church-deacon-ai")

app = FastAPI(title="基督教會數位執事 AI")


LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1").strip()
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

LINE_CONFIGURATION = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
LINE_HANDLER = WebhookHandler(LINE_CHANNEL_SECRET)

QUICK_REPLY_MESSAGES = {
    "你好",
    "哈囉",
    "嗨",
    "hi",
    "hello",
    "test",
    "測試",
    "ping",
    "平安",
    "早安",
    "午安",
    "晚安",
    "謝謝",
    "感謝",
}

HIGH_RISK_KEYWORDS = {
    "自殺",
    "想死",
    "不想活",
    "活不下去",
    "結束生命",
}

SCRIPTURE_KEYWORDS = {"經文", "今日經文", "聖經", "金句"}
PRAYER_KEYWORDS = {"禱告", "代禱", "祈禱", "為我禱告"}

conversation_memory: dict[str, list[dict[str, str]]] = {}


def clean_text(value: Any) -> str:
    """Normalize text and remove HTML/anchor pollution before sending to LINE."""
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
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
        logger.warning("Google Sheet logging skipped: missing or invalid settings")
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
    conversation_memory[user_id] = history[-10:]


def get_memory_text(user_id: str) -> str:
    history = conversation_memory.get(user_id, [])
    if not history:
        return "目前沒有既有對話紀錄。"

    lines = []
    for item in history[-10:]:
        role = "使用者" if item["role"] == "user" else "數位執事 AI"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


def is_quick_reply(message: str) -> bool:
    normalized = message.strip().lower()
    return normalized in QUICK_REPLY_MESSAGES


def detect_high_risk(message: str) -> bool:
    return any(keyword in message for keyword in HIGH_RISK_KEYWORDS)


def detect_intent(message: str) -> str:
    normalized = message.strip().lower()

    if detect_high_risk(message):
        return "高風險訊息"
    if normalized in QUICK_REPLY_MESSAGES:
        return "快速問候"
    if any(keyword in message for keyword in SCRIPTURE_KEYWORDS):
        return "今日經文"
    if any(keyword in message for keyword in PRAYER_KEYWORDS):
        return "禱告代禱"
    return "Gemini 回覆"


def quick_greeting_reply() -> str:
    return clean_text(
        """
        🌿 平安！

        我是基督教會數位執事 AI。

        很高興與您相遇。

        願上帝賜福您今天滿有平安與喜樂。
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


def prayer_reply(user_name: str) -> str:
    return clean_text(
        f"""
        🙏 代禱文

        親愛的天父，

        感謝祢看顧 {user_name}，也知道此刻心中的需要、壓力、盼望與等待。
        求祢用祢的平安保守他的心懷意念，賜下智慧面對今天的事情，
        也賜下力量走過正在經歷的困難。

        主啊，若他心中有憂慮，求祢安慰；
        若他身體疲乏，求祢扶持；
        若他需要方向，求祢引導；
        若他正在等候，求祢堅固他的信心。

        願祢的愛充滿他的家庭、工作、服事與人際關係，
        使他在每一步都經歷祢同在的恩典。

        奉主耶穌基督的名禱告，阿們。
        """
    )


def high_risk_reply() -> str:
    return clean_text(
        """
        我很在意你現在的安全。若你正有傷害自己的念頭，請立刻聯絡身邊可信任的人，或直接撥打以下資源：

        1925 安心專線
        1995 生命線

        若你已經處於立即危險中，請立刻撥打當地緊急電話或前往最近的急診。
        你不需要一個人承受，現在先讓真人陪你一起度過這一刻。
        """
    )


def gemini_reply(user_id: str, user_name: str, message: str) -> str:
    if not GEMINI_API_KEY:
        return "目前 Gemini 尚未設定完成，請稍後再試。"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
你是「基督教會數位執事 AI」。

請用繁體中文回覆，語氣要溫暖、謙和、清楚、有牧養關懷，但不要假裝自己是牧師或真人。
可以提供教會行政、聚會提醒、關懷問候、信仰陪伴、禱告方向與一般資訊協助。
若遇到醫療、法律、財務或高風險心理危機，請提醒使用者尋求合格專業或緊急協助。

禁止輸出 HTML 標籤。若要提供連結，請直接輸出完整網址，例如 https://example.com。

使用者名稱：{user_name}

最近對話記憶：
{get_memory_text(user_id)}

使用者最新訊息：
{message}
"""
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        reply = getattr(response, "text", "") or "我收到您的訊息了，願主賜您平安。"
        return clean_text(reply)
    except Exception:
        logger.exception("Gemini response failed")
        return "抱歉，目前 AI 回覆服務暫時忙碌中。請稍後再試，願主賜您平安。"


def create_reply(user_id: str, user_name: str, message: str) -> tuple[str, str]:
    message = clean_text(message)
    intent = detect_intent(message)

    if intent == "高風險訊息":
        return high_risk_reply(), intent
    if intent == "快速問候":
        return quick_greeting_reply(), intent
    if intent == "今日經文":
        return scripture_reply(), intent
    if intent == "禱告代禱":
        return prayer_reply(user_name), intent

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "OK"}


@app.post("/callback")
async def callback(request: Request) -> dict[str, str]:
    if not LINE_CHANNEL_SECRET:
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_SECRET is missing")

    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        LINE_HANDLER.handle(body, signature)
    except InvalidSignatureError as exc:
        raise HTTPException(status_code=400, detail="Invalid LINE signature") from exc
    except Exception as exc:
        logger.exception("LINE webhook handling failed")
        raise HTTPException(status_code=500, detail="Webhook handling failed") from exc

    return {"status": "OK"}


@LINE_HANDLER.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    user_id = getattr(event.source, "user_id", "") or ""
    user_name = get_user_name(user_id)
    message = clean_text(event.message.text)

    reply, intent = create_reply(user_id, user_name, message)
    reply_to_line(event.reply_token, reply)
    write_google_sheet_log(user_name, message, reply, intent)
