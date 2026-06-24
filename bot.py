from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json, os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========== پورت ساختگی ==========
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

# ========== لیست جدید ۳۰ کشور (طبق درخواست شما) ==========
COUNTRIES = [
    "آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا",
    "لهستان", "هلند", "پرتغال", "اسپانیا", "رومانی", "ژاپن", "کره جنوبی", "اسرائیل",
    "روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران", "چین",
    "پاکستان", "عربستان سعودی", "امارات متحده عربی", "مصر",
    "استرالیا", "اندونزی", "ترکیه", "تایلند", "ویتنام"
]

PAID = {"آمریکا": 50, "روسیه": 50, "چین": 50, "ایران": 25}
FREE = [c for c in COUNTRIES if c not in PAID]
CARD = "6219861815142665"
CARD_HOLDER = "جوانمرد"

# ========== دیتابیس ==========
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"taken": {}, "pending": {}, "banned": [], "force": {}, "count": {}, "locked": [], "vip_requests": {}}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump({"taken": taken, "pending": pending, "banned": banned, "force": force, "count": count, "locked": locked, "vip_requests": vip_requests}, f, ensure_ascii=False, indent=2)

data = load()
taken = data.get("taken", {})
pending = data.get("pending", {})
banned = data.get("banned", [])
force = data.get("force", {})
count = data.get("count", {})
locked = data.get("locked", [])
vip_requests = data.get("vip_requests", {})

# ========== توابع کمکی ==========
def u_c(uid):
    for c, u in taken.items():
        if str(u) == str(uid):
            return c
    return None

def is_banned(uid):
    return int(uid) in banned

def is_locked(c):
    return c in locked

def show_list():
    groups = [
        ("🟦 NATO 🟦", ["آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا", "لهستان", "هلند", "پرتغال", "اسپانیا", "رومانی", "ژاپن", "کره جنوبی", "اسرائیل"]),
        ("🟥 BRICS 🟥", ["روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران", "چین", "پاکستان", "عربستان سعودی", "امارات متحده عربی", "مصر", "استرالیا", "اندونزی", "ترکیه", "تایلند", "ویتنام"])
    ]
    msg = "🌍 **لیست کشورها (عدد بفرستید):**\n\n"
    for title, countries in groups:
        msg += f"{title}\n"
        for c in countries:
            num = COUNTRIES.index(c) + 1
            if c in taken: s = "❌ گرفته"
            elif is_locked(c): s = "🔒 قفل"
            elif c in PAID: s = f"💰 {PAID[c]} هزار"
            else: s = "✅ رایگان"
            msg += f"{num}. {c} → {s}\n"
        msg += "\n"
    return msg

async def notify(text):
    try:
        await app.bot.send_message(CHANNEL_ID, text, reply_to_message_id=MSG_ID, parse_mode="HTML")
    except:
        pass

async def clear_user(uid, reason="توسط کاربر"):
    c = u_c(uid)
    if not c:
        return False
    del taken[c]
    if reason == "توسط ادمین":
        force[str(uid)] = c
    save()
    await notify(f"❌ - {c} خالی شد ({reason})")
    try:
        await app.bot.send_message(int(uid), f"⚠️ کشور {c} {reason} خالی شد.", parse_mode="HTML")
    except:
        pass
    return True

