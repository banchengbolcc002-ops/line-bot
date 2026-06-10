# ===============================
# ✅ 基本套件
# ===============================
from fastapi import FastAPI, Request
import requests

# ===============================
# ✅ Google Sheets
# ===============================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===============================
# ✅ 系統工具
# ===============================
import os, json, random

# ===============================
# ✅ 建立服務
# ===============================
app = FastAPI()

# ===============================
# ✅ LINE TOKEN（換你的）
# ===============================
CHANNEL_ACCESS_TOKEN = "j/RTwDwbyWcvskPUxeO9tspcsxl+Xky8IQn+4Wo3zgSVeOACy3mfKT1R19eZzrMmOr7sMIDnhBT1/f0JzJaGD4 XXhPy+2lufHJrYhxBloM+VkUuLECIo9qw7HqvPM092tKsClQsfv1AntWKv8NBPMgdB04t89/1O/w1cDnyilFU="

# ===============================
# ✅ Google Sheets 連線
# ===============================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_key = json.loads(os.environ["GOOGLE_KEY"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_key, scope)
client = gspread.authorize(creds)

sheet = client.open("linebot-log").sheet1

# ===============================
# ✅ 寫入資料
# ===============================
def log_to_sheet(user_id, msg, reply, intent):

    sheet.append_row([
        str(datetime.now()),  # 時間
        user_id,              # 誰
        msg,                  # 說什麼
        reply,                # 回什麼
        intent                # 類別
    ])


# ===============================
# ✅ 回LINE
# ===============================
def reply_to_line(token, text):

    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "replyToken": token,
            "messages": [{"type": "text", "text": text}]
        }
    )


# ===============================
# ✅ 超強關鍵字系統（核心🔥）
# ===============================

# 👉 每個分類 = 好幾十個關鍵字（總體上百→可擴充到1000+）
INTENT_MAP = {

    "greet": [
        "你好","嗨","hi","hello","早安","午安","晚安",
        "哈囉","安安","yo","hey","hi there"
    ],

    "emotion": [
        "累","疲倦","壓力","煩","崩潰","不爽","心煩",
        "好累","超累","很累","不想做","想休息"
    ],

    "prayer": [
        "禱告","代禱","主啊","求神","祝福我",
        "幫我禱告","需要禱告"
    ],

    "encourage": [
        "加油","努力","撐住","不要放棄","可以嗎",
        "撐不住","快不行"
    ],

    "rollcall": [
        "點名","集合","報到","出席","在嗎"
    ],

    "thanks": [
        "謝謝","感謝","感恩","3q","thx","thanks"
    ],

    "bible": [
