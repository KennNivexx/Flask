from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(_name_)
CORS(app)

@app.route("/")
def home():
    return jsonify({"message": "✅ Flask jalan di Vercel!"})

# handler untuk vercel
def handler(request, response=None):
    return app(request.environ, start_response=lambda *args: None)
