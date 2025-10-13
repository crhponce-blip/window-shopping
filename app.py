# =========================================================
# 🌐 WINDOW SHOPPING — Flask App Final (v3.3, Octubre 2025)
# Autor: Christopher Ponce & GPT-5
# =========================================================

import os
import sqlite3
from datetime import timedelta
from typing import List, Dict, Any
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort
)
from werkzeug.utils import secure_filename

# =========================================================
# 🔧 CONFIGURACIÓN BÁSICA
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.permanent_session_lifetime = timedelta(days=14)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Permitir subida de archivos (RUT / documentos)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    """Valida la extensión de archivos subidos."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# =========================================================
# 🧩 TIPOS Y ROLES (Reglas de creación de usuario)
# =========================================================
TIPOS_VALIDOS = {"compras", "servicios", "mixto", "compraventa"}

ROLES_POR_TIPO: Dict[str, List[str]] = {
    "compras": ["Cliente extranjero"],
    "servicios": ["Agencia de aduana", "Transporte", "Extraportuario", "Packing", "Frigorífico"],
    "compraventa": ["Productor(planta)", "Packing", "Frigorífico", "Exportador"],
    "mixto": ["Packing", "Frigorífico"],
}


# =========================================================
# 🗄️ BASE DE DATOS (SQLite) — Usuarios y autenticación
# =========================================================
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    """Crea la base y la tabla de usuarios si no existen."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            empresa TEXT,
            rol TEXT,
            tipo TEXT,
            pais TEXT,
            rut_doc TEXT
        )
    """)
    conn.commit()
    conn.close()

def migrate_add_rut_doc():
    """Asegura columna rut_doc (idempotente)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN rut_doc TEXT")
        conn.commit()
        print("🛠️ Migración: columna 'rut_doc' agregada a users.")
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

def get_user(email: str):
    """Obtiene un usuario por su email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(email, password, empresa, rol, tipo, pais, rut_doc=None):
    """Agrega un nuevo usuario al sistema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, password, empresa, rol, tipo, pais, rut_doc))
        conn.commit()
        print(f"🆕 Usuario creado: {email}")
    except sqlite3.IntegrityError:
        print(f"⚠️ El usuario {email} ya existe.")
    finally:
        conn.close()

# =========================================================
# 📁 SUBIDA DE ARCHIVOS
# =========================================================
def save_uploaded_file(file_storage) -> str | None:
    """
    Guarda un archivo subido en /static/uploads.
    Retorna la ruta relativa ("uploads/archivo.ext") o None si falla.
    """
    if not file_storage or file_storage.filename == "":
        return None
    if allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file_storage.save(save_path)
        print(f"📂 Archivo guardado: {save_path}")
        return f"uploads/{filename}"
    print("⚠️ Formato de archivo no permitido.")
    return None


# =========================================================
# 👤 SEMILLA — Admin + 2 usuarios por rol (visibilidad de data)
# =========================================================
def create_admin_if_missing():
    """Crea un usuario administrador si no existe."""
    if not get_user("admin@ws.com"):
        add_user(
            email="admin@ws.com",
            password="1234",
            empresa="Window Shopping Admin",
            rol="Exportador",
            tipo="compraventa",
            pais="CL",
            rut_doc=None,
        )
        print("✅ Usuario admin creado: admin@ws.com / 1234")

