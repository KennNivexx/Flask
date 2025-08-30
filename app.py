from flask import Flask, jsonify
app = Flask(_name_)

@app.route("/")   # route test
def home():
    return "Backend works!"

@app.route("/api/menu")  # route API
def get_menu():
    return jsonify([{"name": "Nasi Goreng", "price": 15000}])
