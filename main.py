import os, requests, threading, time
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = os.environ.get("SIM5_KEY")
BASE = "https://5sim.net/v1"
H = {"Authorization": f"Bearer {SIM5}"}
TG = f"https://api.telegram.org/bot{TOKEN}"
EU = ["portugal","romania","estonia","poland","bulgaria","netherlands"]

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot ALIVE"

def tg(method, data):
    try:
        requests.post(f"{TG}/{method}", json=data, timeout=10)
    except:
        pass

def bot_loop():
    offset = 0
    while True:
        try:
            r = requests.get(f"{TG}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                if "message" in u and u["message"].get("text") == "/start":
                    cid = u["message"]["chat"]["id"]
                    kb = {"inline_keyboard": [[{"text":"🇪🇺 Europe Numbers","callback_data":"europe"}],[{"text":"💰 Balance","callback_data":"balance"}]]}
                    tg("sendMessage", {"chat_id": cid, "text": "Welcome PRO 5SIM Bot 🇪🇺\nEurope only!", "reply_markup": kb})
                if "callback_query" in u:
                    cb = u["callback_query"]
                    cid = cb["message"]["chat"]["id"]
                    mid = cb["message"]["message_id"]
                    data = cb["data"]
                    requests.post(f"{TG}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                    if data == "europe":
                        kb = {"inline_keyboard": [[{"text": c.title(), "callback_data": f"buy_{c}"}] for c in EU]}
                        tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": "🇪🇺 SELECT EUROPE:", "reply_markup": kb})
                    elif data.startswith("buy_"):
                        c = data.replace("buy_", "")
                        tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Buying {c}... ⏳"})
                        order = requests.get(f"{BASE}/user/buy/activation/{c}/any/whatsapp", headers=H, timeout=15).json()
                        if "id" in order:
                            kb = {"inline_keyboard": [[{"text":"📩 Get Code","callback_data": f"code_{order['id']}"}],[{"text":"❌ Cancel","callback_data": f"cancel_{order['id']}"}]]}
                            tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"✅ +{order['phone']}\nID: {order['id']}", "reply_markup": kb})
                        else:
                            tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"❌ {order}"})
                    elif data.startswith("code_"):
                        oid = data.replace("code_", "")
                        chk = requests.get(f"{BASE}/user/check/{oid}", headers=H, timeout=10).json()
                        if chk.get("sms"):
                            tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"✅ CODE: {chk['sms'][0]['code']}"})
                        else:
                            tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"⏳ Waiting... {chk.get('status')}"})
                    elif data.startswith("cancel_"):
                        oid = data.replace("cancel_", "")
                        requests.get(f"{BASE}/user/cancel/{oid}", headers=H)
                        tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": "✅ Refunded"})
                    elif data == "balance":
                        p = requests.get(f"{BASE}/user/profile", headers=H).json()
                        tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"💰 Balance: {p.get('balance')}"})
        except Exception as e:
            print(f"loop error {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
