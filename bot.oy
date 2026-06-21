from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json
import os
import random
import string

TOKEN = "8905378875:AAHg4rVLYeY51xdKUDr7zA43jtxmCOUEIeE"
ADMIN_ID = 6106477309
CHANNEL_ID = -1004459846015
MESSAGE_ID = 2
MAX_REGISTRATIONS = 3
DATA_FILE = "bot_data.json"
app = None

FREE_COUNTRIES = ["آلمان", "فرانسه", "بریتانیا", "کانادا", "چین", "روسیه"]
PAID_COUNTRIES = {"آمریکا": {"price": 50, "card": "6219861815142665", "card_holder": "جوانمرد"},"ایران": {"price": 30, "card": "6219861815142665", "card_holder": "جوانمرد"}}
ALL_COUNTRIES = FREE_COUNTRIES + list(PAID_COUNTRIES.keys())

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"taken": {}, "pending": {}, "banned": [], "force_cleared": {}, "user_codes": {}, "registration_count": {}, "locked_countries": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"taken": taken, "pending": pend, "banned": banned, "force_cleared": force, "user_codes": codes, "registration_count": reg_count, "locked_countries": locked}, f, ensure_ascii=False, indent=2)

data = load_data()
taken, pend, banned, force, codes, reg_count, locked = data.get("taken", {}), data.get("pending", {}), data.get("banned", []), data.get("force_cleared", {}), data.get("user_codes", {}), data.get("registration_count", {}), data.get("locked_countries", [])

def get_user_country(user_id):
    for c, u in taken.items():
        if u == user_id:
            return c
    return None

def is_banned(user_id): return user_id in banned
def is_locked(country): return country in locked
def get_reg_count(user_id): return reg_count.get(user_id, 0)
def can_register(user_id): return get_reg_count(user_id) < MAX_REGISTRATIONS
def gen_code(): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def show_list():
    msg = "📋 لیست کشورها:\n\n"
    for i, c in enumerate(ALL_COUNTRIES, 1):
        if c in taken: st = "❌ گرفته شده"
        elif is_locked(c): st = "🔒 قفل شده"
        elif c in PAID_COUNTRIES: st = f"💰 ویژه - {PAID_COUNTRIES[c]['price']} تومان (نیاز به تأیید ادمین)"
        else: st = "✅ رایگان"
        msg += f"{i}. {c} → {st}\n"
    return msg

async def notify_channel(text):
    try:
        await app.bot.send_message(chat_id=CHANNEL_ID, text=text, reply_to_message_id=MESSAGE_ID, parse_mode="HTML")
    except Exception as e:
        print(f"خطا: {e}")

