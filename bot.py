from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json, os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========== پورت ساختگی برای Render ==========
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy():
    try:
        HTTPServer(('0.0.0.0', 10000), DummyHandler).serve_forever()
    except: pass

Thread(target=run_dummy, daemon=True).start()

# ========== تنظیمات ==========
TOKEN = "8650429288:AAFuXGO0WfXR1PQfuxt1Q_gfKFDATtvZdMs"
ADMIN_ID = 6106477309
CHANNEL_ID = -1004298773614
MSG_ID = 11
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
PAID = {"آمریکا": 50, "روسیه": 50, "چین": 50, "ایران": 30}
FREE = [c for c in COUNTRIES if c not in PAID]
CARD = "6219861815142665"

# ========== دیتابیس ==========
def load():
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {"taken": {}, "pending": {}, "banned": [], "force": {}, "count": {}, "locked": []}

def save():
    json.dump({"taken": taken, "pending": pend, "banned": banned, "force": force, "count": count, "locked": locked}, open(DATA_FILE, "w"), ensure_ascii=False, indent=2)

data = load()
taken, pend, banned, force, count, locked = data.get("taken", {}), data.get("pending", {}), data.get("banned", []), data.get("force", {}), data.get("count", {}), data.get("locked", [])

# ========== توابع کمکی ==========
def u_c(uid): return next((c for c, u in taken.items() if u == uid), None)

def show_list():
    groups = [
        ("🟦 NATO 🟦", ["آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا", "لهستان", "هلند", "بلژیک", "پرتغال", "جمهوری چک", "مجارستان", "رومانی", "بلغارستان"]),
        ("🟥 BRICS 🟥", ["روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران", "عربستان سعودی", "امارات متحده عربی", "مصر", "اتیوپی", "اندونزی", "مالزی", "تایلند", "ویتنام", "قزاقستان", "نیجریه"]),
        ("🟩 GLOSA 🟩", ["چین", "ژاپن", "کره جنوبی", "پاکستان", "اسرائیل", "استرالیا", "اسپانیا", "سوئیس", "سوئد", "نروژ", "ترکیه", "فنلاند", "آرژانتین", "مکزیک", "شیلی"])
    ]
    msg = "📋 **لیست کشورها (عدد بفرستید):**\n\n"
    for title, countries in groups:
        msg += f"{title}\n"
        for c in countries:
            num = COUNTRIES.index(c) + 1
            if c in taken: s = "❌ گرفته"
            elif c in locked: s = "🔒 قفل"
            elif c in PAID: s = f"💰 {PAID[c]} هزار"
            else: s = "✅ رایگان"
            msg += f"{num}. {c} → {s}\n"
        msg += "\n"
    return msg

async def notify(text):
    try: await app.bot.send_message(CHANNEL_ID, text, reply_to_message_id=MSG_ID, parse_mode="HTML")
    except: pass

async def clear_user(uid, reason="توسط کاربر"):
    c = u_c(uid)
    if not c: return False
    del taken[c]
    if reason == "توسط ادمین": force[uid] = c
    save()
    await notify(f"❌ - {c} خالی شد ({reason})")
    try: await app.bot.send_message(uid, f"⚠️ کشور {c} {reason} خالی شد.", parse_mode="HTML")
    except: pass
    return True

