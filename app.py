from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8498415880:AAG5Yn6jhXRL85VpNCBkSL1-Y9nS7fL1w98"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# API پایه DEX برای قیمت و لیکوییدیتی
DEX_API = "https://api.dexscreener.com/latest/dex/tokens/"

# حداقل پارامترها برای رد کردن اسکم
MIN_LIQUIDITY = 20000
MAX_TAX = 10
MIN_EXCHANGES = 2

# ---------------------------
# ارسال پیام به تلگرام
# ---------------------------
def send(chat_id, text):
    requests.post(SEND_URL, json={"chat_id": chat_id, "text": text})

# ---------------------------
# اسکن توکن و چک اسکم
# ---------------------------
def scan_token(contract, invest_amount=5):
    try:
        r = requests.get(DEX_API + contract).json()
        if "pairs" not in r or len(r["pairs"]) < MIN_EXCHANGES:
            return None

        pairs = r["pairs"]
        prices = []
        liquidity = []
        dex_names = []
        taxes = []

        for p in pairs:
            price = p.get("priceUsd")
            liq = p.get("liquidity", {}).get("usd", 0)
            buy_tax = p.get("buyTax", 0)
            sell_tax = p.get("sellTax", 0)
            dex = p.get("dexId", "Unknown")

            if price is None or liq < MIN_LIQUIDITY or buy_tax > MAX_TAX or sell_tax > MAX_TAX:
                continue

            prices.append(price)
            liquidity.append(liq)
            dex_names.append(dex)
            taxes.append((buy_tax, sell_tax))

        if len(prices) < 2:
            return None

        highest = max(prices)
        lowest = min(prices)
        diff_percent = (highest - lowest) / lowest * 100
        best_buy_index = prices.index(lowest)
        best_sell_index = prices.index(highest)

        profit = invest_amount * diff_percent / 100
        return {
            "contract": contract,
            "lowest": lowest,
            "highest": highest,
            "diff": diff_percent,
            "profit": profit,
            "buy_dex": dex_names[best_buy_index],
            "sell_dex": dex_names[best_sell_index],
            "liquidity": {dex_names[i]: liquidity[i] for i in range(len(dex_names))},
            "taxes": taxes[best_buy_index],
        }

    except:
        return None

# ---------------------------
# ربات تلگرام
# ---------------------------
@app.route("/", methods=["POST"])
def bot():
    data = request.get_json()
    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    if text.startswith("/scan"):
        parts = text.split(" ")
        if len(parts) < 2:
            send(chat_id, "مثال:\n/scan 0x123abc...")
            return "ok"

        contract = parts[1]
        send(chat_id, "⏳ درحال اسکن توکن...")

        result = scan_token(contract)
        if not result:
            send(chat_id, "❌ توکن پیدا نشد یا اسکم/لیکوییدیتی کم")
            return "ok"

        msg = f"""
🚨 فرصت آربیتراژ یافت شد 🚨

🔗 Contract:
{result['contract']}

💰 اختلاف قیمت: {result['diff']:.2f}%
💵 سود خالص روی 5$:
👉 {result['profit']:.4f} $

🛒 خرید از: {result['buy_dex']}
💸 فروش به: {result['sell_dex']}

📊 لیکوییدیتی:
"""
        for dex, liq in result["liquidity"].items():
            msg += f"{dex}: {liq}$\n"

        msg += f"\n🧾 Taxes:\nBuy: {result['taxes'][0]}%\nSell: {result['taxes'][1]}%"

        send(chat_id, msg)
        return "ok"

    send(chat_id, "پیامت رسید: " + text)
    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "Bot running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
