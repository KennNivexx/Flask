from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
import os, time

app = Flask(__name__)
CORS(app)

DB_URI = "mysql+pymysql://root:poLaaimRkGHBdFcrCaiylBVZcXDbvGGn@metro.proxy.rlwy.net:49974/railway"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---- Helper: lazy engine dengan retry ----
def get_engine(retries=5, delay=2):
    for i in range(retries):
        try:
            engine = create_engine(DB_URI)
            # test connection
            with engine.connect() as conn:
                return engine
        except OperationalError:
            time.sleep(delay)
    raise Exception("Database tidak bisa connect setelah beberapa percobaan")

# ---- ROOT endpoint ----
@app.route("/")
def home():
    return jsonify({"status": "ok", "msg": "Backend jalan di Railway"})

# ---- API Tabel/kolom ----
@app.route("/api/tables")
def api_get_tables():
    engine = get_engine()
    insp = inspect(engine)
    tables = ["menu", "pesanan", "detail_pesanan"]
    all_columns = {}
    for table_name in tables:
        all_columns[table_name] = [
            {"name": col["name"], "type": str(col["type"])}
            for col in insp.get_columns(table_name)
        ]
    return jsonify(all_columns)

# ---- API Menu ----
@app.route("/api/menus", methods=["GET"])
def api_get_menus():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT id, nama, harga, COALESCE(gambar,'') AS gambar, kategori FROM menu ORDER BY id ASC")
        rows = [dict(r._mapping) for r in result]
    return jsonify(rows)

# ---- API Orders minimal ----
@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT * FROM pesanan ORDER BY created_at DESC")
        rows = [dict(r._mapping) for r in result]
    return jsonify(rows)

# ---- MAIN ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
