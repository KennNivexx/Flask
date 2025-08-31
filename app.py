from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# ===== Database Config =====
DB_USER = "root"
DB_PASS = "poLaaimRkGHBdFcrCaiylBVZcXDbvGGn"
DB_HOST = "metro.proxy.rlwy.net"
DB_PORT = 49974
DB_NAME = "railway"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:poLaaimRkGHBdFcrCaiylBVZcXDbvGGn@metro.proxy.rlwy.net:49974/railway"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===== MODELS =====
class Menu(db.Model):
    _tablename_ = "menu"
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    gambar = db.Column(db.String(255))
    kategori = db.Column(db.String(50), default="makanan")

class Pesanan(db.Model):
    _tablename_ = "pesanan"
    id = db.Column(db.Integer, primary_key=True)
    nama_pembeli = db.Column(db.String(255))
    nomor_meja = db.Column(db.String(50))
    total = db.Column(db.Integer)
    status = db.Column(db.String(50), default="dibayar")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship("DetailPesanan", backref="pesanan", cascade="all, delete-orphan")

class DetailPesanan(db.Model):
    _tablename_ = "detail_pesanan"
    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey("pesanan.id"))
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"))
    jumlah = db.Column(db.Integer, default=1)

# ===== ROUTES =====
@app.route("/")
def home():
    return print ({"✅ Backend Jalan Brooo": True})

# ---- API MENUS ----
@app.route("/api/menus", methods=["GET"])
def api_get_menus():
    menus = Menu.query.order_by(Menu.id).all()
    return jsonify([{
        "id": m.id,
        "nama": m.nama,
        "harga": m.harga,
        "gambar": m.gambar or "",
        "kategori": m.kategori
    } for m in menus])

@app.route("/api/menus", methods=["POST"])
def api_add_menu():
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    harga = int(data.get("harga") or 0)
    gambar = data.get("gambar") or None
    kategori = data.get("kategori") if data.get("kategori") in ("makanan","minuman","dessert") else "makanan"

    if not nama or harga <= 0:
        return jsonify({"ok": False, "msg": "Nama/harga tidak valid"}), 400

    m = Menu(nama=nama, harga=harga, gambar=gambar, kategori=kategori)
    db.session.add(m)
    db.session.commit()
    return jsonify({"ok": True, "id": m.id})

@app.route("/api/menus/<int:menu_id>", methods=["PATCH","PUT"])
def api_update_menu(menu_id):
    data = request.json or {}
    m = Menu.query.get(menu_id)
    if not m:
        return jsonify({"ok": False, "msg": "Menu tidak ditemukan"}), 404
    m.nama = data.get("nama", m.nama)
    m.harga = int(data.get("harga") or m.harga)
    m.gambar = data.get("gambar") or m.gambar
    m.kategori = data.get("kategori") or m.kategori
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/menus/<int:menu_id>", methods=["DELETE"])
def api_delete_menu(menu_id):
    m = Menu.query.get(menu_id)
    if m:
        db.session.delete(m)
        db.session.commit()
    return jsonify({"ok": True})

# ---- API ORDERS ----
@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    orders = Pesanan.query.order_by(Pesanan.created_at.desc()).all()
    out = []
    for o in orders:
        out.append({
            "id": o.id,
            "nama_pembeli": o.nama_pembeli,
            "nomor_meja": o.nomor_meja,
            "total": o.total,
            "status": o.status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{
                "menu_id": i.menu_id,
                "jumlah": i.jumlah,
                "nama": Menu.query.get(i.menu_id).nama,
                "harga": Menu.query.get(i.menu_id).harga,
                "gambar": Menu.query.get(i.menu_id).gambar
            } for i in o.items]
        })
    return jsonify(out)

@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.json or {}
    nama = data.get("nama") or ""
    nomor_meja = data.get("nomor_meja") or ""
    cart = data.get("cart") or []

    if not nama or not nomor_meja or not cart:
        return jsonify({"ok": False, "msg": "Data tidak lengkap"}), 400

    total = 0
    pesanan = Pesanan(nama_pembeli=nama, nomor_meja=nomor_meja, total=0)
    db.session.add(pesanan)
    db.session.flush()  # supaya dapat id

    for item in cart:
        menu = Menu.query.get(item["id"])
        if not menu:
            continue
        jumlah = max(1, int(item.get("qty", 1)))
        total += menu.harga * jumlah
        dp = DetailPesanan(pesanan_id=pesanan.id, menu_id=menu.id, jumlah=jumlah)
        db.session.add(dp)

    pesanan.total = total
    db.session.commit()
    return jsonify({"ok": True, "order_id": pesanan.id, "total": total})

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def api_update_order_status(order_id):
    data = request.json or {}
    status = data.get("status")
    o = Pesanan.query.get(order_id)
    if not o:
        return jsonify({"ok": False, "msg": "Order tidak ditemukan"}), 404
    if status not in ("pending","dibayar","selesai"):
        return jsonify({"ok": False, "msg": "status invalid"}), 400
    o.status = status
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
def api_delete_order(order_id):
    o = Pesanan.query.get(order_id)
    if o:
        db.session.delete(o)
        db.session.commit()
    return jsonify({"ok": True})

# ===== MAIN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


