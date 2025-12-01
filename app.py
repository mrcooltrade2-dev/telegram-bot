from flask import Flask, request
import requests

app = Flask(name)

TOKEN = "توکن_رباتت"  # جایگزین کن با توکن واقعی
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

@app.route("/", methods=["POST"])
def bot():
    data = request.get_json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    requests.post(URL, json={
        "chat_id": chat_id,
        "text": "پیامت رسید: " + text
    })

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

if name == "main":
    app.run(host="0.0.0.0", port=8080)