def seed_demo_users():
    """
    Inserta 2 usuarios por cada rol/tipo relevante
    (valida existencia para no duplicar).
    Password por defecto: 1234
    """
    seeds = [
        # compraventa
        ("prod1@demo.cl", "1234", "Productora Valle SpA", "Productor(planta)", "compraventa", "CL"),
        ("prod2@demo.cl", "1234", "Agro Cordillera Ltda.", "Productor(planta)", "compraventa", "CL"),
        ("pack1@demo.cl", "1234", "Packing Maule SpA", "Packing", "compraventa", "CL"),
        ("pack2@demo.cl", "1234", "Packing Sur SpA", "Packing", "compraventa", "CL"),
        ("frio1@demo.cl", "1234", "Frío Centro SpA", "Frigorífico", "compraventa", "CL"),
        ("frio2@demo.cl", "1234", "Patagonia Cold SA", "Frigorífico", "compraventa", "CL"),
        ("exp1@demo.cl", "1234", "Exportadora Andes", "Exportador", "compraventa", "CL"),
        ("exp2@demo.cl", "1234", "Exportadora Pacífico", "Exportador", "compraventa", "CL"),

        # servicios
        ("aduana1@demo.cl", "1234", "Agencia Andes", "Agencia de aduana", "servicios", "CL"),
        ("aduana2@demo.cl", "1234", "Agencia Sur", "Agencia de aduana", "servicios", "CL"),
        ("trans1@demo.cl", "1234", "Transporte Rápido", "Transporte", "servicios", "CL"),
        ("trans2@demo.cl", "1234", "Logística Express", "Transporte", "servicios", "CL"),
        ("extra1@demo.cl", "1234", "Extraportuario Norte", "Extraportuario", "servicios", "CL"),
        ("extra2@demo.cl", "1234", "Extraportuario Sur", "Extraportuario", "servicios", "CL"),

        # mixto
        ("mixpack1@demo.cl", "1234", "Mixto Packing Uno", "Packing", "mixto", "CL"),
        ("mixfrio1@demo.cl", "1234", "Mixto Frio Uno", "Frigorífico", "mixto", "CL"),

        # compras (cliente extranjero)
        ("cliente1@ext.com", "1234", "Importadora Asia Ltd.", "Cliente extranjero", "compras", "US"),
        ("cliente2@ext.com", "1234", "Global Retail HK", "Cliente extranjero", "compras", "HK"),

        # servicio-only con nombres alternos (si quieres más data)
        ("packserv1@demo.cl", "1234", "Packing Servicios SPA", "Packing", "servicios", "CL"),
        ("frioserv1@demo.cl", "1234", "Frío Servicios SPA", "Frigorífico", "servicios", "CL"),
    ]
    for email, pwd, empresa, rol, tipo, pais in seeds:
        if not get_user(email):
            add_user(email, pwd, empresa, rol, tipo, pais)
            print(f"🧑‍💼 Usuario ficticio agregado: {email}")

# Inicialización automática
init_db()
migrate_add_rut_doc()
create_admin_if_missing()
seed_demo_users()


# =========================================================
# 📦 PUBLICACIONES DEMO + Carrito + Ocultos (helpers)
# =========================================================
PUBLICACIONES: List[Dict[str, Any]] = [
    # Ofertas fruta
    {"id": "pub1", "usuario": "exp1@demo.cl", "tipo": "oferta", "rol": "Exportador",
     "empresa": "Exportadora Andes", "producto": "Cerezas Premium", "precio": "USD 7/kg",
     "descripcion": "Lapins 28+, condición exportación."},
    # Servicios
    {"id": "pub2", "usuario": "pack1@demo.cl", "tipo": "servicio", "rol": "Packing",
     "empresa": "Packing Maule SpA", "producto": "Servicio de Embalaje", "precio": "USD 0.50/kg",
     "descripcion": "Clamshell y flowpack. BRC/IFS."},
    {"id": "pub3", "usuario": "frio1@demo.cl", "tipo": "servicio", "rol": "Frigorífico",
     "empresa": "Frío Centro SpA", "producto": "Almacenamiento Refrigerado", "precio": "USD 0.20/kg",
     "descripcion": "Cámaras -1 a 10°C, AC, monitoreo 24/7."},
    {"id": "pub4", "usuario": "aduana1@demo.cl", "tipo": "servicio", "rol": "Agencia de aduana",
     "empresa": "Agencia Andes", "producto": "Tramitación Exportación", "precio": "USD 200/trámite",
     "descripcion": "DUS, MIC/DTA, doc y aforo."},
    # Demandas
    {"id": "pub5", "usuario": "cliente1@ext.com", "tipo": "demanda", "rol": "Cliente extranjero",
     "empresa": "Importadora Asia Ltd.", "producto": "Demanda Fruta Chilena", "precio": "Consultar",
     "descripcion": "Cereza, arándano y uva, semanas 46-3."},
]