# ========== دستورات ==========
async def start(update, context):
    u = update.effective_user
    if not u: return
    uid = u.id
    if uid in banned: return await update.message.reply_text("⛔ شما بن هستید.")
    c = u_c(uid)
    rem = MAX_REG - count.get(uid, 0)
    if c:
        kb = [[InlineKeyboardButton("🗑️ خالی کردن", callback_data=f"clr_req_{uid}")]]
        return await update.message.reply_text(f"👋 کشور {c} رو دارید.\n📊 {rem} بار مونده", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    if rem <= 0: return await update.message.reply_text("⛔ به حد مجاز رسیدید.", parse_mode="HTML")
    await update.message.reply_text(f"سلام!\n{show_list()}\nعدد بفرست.\n📊 {rem} بار مونده", parse_mode="HTML")

async def clear_cmd(update, context):
    u = update.effective_user
    if not u: return
    uid = u.id
    if uid in banned: return await update.message.reply_text("⛔ بن هستید.")
    c = u_c(uid)
    if not c: return await update.message.reply_text("❌ کشوری ندارید.")
    kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clr_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clr_no_{uid}")]]
    await update.message.reply_text(f"⚠️ کشور {c} رو خالی کنی؟", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def reset_chance(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        count[uid] = 0
        save()
        await update.message.reply_text(f"✅ شانس کاربر {uid} ریست شد.")
        try: await app.bot.send_message(uid, "✅ شانس شما توسط ادمین ریست شد.")
        except: pass
    except: await update.message.reply_text("فرمت: /reset_chance [user_id]")

async def lock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    c = " ".join(context.args)
    if not c or c not in COUNTRIES: return await update.message.reply_text("فرمت: /lock [کشور]")
    if c in locked: return await update.message.reply_text(f"🔒 {c} قفل است.")
    locked.append(c)
    save()
    await update.message.reply_text(f"🔒 {c} قفل شد.")
    await notify(f"🔒 - {c} قفل شد")

async def unlock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    c = " ".join(context.args)
    if not c or c not in COUNTRIES: return await update.message.reply_text("فرمت: /unlock [کشور]")
    if c not in locked: return await update.message.reply_text(f"🔓 {c} قفل نیست.")
    locked.remove(c)
    save()
    await update.message.reply_text(f"🔓 {c} باز شد.")
    await notify(f"🔓 - {c} باز شد")

async def forceclear_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        c = u_c(uid)
        if not c: return await update.message.reply_text(f"کاربر {uid} کشوری ندارد.")
        await clear_user(uid, "توسط ادمین")
        await update.message.reply_text(f"✅ {c} از {uid} خالی شد.")
    except: await update.message.reply_text("فرمت: /forceclear [user_id]")

async def ban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if uid in banned: return await update.message.reply_text("قبلاً بن شده.")
        await clear_user(uid, "به دلیل بن شدن")
        banned.append(uid)
        save()
        await update.message.reply_text(f"✅ {uid} بن شد.")
    except: await update.message.reply_text("فرمت: /ban [user_id]")

async def unban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if uid not in banned: return await update.message.reply_text("بن نیست.")
        banned.remove(uid)
        save()
        await update.message.reply_text(f"✅ {uid} آنبن شد.")
    except: await update.message.reply_text("فرمت: /unban [user_id]")

async def restore_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if uid not in force: return await update.message.reply_text(f"❌ کاربر {uid} کشوری ندارد.")
        c = force[uid]
        if c in taken: return await update.message.reply_text(f"❌ {c} گرفته شده.")
        taken[c] = uid
        del force[uid]
        save()
        await update.message.reply_text(f"✅ {c} به {uid} برگشت.")
    except: await update.message.reply_text("فرمت: /restore [user_id]")

async def list_banned_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return await update.message.reply_text("⛔ دسترسی ندارید.")
    await update.message.reply_text("📋 بن‌ها:\n" + "\n".join([f"🆔 {u}" for u in banned]) if banned else "هیچ کس بن نیست.")

async def list_cmd(update, context):
    await update.message.reply_text(f"📋 کشورها:\n{show_list()}", parse_mode="HTML")

# ========== انتخاب کشور ==========
async def handle_selection(update, context):
    u = update.effective_user
    if not u: return
    uid = u.id
    if uid in banned: return await update.message.reply_text("⛔ بن هستید.")
    if count.get(uid, 0) >= MAX_REG: return await update.message.reply_text(f"⛔ به حد مجاز ({MAX_REG}) رسیدید.")
    text = update.message.text.strip()
    if not text.isdigit(): return await update.message.reply_text("عدد بفرست.")
    num = int(text) - 1
    if num < 0 or num >= len(COUNTRIES): return await update.message.reply_text(f"عدد ۱ تا {len(COUNTRIES)} باشه.")
    selected = COUNTRIES[num]
    if selected in locked: return await update.message.reply_text(f"🔒 {selected} قفل.")
    if uid in force and force[uid] == selected: return await update.message.reply_text(f"⛔ نمیتوانید {selected} را بگیرید.")
    if u_c(uid): return await update.message.reply_text("⚠️ قبلا کشور گرفتی.")
    if selected in taken: return await update.message.reply_text(f"❌ {selected} گرفته شده.")
    if selected in FREE:
        taken[selected] = uid
        count[uid] = count.get(uid, 0) + 1
        save()
        await update.message.reply_text(f"✅ کشور {selected} برای شما ثبت شد!\n📊 {MAX_REG - count[uid]} بار دیگر می‌توانید ثبت‌نام کنید.\nبرای خالی کردن: /clear", parse_mode="HTML")
        await notify(f"✅ - {selected} پر شد")
        username = f"@{u.username}" if u.username else "ندارد"
        await app.bot.send_message(ADMIN_ID, f"📢 {selected} پر شد!\n👤 {u.first_name}\n🆔 {uid}\n👤 {username}", parse_mode="HTML")
        return
    if selected in PAID:
        pend[uid] = {"country": selected, "username": u.username, "first_name": u.first_name, "status": "waiting_for_admin_approval"}
        save()
        kb = [[InlineKeyboardButton("✅ تأیید", callback_data=f"allow_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"deny_{uid}")]]
        await context.bot.send_message(ADMIN_ID, f"📢 درخواست {selected}\n👤 {u.first_name}\n🆔 {uid}\n@{u.username if u.username else 'ندارد'}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        await update.message.reply_text(f"🔔 درخواست شما برای {selected} به ادمین ارسال شد.")

# ========== دکمه‌ها و فیش ==========
async def admin_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data.split("_")
    if data[0] == "clr":
        uid = q.from_user.id
        if data[1] == "req":
            if uid in banned: return await q.edit_message_text("⛔ بن هستید.")
            c = u_c(uid)
            if not c: return await q.edit_message_text("کشوری ندارید.")
            kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clr_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clr_no_{uid}")]]
            await q.edit_message_text(f"⚠️ مطمئنی؟", reply_markup=InlineKeyboardMarkup(kb))
        elif data[1] == "yes":
            await clear_user(uid, "توسط کاربر")
            await q.edit_message_text(f"🗑️ خالی شد.\n📊 {MAX_REG - count.get(uid, 0)} بار مونده.")
        else:
            await q.edit_message_text("لغو شد.")
        return
    uid = int(data[1])
    if uid not in pend: return await q.edit_message_text("منقضی شده.")
    p = pend[uid]
    if data[0] == "allow":
        p["status"] = "waiting_for_payment"
        save()
        c = p["country"]
        await context.bot.send_message(uid, f"✅ مجوز خرید {c} صادر شد.\nشماره کارت: {CARD}\nبه نام جوانمرد\nپس از واریز، فیش رو بفرست.")
        await q.edit_message_text(f"✅ مجوز صادر شد.")
    else:
        del pend[uid]
        save()
        await context.bot.send_message(uid, "❌ درخواست شما رد شد.")
        await q.edit_message_text("رد شد.")

async def handle_photo(update, context):
    u = update.effective_user
    if not u: return
    uid = u.id
    if uid in banned: return await update.message.reply_text("⛔ بن هستید.")
    if uid not in pend: return await update.message.reply_text("درخواستی ندارید.")
    p = pend[uid]
    if p["status"] != "waiting_for_payment": return await update.message.reply_text("در مرحله دیگری هستید.")
    photo = await update.message.photo[-1].get_file()
    path = f"receipt_{uid}.jpg"
    await photo.download_to_drive(path)
    p["status"] = "waiting_for_final_approval"
    save()
    kb = [[InlineKeyboardButton("✅ تأیید", callback_data=f"fin_accept_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"fin_reject_{uid}")]]
    await context.bot.send_photo(ADMIN_ID, photo=open(path, "rb"), caption=f"فیش پرداخت\nکاربر: {p['first_name']}\nکشور: {p['country']}\n🆔 {uid}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    await update.message.reply_text("✅ فیش ارسال شد. منتظر تأیید باشید.")

async def final_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data.split("_")
    uid = int(data[2])
    if uid not in pend: return await q.edit_message_caption("منقضی شده.")
    p = pend[uid]
    if p["status"] != "waiting_for_final_approval": return await q.edit_message_caption("مرحله اشتباه.")
    if data[1] == "accept":
        c = p["country"]
        if uid in banned or c in locked or count.get(uid, 0) >= MAX_REG:
            del pend[uid]
            save()
            return await q.edit_message_caption("خطا در ثبت.")
        taken[c] = uid
        count[uid] = count.get(uid, 0) + 1
        del pend[uid]
        save()
        await context.bot.send_message(uid, f"✅ کشور {c} برای شما ثبت شد!\n📊 {MAX_REG - count[uid]} بار دیگر می‌توانید ثبت‌نام کنید.\nبرای خالی کردن: /clear", parse_mode="HTML")
        await q.edit_message_caption(f"✅ {c} ثبت شد.")
        await notify(f"✅ - {c} پر شد")
        username = f"@{update.effective_user.username}" if update.effective_user.username else "ندارد"
        await app.bot.send_message(ADMIN_ID, f"✅ {c} توسط {username} (پرداخت ویژه)", parse_mode="HTML")
    else:
        del pend[uid]
        save()
        await context.bot.send_message(uid, "❌ پرداخت شما رد شد.")
        await q.edit_message_caption("رد شد.")

# ========== راه‌اندازی ==========
def main():
    global app
    app = Application.builder().token(TOKEN).build()
    for cmd, func in [("start", start), ("clear", clear_cmd), ("list", list_cmd), ("forceclear", forceclear_cmd), ("ban", ban_cmd), ("unban", unban_cmd), ("list_banned", list_banned_cmd), ("restore", restore_cmd), ("lock", lock_cmd), ("unlock", unlock_cmd), ("reset_chance", reset_chance)]:
        app.add_handler(CommandHandler(cmd, func))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(clr|allow|deny)_"))
    app.add_handler(CallbackQueryHandler(final_callback, pattern="^fin_(accept|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ ربات بدون کد اختصاصی روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
