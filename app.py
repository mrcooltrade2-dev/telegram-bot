from flask import Flask, request, render_template_string
import requests
import threading
import time

app = Flask(__name__)

# -----------------------------
# توکن تلگرام و سرمایه کاربر
# -----------------------------
TOKEN = "8498415880:AAG5Yn6jhXRL85VpNCBkSL1-Y9nS7fL1w98"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
USER_CAPITAL = 5  # دلاری که میخوای براش محاسبه بشه

# -----------------------------
# پارامترهای اسکن
# -----------------------------
DEX_LIST = ["PancakeSwap", "ApeSwap", "BabyDogeSwap", "Biswap", "MDEX", "Nomiswap"]
MIN_DIFF = 30
MIN_LIQUIDITY = 20000
MAX_TAX = 10
SCAN_INTERVAL = 30*60  # 30 دقیقه

history = []

# -----------------------------
# ارسال پیام تلگرام
# -----------------------------
def send_telegram(text):
    requests.post(SEND_URL, json={"chat_id": TOKEN.split(":")[0], "text": text})

# -----------------------------
# گرفتن لیست توکن‌ها از Dexscreener API
# -----------------------------
def get_bsc_tokens():
    try:
        url = "https://api.dexscreener.com/latest/dex/tokens/bsc"  # نمونه API
        r = requests.get(url).json()
        tokens = [t['address'] for t in r.get('pairs', [])]
        return list(set(tokens))  # حذف تکراری
    except:
        return []

# -----------------------------
# اسکن یک توکن
# -----------------------------
def scan_token(contract):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract}"
        r = requests.get(url).json()
        pairs = r.get("pairs", [])
        valid_pairs = []

        for p in pairs:
            dex = p.get("dexId")
            if dex not in DEX_LIST:
                continue
            price = p.get("priceUsd")
            liquidity = p.get("liquidity", {}).get("usd", 0)
            buy_tax = p.get("buyTax", 0)
            sell_tax = p.get("sellTax", 0)
            if price is None or liquidity < MIN_LIQUIDITY or buy_tax > MAX_TAX or sell_tax > MAX_TAX:
                continue
            valid_pairs.append({"dex": dex, "price": float(price), "liq": float(liquidity),
                                "buy_tax": buy_tax, "sell_tax": sell_tax})

        if len(valid_pairs) < 2:
            return None

        sorted_pairs = sorted(valid_pairs, key=lambda x: x["price"])
        buy = sorted_pairs[0]
        sell = sorted_pairs[-1]
        diff = (sell["price"] - buy["price"])/buy["price"]*100
        if diff < MIN_DIFF:
            return None

        profit = USER_CAPITAL * diff / 100
        max_trades = int(USER_CAPITAL / buy["price"]) if buy["price"] > 0 else 0

        return {
            "contract": contract,
            "diff": diff,
            "profit": profit,
            "buy_dex": buy["dex"],
            "sell_dex": sell["dex"],
            "liq": {p["dex"]: p["liq"] for p in valid_pairs},
            "tax": {"buy": buy["buy_tax"], "sell": sell["sell_tax"]},
            "max_trades": max_trades
        }

    except:
        return None

# -----------------------------
# اسکن دوره‌ای کل بازار
# -----------------------------
def auto_scan():
    while True:
        contracts = get_bsc_tokens()
        for c in contracts:
            res = scan_token(c)
            if res:
                msg = f"""
🚨 فرصت آربیتراژ یافت شد 🚨

🔗 Contract:
{res['contract']}

💰 اختلاف قیمت: {res['diff']:.2f}%

💵 سود خالص روی {USER_CAPITAL}$:
👉 {res['profit']:.4f} $

🛒 خرید از: {res['buy_dex']}
💸 فروش به: {res['sell_dex']}

📊 لیکوییدیتی:
"""
                for dex, liq in res["liq"].items():
                    msg += f"{dex}: {liq}$\n"

                msg += f"\n🧾 Taxes:\nBuy: {res['tax']['buy']}%\nSell: {res['tax']['sell']}%"
                msg += f"\n💹 تعداد دفعات قابل معامله: {res['max_trades']}"

                send_telegram(msg)

                history.insert(0, msg)
                if len(history) > 10:
                    history.pop()
        time.sleep(SCAN_INTERVAL)

# -----------------------------
# وبهوک تلگرام
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot running!"  
   @app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    data = request.get_json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(send_url, json={"chat_id": chat_id, "text": f"پیامت رسید: {text}"})
    return "ok"

# -----------------------------
# داشبورد وب ساده
# -----------------------------
@app.route("/dashboard")
def dashboard():
    html = """
<html>
<head><title>Arbitrage Dashboard</title>
<meta http-equiv="refresh" content="30">
</head>
<body>
<h2>آخرین فرصت‌های آربیتراژ</h2>
{% for item in history %}
<div style="border:1px solid #ccc; margin:5px; padding:5px; white-space: pre-line;">
{{ item }}
</div>
{% endfor %}
</body>
</html>
"""
    return render_template_string(html, history=history)

# -----------------------------
# اجرا
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=auto_scan).start()
    app.run(host="0.0.0.0", port=80)
