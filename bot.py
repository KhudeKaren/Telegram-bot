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
TOKEN = "8846132875:AAEyWN026I6C1QgU8QQEjVaALCI4tasW350"
ADMIN_ID = 6106477309
CHANNEL_ID = -1004298773614
MSG_ID = 11
DATA_FILE = "bot_data.json"
app = None

# ========== لیست کشورها ==========
COUNTRIES = [
    "آمریکا", "بریتانیا", "فرانسه", "آلمان", "دانمارک", "ایتالیا", "کانادا",
    "لهستان", "هلند", "بلژیک", "پرتغال", "جمهوری چک", "مجارستان", "رومانی",
    "ترکیه", "روسیه", "هند", "برزیل", "آفریقای جنوبی", "ایران",
    "عربستان سعودی", "امارات متحده عربی", "مصر", "اتیوپی", "اندونزی",
    "کره جنوبی", "پاکستان", "اسرائیل", "تایلند", "ژاپن"
]

VIP = ["آمریکا", "روسیه", "چین", "ایران"]
VIP_PRICE = {"آمریکا": 50, "روسیه": 50, "چین": 50, "ایران": 30}
CARD = "6219861815142665"
CARD_HOLDER = "جوانمرد"

# ========== دیتابیس ==========
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "pending": {}, "vip_requests": {}}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump({"users": users, "pending": pending, "vip_requests": vip_requests}, f, ensure_ascii=False, indent=2)

data = load()
users = data.get("users", {})
pending = data.get("pending", {})
vip_requests = data.get("vip_requests", {})

def get_user_country(uid):
    return users.get(str(uid))

def is_admin(uid):
    return uid == ADMIN_ID

async def notify_channel(text, photo=None):
    try:
        if photo:
            await app.bot.send_photo(CHANNEL_ID, photo=photo, caption=text, parse_mode="HTML")
        else:
            await app.bot.send_message(CHANNEL_ID, text, reply_to_message_id=MSG_ID, parse_mode="HTML")
    except:
        pass

# ========== دستورات ادمین ==========
async def set_country(update, context):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    
    try:
        args = context.args
        if len(args) < 2:
            return await update.message.reply_text("فرمت: /set [user_id] [نام کشور]")
        
        uid = args[0]
        country = " ".join(args[1:])
        if country not in COUNTRIES:
            return await update.message.reply_text(f"کشور {country} در لیست نیست.")
        users[uid] = country
        save()
        await update.message.reply_text(f"✅ کاربر {uid} با کشور {country} ثبت شد.")
        try:
            await app.bot.send_message(int(uid), f"✅ شما به عنوان {country} ثبت شدید.")
        except:
            pass
    except:
        await update.message.reply_text("خطا! فرمت: /set [user_id] [نام کشور]")

async def list_users(update, context):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ شما اجازه این کار را ندارید.")
    if not users:
        return await update.message.reply_text("هیچ کاربری ثبت نشده.")
    msg = "📋 لیست کاربران:\n\n"
    for uid, country in users.items():
        msg += f"🆔 {uid} → {country}\n"
    await update.message.reply_text(msg)

# ========== دکمه‌های VIP ==========
async def vip_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[1]
    uid = data[2]
    
    if uid not in vip_requests:
        await query.edit_message_text("❌ این درخواست منقضی شده.")
        return
    
    info = vip_requests[uid]
    country = info["country"]
    user = info["user"]
    
    if action == "accept":
        price = VIP_PRICE.get(country, 50)
        await app.bot.send_message(
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
        await query.edit_message_text(f"✅ مجوز خرید {country} برای کاربر صادر شد.")
    else:
        await app.bot.send_message(int(uid), f"❌ درخواست شما برای {country} رد شد.")
        await query.edit_message_text(f"❌ درخواست {country} رد شد.")
        del vip_requests[uid]
        save()

# ========== دریافت فیش ==========
async def handle_receipt(update, context):
    uid = str(update.effective_user.id)
    
    if uid not in vip_requests or vip_requests[uid].get("status") != "waiting_for_payment":
        return False
    
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
    
    await app.bot.send_photo(
        ADMIN_ID,
        photo=open(path, "rb"),
        caption=f"📸 فیش پرداخت\n👤 {update.effective_user.first_name}\n🆔 {uid}\n🌍 {vip_requests[uid]['country']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.message.reply_text("✅ فیش شما ارسال شد. منتظر تأیید نهایی باشید.")
    return True

# ========== تأیید نهایی ==========
async def final_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[1]
    uid = data[2]
    
    if uid not in vip_requests:
        await query.edit_message_caption("❌ منقضی شده.")
        return
    
    info = vip_requests[uid]
    country = info["country"]
    
    if action == "accept":
        users[uid] = country
        await app.bot.send_message(int(uid), f"✅ کشور {country} برای شما ثبت شد!")
        await notify_channel(f"✅ - {country} پر شد")
        del vip_requests[uid]
        save()
        await query.edit_message_caption(f"✅ {country} برای کاربر ثبت شد.")
    else:
        await app.bot.send_message(int(uid), f"❌ پرداخت شما رد شد.")
        await query.edit_message_caption(f"❌ پرداخت رد شد.")
        del vip_requests[uid]
        save()

# ========== انتخاب کشور ==========
async def handle_selection(update, context):
    uid = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if not text.isdigit():
        return await update.message.reply_text("لطفاً عدد بفرست.")
    
    num = int(text) - 1
    if num < 0 or num >= len(COUNTRIES):
        return await update.message.reply_text(f"عدد بین ۱ تا {len(COUNTRIES)} باشه.")
    
    selected = COUNTRIES[num]
    
    if uid in users:
        return await update.message.reply_text("⚠️ شما قبلاً کشور دارید.")
    
    if selected in VIP:
        # درخواست VIP به ادمین
        vip_requests[uid] = {
            "country": selected,
            "user": update.effective_user,
            "status": "waiting_for_admin"
        }
        save()
        
        keyboard = [
            [InlineKeyboardButton("✅ تأیید", callback_data=f"vip_accept_{uid}")],
            [InlineKeyboardButton("❌ رد", callback_data=f"vip_reject_{uid}")]
        ]
        await app.bot.send_message(
            ADMIN_ID,
            f"📢 درخواست {selected}\n👤 {update.effective_user.first_name}\n🆔 {uid}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"🔔 درخواست شما برای {selected} به ادمین ارسال شد.")
    else:
        users[uid] = selected
        save()
        await update.message.reply_text(f"✅ کشور {selected} برای شما ثبت شد!")
        await notify_channel(f"✅ - {selected} پر شد")

# ========== راه‌اندازی ==========
def main():
    global app
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_country))
    app.add_handler(CommandHandler("list_users", list_users))
    
    app.add_handler(CallbackQueryHandler(vip_callback, pattern="^vip_(accept|reject)_"))
    app.add_handler(CallbackQueryHandler(final_callback, pattern="^final_(accept|reject)_"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    print("✅ ربات VIP با انتخاب عدد روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
