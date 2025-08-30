from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, static_folder='static', template_folder='templates')

conn = mysql.connector.connect(
    host = sql312.infinityfree.com
    user = if0_39823849
    password = TXzWsbeNZO5MEV9
    database = if0_39823849_restoran

# ----- PAGES -----
@app.route("/")
def page_menu():
    return render_template("menu.html")

@app.route("/penjual")
def page_penjual():
    return render_template("penjual.html")

# ----- API menus -----
@app.route("/api/menus", methods=["GET"])
def api_get_menus():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nama, harga, COALESCE(gambar,'') AS gambar, kategori FROM menu ORDER BY id ASC")
    rows = cur.fetchall()
    cur.close(); conn.close()
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
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO menu (nama,harga,gambar,kategori) VALUES (%s,%s,%s,%s)", (nama,harga,gambar,kategori))
    menu_id = cur.lastrowid
    cur.close(); conn.close()
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
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE menu SET nama=%s, harga=%s, gambar=%s, kategori=%s WHERE id=%s",
                (nama,harga,gambar,kategori,menu_id))
    cur.close(); conn.close()
    return jsonify({"ok": True})

@app.route("/api/menus/<int:menu_id>", methods=["DELETE"])
def api_delete_menu(menu_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    cur.close(); conn.close()
    return jsonify({"ok": True})

# ----- API orders -----
@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM pesanan ORDER BY created_at DESC")
    orders = cur.fetchall()
    for o in orders:
        cur2 = conn.cursor(dictionary=True)
        cur2.execute("""
            SELECT d.jumlah, m.id AS menu_id, m.nama, m.harga, m.gambar
            FROM detail_pesanan d
            JOIN menu m ON m.id = d.menu_id
            WHERE d.pesanan_id = %s
        """, (o['id'],))
        o['items'] = cur2.fetchall()
        cur2.close()
    cur.close(); conn.close()
    return jsonify(orders)

@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.get_json(force=True, silent=True) or {}
    nama = (data.get("nama") or data.get("nama_pembeli") or "").strip()
    nomor_meja = (data.get("nomorMeja") or data.get("nomor_meja") or "").strip()
    cart = data.get("cart") or data.get("items") or []
    if not nama or not nomor_meja or not cart:
        return jsonify({"ok": False, "msg": "Data tidak lengkap"}), 400
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    total = 0
    clean = []
    for it in cart:
        try:
            menu_id = int(it.get("id"))
            qty = max(1, int(it.get("qty")))
        except:
            continue
        cur.execute("SELECT id, harga FROM menu WHERE id=%s", (menu_id,))
        row = cur.fetchone()
        if not row:
            continue
        total += int(row["harga"]) * qty
        clean.append({"menu_id": int(row["id"]), "qty": qty})
    if total <= 0 or not clean:
        cur.close(); conn.close()
        return jsonify({"ok": False, "msg": "Keranjang kosong/invalid"}), 400
    cur2 = conn.cursor()
    cur2.execute(
        "INSERT INTO pesanan (nama_pembeli, nomor_meja, total, status, created_at) "
        "VALUES (%s,%s,%s,%s,NOW())",
        (nama, nomor_meja, total, "dibayar")
    )
    order_id = cur2.lastrowid
    for it in clean:
        cur2.execute(
            "INSERT INTO detail_pesanan (pesanan_id, menu_id, jumlah) VALUES (%s,%s,%s)",
            (order_id, it["menu_id"], it["qty"])
        )
    conn.commit()
    cur2.close(); cur.close(); conn.close()
    return jsonify({"ok": True, "order_id": order_id, "total": total})

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def api_update_order_status(order_id):
    data = request.json or {}
    status = data.get("status")
    if status not in ("pending","dibayar","selesai"):
        return jsonify({"ok": False, "msg": "status invalid"}), 400
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status, order_id))
    cur.close(); conn.close()
    return jsonify({"ok": True})

@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
def api_delete_order(order_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM detail_pesanan WHERE pesanan_id=%s", (order_id,))
    cur.execute("DELETE FROM pesanan WHERE id=%s", (order_id,))
    cur.close(); conn.close()
    return jsonify({"ok": True})

if __name__ == "__main__":

    app.run(debug=True)

