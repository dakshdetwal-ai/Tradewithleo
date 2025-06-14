import time
import requests
import json
import threading
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# === CONFIG ===
TRADINGVIEW_WEBHOOK_URL = "https://scanner.tradingview.com/crypto/scan"
TELEGRAM_TOKEN = "7989439298:AAH1Rs04aI1CVi0SOOCD6oYPpxdsDYGPkXw"
ADMIN_PANEL_CODE = "daksh.admin.panel"
UPI_ID = "dakshdetwal@fam"

# === STATE ===
users = {}
active_signal = None
cooldown = False

# === FUNCTION TO FETCH BTC/USDT PRICE FROM TRADINGVIEW ===
def fetch_btc_price():
    payload = {
        "symbols": {"tickers": ["BINANCE:BTCUSDT"], "query": {"types": []}},
        "columns": ["close"]
    }
    response = requests.post(TRADINGVIEW_WEBHOOK_URL, json=payload)
    price = response.json()['data'][0]['d'][0]
    return price

# === AI-BASED MOCK ANALYZER (SMC + TRAP LOGIC SIMULATION) ===
def analyze_market():
    global active_signal
    price = fetch_btc_price()
    direction = "LONG" if int(datetime.now().second) % 2 == 0 else "SHORT"
    if not active_signal:
        entry = round(price, 2)
        tp = round(price * (1.01 if direction == "LONG" else 0.99), 2)
        sl = round(price * (0.99 if direction == "LONG" else 1.01), 2)
        active_signal = {
            "direction": direction,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "time": datetime.now()
        }
        return active_signal
    else:
        current_price = price
        if active_signal['direction'] == "LONG" and current_price < active_signal['entry'] * 0.997:
            return "REVERSE"
        elif active_signal['direction'] == "SHORT" and current_price > active_signal['entry'] * 1.003:
            return "REVERSE"
    return None

# === SEND SIGNAL TO ALL USERS ===
async def send_signal_to_all_users(application):
    signal = analyze_market()
    if signal == "REVERSE":
        for user_id in users:
            await application.bot.send_message(chat_id=user_id, text="⚠️ Market direction has changed! Consider exiting your current position.")
        global active_signal
        active_signal = None
    elif isinstance(signal, dict):
        msg = f"""📈 *LEO Signal Alert*

✅ *Pair:* BTC/USDT
📊 *Direction:* {signal['direction']}
🔍 *Reason:* AI + SMC Strategy + Trap Logic
🎯 *Entry:* ${signal['entry']}
🎯 *TP:* ${signal['tp']}
🛡️ *SL:* ${signal['sl']}
🧠 *Technique:* SMC with Trap Identification
🕒 *Time:* {signal['time'].strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Use proper risk management.
"""
        for user_id in users:
            await application.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in users:
        users[user_id] = {
            "start_time": datetime.now(),
            "is_premium": False
        }
        await context.bot.send_message(chat_id=user_id, text="🤖 Welcome to Leo AI BTC/USDT Analyzer. You have a 1-hour free trial!")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = users.get(user_id)
    now = datetime.now()

    if not user:
        await start(update, context)
        return

    if user['is_premium'] or now - user['start_time'] < timedelta(hours=1):
        signal = active_signal
        if signal:
            msg = f"""📈 *LEO Signal Alert*

✅ *Pair:* BTC/USDT
📊 *Direction:* {signal['direction']}
🔍 *Reason:* AI + SMC Strategy + Trap Logic
🎯 *Entry:* ${signal['entry']}
🎯 *TP:* ${signal['tp']}
🛡️ *SL:* ${signal['sl']}
🧠 *Technique:* SMC with Trap Identification
🕒 *Time:* {signal['time'].strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Use proper risk management.
"""
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=user_id, text="🔎 No active signal right now. Please wait for next analysis.")
    else:
        await context.bot.send_message(chat_id=user_id, text=f"⏳ Your trial has expired! Please pay ₹59 (1 month) or ₹599 (12 months).\nSend your Chat ID + payment proof to 📧 collabxdaksh.com\n📥 UPI: {UPI_ID}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    message = update.message.text
    if message == ADMIN_PANEL_CODE:
        users[user_id] = {"start_time": datetime.now(), "is_premium": True}
        await context.bot.send_message(chat_id=user_id, text="✅ Admin code accepted! Lifetime access granted.")

# === SCHEDULER ===
def run_schedule(app):
    async def loop():
        while True:
            await send_signal_to_all_users(app)
            await asyncio.sleep(900)  # 15 minutes
    import asyncio
    asyncio.run(loop())

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    threading.Thread(target=run_schedule, args=(app,), daemon=True).start()

    print("🤖 Leo bot is running...")
    app.run_polling()
