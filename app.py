from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8498415880:AAG5Yn6jhXRL85VpNCBkSL1-Y9nS7fL1w98"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

@app.route("/webhook/" + TOKEN, methods=["POST"])
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
