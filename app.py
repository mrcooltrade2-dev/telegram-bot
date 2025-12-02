from flask import Flask, request, render_template_string
import requests
import threading
import time

app = Flask(__name__)

# ===========================
# 🔐 تنظیمات اصلی
# ===========================
TOKEN = "8498415880:AAG5Yn6jhXRL85VpNCBkSL1-Y9nS7fL1w98"
CHAT_ID = "1317187522"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

USER_CAPITAL = 5

# ===========================
# ⚙️ تنظیمات اسکن
# ===========================
DEX_LIST = ["pancakeswap", "apeswap", "babydogeswap", "biswap", "mdex", "nomiswap"]
MIN_DIFF = 30
MIN_LIQ = 20000
MAX_TAX = 10
SCAN_INTERVAL = 90

history = []


# ===========================
# 📩 ارسال پیام تلگرام
# ===========================
def send_telegram(text):
    try:
        requests.post(SEND_URL, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except:
        pass


# ===========================
# 🔄 نگه داشتن Render بیدار
# ===========================
def keep_alive():
    while True:
        try:
            requests.get("https://telegram-bot-5iz6.onrender.com/")
        except:
            pass
        time.sleep(40)


# ===========================
# 📡 گرفتن لیست توکن‌ها
# ===========================
def get_token_list():
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=bsc"
        r = requests.get(url, timeout=10).json()
        return list({p["baseToken"]["address"] for p in r.get("pairs", [])})
    except:
        return []


# ===========================
# 🔎 اسکن هر توکن
# ===========================
def scan_token(contract):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract}"
        r = requests.get(url, timeout=10).json()
        pairs = r.get("pairs", [])

        valid = []
        for p in pairs:
            dex = p.get("dexId", "").lower()
            if dex not in DEX_LIST:
                continue

            price = p.get("priceUsd")
            liq = p.get("liquidity", {}).get("usd", 0)
            buy_tax = p.get("buyTax", 0)
            sell_tax = p.get("sellTax", 0)

            if not price:
                continue
            if liq < MIN_LIQ or buy_tax > MAX_TAX or sell_tax > MAX_TAX:
                continue

            valid.append({
                "dex": dex,
                "price": float(price),
                "liq": float(liq),
                "buy_tax": buy_tax,
                "sell_tax": sell_tax
            })

        if len(valid) < 2:
            return None

        low = min(valid, key=lambda x: x["price"])
        high = max(valid, key=lambda x: x["price"])

        diff = (high["price"] - low["price"]) / low["price"] * 100
        if diff < MIN_DIFF:
            return None

        profit = USER_CAPITAL * diff / 100
        max_trades = int(USER_CAPITAL / low["price"])

        return {
            "contract": contract,
            "diff": diff,
            "profit": profit,
            "buy": low["dex"],
            "sell": high["dex"],
            "liq": {v["dex"]: v["liq"] for v in valid},
            "tax": {"buy": low["buy_tax"], "sell": high["sell_tax"]},
            "max_trades": max_trades
        }

    except:
        return None


# ===========================
# 🤖 اسکن خودکار
# ===========================
def auto_scan():
    time.sleep(5)
    send_telegram("♻️ اسکن خودکار فعال شد!")

    while True:
        tokens = get_token_list()

        for c in tokens:
            result = scan_token(c)
            if result:
                msg = f"""
🚨 *فرصت آربیتراژ پیدا شد* 🚨

🔗 *Contract:*  
`{result['contract']}`

💰 *اختلاف قیمت:* {result['diff']:.2f}%

💵 *سود روی {USER_CAPITAL}$:*  
👉 `{result['profit']:.4f}$`

🛒 *خرید از:* {result['buy']}
💸 *فروش به:* {result['sell']}

📊 *لیکوییدیتی:*
"""
                for d, l in result["liq"].items():
                    msg += f"- {d}: {l}$\n"

                msg += f"""
🧾 *Taxes:*  
Buy: {result['tax']['buy']}%  
Sell: {result['tax']['sell']}%

🔄 *تعداد دفعات معامله مجاز:* {result['max_trades']}
"""

                send_telegram(msg)

                history.insert(0, msg)
                if len(history) > 10:
                    history.pop()

        time.sleep(SCAN_INTERVAL)


# ===========================
# 🌐 روت‌های وب
# ===========================
@app.route("/")
def home():
    return "Bot Running"

@app.route("/dashboard")
def dashboard():
    html = """
    <html><body>
    <h2>آخرین فرصت‌های آربیتراژ</h2>
    {% for item in history %}
    <div style="border:1px solid #aaa;margin:6px;padding:6px;white-space:pre-line">
    {{ item }}
    </div>
    {% endfor %}
    </body></html>
    """
    return render_template_string(html, history=history)


@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    try:
        data = request.get_json()
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"پیامت رسید: {text}"}
        )
    except:
        pass
    return "ok"


# ===========================
# 🚀 اجرا
# ===========================
if __name__ == "__main__":
    threading.Thread(target=auto_scan).start()
    threading.Thread(target=keep_alive).start()
    app.run(host="0.0.0.0", port=10000)
