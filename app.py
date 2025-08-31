from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from sqlalchemy import create_engine, inspect

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# ---- Database Config ----
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://root:poLaaimRkGHBdFcrCaiylBVZcXDbvGGn@metro.proxy.rlwy.net:49974/railway"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

engine = create_engine("mysql+pymysql://root:poLaaimRkGHBdFcrCaiylBVZcXDbvGGn@metro.proxy.rlwy.net:49974/railway")

insp = inspect(engine)

print("Tables:", insp.get_table_names())

# Daftar tabel yang kamu punya
tables = ["detail_pesanan", "menu", "pesanan"]

for table_name in tables:
    print(f"\nColumns for table '{table_name}':")
    for col in insp.get_columns(table_name):
        print(f"- {col['name']} ({col['type']})")
# ---- PAGES ----
@app.route("/")
def home():
    return "✅ Backend Jalan Brooo"

@app.route("/menu")
def page_menu():
    return render_template("menu.html")

@app.route("/penjual")
def page_penjual():
    return render_template("penjual.html")

# ---- API MENUS ----
@app.route("/api/menus", methods=["GET"])
def api_get_menus():
    with db.engine.connect() as conn:
        result = conn.execute(
            "SELECT id, nama, harga, COALESCE(gambar,'') AS gambar, kategori FROM menu ORDER BY id ASC"
        )
        rows = [dict(r._mapping) for r in result]
    return jsonify(rows)

@app.route("/api/menus", methods=["POST"])
def api_add_menu():
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    try:
        harga = int(data.get("harga") or 0)
    except:
        harga = 0
    gambar = (data.get("gambar") or "").strip() or None
    kategori = data.get("kategori") if data.get("kategori") in ("makanan","minuman","dessert") else "makanan"

    if not nama or harga <= 0:
        return jsonify({"ok": False, "msg": "Nama/harga tidak valid"}), 400

    with db.engine.begin() as conn:
        result = conn.execute(
            "INSERT INTO menu (nama,harga,gambar,kategori) VALUES (%s,%s,%s,%s)",
            (nama,harga,gambar,kategori)
        )
        menu_id = result.lastrowid
    return jsonify({"ok": True, "id": menu_id})

@app.route("/api/menus/<int:menu_id>", methods=["PATCH","PUT"])
def api_update_menu(menu_id):
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    try:
        harga = int(data.get("harga") or 0)
    except:
        harga = 0
    gambar = (data.get("gambar") or "").strip() or None
    kategori = data.get("kategori") if data.get("kategori") in ("makanan","minuman","dessert") else "makanan"

    with db.engine.begin() as conn:
        conn.execute(
            "UPDATE menu SET nama=%s, harga=%s, gambar=%s, kategori=%s WHERE id=%s",
            (nama,harga,gambar,kategori,menu_id)
        )
    return jsonify({"ok": True})

@app.route("/api/menus/<int:menu_id>", methods=["DELETE"])
def api_delete_menu(menu_id):
    with db.engine.begin() as conn:
        conn.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    return jsonify({"ok": True})

# ---- API ORDERS ----
@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    with db.engine.connect() as conn:
        result = conn.execute("SELECT * FROM pesanan ORDER BY created_at DESC")
        orders = [dict(r._mapping) for r in result]

        for o in orders:
            items = conn.execute(
                """
                SELECT d.jumlah, m.id AS menu_id, m.nama, m.harga, m.gambar
                FROM detail_pesanan d
                JOIN menu m ON m.id = d.menu_id
                WHERE d.pesanan_id = %s
                """,
                (o["id"],)
            )
            o["items"] = [dict(r._mapping) for r in items]
    return jsonify(orders)

@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.get_json(force=True, silent=True) or {}
    nama = (data.get("nama") or data.get("nama_pembeli") or "").strip()
    nomor_meja = (data.get("nomorMeja") or data.get("nomor_meja") or "").strip()
    cart = data.get("cart") or data.get("items") or []

    if not nama or not nomor_meja or not cart:
        return jsonify({"ok": False, "msg": "Data tidak lengkap"}), 400

    total = 0
    clean = []
    with db.engine.connect() as conn:
        for it in cart:
            try:
                menu_id = int(it.get("id"))
                qty = max(1, int(it.get("qty")))
            except:
                continue
            row = conn.execute("SELECT id, harga FROM menu WHERE id=%s", (menu_id,)).fetchone()
            if not row:
                continue
            total += int(row.harga) * qty
            clean.append({"menu_id": int(row.id), "qty": qty})

    if total <= 0 or not clean:
        return jsonify({"ok": False, "msg": "Keranjang kosong/invalid"}), 400

    with db.engine.begin() as conn:
        result = conn.execute(
            "INSERT INTO pesanan (nama_pembeli, nomor_meja, total, status, created_at) "
            "VALUES (%s,%s,%s,%s,NOW())",
            (nama, nomor_meja, total, "dibayar")
        )
        order_id = result.lastrowid
        for it in clean:
            conn.execute(
                "INSERT INTO detail_pesanan (pesanan_id, menu_id, jumlah) VALUES (%s,%s,%s)",
                (order_id, it["menu_id"], it["qty"])
            )
    return jsonify({"ok": True, "order_id": order_id, "total": total})

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def api_update_order_status(order_id):
    data = request.json or {}
    status = data.get("status")
    if status not in ("pending","dibayar","selesai"):
        return jsonify({"ok": False, "msg": "status invalid"}), 400
    with db.engine.begin() as conn:
        conn.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status, order_id))
    return jsonify({"ok": True})

@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
def api_delete_order(order_id):
    with db.engine.begin() as conn:
        conn.execute("DELETE FROM detail_pesanan WHERE pesanan_id=%s", (order_id,))
        conn.execute("DELETE FROM pesanan WHERE id=%s", (order_id,))
    return jsonify({"ok": True})

# ---- MAIN ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)