def get_cart() -> List[Dict[str, Any]]:
    return session.setdefault("cart", [])

def save_cart(cart: List[Dict[str, Any]]) -> None:
    session["cart"] = cart

def add_to_cart(item: Dict[str, Any]) -> None:
    cart = get_cart()
    if not any(i.get("id") == item.get("id") for i in cart):
        cart.append(item)
        save_cart(cart)

def remove_from_cart(index: int) -> bool:
    cart = get_cart()
    if 0 <= index < len(cart):
        cart.pop(index)
        save_cart(cart)
        return True
    return False

def clear_cart() -> None:
    save_cart([])

def get_hidden_items() -> List[str]:
    return session.setdefault("hidden_items", [])

def hide_item(item_id: str) -> None:
    hidden = get_hidden_items()
    if item_id not in hidden:
        hidden.append(item_id)
        session["hidden_items"] = hidden

def unhide_all() -> None:
    session["hidden_items"] = []
# =========================================================
# 🔐 PERMISOS DE VISIBILIDAD
# =========================================================
PERMISOS: Dict[str, Dict[str, List[str]]] = {
    "fruta_oferta_visible_por_rol": {
        "Packing": ["Productor(planta)"],
        "Frigorífico": ["Productor(planta)", "Packing"],
        "Exportador": ["Productor(planta)", "Packing", "Frigorífico", "Exportador"],
        "Cliente extranjero": ["Exportador"],
        "Productor(planta)": ["Packing", "Frigorífico", "Exportador"],
        "Agencia de aduana": [], "Transporte": [], "Extraportuario": [],
    },
    "fruta_demanda_visible_por_rol": {
        "Productor(planta)": ["Exportador", "Packing", "Frigorífico", "Productor(planta)"],
        "Packing": ["Exportador", "Frigorífico", "Packing"],
        "Frigorífico": ["Exportador", "Packing", "Frigorífico"],
        "Exportador": ["Exportador"],
        "Cliente extranjero": ["Exportador"],
        "Agencia de aduana": [], "Transporte": [], "Extraportuario": [],
    },
    "servicios_compra_de": {
        "Productor(planta)": ["Transporte", "Packing", "Frigorífico"],
        "Packing": ["Transporte", "Frigorífico"],
        "Frigorífico": ["Transporte", "Packing"],
        "Exportador": ["Agencia de aduana", "Transporte", "Extraportuario", "Packing", "Frigorífico"],
        "Cliente extranjero": [],
        "Agencia de aduana": [], "Transporte": [], "Extraportuario": [],
    },
}
def publica_es_visible_para_rol(pub: Dict[str, Any], rol_usuario: str) -> bool:
    if not pub or not rol_usuario:
        return False
    tipo_pub = pub.get("tipo"); rol_pub = pub.get("rol")
    if tipo_pub == "oferta":
        return rol_pub in PERMISOS["fruta_oferta_visible_por_rol"].get(rol_usuario, [])
    if tipo_pub == "demanda":
        return rol_pub in PERMISOS["fruta_demanda_visible_por_rol"].get(rol_usuario, [])
    if tipo_pub == "servicio":
        return rol_pub in PERMISOS["servicios_compra_de"].get(rol_usuario, [])
    return False
def publicaciones_visibles(usuario: Dict[str, Any]) -> List[Dict[str, Any]]:
    hidden = set(session.get("hidden_items", []))
    rol = (usuario or {}).get("rol", "")
    out: List[Dict[str, Any]] = []
    for p in PUBLICACIONES:
        if p.get("id") in hidden:
            continue
        if publica_es_visible_para_rol(p, rol):
            out.append(p)
    return out
