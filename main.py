import os, requests, time
from threading import Thread
from flask import Flask
import telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = os.environ.get("SIM5_KEY")
BASE = "https://5sim.net/v1"
HEADERS = {"Authorization": f"Bearer {SIM5}"}
API = f"https://api.telegram.org/bot{TOKEN}"
EUROPE = ["portugal", "romania", "estonia", "poland", "bulgaria", "netherlands", "sweden"]

def send(cid, txt, markup=None):
    try:
        data = {"chat_id": cid, "text": txt, "parse_mode": "HTML"}
        if markup:
            import json
            data["reply_markup"] = json.dumps(markup.to_dict() if hasattr(markup, 'to_dict') else markup)
        requests.post(f"{API}/sendMessage", json=data, timeout=10)
    except:
        pass

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is ALIVE"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🇪🇺 Europe Numbers", callback_data="europe")],[InlineKeyboardButton("💰 Balance", callback_data="balance")]]
    await update.message.reply_text("Welcome to PRO 5SIM Bot 🇪🇺", reply_markup=InlineKeyboardMarkup(kb))

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "europe":
        kb = []
        for c in EUROPE:
            kb.append([InlineKeyboardButton(c.title(), callback_data=f"buy_{c}")])
        await q.edit_message_text("🇪🇺 SELECT EUROPE:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("buy_"):
        country = data.replace("buy_", "")
        await q.edit_message_text(f"Buying {country}... ⏳")
        try:
            r = requests.get(f"{BASE}/user/buy/activation/{country}/any/whatsapp", headers=HEADERS, timeout=15).json()
            if "id" in r:
                kb = [[InlineKeyboardButton("📩 Get Code", callback_data=f"code_{r['id']}")],[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{r['id']}")]]
                await q.edit_message_text(f"✅ Number: +{r['phone']}\nID: {r['id']}\nGo WhatsApp now!", reply_markup=InlineKeyboardMarkup(kb))
            else:
                await q.edit_message_text(f"❌ Error: {r}")
        except Exception as e:
            await q.edit_message_text(f"❌ Error: {e}")
    elif data.startswith("code_"):
        oid = data.replace("code_", "")
        try:
            r = requests.get(f"{BASE}/user/check/{oid}", headers=HEADERS, timeout=10).json()
            if r.get("sms"):
                await q.edit_message_text(f"✅ CODE: {r['sms'][0]['code']}")
            else:
                await q.edit_message_text(f"⏳ Waiting... Status: {r.get('status')}")
        except Exception as e:
            await q.edit_message_text(f"Error {e}")
    elif data.startswith("cancel_"):
        oid = data.replace("cancel_", "")
        requests.get(f"{BASE}/user/cancel/{oid}", headers=HEADERS)
        await q.edit_message_text("✅ Cancelled & Refunded")
    elif data == "balance":
        try:
            r = requests.get(f"{BASE}/user/profile", headers=HEADERS).json()
            await q.edit_message_text(f"💰 Balance: {r.get('balance')} RUB")
        except:
            await q.edit_message_text("Error balance")

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CallbackQueryHandler(btn_handler))
    application.run_polling()

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    time.sleep(2)
    run_bot()
