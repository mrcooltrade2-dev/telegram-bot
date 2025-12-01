from flask import Flask, request
import requests

app = Flask(name)

TOKEN = "8498415880:AAG5Yn6jhXRL85VpNCBkSL1-Y9nS7fL1w98

" 
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