# =========================================================
# 👥 USERS DEMO para vistas /clientes y detalles
# =========================================================
def _normaliza_items(items: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in items or []:
        nombre = it.get("producto") or it.get("servicio") or it.get("variedad") or "Item"
        tipo = it.get("tipo") or "item"
        detalle = it.get("detalle") or it.get("descripcion") or ""
        out.append({"nombre": nombre, "tipo": tipo, "detalle": detalle})
    return out
def _armar_cliente_desde_users(username: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": _normaliza_items(data.get("items")),
        "email": data.get("email", username),
        "perfil_tipo": data.get("tipo", ""),
    }
# Diccionario demo para /clientes (coherente con semillas)
USERS: Dict[str, Dict[str, Any]] = {
    "exp1@demo.cl": {"empresa": "Exportadora Andes", "rol": "Exportador", "tipo": "compraventa",
        "descripcion": "Exportación fruta fresca.", "items": [
            {"tipo": "oferta", "producto": "Cereza Lapins", "detalle": "28+, USD 7/kg"},
        ], "email": "exp1@demo.cl"},
    "pack1@demo.cl": {"empresa": "Packing Maule SpA", "rol": "Packing", "tipo": "compraventa",
        "descripcion": "Embalaje BRC/IFS.", "items": [
            {"tipo": "servicio", "servicio": "Embalaje clamshell", "detalle": "0.50/kg"},
        ], "email": "pack1@demo.cl"},
    "frio1@demo.cl": {"empresa": "Frío Centro SpA", "rol": "Frigorífico", "tipo": "compraventa",
        "descripcion": "Cámaras -1 a 10°C.", "items": [
            {"tipo": "servicio", "servicio": "Frío y AC", "detalle": "0.20/kg"},
        ], "email": "frio1@demo.cl"},
    "cliente1@ext.com": {"empresa": "Importadora Asia Ltd.", "rol": "Cliente extranjero", "tipo": "compras",
        "descripcion": "Demanda frutas.", "items": [
            {"tipo": "demanda", "producto": "Cereza", "detalle": "semana 48-3"},
        ], "email": "cliente1@ext.com"},
}
# =========================================================
# 🌍 MULTILENGUAJE (igual que tu versión, con set_lang y t())
# =========================================================
TRANSLATIONS = {
    "Inicio": {"en": "Home", "zh": "主頁"},
    "Empresas": {"en": "Companies", "zh": "公司"},
    "Servicios": {"en": "Services", "zh": "服務"},
    "Carrito": {"en": "Cart", "zh": "購物車"},
    "Perfil": {"en": "Profile", "zh": "個人資料"},
    "Ayuda": {"en": "Help", "zh": "幫助"},
    "Iniciar sesión": {"en": "Login", "zh": "登入"},
    "Registrarse": {"en": "Register", "zh": "註冊"},
    "Salir": {"en": "Logout", "zh": "登出"},
    "Comercio Internacional": {"en": "International Trade", "zh": "國際貿易"},
    "Bienvenido a Window Shopping": {"en": "Welcome to Window Shopping","zh": "歡迎來到 Window Shopping"},
    "Conectamos productores chilenos con compradores internacionales":
        {"en": "Connecting Chilean producers with international buyers","zh": "連接智利生產商與國際買家"},
    "Comienza ahora": {"en": "Start now", "zh": "立即開始"},
    "Explora nuestros servicios": {"en": "Explore our services", "zh": "探索我們的服務"},
    "Compra y Venta": {"en": "Buy & Sell", "zh": "買賣"},
    "Servicios Logísticos": {"en": "Logistic Services", "zh": "物流服務"},
    "Sostenibilidad": {"en": "Sustainability", "zh": "永續發展"},
    "Ver Demandas": {"en": "View Demands", "zh": "查看需求"},
    "Explorar Ofertas": {"en": "Browse Offers", "zh": "瀏覽商品"},
    "Explorar Servicios": {"en": "Explore Services", "zh": "探索服務"},
    "Panel de Usuario": {"en": "User Dashboard", "zh": "用戶主頁"},
    "Agregado al carrito": {"en": "Added to cart", "zh": "已加入購物車"},
    "Eliminado del carrito": {"en": "Removed from cart", "zh": "已刪除"},
    "Carrito vaciado": {"en": "Cart cleared", "zh": "購物車已清空"},
    "Publicación no encontrada": {"en": "Item not found", "zh": "找不到項目"},
    "Publicación ocultada": {"en": "Item hidden", "zh": "項目已隱藏"},
    "Publicaciones restauradas": {"en": "Hidden items restored", "zh": "已恢復隱藏項目"},
    "Página no encontrada": {"en": "Page not found", "zh": "找不到頁面"},
    "Error interno del servidor": {"en": "Internal server error", "zh": "伺服器內部錯誤"},
}
@app.context_processor
def inject_translator():
    def t(es: str, en: str = None, zh: str = None) -> str:
        lang = session.get("lang", "es")
        if lang == "en":
            return TRANSLATIONS.get(es, {}).get("en") or (en if en else es)
        if lang == "zh":
            return TRANSLATIONS.get(es, {}).get("zh") or (zh if zh else es)
        return es
    return dict(t=t)
@app.route("/set_lang", methods=["POST"])
def set_lang():
    lang = request.form.get("lang", "es")
    session["lang"] = lang
    flash("🌍 Idioma cambiado correctamente.", "info")
    print(f"🌍 Idioma establecido: {lang}")
    return redirect(request.referrer or url_for("home"))
# =========================================================
# 🔑 AUTH (login / logout / register con RUT y rol por tipo)
# =========================================================
def _normaliza_tipo(tipo: str) -> str:
    tipo = (tipo or "").strip().lower()
    if tipo in {"compra-venta", "compra_venta", "cv"}:
        return "compraventa"
    return tipo if tipo in TIPOS_VALIDOS else ""
def _rol_valido_para_tipo(rol: str, tipo: str) -> bool:
    return rol in ROLES_POR_TIPO.get(tipo, [])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = ((request.form.get("username") or request.form.get("usuario") or "").strip().lower())
        password = (request.form.get("password") or "").strip()
        user = get_user(email)
        if user and user["password"] == password:
            session["user"] = {
                "id": user["id"], "email": user["email"], "empresa": user["empresa"],
                "rol": user["rol"], "tipo": user["tipo"], "pais": user["pais"], "rut_doc": user["rut_doc"]
            }
            session.permanent = True
            return redirect(url_for("dashboard"))
        flash("Credenciales incorrectas", "error")
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("home"))
@app.route("/register", methods=["GET", "POST"])
def register():
    roles_catalogo = [
        "Cliente extranjero", "Productor(planta)", "Packing", "Frigorífico",
        "Exportador", "Agencia de aduana", "Extraportuario", "Transporte",
    ]
    tipos_catalogo = ["compras", "servicios", "mixto", "compraventa"]
    if request.method == "POST":
        email = ((request.form.get("usuario") or request.form.get("username") or "").strip().lower())
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        tipo = _normaliza_tipo(request.form.get("tipo") or "")
        pais = (request.form.get("pais") or "CL").strip().upper()
        # archivo RUT opcional
        rut_file = request.files.get("rut_file")
        rut_doc_path = save_uploaded_file(rut_file) if rut_file else None
        # Validaciones
        if not all([email, password, empresa, rol, tipo]):
            flash("Todos los campos son obligatorios.", "error"); return redirect(url_for("register"))
        if not _rol_valido_para_tipo(rol, tipo):
            flash("El rol seleccionado no corresponde al tipo de cuenta.", "error"); return redirect(url_for("register"))
        if rol == "Cliente extranjero" and tipo != "compras":
            flash("Cliente extranjero solo puede ser tipo 'compras'.", "error"); return redirect(url_for("register"))
        if rol == "Exportador" and tipo not in {"compraventa"}:
            flash("Exportador debe ser tipo 'compraventa'.", "error"); return redirect(url_for("register"))
        if len(pais) != 2:
            flash("El código de país debe tener 2 letras (ej: CL, US).", "error"); return redirect(url_for("register"))
        if get_user(email):
            flash("El usuario ya existe.", "error"); return redirect(url_for("register"))
        add_user(email, password, empresa, rol, tipo, pais, rut_doc=rut_doc_path)
        flash("Usuario registrado exitosamente.", "success")
        return redirect(url_for("login"))
    # GET con preset ?tipo=
    pre_tipo = _normaliza_tipo(request.args.get("tipo") or "")
    roles_filtrados = ROLES_POR_TIPO.get(pre_tipo, roles_catalogo) if pre_tipo else roles_catalogo
    return render_template("register.html",
                           roles=roles_filtrados, tipos=tipos_catalogo, roles_por_tipo=ROLES_POR_TIPO)