async def clear_user_country(user_id, reason="توسط کاربر"):
    c = get_user_country(user_id)
    if not c:
        return False
    del taken[c]
    if reason == "توسط ادمین":
        force[user_id] = c
    save_data()
    await notify_channel(f"❌ - {c} خالی شد ({reason})")
    try:
        await app.bot.send_message(chat_id=user_id, text=f"⚠️ کشور {c} {reason} خالی شد.", parse_mode="HTML")
    except:
        pass
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ شما بن هستید.")
        return
    rem = MAX_REGISTRATIONS - get_reg_count(uid)
    reg_info = f"\n\n📊 {rem} بار دیگر می‌توانید کشور بگیرید." if rem > 0 else "\n\n⛔ به حد مجاز رسیده‌اید."
    c = get_user_country(uid)
    if c:
        keyboard = [[InlineKeyboardButton("🗑️ خالی کردن کشور", callback_data=f"clear_req_{uid}")]]
        await update.message.reply_text(f"👋 کشور {c} رو دارید.{reg_info}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if rem <= 0:
        await update.message.reply_text("⛔ به حد مجاز رسیده‌اید.", parse_mode="HTML")
        return
    await update.message.reply_text(f"سلام! لیست کشورها:\n{show_list()}\nعدد مورد نظر رو بفرست.{reg_info}", parse_mode="HTML")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ بن هستید.")
        return
    c = get_user_country(uid)
    if not c:
        await update.message.reply_text("❌ کشوری ندارید.")
        return
    keyboard = [[InlineKeyboardButton("✅ بله", callback_data=f"clear_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clear_no_{uid}")]]
    await update.message.reply_text(f"⚠️ مطمئنی کشور {c} رو خالی کنی؟", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def force_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("فرمت: /forceclear [user_id]")
        return
    c = get_user_country(uid)
    if not c:
        await update.message.reply_text(f"کاربر {uid} کشوری ندارد.")
        return
    await clear_user_country(uid, "توسط ادمین")
    await update.message.reply_text(f"✅ کشور {c} از کاربر {uid} خالی شد.")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
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
    await clear_user_country(uid, "به دلیل بن شدن")
    banned.append(uid)
    save_data()
    await update.message.reply_text(f"✅ کاربر {uid} بن شد.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
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
    save_data()
    await update.message.reply_text(f"✅ کاربر {uid} آنبن شد.")

async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    if not banned:
        await update.message.reply_text("هیچ کس بن نیست.")
        return
    await update.message.reply_text("📋 لیست بن‌ها:\n" + "\n".join([f"🆔 {u}" for u in banned]))

async def list_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📋 لیست کشورها:\n{show_list()}", parse_mode="HTML")

async def restore_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
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
    save_data()
    await update.message.reply_text(f"✅ کشور {c} به کاربر {uid} بازگردانده شد.")

async def lock_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        c = " ".join(context.args)
        if not c:
            await update.message.reply_text("فرمت: /lock [نام کشور]")
            return
        if c not in ALL_COUNTRIES:
            await update.message.reply_text(f"کشور {c} وجود ندارد.")
            return
        if c in locked:
            await update.message.reply_text(f"🔒 کشور {c} قبلاً قفل است.")
            return
        locked.append(c)
        save_data()
        await update.message.reply_text(f"🔒 کشور {c} قفل شد.")
        await notify_channel(f"🔒 - {c} قفل شد")
    except:
        await update.message.reply_text("خطا!")

async def unlock_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    try:
        c = " ".join(context.args)
        if not c:
            await update.message.reply_text("فرمت: /unlock [نام کشور]")
            return
        if c not in ALL_COUNTRIES:
            await update.message.reply_text(f"کشور {c} وجود ندارد.")
            return
        if c not in locked:
            await update.message.reply_text(f"🔓 کشور {c} قفل نیست.")
            return
        locked.remove(c)
        save_data()
        await update.message.reply_text(f"🔓 کشور {c} باز شد.")
        await notify_channel(f"🔓 - {c} باز شد")
    except:
        await update.message.reply_text("خطا!")

async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
    uid = user.id
    if is_banned(uid):
        await update.message.reply_text("⛔ بن هستید.")
        return
    if not can_register(uid):
        await update.message.reply_text(f"⛔ به حد مجاز ({MAX_REGISTRATIONS} بار) رسیده‌اید.")
        return
    if uid in force:
        await update.message.reply_text(f"⛔ قبلاً کشور {force[uid]} توسط ادمین گرفته شد. فقط نمی‌توانید همان کشور را بگیرید.", parse_mode="HTML")
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("لطفاً عدد بفرست.")
        return
    index = int(text) - 1
    if index < 0 or index >= len(ALL_COUNTRIES):
        await update.message.reply_text("عدد نامعتبر.")
        return
    selected = ALL_COUNTRIES[index]
    if is_locked(selected):
        await update.message.reply_text(f"🔒 کشور {selected} قفل شده.")
        return
    if uid in force and force[uid] == selected:
        await update.message.reply_text(f"⛔ نمی‌توانید دوباره کشور {selected} را بگیرید.")
        return
    if get_user_country(uid):
        await update.message.reply_text("⚠️ قبلاً کشور گرفتی.")
        return
    if selected in taken:
        await update.message.reply_text(f"❌ کشور {selected} گرفته شده.")
        return
    if selected in FREE_COUNTRIES:
        taken[selected] = uid
        reg_count[uid] = get_reg_count(uid) + 1
        code = gen_code()
        codes.setdefault(uid, []).append(code)
        save_data()
        await update.message.reply_text(
            f"✅ کشور {selected} ثبت شد!\n🔑 کد: <code>{code}</code>\n📊 {MAX_REGISTRATIONS - get_reg_count(uid)} بار باقی‌مانده.\n\n⚠️ این کد را به کسی ندهید.\nبرای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await notify_channel(f"✅ - {selected} پر شد")
        username = f"@{user.username}" if user.username else "ندارد"
        await app.bot.send_message(chat_id=ADMIN_ID, text=f"📢 {selected} پر شد!\n👤 {user.first_name}\n🆔 <code>{uid}</code>\n👤 {username}\n🔑 <code>{code}</code>", parse_mode="HTML")
        return
    if selected in PAID_COUNTRIES:
        pend[uid] = {"country": selected, "username": user.username, "first_name": user.first_name, "status": "waiting_for_admin_approval", "chat_id": update.message.chat_id}
        save_data()
        keyboard = [[InlineKeyboardButton("✅ تأیید", callback_data=f"allow_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"deny_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"درخواست خرید {selected} از {user.first_name}", reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text(f"🔔 درخواست شما برای {selected} به ادمین ارسال شد.")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            c = get_user_country(uid)
            if not c:
                await query.edit_message_text("کشوری ندارید.")
                return
            keyboard = [[InlineKeyboardButton("✅ بله", callback_data=f"clear_yes_{uid}"), InlineKeyboardButton("❌ نه", callback_data=f"clear_no_{uid}")]]
            await query.edit_message_text(f"⚠️ مطمئنی؟", reply_markup=InlineKeyboardMarkup(keyboard))
        elif parts[1] == "yes":
            await clear_user_country(uid, "توسط کاربر")
            await query.edit_message_text(f"🗑️ کشور خالی شد.\n📊 {MAX_REGISTRATIONS - get_reg_count(uid)} بار باقی‌مانده.")
        elif parts[1] == "no":
            await query.edit_message_text("لغو شد.")
        return
    uid = int(parts[1])
    if uid not in pend:
        await query.edit_message_text("منقضی شده.")
        return
    p = pend[uid]
    if action == "allow":
        p["status"] = "waiting_for_payment"
        save_data()
        c = p["country"]
        await context.bot.send_message(chat_id=uid, text=f"✅ مجوز خرید {c} صادر شد.\nشماره کارت: {PAID_COUNTRIES[c]['card']}\nبه نام {PAID_COUNTRIES[c]['card_holder']}\nپس از واریز، فیش رو بفرست.")
        await query.edit_message_text(f"✅ مجوز صادر شد.")
    elif action == "deny":
        del pend[uid]
        save_data()
        await context.bot.send_message(chat_id=uid, text="❌ درخواست شما رد شد.")
        await query.edit_message_text("رد شد.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    file_path = f"receipt_{uid}.jpg"
    await photo_file.download_to_drive(file_path)
    p["status"] = "waiting_for_final_approval"
    p["photo_path"] = file_path
    save_data()
    keyboard = [[InlineKeyboardButton("✅ تأیید", callback_data=f"final_accept_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"final_reject_{uid}")]]
    caption = f"فیش پرداخت\nکاربر: {p['first_name']}\nکشور: {p['country']}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=open(file_path, "rb"), caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ فیش ارسال شد. منتظر تأیید باشید.")

async def handle_final_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            save_data()
            await query.edit_message_caption(caption="کاربر بن است.")
            return
        if is_locked(c):
            del pend[uid]
            save_data()
            await query.edit_message_caption(caption=f"❌ کشور {c} قفل است.")
            await context.bot.send_message(chat_id=uid, text=f"❌ کشور {c} قفل شده.")
            return
        if not can_register(uid):
            del pend[uid]
            save_data()
            await query.edit_message_caption(caption=f"⛔ به حد مجاز رسیده.")
            await context.bot.send_message(chat_id=uid, text=f"⛔ به حد مجاز رسیده‌اید.")
            return
        taken[c] = uid
        reg_count[uid] = get_reg_count(uid) + 1
        code = gen_code()
        codes.setdefault(uid, []).append(code)
        del pend[uid]
        save_data()
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ کشور {c} ثبت شد!\n🔑 کد: <code>{code}</code>\n📊 {MAX_REGISTRATIONS - get_reg_count(uid)} بار باقی‌مانده.\n\n⚠️ این کد را به کسی ندهید.\nبرای خالی کردن: /clear",
            parse_mode="HTML"
        )
        await query.edit_message_caption(caption=f"✅ {c} ثبت شد.")
        await notify_channel(f"✅ - {c} پر شد")
        user_obj = update.effective_user
        username = f"@{user_obj.username}" if user_obj and user_obj.username else "ندارد"
        await app.bot.send_message(chat_id=ADMIN_ID, text=f"✅ {c} توسط {username} پر شد (پرداخت ویژه)\n🔑 <code>{code}</code>", parse_mode="HTML")
    elif action == "reject":
        del pend[uid]
        save_data()
        await context.bot.send_message(chat_id=uid, text="❌ پرداخت رد شد.")
        await query.edit_message_caption(caption="رد شد.")

def main():
    global app
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("list", list_countries))
    app.add_handler(CommandHandler("forceclear", force_clear))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("list_banned", list_banned))
    app.add_handler(CommandHandler("restore", restore_country))
    app.add_handler(CommandHandler("lock", lock_country))
    app.add_handler(CommandHandler("unlock", unlock_country))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^(allow|deny|clear)_"))
    app.add_handler(CallbackQueryHandler(handle_final_callback, pattern="^final_(accept|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_country_selection))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ ربات روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
