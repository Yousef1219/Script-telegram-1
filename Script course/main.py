#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import os
import json
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.tl.types import User, MessageEntityMentionName
from telethon.errors import FloodWaitError

# ================== الإعدادات المشتركة ==================
KEYWORDS = {"خصوصي", "مدرس", "شرح", "ابغى شرح", "اريد شرح", "أريد توضيح", "ابغى خصوصي"}
MESSAGE_COOLDOWN = 300
MAX_ALERTS_PER_USER = 3
ALERT_GROUP_NAME = "جروب عامة و خاصة"
OLD_MESSAGES_LIMIT = 5000  # ← مراجعة حتى 5000 رسالة قديمة
LAST_IDS_FILE = "last_ids.json"

# ================== الحساب الأول (@Mustavan) ==================
API_ID_1 = 36250769
API_HASH_1 = "c7b8f9ed4febd1c11774cb90600d37b1"
SESSION_1 = "account_mustavan"

# ================== الحساب الثاني (@MOSTAVAN) ==================
API_ID_2 = 32209102
API_HASH_2 = "f5178e0304b5405841e2890741b7fbf0"
SESSION_2 = "account_mostavan"

# ================== قائمة الجروبات الموحّدة (بدون تكرار) ==================
ALL_UNIQUE_CHATS = {
    -1001899175509, -1001180462062, -1001398472728, -1001439483156, -1001347961658,
    -1001334211809, -1001565590875, -1002599349894, -1001229716070, -1001742415184,
    -1001975743341, -1001540385756, -1001759737120, -1001161147025, -1001123068370,
    -1001355987441, -1001386937107, -1001483339664, -1001517797071, -1001944047483,
    -1001271636531, -1002120652950, -1001285593255, -1002171265701, -1002348060198,
    -1001247444286, -1002187784014, -1001444285532, -1001839607110, -1001157851266,
    -1001498491016, -1001432704369, -1002129547057, -1001144261296, -1001960833615,
    -1002952263548, -1002285376265, -1001776723259, -1002863607413, -1001465569676,
    -1001465367087, -1001172715786, -1001508596246, -1002196005230, -1001973946485,
    -1002217091933, -1001227269667, -1002748051542, -1001774462290, -1001812822957,
    -1002073626400, -1002126707773, -1001741685847, -1002438781233, -1002061379495,
    -1001288596620, -1002054062062, -1002744645848, -1002279233213, -1002026597182,
    -1002008173841, -1002158654429, -1001275853758, -1001264969322, -1002141297765,
    -1002287049594, -1002484579522, -1001204644956, -1001433867488, -1001778943282,
    -1002244614166, -1002412940590, -1001841568421, -1001928643073, -1001326555965,
    -1002736802896, -1001279282015, -1002465866722, -1002139712335, -1002191389830,
    -1002261066904, -1002006635608, -1002593184202, -1002257862294, -1001820801182,
    -1001140016482, -1002307222601, -1002060567888, -1001156232365, -1002446388208,
    -1001993357060, -1002292008803, -1003195030979, -1001087394557, -1001030984630,
    -1002184474655, -1001481181753, -1002357422686, -1001839406125, -1002813576704,
    -1002547003728, -1002022350382, -1001145255393, -1001158855813, -1001752638277,
    -1002267857676, -2073412676431, -1001203935067, -1001417406639, -1001292434932,
    -1001335789985, -1001340259022, -1001414190863, -1001429135136, -1001363696242,
    -1001294987118, -1002829090688, -1002587472001, -1002314277494, -1002316555252,
    -1002460397475, -1002319123486, -1001733815413, -1001434225457, -5014175560,
    -1001972957893, -1001855963107, -1002754658529, -1001830198986, -1001225032064,
    -1001343047107, -1003076989518, -1002945394469, -2073148103034, -1001881983944,
    -1002930611289, -1002945690441, -1002951996184, -1002835268752, -1001290899430,
    -4815029745, -1001590976803, -1002156825354, -1002987884662, -1002995628620,
    -1002756861061, -1002182588231, -1002150205281, -1002632088939, -2072756861061,
    -1003003403454, -1001976308834, -1002423237629, -1002769647005, -1001424043722,
    -1001555778774, -2072754658529, -1002613640925, -1002682305304, -1002841951726,
    -2072841951726, -1002200194385, -1002884225861, -1002820279890, -1002755323143,
    -4661516529, -1002861591187, -1001127718941, -1002505638770, -1002088055511,
    -1002504859816, -1001594461368, -1002101742162, -1002275547152, -1001718543257,
    -1002123330141, -1002242187983, -1002561518994, -1002468013398, -1002175526253,
    -1002154809090, -1002196427231, -1002186506301, -1001312844466, -1002320044892,
    -1001005928760, -1002076923649, -1002169161316, -1001891252357, -1002211084338,
    -1002146767914, -1001312409852, -1002142602137, -1001982606041, -1001257127802,
    -1001579126316, -1001146078175, -1001571167513, -1001124852608, -1001274662390,
    -1001221546014, -1001459452060
}

# ========== دوال مساعدة ==========
def load_last_ids():
    if os.path.exists(LAST_IDS_FILE):
        try:
            with open(LAST_IDS_FILE, "r", encoding="utf-8") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except:
            return {}
    return {}

