from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json, os, random, string

# ========== تنظیمات ==========
TOKEN = "8905378875:AAHg4rVLYeY51xdKUDr7zA43jtxmCOUEIeE"
ADMIN_ID = 6106477309
CHANNEL_ID = -1004298773614
MESSAGE_ID = 11
MAX_REG = 3
DATA_FILE = "bot_data.json"
app = None

# ========== کشورها ==========
COUNTRIES = [
    "آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا",
    "لهستان", "هلند", "بلژیک", "پرتغال", "جمهوری چک", "مجارستان", "رومانی",
    "بلغارستان", "روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران",
    "عربستان سعودی", "امارات متحده عربی", "مصر", "اتیوپی", "اندونزی",
    "مالزی", "تایلند", "ویتنام", "قزاقستان", "نیجریه", "چین", "ژاپن",
    "کره جنوبی", "پاکستان", "اسرائیل", "استرالیا", "اسپانیا", "سوئیس",
    "سوئد", "نروژ", "ترکیه", "فنلاند", "آرژانتین", "مکزیک", "شیلی"
]

FREE = [
    "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا",
    "لهستان", "هلند", "بلژیک", "پرتغال", "جمهوری چک", "مجارستان",
    "رومانی", "بلغارستان", "هند", "برزیل", "آفریقای جنوبی",
    "عربستان سعودی", "امارات متحده عربی", "مصر", "اتیوپی", "اندونزی",
    "مالزی", "تایلند", "ویتنام", "قزاقستان", "نیجریه", "ژاپن",
    "کره جنوبی", "پاکستان", "اسرائیل", "استرالیا", "اسپانیا", "سوئیس",
    "سوئد", "نروژ", "ترکیه", "فنلاند", "آرژانتین", "مکزیک", "شیلی"
]

PAID = {
    "آمریکا": 50, "روسیه": 50, "چین": 50, "ایران": 30
}
ALL = FREE + list(PAID.keys())
CARD = "6219861815142665"
CARD_HOLDER = "جوانمرد"

# ========== دیتابیس ==========
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"taken": {}, "pending": {}, "banned": [], "force": {}, "codes": {}, "count": {}, "locked": []}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump({"taken": taken, "pending": pend, "banned": banned, "force": force, "codes": codes, "count": count, "locked": locked}, f, ensure_ascii=False, indent=2)

data = load()
taken, pend, banned, force, codes, count, locked = data.get("taken", {}), data.get("pending", {}), data.get("banned", []), data.get("force", {}), data.get("codes", {}), data.get("count", {}), data.get("locked", [])

def user_country(uid):
    for c, u in taken.items():
        if u == uid: return c
    return None

def is_banned(uid): return uid in banned
def is_locked(c): return c in locked
def reg_count(uid): return count.get(uid, 0)
def can_reg(uid): return reg_count(uid) < MAX_REG
def gen_code(): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ========== نمایش لیست با شماره ==========
def show_list():
    groups = {
        "🟦 NATO 🟦": ["آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا", "لهستان", "هلند", "بلژیک", "پرتغال", "جمهوری چک", "مجارستان", "رومانی", "بلغارستان"],
        "🟥 BRICS 🟥": ["روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران", "عربستان سعودی", "امارات متحده عربی", "مصر", "اتیوپی", "اندونزی", "مالزی", "تایلند", "ویتنام", "قزاقستان", "نیجریه"],
        "🟩 GLOSA 🟩": ["چین", "ژاپن", "کره جنوبی", "پاکستان", "اسرائیل", "استرالیا", "اسپانیا", "سوئیس", "سوئد", "نروژ", "ترکیه", "فنلاند", "آرژانتین", "مکزیک", "شیلی"]
    }
    msg = "📋 **لیست کشورها (عدد رو بفرستید):**\n\n"
    for title, countries in groups.items():
        msg += f"{title}\n"
        for c in countries:
            num = COUNTRIES.index(c) + 1
            if c in taken: s = "❌ گرفته شده"
            elif is_locked(c): s = "🔒 قفل شده"
            elif c in PAID: s = f"💰 ویژه - {PAID[c]} هزار تومان"
            else: s = "✅ رایگان"
            msg += f"{num}. {c} → {s}\n"
        msg += "\n"
    return msg