@app.route("/register_router")
def register_router():
    return render_template("register_router.html")
# =========================================================
# 🧭 RUTAS — Dashboard, Compras, Ventas, Servicios, Clientes
# =========================================================
def login_requerido():
    if "user" not in session:
        flash("Debes iniciar sesión para acceder a esta sección.", "error")
        return False
    return True

@app.route("/dashboard")
def dashboard():
    if not login_requerido(): return redirect(url_for("login"))
    user = session.get("user", {})
    publicaciones = publicaciones_visibles(user)
    return render_template("dashboard.html",
                           user=user, publicaciones=publicaciones,
                           rol=user.get("rol",""), tipo=user.get("tipo",""),
                           empresa=user.get("empresa",""), pais=user.get("pais",""),
                           titulo="Panel de Usuario")

@app.route("/compras")
def compras():
    if not login_requerido(): return redirect(url_for("login"))
    user = session["user"]
    publicaciones = [p for p in PUBLICACIONES if p["tipo"] in ("oferta","servicio")
                     and publica_es_visible_para_rol(p, user["rol"])]
    return render_template("compras.html", publicaciones=publicaciones)

@app.route("/ventas")
def ventas():
    if not login_requerido(): return redirect(url_for("login"))
    user = session["user"]
    publicaciones = [p for p in PUBLICACIONES if p["tipo"]=="demanda"
                     and publica_es_visible_para_rol(p, user["rol"])]
    # Tu template de demandas se llama DETALLE.VENTAS.HTML, pero la ruta de listado usa "ventas.html".
    # Si prefieres, renómbralo a ventas.html. Aquí devolvemos "ventas.html".
    try:
        return render_template("ventas.html", publicaciones=publicaciones, demandas=publicaciones)
    except:
        # fallback a nombre alternativo que compartiste
        return render_template("detalle_ventas.html", publicaciones=publicaciones, demandas=publicaciones)

