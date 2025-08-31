from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status":"ok"})

@app.route("/api/menus")
def menus():
    return jsonify([
        {"id":1,"nama":"Nasi Goreng","harga":15000,"kategori":"makanan","gambar":""},
        {"id":2,"nama":"Es Teh","harga":5000,"kategori":"minuman","gambar":""}
    ])

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