# ========== start ==========
async def start(update, context):
    u = update.effective_user
    if not u:
        return
    uid = u.id
    if is_banned(uid):
        return await update.message.reply_text("⛔ شما بن هستید.")
    c = u_c(uid)
    rem = MAX_REG - count.get(str(uid), 0)
    if c:
        kb = [[InlineKeyboardButton("🗑️ خالی کردن", callback_data=f"clr_req_{uid}")]]
        return await update.message.reply_text(
            f"👋 شما به عنوان **{c}** ثبت شده‌اید.\n"
            f"📊 {rem} بار دیگر می‌توانید ثبت‌نام کنید.\n"
            f"برای خالی کردن: /clear",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
    if rem <= 0:
        return await update.message.reply_text("⛔ به حد مجاز رسیدید.", parse_mode="HTML")
    await update.message.reply_text(f"{show_list()}\nعدد مورد نظر را بفرستید.\n📊 {rem} بار باقی‌مانده.", parse_mode="HTML")

# ========== clear ==========
async def clear_cmd(update, context):
    u = update.effective_user
    if not u:
        return
    uid = u.id
    if is_banned(uid):
        return await update.message.reply_text("⛔ بن هستید.")
    c = u_c(uid)
    if not c:
        return await update.message.reply_text("❌ کشوری ندارید.")
    kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clr_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clr_no_{uid}")]]
    await update.message.reply_text(f"⚠️ کشور {c} رو خالی کنی؟", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# ========== دستورات ادمین ==========
async def set_country(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    try:
        args = context.args
        if len(args) < 2:
            return await update.message.reply_text("فرمت: /set [user_id] [نام کشور]")
        uid = args[0]
        country = " ".join(args[1:])
        if country not in COUNTRIES:
            return await update.message.reply_text(f"کشور {country} در لیست نیست.")
        if is_locked(country):
            return await update.message.reply_text(f"🔒 کشور {country} قفل است.")
        if country in taken:
            return await update.message.reply_text(f"❌ کشور {country} قبلاً گرفته شده.")
        taken[country] = uid
        count[str(uid)] = count.get(str(uid), 0) + 1
        save()
        await update.message.reply_text(f"✅ کاربر {uid} با کشور {country} ثبت شد.")
        await notify(f"✅ - {country} پر شد")
        try:
            await app.bot.send_message(
                int(uid),
                f"✅ شما به عنوان **{country}** ثبت شدید.\n\n"
                f"برای خالی کردن کشور، از دستور `/clear` استفاده کنید.",
                parse_mode="HTML"
            )
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def remove_user(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    try:
        uid = context.args[0]
        c = u_c(uid)
        if not c:
            return await update.message.reply_text(f"کاربر {uid} ثبت نشده.")
        del taken[c]
        if str(uid) in count:
            del count[str(uid)]
        save()
        await update.message.reply_text(f"✅ کاربر {uid} حذف شد.")
        try:
            await app.bot.send_message(int(uid), "❌ شما از ربات حذف شدید.")
        except:
            pass
    except:
        await update.message.reply_text("فرمت: /remove [user_id]")

async def list_users(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    if not taken:
        return await update.message.reply_text("هیچ کاربری ثبت نشده.")
    msg = "📋 لیست کاربران:\n\n"
    for country, uid in taken.items():
        msg += f"🆔 {uid} → {country}\n"
    await update.message.reply_text(msg)

# ========== لاک ==========
async def lock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    c = " ".join(context.args)
    if not c or c not in COUNTRIES:
        return await update.message.reply_text("فرمت: /lock [کشور]")
    if c in locked:
        return await update.message.reply_text(f"🔒 {c} قفل است.")
    locked.append(c)
    save()
    await update.message.reply_text(f"🔒 {c} قفل شد.")
    await notify(f"🔒 - {c} قفل شد")

async def unlock_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    c = " ".join(context.args)
    if not c or c not in COUNTRIES:
        return await update.message.reply_text("فرمت: /unlock [کشور]")
    if c not in locked:
        return await update.message.reply_text(f"🔓 {c} قفل نیست.")
    locked.remove(c)
    save()
    await update.message.reply_text(f"🔓 {c} باز شد.")
    await notify(f"🔓 - {c} باز شد")

# ========== بن ==========
async def ban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if uid in banned:
            return await update.message.reply_text("قبلاً بن شده.")
        await clear_user(uid, "به دلیل بن شدن")
        banned.append(uid)
        save()
        await update.message.reply_text(f"✅ {uid} بن شد.")
    except:
        await update.message.reply_text("فرمت: /ban [user_id]")

async def unban_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if uid not in banned:
            return await update.message.reply_text("بن نیست.")
        banned.remove(uid)
        save()
        await update.message.reply_text(f"✅ {uid} آنبن شد.")
    except:
        await update.message.reply_text("فرمت: /unban [user_id]")

async def list_banned_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    await update.message.reply_text("📋 بن‌ها:\n" + "\n".join([f"🆔 {u}" for u in banned]) if banned else "هیچ کس بن نیست.")

async def forceclear_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        c = u_c(uid)
        if not c:
            return await update.message.reply_text(f"کاربر {uid} کشوری ندارد.")
        await clear_user(uid, "توسط ادمین")
        await update.message.reply_text(f"✅ {c} از {uid} خالی شد.")
    except:
        await update.message.reply_text("فرمت: /forceclear [user_id]")

async def restore_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        if str(uid) not in force:
            return await update.message.reply_text(f"❌ کاربر {uid} کشوری ندارد که به زور گرفته شده باشد.")
        c = force[str(uid)]
        if c in taken:
            return await update.message.reply_text(f"❌ {c} گرفته شده.")
        taken[c] = uid
        del force[str(uid)]
        save()
        await update.message.reply_text(f"✅ {c} به {uid} برگشت.")
    except:
        await update.message.reply_text("فرمت: /restore [user_id]")

async def reset_chance(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی ندارید.")
    try:
        uid = int(context.args[0])
        count[str(uid)] = 0
        save()
        await update.message.reply_text(f"✅ شانس کاربر {uid} ریست شد.")
    except:
        await update.message.reply_text("فرمت: /reset_chance [user_id]")

async def list_cmd(update, context):
    await update.message.reply_text(f"{show_list()}", parse_mode="HTML")

# ========== VIP ==========
async def vip_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data.split("_")
    action = data[1]
    uid = data[2]
    
    if uid not in vip_requests:
        await q.edit_message_text("❌ این درخواست منقضی شده.")
        return
    
    info = vip_requests[uid]
    country = info["country"]
    
    if action == "accept":
        price = PAID.get(country, 50)
        await context.bot.send_message(
            int(uid),
            f"✅ مجوز خرید {country} صادر شد!\n\n"
            f"💳 شماره کارت: `{CARD}`\n"
            f"👤 به نام: {CARD_HOLDER}\n"
            f"💰 مبلغ: {price} هزار تومان\n\n"
            f"📸 پس از واریز، تصویر فیش را ارسال کنید.",
            parse_mode="HTML"
        )
        vip_requests[uid]["status"] = "waiting_for_payment"
        save()
        await q.edit_message_text(f"✅ مجوز خرید {country} صادر شد.")
    else:
        await context.bot.send_message(int(uid), f"❌ درخواست شما برای {country} رد شد.")
        await q.edit_message_text(f"❌ درخواست {country} رد شد.")
        del vip_requests[uid]
        save()

async def handle_receipt(update, context):
    uid = str(update.effective_user.id)
    
    if uid not in vip_requests or vip_requests[uid].get("status") != "waiting_for_payment":
        # اگر کاربر درخواست VIP ندارد، بیانیه نیست پس نادیده بگیر
        return
    
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    path = f"receipt_{uid}.jpg"
    await photo_file.download_to_drive(path)
    
    vip_requests[uid]["status"] = "waiting_for_approval"
    vip_requests[uid]["photo"] = path
    save()
    
    keyboard = [
        [InlineKeyboardButton("✅ تأیید نهایی", callback_data=f"final_accept_{uid}")],
        [InlineKeyboardButton("❌ رد", callback_data=f"final_reject_{uid}")]
    ]
    
    await context.bot.send_photo(
        ADMIN_ID,
        photo=open(path, "rb"),
        caption=f"📸 فیش پرداخت\n👤 {update.effective_user.first_name}\n🆔 {uid}\n🌍 {vip_requests[uid]['country']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.message.reply_text("✅ فیش شما ارسال شد. منتظر تأیید نهایی باشید.")

async def final_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data.split("_")
    action = data[1]
    uid = data[2]
    
    if uid not in vip_requests:
        await q.edit_message_caption("❌ منقضی شده.")
        return
    
    info = vip_requests[uid]
    country = info["country"]
    
    if action == "accept":
        if is_locked(country):
            await context.bot.send_message(int(uid), f"❌ کشور {country} قفل است.")
            await q.edit_message_caption(f"❌ {country} قفل است.")
            del vip_requests[uid]
            save()
            return
        taken[country] = uid
        count[str(uid)] = count.get(str(uid), 0) + 1
        await context.bot.send_message(
            int(uid),
            f"✅ کشور {country} برای شما ثبت شد!\n\n"
            f"برای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await notify(f"✅ - {country} پر شد")
        del vip_requests[uid]
        save()
        await q.edit_message_caption(f"✅ {country} ثبت شد.")
    else:
        await context.bot.send_message(int(uid), f"❌ پرداخت شما رد شد.")
        await q.edit_message_caption(f"❌ رد شد.")
        del vip_requests[uid]
        save()

# ========== انتخاب کشور ==========
async def handle_selection(update, context):
    u = update.effective_user
    if not u:
        return
    uid = str(u.id)
    if is_banned(int(uid)):
        return await update.message.reply_text("⛔ بن هستید.")
    if count.get(uid, 0) >= MAX_REG:
        return await update.message.reply_text(f"⛔ به حد مجاز ({MAX_REG}) رسیدید.")
    text = update.message.text.strip()
    if not text.isdigit():
        return await update.message.reply_text("لطفاً عدد بفرست.")
    num = int(text) - 1
    if num < 0 or num >= len(COUNTRIES):
        return await update.message.reply_text(f"عدد بین ۱ تا {len(COUNTRIES)} باشه.")
    selected = COUNTRIES[num]
    if is_locked(selected):
        return await update.message.reply_text(f"🔒 {selected} قفل.")
    if uid in force and force[uid] == selected:
        return await update.message.reply_text(f"⛔ نمیتوانید {selected} را بگیرید.")
    if u_c(uid):
        return await update.message.reply_text("⚠️ قبلا کشور گرفتی.")
    if selected in taken:
        return await update.message.reply_text(f"❌ {selected} گرفته شده.")
    if selected in FREE:
        taken[selected] = uid
        count[uid] = count.get(uid, 0) + 1
        save()
        await update.message.reply_text(
            f"✅ کشور {selected} برای شما ثبت شد!\n"
            f"📊 {MAX_REG - count[uid]} بار دیگر می‌توانید ثبت‌نام کنید.\n"
            f"برای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await notify(f"✅ - {selected} پر شد")
        username = f"@{u.username}" if u.username else "ندارد"
        await context.bot.send_message(
            ADMIN_ID,
            f"📢 {selected} پر شد!\n👤 {u.first_name}\n🆔 {uid}\n👤 {username}",
            parse_mode="HTML"
        )
        return
    if selected in PAID:
        vip_requests[uid] = {
            "country": selected,
            "user": u,
            "status": "waiting_for_admin"
        }
        save()
        keyboard = [
            [InlineKeyboardButton("✅ تأیید", callback_data=f"vip_accept_{uid}")],
            [InlineKeyboardButton("❌ رد", callback_data=f"vip_reject_{uid}")]
        ]
        await context.bot.send_message(
            ADMIN_ID,
            f"📢 درخواست {selected}\n👤 {u.first_name}\n🆔 {uid}\n@{u.username if u.username else 'ندارد'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        await update.message.reply_text(f"🔔 درخواست شما برای {selected} به ادمین ارسال شد.")

# ========== دکمه‌های clear ==========
async def admin_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data.split("_")
    if data[0] == "clr":
        uid = q.from_user.id
        if data[1] == "req":
            if is_banned(uid):
                return await q.edit_message_text("⛔ بن هستید.")
            c = u_c(uid)
            if not c:
                return await q.edit_message_text("کشوری ندارید.")
            kb = [[InlineKeyboardButton("✅ بله", callback_data=f"clr_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clr_no_{uid}")]]
            await q.edit_message_text(f"⚠️ مطمئنی؟", reply_markup=InlineKeyboardMarkup(kb))
        elif data[1] == "yes":
            await clear_user(uid, "توسط کاربر")
            await q.edit_message_text(f"🗑️ خالی شد.\n📊 {MAX_REG - count.get(str(uid), 0)} بار مونده.")
        else:
            await q.edit_message_text("لغو شد.")
        return

async def list_users(update, context):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    
    if not users:
        return await update.message.reply_text("📋 هیچ کاربری ثبت نشده.")
    
    msg = "📋 **لیست کاربران ثبت‌شده:**\n\n"
    for uid, country in users.items():
        msg += f"🆔 {uid} → {country}\n"
    
    await update.message.reply_text(msg, parse_mode="HTML")

# ========== راه‌اندازی ==========
def main():
    global app
    app = Application.builder().token(TOKEN).build()
    for cmd, func in [
        ("start", start), ("clear", clear_cmd), ("list", list_cmd),
        ("set", set_country), ("remove", remove_user), ("list_users", list_users),
        ("forceclear", forceclear_cmd), ("restore", restore_cmd),
        ("ban", ban_cmd), ("unban", unban_cmd), ("list_banned", list_banned_cmd),
        ("lock", lock_cmd), ("unlock", unlock_cmd), ("reset_chance", reset_chance)
    ]:
        app.add_handler(CommandHandler(cmd, func))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^clr_"))
    app.add_handler(CallbackQueryHandler(vip_callback, pattern="^vip_(accept|reject)_"))
    app.add_handler(CallbackQueryHandler(final_callback, pattern="^final_(accept|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    print("✅ ربات کامل با VIP و لیست جدید روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