@app.route("/servicios")
def servicios():
    if not login_requerido(): return redirect(url_for("login"))
    user = session["user"]
    publicaciones = [p for p in PUBLICACIONES if p["tipo"]=="servicio"
                     and publica_es_visible_para_rol(p, user["rol"])]
    try:
        return render_template("servicios.html", publicaciones=publicaciones)
    except:
        return render_template("detalle_servicios.html", publicaciones=publicaciones)

@app.route("/clientes")
def clientes():
    if not login_requerido(): return redirect(url_for("login"))
    lista = [_armar_cliente_desde_users(username, data) for username, data in USERS.items()]
    lista.sort(key=lambda c: (c.get("empresa") or "").lower())
    return render_template("clientes.html", clientes=lista)

@app.route("/clientes/<username>")
def cliente_detalle(username):
    if username not in USERS: abort(404)
    c = _armar_cliente_desde_users(username, USERS[username])
    # Tu template de detalle “DETALLE_SERVICIOS.HTML” espera 'comp' en un caso;
    # aquí devolvemos 'c' para plantillas genéricas de cliente.
    try:
        return render_template("cliente_detalle.html", c=c)
    except:
        return render_template("detalle_servicios.html", comp=c)

@app.route("/clientes/<username>/mensaje", methods=["POST"])
def enviar_mensaje(username):
    if not login_requerido(): return redirect(url_for("login"))
    if username not in USERS: abort(404)
    mensaje = (request.form.get("mensaje") or "").strip()
    if not mensaje:
        flash("El mensaje no puede estar vacío.", "error")
        return redirect(url_for("cliente_detalle", username=username))
    flash("Mensaje enviado correctamente.", "success")
    return redirect(url_for("cliente_detalle", username=username))


