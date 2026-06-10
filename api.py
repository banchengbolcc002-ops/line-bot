import random

seen_users = set()

def handle_message(user_msg, user_id):

    msg = user_msg.strip().lower()

    # ==========================================
    # ✅ 0️⃣ 新使用者引導（一次）
    # ==========================================
    if user_id not in seen_users:
        seen_users.add(user_id)
        return "👋 歡迎！試試：點名 / 禱告 / 經文"

    # ==========================================
    # ✅ 1️⃣ 精準控制（最高優先）
    # ==========================================
    if msg in ["到", "到了", "已到", "我到了"]:
        attendance.add(user_id)
        return f"✅ 已記錄，目前 {len(attendance)} 人到"

    # ==========================================
    # ✅ 2️⃣ 強情緒保護（安全層🔥）
    # ==========================================
    strong_emotion = ["想死","自殺","活不下去","撐不下去"]

    if any(w in msg for w in strong_emotion):
        return random.choice([
            "💛 你很重要，神沒有離開你",
            "🙏 我們可以一起禱告，你不是一個人",
            "🌿 再難的時候，神仍然與你同在"
        ])

    # ==========================================
    # ✅ 3️⃣ 關鍵字系統（穩定層）
    # ==========================================
    keyword_map = {

        "rollcall": ["點名","報到","集合"],
        "emotion": ["累","難過","壓力","崩潰","煩"],
        "prayer": ["禱告","代禱","主啊"],
        "encourage": ["加油","不要放棄"],
        "greet": ["早安","你好","hi"],
        "thank": ["謝謝","感謝"],
        "bible": ["經文","聖經"]
    }

    for intent, keywords in keyword_map.items():
        if any(k in msg for k in keywords):

            if intent == "rollcall":
                attendance.clear()
                return "📢 點名開始，請回：到 ✅"

            elif intent == "emotion":
                return random.choice([
                    "💛 辛苦了，你不是一個人",
                    "🌿 願神給你平安",
                ])

            elif intent == "prayer":
                return "🙏 願主看顧你，帶領你"

            elif intent == "encourage":
                return "🔥 你可以的，不要放棄！"

            elif intent == "greet":
                return "🌿 平安！"

            elif intent == "thank":
                return "🙏 感謝主！"

            elif intent == "bible":
                return random.choice([
                    "📖 詩篇23:1 耶和華是我的牧者",
                    "📖 腓立比書4:13 我靠主凡事都能"
                ])

    # ==========================================
    # ✅ 4️⃣ AI模糊語意（核心🔥🔥🔥）
    # ==========================================
    semantic_map = {

        "help": ["怎麼辦","怎麼用","可以幫我","我該怎麼做"],
        "life": ["人生","意義","方向","未來","迷惘"],
        "tired": ["好累","撐不住","真的很累"],
        "lost": ["不知道怎麼辦","不知道方向"]
    }

    for intent, patterns in semantic_map.items():
        if any(p in msg for p in patterns):

            if intent == "help":
                return "🤖 你可以試試：點名 / 禱告 / 經文"

            elif intent == "life":
                return "🌿 有時候方向比速度更重要，願神帶領你"

            elif intent == "tired":
                return "💛 你可以休息一下，神仍然與你同在"

            elif intent == "lost":
                return "✨ 當你迷惘時，可以試著停下來尋求神"

    # ==========================================
    # ✅ 5️⃣ fallback策略（關鍵🔥）
    # ==========================================
    confidence_words = ["嗎","怎麼","可以","有沒有","要不要"]

    # 👉 如果很像問題 → 給提示
    if any(w in msg for w in confidence_words):
        return "🤖 我目前支援：點名、禱告、經文"

    # 👉 低機率提示（防干擾）
    if random.random() < 0.03:
        return "😊 試試：禱告 / 點名 / 經文"

    # ==========================================
    # ✅ 6️⃣ 最終控制（不亂回🔥）
    # ==========================================
    return None
