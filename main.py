import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask
import threading

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
API_5SIM = "YOUR_5SIM_API_KEY"
ADMIN_ID = 123456789

EUROPE_COUNTRIES = ["portugal", "romania", "estonia", "poland", "bulgaria", "netherlands"]

def get_balance_5sim():
    r = requests.get("https://5sim.net/v1/user/profile", headers={"Authorization": f"Bearer {API_5SIM}"}).json()
    return r.get("balance")

def buy_number(country, operator="any", product="whatsapp"):
    url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
    r = requests.get(url, headers={"Authorization": f"Bearer {API_5SIM}"}).json()
    return r

def get_sms(order_id):
    url = f"https://5sim.net/v1/user/check/{order_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {API_5SIM}"}).json()
    return r

def cancel_order(order_id):
    url = f"https://5sim.net/v1/user/cancel/{order_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {API_5SIM}"}).json()
    return r

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇪🇺 Europe Numbers", callback_data="europe")],
        [InlineKeyboardButton("💰 Check Balance", callback_data="balance")],
        [InlineKeyboardButton("📞 My Numbers", callback_data="my_numbers")],
        [InlineKeyboardButton("💬 Support", callback_data="support")]
    ]
    await update.message.reply_text(
        "Welcome to PRO 5SIM Bot 🇪🇺\nNo sleep, Instant delivery, Auto-refund",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def europe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for country in EUROPE_COUNTRIES:
        try:
            url = f"https://5sim.net/v1/guest/prices?product=whatsapp&country={country}"
            price_data = requests.get(url).json()
            price = price_data[country]['whatsapp'][0]['cost']
            keyboard.append([InlineKeyboardButton(f"{country.title()} - ${price}", callback_data=f"buy_{country}")])
        except:
            keyboard.append([InlineKeyboardButton(f"{country.title()}", callback_data=f"buy_{country}")])

    await query.edit_message_text(
        "🇪🇺 SELECT EUROPE COUNTRY:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    country = query.data.replace("buy_", "")
    await query.answer()
    await query.edit_message_text(f"Buying {country} number... ⏳")

    order = buy_number(country)
    if "id" in order:
        order_id = order["id"]
        phone = order["phone"]
        context.user_data['last_order'] = order_id

        keyboard = [
            [InlineKeyboardButton("📩 Get Code (/code)", callback_data=f"code_{order_id}")],
            [InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cancel_{order_id}")]
        ]
        await query.edit_message_text(
            f"✅ Number Bought!\n\nCountry: {country.title()}\nNumber: +{phone}\nID: {order_id}\n\nGo to WhatsApp and enter number. Then click Get Code.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(f"❌ Error: {order}")

async def code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = query.data.replace("code_", "")
    await query.answer()

    sms_data = get_sms(order_id)
    if sms_data.get("sms"):
        code = sms_data["sms"][0]["code"]
        await query.edit_message_text(f"✅ YOUR CODE: {code}\n\nUse am now! Then click Finish.")
    else:
        await query.edit_message_text(f"⏳ Waiting for SMS... Status: {sms_data.get('status')}\nTry again in 10 sec.\n\nIf e show BANNED, click Cancel for auto-refund.")

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = query.data.replace("cancel_", "")
    cancel_order(order_id)
    await query.edit_message_text(f"✅ Order {order_id} cancelled. Money refunded automatically to your balance!")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is ALIVE - No Sleep"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(europe, pattern="europe"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="buy_"))
    application.add_handler(CallbackQueryHandler(code_callback, pattern="code_"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="cancel_"))

    print("PRO BOT STARTED - No sleep")
    application.run_polling()