def save_last_id(chat_id, msg_id):
    last_ids = load_last_ids()
    last_ids[chat_id] = msg_id
    with open(LAST_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(last_ids, f)

last_messages = defaultdict(lambda: {"time": 0, "count": 0})

async def run_account(api_id, api_hash, session_name):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    me = await client.get_me()
    print(f"🟢 {me.first_name} (@{me.username or 'N/A'}) جاهز!")

    # البحث عن جروب التنبيهات
    alert_entity = None
    async for dialog in client.iter_dialogs():
        if dialog.is_group and dialog.name == ALERT_GROUP_NAME:
            alert_entity = dialog.entity
            break

    if not alert_entity:
        print(f"❌ خطأ: لم يُعثر على '{ALERT_GROUP_NAME}'!")
        return

    last_ids = load_last_ids()

    # === مراجعة الرسائل القديمة (مرة واحدة عند التشغيل) ===
    print(f"🔍 بدء مراجعة حتى {OLD_MESSAGES_LIMIT} رسالة قديمة لـ @{me.username}...")
    for chat_id in ALL_UNIQUE_CHATS:
        try:
            count = 0
            async for msg in client.iter_messages(chat_id, limit=OLD_MESSAGES_LIMIT):
                if not msg.text:
                    continue
                msg_id = msg.id
                if msg_id <= last_ids.get(chat_id, 0):
                    break

                text = msg.raw_text.lower()
                if any(k in text for k in KEYWORDS):
                    sender = await msg.get_sender()
                    if not isinstance(sender, User) or sender.bot:
                        continue

                    name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "غير معروف"
                    username = f"@{sender.username}" if sender.username else "❌ لا يوجد يوزرنيم"
                    chat_title = getattr(await msg.get_chat(), "title", "غير معروف")

                    link = ""
                    chat = await msg.get_chat()
                    if hasattr(chat, 'username') and chat.username:
                        link = f"https://t.me/{chat.username}/{msg.id}"
                    elif chat.id < 0:
                        real_id = str(chat.id)
                        if real_id.startswith('-100'):
                            link = f"https://t.me/c/{real_id[4:]}/{msg.id}"
                        else:
                            link = f"https://t.me/c/{real_id[1:]}/{msg.id}"

                    alert_msg = f"""🔔 طلب مساعدة جديد (قديم)

👤 الاسم: {name}
📱 اليوزر: {username}
👥 الجروب/القناة: {chat_title}

🔗 الرابط:
{link}

📜 الرسالة:
{msg.raw_text}
""".strip()

                    try:
                        mention = MessageEntityMentionName(offset=0, length=1, user_id=me.id)
                        await client.send_message(alert_entity, alert_msg, formatting_entities=[mention])
                        print(f"📩 تنبيه قديم من @{me.username} → {chat_title}")
                    except Exception as e:
                        print(f"⚠️ فشل إرسال تنبيه قديم: {e}")

                last_ids[chat_id] = msg_id
                save_last_id(chat_id, msg_id)
                count += 1
                if count % 100 == 0:
                    await asyncio.sleep(1)
        except Exception as e:
            continue

    print(f"✅ اكتملت مراجعة الرسائل القديمة لـ @{me.username}.")

    # === مراقبة الرسائل الجديدة ===
    @client.on(events.NewMessage(chats=list(ALL_UNIQUE_CHATS)))
    async def handler(event):
        sender = await event.get_sender()
        if not isinstance(sender, User) or sender.bot:
            return

        text = event.raw_text.lower()
        if not any(k in text for k in KEYWORDS):
            return

        now = time.time()
        data = last_messages[event.sender_id]
        if now - data["time"] < MESSAGE_COOLDOWN and data["count"] >= MAX_ALERTS_PER_USER:
            return

        name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "غير معروف"
        username = f"@{sender.username}" if sender.username else "❌ لا يوجد يوزرنيم"
        chat_title = getattr(await event.get_chat(), "title", "غير معروف")

        link = ""
        chat = await event.get_chat()
        if hasattr(chat, 'username') and chat.username:
            link = f"https://t.me/{chat.username}/{event.id}"
        elif chat.id < 0:
            real_id = str(chat.id)
            if real_id.startswith('-100'):
                link = f"https://t.me/c/{real_id[4:]}/{event.id}"
            else:
                link = f"https://t.me/c/{real_id[1:]}/{event.id}"

        alert_msg = f"""🔔 طلب مساعدة جديد

👤 الاسم: {name}
📱 اليوزر: {username}
👥 الجروب/القناة: {chat_title}

🔗 الرابط:
{link}

📜 الرسالة:
{event.raw_text}
""".strip()

        try:
            mention = MessageEntityMentionName(offset=0, length=1, user_id=me.id)
            await client.send_message(alert_entity, alert_msg, formatting_entities=[mention], silent=False)
            data["time"] = now
            data["count"] += 1
            print(f"✅ تنبيه من @{me.username}: تم الإرسال!")
        except Exception as e:
            print(f"⚠️ خطأ في @{me.username}: {e}")

        # حفظ آخر ID
        last_ids[event.chat_id] = event.id
        save_last_id(event.chat_id, event.id)

    # إعادة المحاولة عند فقدان الاتصال
    while True:
        try:
            await client.run_until_disconnected()
        except (ConnectionError, OSError):
            print(f"🔄 @{me.username}: انقطاع اتصال. إعادة المحاولة خلال 10 ثوانٍ...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"💥 خطأ غير متوقع في @{me.username}: {e}")
            await asyncio.sleep(30)

async def main():
    task1 = run_account(API_ID_1, API_HASH_1, SESSION_1)
    task2 = run_account(API_ID_2, API_HASH_2, SESSION_2)
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())