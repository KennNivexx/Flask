from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(_name_, static_folder='static', template_folder='templates')
CORS(app)

# ---- Database Config ----
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql:/root:poLaaimRkGHBdFcrCaiylBVZcXDbvGGn@metro.proxy.rlwy.net:3306/railway"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---- MODELS ----
class Menu(db.Model):
    _tablename_ = "menu"
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    gambar = db.Column(db.String(255), nullable=True)
    kategori = db.Column(db.String(50), nullable=False)

class Pesanan(db.Model):
    _tablename_ = "pesanan"
    id = db.Column(db.Integer, primary_key=True)
    nama_pembeli = db.Column(db.String(255))
    nomor_meja = db.Column(db.String(50))
    total = db.Column(db.Integer)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class DetailPesanan(db.Model):
    _tablename_ = "detail_pesanan"
    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey("pesanan.id"))
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"))
    jumlah = db.Column(db.Integer)

# ---- PAGES ----
@app.route("/")
def home():
    return jsonify({"✅ Backend Jalan Brooo": True})

@app.route("/menu")
def page_menu():
    return render_template("menu.html")

@app.route("/penjual")
def page_penjual():
    return render_template("penjual.html")

# ---- API MENUS ----
@app.route("/api/menus", methods=["GET"])
def api_get_menus():
    menus = Menu.query.order_by(Menu.id.asc()).all()
    rows = [{
        "id": m.id,
        "nama": m.nama,
        "harga": m.harga,
        "gambar": m.gambar or "",
        "kategori": m.kategori
    } for m in menus]
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

    m = Menu(nama=nama, harga=harga, gambar=gambar, kategori=kategori)
    db.session.add(m)
    db.session.commit()
    return jsonify({"ok": True, "id": m.id})

# Update & Delete mirip, bisa ditambahkan sesuai versi kamu

# ---- API ORDERS ----
@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    orders = Pesanan.query.order_by(Pesanan.created_at.desc()).all()
    result = []
    for o in orders:
        items = DetailPesanan.query.filter_by(pesanan_id=o.id).all()
        item_list = []
        for i in items:
            menu = Menu.query.get(i.menu_id)
            item_list.append({
                "menu_id": menu.id,
                "nama": menu.nama,
                "harga": menu.harga,
                "jumlah": i.jumlah,
                "gambar": menu.gambar or ""
            })
        result.append({
            "id": o.id,
            "nama_pembeli": o.nama_pembeli,
            "nomor_meja": o.nomor_meja,
            "total": o.total,
            "status": o.status,
            "created_at": o.created_at,
            "items": item_list
        })
    return jsonify(result)

# Buat order baru
@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    nomor_meja = (data.get("nomor_meja") or "").strip()
    cart = data.get("cart") or []

    if not nama or not nomor_meja or not cart:
        return jsonify({"ok": False, "msg": "Data tidak lengkap"}), 400

    total = 0
    order_items = []
    for it in cart:
        menu = Menu.query.get(it["id"])
        if not menu:
            continue
        qty = max(1, int(it.get("qty", 1)))
        total += menu.harga * qty
        order_items.append({"menu": menu, "qty": qty})

    if total <= 0:
        return jsonify({"ok": False, "msg": "Keranjang kosong/invalid"}), 400

    order = Pesanan(nama_pembeli=nama, nomor_meja=nomor_meja, total=total, status="dibayar")
    db.session.add(order)
    db.session.commit()

    for i in order_items:
        dp = DetailPesanan(pesanan_id=order.id, menu_id=i["menu"].id, jumlah=i["qty"])
        db.session.add(dp)
    db.session.commit()
    return jsonify({"ok": True, "order_id": order.id, "total": total})

# ---- MAIN ----
if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    db.create_all()
    app.run(host="0.0.0.0", port=port)