# =========================================================
# 🛒 CARRITO — agregar, eliminar(POST), vaciar(POST), confirmar(POST)
# =========================================================
@app.route("/carrito")
def carrito():
    if not login_requerido(): return redirect(url_for("login"))
    return render_template("carrito.html", cart=get_cart())

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    if not login_requerido(): return redirect(url_for("login"))
    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if pub:
        add_to_cart(pub); flash("Agregado al carrito.", "success")
    else:
        flash("Publicación no encontrada.", "error")
    return redirect(request.referrer or url_for("carrito"))

@app.route("/carrito/agregar_directo", methods=["POST"])
def carrito_agregar_directo():
    if not login_requerido(): return redirect(url_for("login"))
    empresa = request.form.get("empresa")
    producto = request.form.get("producto") or ""
    servicio = request.form.get("servicio") or ""
    item = {"id": f"direct-{empresa}-{producto or servicio}", "empresa": empresa,
            "rol": "-", "descripcion": producto or servicio, "tipo": "servicio"}
    add_to_cart(item); flash("Agregado al carrito.", "success")
    return redirect(request.referrer or url_for("carrito"))

@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
def carrito_eliminar(index):
    if not login_requerido(): return redirect(url_for("login"))
    if remove_from_cart(index):
        flash("Eliminado del carrito.", "success")
    else:
        flash("Ítem no encontrado.", "error")
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar", methods=["POST"])
def carrito_vaciar():
    if not login_requerido(): return redirect(url_for("login"))
    clear_cart(); flash("Carrito vaciado.", "info")
    return redirect(url_for("carrito"))

@app.route("/carrito/confirmar", methods=["POST"])
def carrito_confirmar():
    if not login_requerido(): return redirect(url_for("login"))
    if not get_cart():
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("carrito"))
    # (Simulación de confirmar pedido)
    clear_cart()
    flash("✅ Pedido confirmado. Te contactaremos pronto.", "success")
    return redirect(url_for("carrito"))


# =========================================================
# 👁️ Ocultar/Restaurar publicaciones
# =========================================================
@app.route("/ocultar/<pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    if not login_requerido(): return redirect(url_for("login"))
    hide_item(pub_id); flash("Publicación ocultada.", "info")
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    if not login_requerido(): return redirect(url_for("login"))
    unhide_all(); flash("Publicaciones restauradas.", "success")
    return redirect(url_for("dashboard"))


# =========================================================
# 🙍 Perfil + Home + Ayuda
# =========================================================
@app.route("/perfil")
def perfil():
    if "user" not in session:
        flash("Debes iniciar sesión para ver tu perfil.", "error")
        return redirect(url_for("login"))
    return render_template("perfil.html", user=session["user"])

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html")


# =========================================================
# 🧯 Errores
# =========================================================
@app.errorhandler(404)
def not_found_error(error):
    try:
        return render_template("404.html"), 404
    except Exception as e:
        print(f"Error 404: {e}")
        return "<h1>404</h1><p>Página no encontrada</p>", 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template("500.html"), 500
    except Exception as e:
        print(f"Error 500: {e}")
        return "<h1>500</h1><p>Error interno del servidor</p>", 500


# =========================================================
# 🚀 Arranque local (Render usa: gunicorn app:app)
# =========================================================
if __name__ == "__main__":
    print("🚀 Iniciando Window Shopping (v3.3)…")
    app.run(debug=True, host="0.0.0.0", port=5000)