# ========== اعلان کانال ==========
async def notify(text):
    try:
        await app.bot.send_message(chat_id=CHANNEL_ID, text=text, reply_to_message_id=MESSAGE_ID, parse_mode="HTML")
    except Exception as e:
        print(f"خطا: {e}")

async def clear_user(uid, reason="توسط کاربر"):
    c = user_country(uid)
    if not c: return False
    del taken[c]
    if reason == "توسط ادمین":
        force[uid] = c
    save()
    await notify(f"❌ - {c} خالی شد ({reason})")
    try:
        await app.bot.send_message(chat_id=uid, text=f"⚠️ کشور {c} {reason} خالی شد.", parse_mode="HTML")
    except: pass
    return True

# ========== دستورات ==========
async def start(update, context):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ شما بن هستید.")
        return
    rem = MAX_REG - reg_count(uid)
    c = user_country(uid)
    if c:
        kb = [[InlineKeyboardButton("🗑️ خالی کردن کشور", callback_data=f"clear_req_{uid}")]]
        await update.message.reply_text(f"👋 کشور {c} رو دارید.\n📊 {rem} بار باقی‌مانده.", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return
    if rem <= 0:
        await update.message.reply_text("⛔ به حد مجاز رسیده‌اید.", parse_mode="HTML")
        return
    await update.message.reply_text(f"سلام!\n{show_list()}\nعدد مورد نظر رو بفرست.\n📊 {rem} بار باقی‌مانده.", parse_mode="HTML")

async def clear_cmd(update, context):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ بن هستید.")
        return
    c = user_country(uid)
    if not c:
        await update.message.reply_text("❌ کشوری ندارید.")
        return
    kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clear_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clear_no_{uid}")]]
    await update.message.reply_text(f"⚠️ مطمئنی کشور {c} رو خالی کنی؟", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# ========== ریست کردن شانس (ادمین) ==========
async def reset_chance(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
        if uid not in count:
            await update.message.reply_text(f"❌ کاربر {uid} هیچ کشوری پر نکرده.")
            return
        count[uid] = 0
        save()
        await update.message.reply_text(f"✅ تعداد دفعات ثبت‌نام کاربر {uid} به ۰ ریست شد.")
        try:
            await app.bot.send_message(chat_id=uid, text=f"✅ شانس شما برای ثبت‌نام کشور توسط ادمین ریست شد. می‌توانید دوباره {MAX_REG} بار کشور بگیرید.")
        except: pass
    except:
        await update.message.reply_text("فرمت: /reset_chance [user_id]")

# ========== مدیریت انتخاب کشور ==========
async def handle_selection(update, context):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ بن هستید.")
        return
    if not can_reg(uid):
        await update.message.reply_text(f"⛔ به حد مجاز ({MAX_REG} بار) رسیده‌اید.")
        return
    if uid in force:
        await update.message.reply_text(f"⛔ قبلاً کشور {force[uid]} توسط ادمین گرفته شد.", parse_mode="HTML")
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("لطفاً عدد بفرست.")
        return
    num = int(text) - 1
    if num < 0 or num >= len(COUNTRIES):
        await update.message.reply_text(f"عدد باید بین ۱ تا {len(COUNTRIES)} باشه.")
        return
    selected = COUNTRIES[num]
    if is_locked(selected):
        await update.message.reply_text(f"🔒 کشور {selected} قفل شده.")
        return
    if uid in force and force[uid] == selected:
        await update.message.reply_text(f"⛔ نمی‌توانید دوباره کشور {selected} را بگیرید.")
        return
    if user_country(uid):
        await update.message.reply_text("⚠️ قبلاً کشور گرفتی.")
        return
    if selected in taken:
        await update.message.reply_text(f"❌ کشور {selected} گرفته شده.")
        return
    if selected in FREE:
        taken[selected] = uid
        count[uid] = reg_count(uid) + 1
        code = gen_code()
        codes.setdefault(uid, []).append(code)
        save()
        await update.message.reply_text(
            f"✅ کشور {selected} ثبت شد!\n🔑 کد: <code>{code}</code>\n📊 {MAX_REG - reg_count(uid)} بار باقی‌مانده.\n\n⚠️ این کد را به کسی ندهید.\nبرای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await notify(f"✅ - {selected} پر شد")
        username = f"@{user.username}" if user.username else "ندارد"
        await app.bot.send_message(chat_id=ADMIN_ID, text=f"📢 {selected} پر شد!\n👤 {user.first_name}\n🆔 <code>{uid}</code>\n👤 {username}\n🔑 <code>{code}</code>", parse_mode="HTML")
        return
    if selected in PAID:
        pend[uid] = {"country": selected, "username": user.username, "first_name": user.first_name, "status": "waiting_for_admin_approval", "chat_id": update.message.chat_id}
        save()
        kb = [[InlineKeyboardButton("✅ تأیید", callback_data=f"allow_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"deny_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 درخواست خرید {selected}\n👤 {user.first_name}\n🆔 <code>{uid}</code>\n👤 @{user.username if user.username else 'ندارد'}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        await update.message.reply_text(f"🔔 درخواست شما برای {selected} به ادمین ارسال شد.")

# ========== بقیه توابع (clear, ban, lock, etc) ==========
async def lock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    c = " ".join(context.args)
    if not c:
        await update.message.reply_text("فرمت: /lock [نام کشور]")
        return
    if c not in ALL:
        await update.message.reply_text(f"کشور {c} وجود ندارد.")
        return
    if c in locked:
        await update.message.reply_text(f"🔒 کشور {c} قبلاً قفل است.")
        return
    locked.append(c)
    save()
    await update.message.reply_text(f"🔒 کشور {c} قفل شد.")
    await notify(f"🔒 - {c} قفل شد")

async def unlock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    c = " ".join(context.args)
    if not c or c not in ALL:
        await update.message.reply_text("فرمت: /unlock [نام کشور]")
        return
    if c not in locked:
        await update.message.reply_text(f"🔓 کشور {c} قفل نیست.")
        return
    locked.remove(c)
    save()
    await update.message.reply_text(f"🔓 کشور {c} باز شد.")
    await notify(f"🔓 - {c} باز شد")

async def forceclear_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("فرمت: /forceclear [user_id]")
        return
    c = user_country(uid)
    if not c:
        await update.message.reply_text(f"کاربر {uid} کشوری ندارد.")
        return
    await clear_user(uid, "توسط ادمین")
    await update.message.reply_text(f"✅ کشور {c} از کاربر {uid} خالی شد.")

async def ban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("فرمت: /ban [user_id]")
        return
    if uid in banned:
        await update.message.reply_text("قبلاً بن شده.")
        return
    await clear_user(uid, "به دلیل بن شدن")
    banned.append(uid)
    save()
    await update.message.reply_text(f"✅ کاربر {uid} بن شد.")

async def unban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("فرمت: /unban [user_id]")
        return
    if uid not in banned:
        await update.message.reply_text("بن نیست.")
        return
    banned.remove(uid)
    save()
    await update.message.reply_text(f"✅ کاربر {uid} آنبن شد.")

async def restore_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("فرمت: /restore [user_id]")
        return
    if uid not in force:
        await update.message.reply_text(f"❌ کاربر {uid} کشوری ندارد که به زور گرفته شده باشد.")
        return
    c = force[uid]
    if c in taken:
        await update.message.reply_text(f"❌ کشور {c} قبلاً توسط شخص دیگری گرفته شده.")
        return
    taken[c] = uid
    del force[uid]
    save()
    await update.message.reply_text(f"✅ کشور {c} به کاربر {uid} بازگردانده شد.")

async def list_banned_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    if not banned:
        await update.message.reply_text("هیچ کس بن نیست.")
        return
    await update.message.reply_text("📋 لیست بن‌ها:\n" + "\n".join([f"🆔 {u}" for u in banned]))

async def list_cmd(update, context):
    await update.message.reply_text(f"📋 لیست کشورها:\n{show_list()}", parse_mode="HTML")

async def admin_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    action = parts[0]
    if action == "clear":
        uid = query.from_user.id
        if parts[1] == "req":
            if is_banned(uid):
                await query.edit_message_text("⛔ بن هستید.")
                return
            c = user_country(uid)
            if not c:
                await query.edit_message_text("کشوری ندارید.")
                return
            kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clear_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clear_no_{uid}")]]
            await query.edit_message_text(f"⚠️ مطمئنی؟", reply_markup=InlineKeyboardMarkup(kb))
        elif parts[1] == "yes":
            await clear_user(uid, "توسط کاربر")
            await query.edit_message_text(f"🗑️ کشور خالی شد.\n📊 {MAX_REG - reg_count(uid)} بار باقی‌مانده.")
        else:
            await query.edit_message_text("لغو شد.")
        return
    uid = int(parts[1])
    if uid not in pend:
        await query.edit_message_text("منقضی شده.")
        return
    p = pend[uid]
    if action == "allow":
        p["status"] = "waiting_for_payment"
        save()
        c = p["country"]
        await context.bot.send_message(chat_id=uid, text=f"✅ مجوز خرید {c} صادر شد.\nشماره کارت: {CARD}\nبه نام {CARD_HOLDER}\nپس از واریز، فیش رو بفرست.")
        await query.edit_message_text(f"✅ مجوز صادر شد.")
    else:
        del pend[uid]
        save()
        await context.bot.send_message(chat_id=uid, text="❌ درخواست شما رد شد.")
        await query.edit_message_text("رد شد.")

async def handle_photo(update, context):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ بن هستید.")
        return
    if uid not in pend:
        await update.message.reply_text("درخواستی ندارید.")
        return
    p = pend[uid]
    if p["status"] != "waiting_for_payment":
        await update.message.reply_text("در مرحله دیگری هستید.")
        return
    photo_file = await update.message.photo[-1].get_file()
    path = f"receipt_{uid}.jpg"
    await photo_file.download_to_drive(path)
    p["status"] = "waiting_for_final_approval"
    p["photo_path"] = path
    save()
    kb = [[InlineKeyboardButton("✅ تأیید", callback_data=f"final_accept_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"final_reject_{uid}")]]
    caption = f"فیش پرداخت\nکاربر: {p['first_name']}\nکشور: {p['country']}\n🆔 <code>{uid}</code>"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=open(path, "rb"), caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    await update.message.reply_text("✅ فیش ارسال شد. منتظر تأیید باشید.")

async def final_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    action = parts[1]
    uid = int(parts[2])
    if uid not in pend:
        await query.edit_message_caption(caption="منقضی شده.")
        return
    p = pend[uid]
    if p["status"] != "waiting_for_final_approval":
        await query.edit_message_caption(caption="مرحله اشتباه.")
        return
    if action == "accept":
        c = p["country"]
        if is_banned(uid):
            del pend[uid]
            save()
            await query.edit_message_caption(caption="کاربر بن است.")
            return
        if is_locked(c):
            del pend[uid]
            save()
            await query.edit_message_caption(caption=f"❌ کشور {c} قفل است.")
            await context.bot.send_message(chat_id=uid, text=f"❌ کشور {c} قفل شده.")
            return
        if not can_reg(uid):
            del pend[uid]
            save()
            await query.edit_message_caption(caption=f"⛔ به حد مجاز رسیده.")
            await context.bot.send_message(chat_id=uid, text=f"⛔ به حد مجاز رسیده‌اید.")
            return
        taken[c] = uid
        count[uid] = reg_count(uid) + 1
        code = gen_code()
        codes.setdefault(uid, []).append(code)
        del pend[uid]
        save()
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ کشور {c} ثبت شد!\n🔑 کد: <code>{code}</code>\n📊 {MAX_REG - reg_count(uid)} بار باقی‌مانده.\n\n⚠️ این کد را به کسی ندهید.\nبرای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await query.edit_message_caption(caption=f"✅ {c} ثبت شد.")
        await notify(f"✅ - {c} پر شد")
        username = f"@{update.effective_user.username}" if update.effective_user.username else "ندارد"
        await app.bot.send_message(chat_id=ADMIN_ID, text=f"✅ {c} توسط {username} پر شد (پرداخت ویژه)\n🔑 <code>{code}</code>", parse_mode="HTML")
    else:
        del pend[uid]
        save()
        await context.bot.send_message(chat_id=uid, text="❌ پرداخت رد شد.")
        await query.edit_message_caption(caption="رد شد.")

# ========== راه‌اندازی ==========
def main():
    global app
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("forceclear", forceclear_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("list_banned", list_banned_cmd))
    app.add_handler(CommandHandler("restore", restore_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))
    app.add_handler(CommandHandler("reset_chance", reset_chance))  # دستور جدید
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(allow|deny|clear)_"))
    app.add_handler(CallbackQueryHandler(final_callback, pattern="^final_(accept|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ ربات با شماره‌گذاری اصلاح‌شده روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
