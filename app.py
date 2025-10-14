# =========================================================
# 🌐 WINDOW SHOPPING — Flask App Final (v3.3, Octubre 2025)
# Autor: Christopher Ponce & GPT-5
# =========================================================

import os
import sqlite3
from datetime import timedelta, datetime
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

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Subida de archivos
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# =========================================================
# 🌎 SISTEMA MULTI-IDIOMA
# =========================================================
def t(es, en="", zh=""):
    lang = session.get("lang", "es")
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

app.jinja_env.globals.update(t=t)

from flask import session as _s, redirect as _r, request as _rq

@app.route("/lang/<code>")
def cambiar_idioma(code):
    _s["lang"] = code
    return _r(_rq.referrer or url_for("home"))

# =========================================================
# 🧩 TIPOS Y ROLES
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
            rut_doc TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)
    conn.commit()
    conn.close()

def migrate_add_column(colname: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {colname} TEXT")
        conn.commit()
        print(f"🛠️ Migración: columna '{colname}' agregada a users.")
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

def migrate_add_rut_doc():
    migrate_add_column("rut_doc")

def migrate_add_contact_fields():
    migrate_add_column("direccion")
    migrate_add_column("telefono")

def get_user(email: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(email, password, empresa, rol, tipo, pais, rut_doc=None, direccion=None, telefono=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc, direccion, telefono)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, password, empresa, rol, tipo, pais, rut_doc, direccion, telefono))
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
# 👤 SEMILLA — Admin + 2 usuarios por rol
# =========================================================
def create_admin_if_missing():
    if not get_user("admin@ws.com"):
        add_user(
            email="admin@ws.com",
            password="1234",
            empresa="Window Shopping Admin",
            rol="Exportador",
            tipo="compraventa",
            pais="CL",
            rut_doc=None,
            direccion="Santiago, CL",
            telefono="+56 2 2222 2222",
        )
        print("✅ Usuario admin creado: admin@ws.com / 1234")

def seed_demo_users():
    seeds = [
        # compraventa
        ("prod1@demo.cl","1234","Productora Valle SpA","Productor(planta)","compraventa","CL","", "Curicó, CL","+56 9 1111 1111"),
        ("prod2@demo.cl","1234","Agro Cordillera Ltda.","Productor(planta)","compraventa","CL","", "Rancagua, CL","+56 9 2222 2222"),
        ("pack1@demo.cl","1234","Packing Maule SpA","Packing","compraventa","CL","", "Talca, CL","+56 9 3333 3333"),
        ("pack2@demo.cl","1234","Packing Sur SpA","Packing","compraventa","CL","", "Osorno, CL","+56 9 4444 4444"),
        ("frio1@demo.cl","1234","Frío Centro SpA","Frigorífico","compraventa","CL","", "San Fernando, CL","+56 9 5555 5555"),
        ("frio2@demo.cl","1234","Patagonia Cold SA","Frigorífico","compraventa","CL","", "Punta Arenas, CL","+56 9 6666 6666"),
        ("exp1@demo.cl","1234","Exportadora Andes","Exportador","compraventa","CL","", "Providencia, CL","+56 2 2345 6789"),
        ("exp2@demo.cl","1234","Exportadora Pacífico","Exportador","compraventa","CL","", "Vitacura, CL","+56 2 2567 8901"),
        # servicios
        ("aduana1@demo.cl","1234","Agencia Andes","Agencia de aduana","servicios","CL","", "Valparaíso, CL","+56 32 222 2222"),
        ("aduana2@demo.cl","1234","Agencia Sur","Agencia de aduana","servicios","CL","", "San Antonio, CL","+56 35 233 3333"),
        ("trans1@demo.cl","1234","Transporte Rápido","Transporte","servicios","CL","", "Santiago, CL","+56 2 2777 7777"),
        ("trans2@demo.cl","1234","Logística Express","Transporte","servicios","CL","", "Concepción, CL","+56 41 2888 8888"),
        ("extra1@demo.cl","1234","Extraportuario Norte","Extraportuario","servicios","CL","", "Antofagasta, CL","+56 55 2999 9999"),
        ("extra2@demo.cl","1234","Extraportuario Sur","Extraportuario","servicios","CL","", "Puerto Montt, CL","+56 65 211 1111"),
        # mixto
        ("mixpack1@demo.cl","1234","Mixto Packing Uno","Packing","mixto","CL","", "Talagante, CL","+56 2 2123 4567"),
        ("mixfrio1@demo.cl","1234","Mixto Frio Uno","Frigorífico","mixto","CL","", "Chillán, CL","+56 42 2987 6543"),
        # compras (cliente extranjero)
        ("cliente1@ext.com","1234","Importadora Asia Ltd.","Cliente extranjero","compras","US","", "Miami, US","+1 305 555 0101"),
        ("cliente2@ext.com","1234","Global Retail HK","Cliente extranjero","compras","HK","", "Kowloon, HK","+852 5555 0101"),
        # servicio-only extra
        ("packserv1@demo.cl","1234","Packing Servicios SPA","Packing","servicios","CL","", "Quillota, CL","+56 33 244 4444"),
        ("frioserv1@demo.cl","1234","Frío Servicios SPA","Frigorífico","servicios","CL","", "La Calera, CL","+56 33 255 5555"),
    ]
    for email, pwd, empresa, rol, tipo, pais, rut_doc, direccion, telefono in seeds:
        if not get_user(email):
            add_user(email, pwd, empresa, rol, tipo, pais, rut_doc=rut_doc, direccion=direccion, telefono=telefono)
            print(f"🧑‍💼 Usuario ficticio agregado: {email}")

# Inicialización
init_db()
migrate_add_rut_doc()
migrate_add_contact_fields()
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
        cart.pop(index); save_cart(cart); return True
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
        "Productor(planta)": ["Packing", "Frigorífico", "Exportador"],  # puede vender a estos
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
# 🌍 MULTILENGUAJE (inyector + set_lang)
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
    # Nuevas claves usadas en formularios y panel
    "Dirección": {"en": "Address", "zh": "地址"},
    "Teléfono": {"en": "Phone", "zh": "電話"},
    "Oferta": {"en": "Offer", "zh": "供應"},
    "Demanda": {"en": "Demand", "zh": "需求"},
    "Compra": {"en": "Buy", "zh": "採購"},
    "Venta": {"en": "Sell", "zh": "銷售"},
    "Servicio": {"en": "Service", "zh": "服務"},
    "Agregar ítem": {"en": "Add item", "zh": "新增項目"},
    "Eliminar ítem": {"en": "Remove item", "zh": "刪除項目"},
    "Guardar": {"en": "Save", "zh": "儲存"},
    "Cancelar": {"en": "Cancel", "zh": "取消"},
    "Enviar mensaje": {"en": "Send message", "zh": "發送訊息"},
    "Rol": {"en": "Role", "zh": "角色"},
    "Tipo": {"en": "Type", "zh": "類型"},
    "País": {"en": "Country", "zh": "國家"},
    "Empresa": {"en": "Company", "zh": "公司"},
    "Precio": {"en": "Price", "zh": "價格"},
    "Ver Detalle": {"en": "View Detail", "zh": "查看詳情"},
    "Empresas Registradas": {"en": "Registered Companies", "zh": "已註冊公司"},
    "No hay empresas registradas para mostrar.": {"en": "No companies to show.", "zh": "沒有可顯示的公司。"},
    "Productos o Servicios": {"en": "Products or Services", "zh": "產品或服務"},
    "Escribe un mensaje...": {"en": "Write a message...", "zh": "寫一條訊息..."},
    "Volver": {"en": "Back", "zh": "返回"},
    "Perfil de Usuario": {"en": "User Profile", "zh": "用戶檔案"},
       "Documento RUT": {"en": "RUT document", "zh": "稅號文件"},
    "Opciones": {"en": "Options", "zh": "選項"},
    "Agregar item": {"en": "Add item", "zh": "新增項目"},
    "Eliminar item": {"en": "Delete item", "zh": "刪除項目"},
    "Ocultar de vista": {"en": "Hide from view", "zh": "隱藏"},
    "Restaurar ocultos": {"en": "Restore hidden", "zh": "恢復隱藏"},
    "Ofertas Disponibles": {"en": "Available Offers", "zh": "可用報價"},
    "Demandas y Solicitudes": {"en": "Demands and Requests", "zh": "需求與請求"},
    "No hay servicios disponibles.": {"en": "No services available.", "zh": "目前沒有可用的服務。"},
    "No hay publicaciones visibles para tu rol": {"en": "No publications visible for your role", "zh": "你的角色無可見的項目"},
    "Publicaciones": {"en": "Publications", "zh": "刊登"},
    "Buscar": {"en": "Search", "zh": "搜尋"},
    "País (Código ISO de 2 letras)": {"en": "Country (ISO 2-letter code)", "zh": "國家（ISO 2 字母代碼）"}
}
# =========================================================
# 🌐 FUNCIONES DE IDIOMA
# =========================================================
@app.context_processor
def inject_translations():
    """Permite usar traducciones desde cualquier template."""
    def translate(text):
        lang = session.get("lang", "es")
        if text in TRANSLATIONS and lang in TRANSLATIONS[text]:
            return TRANSLATIONS[text][lang]
        return text
    return dict(t=translate)

@app.route("/set_lang", methods=["POST", "GET"])
def set_lang():
    """Establece el idioma actual de sesión."""
    lang = request.args.get("lang") or request.form.get("lang") or "es"
    session["lang"] = lang
    flash(f"🌐 Idioma cambiado a: {lang}", "info")
    return redirect(request.referrer or url_for("home"))
# =========================================================
# 🧭 RUTAS PRINCIPALES
# =========================================================

@app.route("/")
def home():
    lang = session.get("lang", "es")
    titulo = t("Inicio", "Home", "主頁")
    return render_template("home.html", titulo=titulo)


# =========================================================
# 🔐 LOGIN / LOGOUT / REGISTRO
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = get_user(email)

        if user and user["password"] == password:
            session["user"] = dict(user)
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"), "success")
            return redirect(url_for("dashboard"))
        else:
            flash(t("Correo o contraseña incorrectos", "Invalid credentials", "電子郵件或密碼錯誤"), "error")

    return render_template("login.html", titulo=t("Iniciar sesión", "Login", "登入"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Has cerrado sesión", "You have logged out", "您已登出"), "info")
    return redirect(url_for("home"))


@app.route("/register_router")
def register_router():
    return render_template("registro_tipo.html", titulo=t("Tipo de cuenta", "Account type", "帳戶類型"))


@app.route("/register/<tipo>", methods=["GET", "POST"])
def register(tipo):
    if request.method == "POST":
        data = {k: request.form.get(k) for k in
                ["email", "password", "empresa", "rol", "pais", "direccion", "telefono"]}
        file = request.files.get("rut_doc")
        rut_path = save_uploaded_file(file)

        add_user(
            email=data["email"],
            password=data["password"],
            empresa=data["empresa"],
            rol=data["rol"],
            tipo=tipo,
            pais=data["pais"],
            rut_doc=rut_path,
            direccion=data["direccion"],
            telefono=data["telefono"],
        )
        flash(t("Registro exitoso", "Registration successful", "註冊成功"), "success")
        return redirect(url_for("login"))

    roles = ROLES_POR_TIPO.get(tipo, [])
    return render_template("registro.html", tipo=tipo, roles=roles, titulo=t("Registro", "Register", "註冊"))


# =========================================================
# 🧑‍💼 DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    publicaciones = publicaciones_visibles(user)

    return render_template(
        "dashboard.html",
        user=user,
        publicaciones=publicaciones,
        titulo=t("Panel de Usuario", "User Dashboard", "用戶主頁")
    )


# =========================================================
# 🧺 CARRITO
# =========================================================

@app.route("/carrito")
def carrito():
    cart = get_cart()
    return render_template("carrito.html", cart=cart, titulo=t("Carrito", "Cart", "購物車"))


@app.route("/carrito/agregar/<pub_id>", methods=["POST", "GET"])
def carrito_agregar(pub_id):
    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(request.referrer or url_for("dashboard"))
    add_to_cart(pub)
    flash(t("Agregado al carrito", "Added to cart", "已加入購物車"), "success")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
def carrito_eliminar(index):
    if remove_from_cart(index):
        flash(t("Eliminado del carrito", "Removed from cart", "已刪除"), "info")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar", methods=["POST"])
def carrito_vaciar():
    clear_cart()
    flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"), "info")
    return redirect(url_for("carrito"))


# =========================================================
# 🧱 PUBLICACIONES / OCULTAR
# =========================================================

@app.route("/ocultar/<pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    hide_item(pub_id)
    flash(t("Publicación ocultada", "Item hidden", "項目已隱藏"), "info")
    return redirect(url_for("dashboard"))


@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    unhide_all()
    flash(t("Publicaciones restauradas", "Hidden items restored", "已恢復隱藏項目"), "success")
    return redirect(url_for("dashboard"))


# =========================================================
# 🏢 CLIENTES / DETALLE
# =========================================================

@app.route("/clientes")
def clientes():
    data = []
    for username, info in USERS.items():
        data.append(_armar_cliente_desde_users(username, info))
    return render_template("clientes.html", clientes=data, titulo=t("Empresas", "Companies", "公司"))


@app.route("/clientes/<username>")
def cliente_detalle(username):
    if username not in USERS:
        abort(404)
    cliente = _armar_cliente_desde_users(username, USERS[username])
    return render_template("cliente_detalle.html", c=cliente, titulo=cliente["empresa"])


# =========================================================
# 🛒 COMPRAS / VENTAS / SERVICIOS
# =========================================================

@app.route("/compras")
def compras():
    q = request.args.get("q", "").lower()
    visibles = [p for p in PUBLICACIONES if p["tipo"] == "oferta"]
    if q:
        visibles = [p for p in visibles if q in p["empresa"].lower() or q in p["producto"].lower()]
    return render_template("compras.html", data=visibles, titulo=t("Ofertas Disponibles", "Available Offers", "可用報價"))


@app.route("/ventas")
def ventas():
    visibles = [p for p in PUBLICACIONES if p["tipo"] == "demanda"]
    return render_template("ventas.html", publicaciones=visibles, titulo=t("Demandas y Solicitudes", "Demands and Requests", "需求與請求"))


@app.route("/servicios")
def servicios():
    visibles = [p for p in PUBLICACIONES if p["tipo"] == "servicio"]
    return render_template("servicios.html", publicaciones=visibles, titulo=t("Servicios", "Services", "服務"))


# =========================================================
# ⚙️ ERRORES
# =========================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message=t("Página no encontrada", "Page not found", "找不到頁面")), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", code=500, message=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤")), 500


# =========================================================
# 🚀 RUN LOCAL (solo debug)
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
# =========================================================
# 🧩 GESTIÓN DE PUBLICACIONES (OFERTA / DEMANDA / SERVICIO)
# =========================================================

import uuid  # Para generar IDs únicos de publicaciones

# --- Subtipos según flujo y tipo ---
SUBTIPOS_POR_TIPO = {
    "oferta": ["Compra", "Venta", "Servicio"],
    "demanda": ["Compra", "Venta", "Servicio"]
}


@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite crear una nueva publicación (oferta o demanda) según perfil."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para publicar.", "You must log in to post.", "您必須登入以發布"), "error")
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    tipo_cuenta = user.get("tipo", "")

    if request.method == "POST":
        tipo_pub = request.form.get("tipo_pub")          # oferta / demanda
        subtipo = request.form.get("subtipo")            # compra / venta / servicio
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip()

        # Validación de campos
        if not all([tipo_pub, subtipo, producto, descripcion]):
            flash(t("Todos los campos son obligatorios.", "All fields are required.", "所有欄位都是必填的"), "error")
            return redirect(url_for("publicar"))

        # Asegurar precio legible
        if not precio:
            precio = "Consultar"

        # Generar ID único seguro
        pub_id = f"pub_{uuid.uuid4().hex[:8]}"

        nueva_pub = {
            "id": pub_id,
            "usuario": user.get("email"),
            "tipo": tipo_pub,                # oferta o demanda
            "rol": rol,
            "empresa": user.get("empresa"),
            "producto": producto,
            "precio": precio,
            "descripcion": f"{subtipo.upper()} — {descripcion}",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        PUBLICACIONES.append(nueva_pub)
        flash(t("Publicación agregada correctamente.", "Post added successfully.", "成功新增發布"), "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "publicar.html",
        subtipo_opciones=SUBTIPOS_POR_TIPO,
        titulo=t("Nueva Publicación", "New Post", "新增發布"),
        user=user
    )


# =========================================================
# 🧹 ELIMINAR PUBLICACIÓN (Solo propias)
# =========================================================

@app.route("/publicacion/eliminar/<pub_id>", methods=["POST"])
def eliminar_publicacion(pub_id):
    """Permite eliminar publicaciones creadas por el usuario logueado."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    global PUBLICACIONES
    antes = len(PUBLICACIONES)

    # Filtra publicaciones que no coinciden con el ID o no pertenecen al usuario
    PUBLICACIONES = [
        p for p in PUBLICACIONES
        if not (p["id"] == pub_id and p["usuario"] == user["email"])
    ]

    despues = len(PUBLICACIONES)

    if antes > despues:
        flash(t("Publicación eliminada correctamente.", "Post deleted successfully.", "已刪除發布"), "success")
    else:
        flash(t("No se encontró la publicación o no tienes permiso.", "Not found or no permission.", "未找到或無權限"), "error")

    return redirect(url_for("dashboard"))
# =========================================================
# 🧭 DASHBOARD EXTENDIDO CON FILTROS Y VISTAS POR PERFIL
# =========================================================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Muestra el panel de usuario con publicaciones filtradas y acciones dinámicas."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    tipo = user.get("tipo", "")
    filtro = request.args.get("filtro", "oferta")  # valor por defecto

    # Determina el conjunto de publicaciones visibles según permisos
    publicaciones = [
        p for p in PUBLICACIONES
        if publica_es_visible_para_rol(p, rol) and p["tipo"] == filtro
    ]

    # Ordenar publicaciones más recientes primero (por fecha si existe)
    publicaciones.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    # Extrae solo las publicaciones del propio usuario
    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard.html",
        user=user,
        publicaciones=publicaciones,
        propias=propias,
        filtro=filtro,
        titulo=t("Panel de Usuario", "User Dashboard", "用戶主頁"),
    )


# =========================================================
# 🔄 CAMBIO DE FILTRO EN DASHBOARD (AJAX SIMPLIFICADO)
# =========================================================

@app.route("/dashboard/filtro/<tipo>")
def cambiar_filtro_dashboard(tipo):
    """Permite cambiar el filtro de vista del panel (oferta/demanda/servicio)."""
    if tipo not in ["oferta", "demanda", "servicio"]:
        flash(t("Filtro inválido", "Invalid filter", "無效的篩選條件"), "error")
        return redirect(url_for("dashboard"))
    return redirect(url_for("dashboard", filtro=tipo))


# =========================================================
# 📊 PANEL DE CONTROL: RESUMEN POR ROL Y ACCIONES RÁPIDAS
# =========================================================

@app.route("/panel_info")
def panel_info():
    """Devuelve un resumen visual del rol y tipo actual (demo para templates)."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    tipo = user.get("tipo", "")

    info = {
        "rol": rol,
        "tipo": tipo,
        "total_publicaciones": len([p for p in PUBLICACIONES if p["usuario"] == user["email"]]),
        "puede_ofertar": tipo in ["compraventa", "mixto"],
        "puede_demandar": tipo in ["compras", "compraventa", "mixto"],
        "puede_servicios": tipo in ["servicios", "mixto", "compraventa"],
    }

    return info


# =========================================================
# ⚡ ACTUALIZACIÓN VISUAL DE LAS VISTAS (RUTAS DE AYUDA)
# =========================================================

@app.route("/refresh_dashboard")
def refresh_dashboard():
    """Recarga el panel manteniendo el filtro actual."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    filtro_actual = request.args.get("filtro", "oferta")
    return redirect(url_for("dashboard", filtro=filtro_actual))


@app.route("/mis_publicaciones")
def mis_publicaciones():
    """Muestra solo las publicaciones propias del usuario."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    return render_template(
        "mis_publicaciones.html",
        user=user,
        publicaciones=propias,
        titulo=t("Mis Publicaciones", "My Posts", "我的發布")
    )


# =========================================================
# 🧭 LÓGICA PARA COMBINAR VISTAS (COMPRAS / VENTAS / SERVICIOS)
# =========================================================

@app.route("/empresas_filtradas/<categoria>")
def empresas_filtradas(categoria):
    """
    Muestra empresas según la categoría seleccionada:
    compras -> empresas que venden
    ventas  -> empresas que compran
    servicios -> empresas que ofrecen servicios
    """
    if categoria not in ["compras", "ventas", "servicios"]:
        abort(404)

    data = []
    for username, info in USERS.items():
        if categoria == "compras" and info["tipo"] in ["compraventa", "mixto"]:
            data.append(_armar_cliente_desde_users(username, info))
        elif categoria == "ventas" and info["tipo"] in ["compras", "compraventa"]:
            data.append(_armar_cliente_desde_users(username, info))
        elif categoria == "servicios" and info["tipo"] == "servicios":
            data.append(_armar_cliente_desde_users(username, info))

    # ✅ Mejora visual: ordenar empresas alfabéticamente
    data.sort(key=lambda x: x["empresa"])

    return render_template(
        "clientes.html",
        clientes=data,
        titulo=t("Empresas", "Companies", "公司"),
        categoria=categoria
    )
# =========================================================
# 💬 MENSAJERÍA ENTRE USUARIOS (desde perfil empresa)
# =========================================================

MENSAJES: list[dict[str, str]] = []  # almacenamiento temporal en memoria

@app.route("/mensaje/enviar/<username>", methods=["POST"])
def enviar_mensaje(username):
    """Permite enviar un mensaje a otra empresa registrada."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para enviar mensajes.",
                "You must log in to send messages.",
                "您必須登入才能發送訊息"), "error")
        return redirect(url_for("login"))

    if username not in USERS:
        flash(t("Usuario destino no encontrado.",
                "Target user not found.",
                "找不到目標用戶"), "error")
        return redirect(url_for("clientes"))

    contenido = request.form.get("mensaje", "").strip()
    if not contenido:
        flash(t("El mensaje no puede estar vacío.",
                "Message cannot be empty.",
                "訊息不能為空"), "error")
        return redirect(url_for("cliente_detalle", username=username))

    mensaje = {
        "de": user.get("empresa"),
        "para": USERS[username]["empresa"],
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "contenido": contenido,
    }
    MENSAJES.append(mensaje)

    flash(t("Mensaje enviado correctamente.",
            "Message sent successfully.",
            "訊息已成功發送"), "success")
    return redirect(url_for("cliente_detalle", username=username))


@app.route("/mensajes")
def ver_mensajes():
    """Muestra los mensajes recibidos (solo modo demo)."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    empresa_actual = user.get("empresa")
    recibidos = [m for m in MENSAJES if m["para"] == empresa_actual]

    return render_template(
        "mensajes.html",
        mensajes=recibidos,
        titulo=t("Mensajes recibidos", "Received messages", "收到的訊息")
    )


# =========================================================
# 🌍 IDIOMA / TRADUCCIONES FINALES
# =========================================================

@app.route("/set_lang", methods=["POST", "GET"])
def set_lang():
    """Cambia el idioma de la sesión (desde el menú o bandera)."""
    lang = request.form.get("lang") or request.args.get("lang")
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma cambiado correctamente.",
                "Language changed successfully.",
                "語言已成功更改"), "info")
    else:
        flash(t("Idioma no soportado.",
                "Unsupported language.",
                "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))


@app.context_processor
def inject_translations():
    """Inyector global de función t() para usar en todos los templates."""
    return dict(t=t)


# =========================================================
# 🧭 RUTAS ADICIONALES / UTILIDADES
# =========================================================

@app.route("/perfil")
def perfil():
    """Muestra el perfil actual del usuario logueado."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.",
                "You must log in to view your profile.",
                "您必須登入才能查看個人資料"), "error")
        return redirect(url_for("login"))
    return render_template("perfil.html", user=user,
                           titulo=t("Perfil de Usuario",
                                    "User Profile",
                                    "用戶檔案"))


@app.route("/ayuda")
def ayuda():
    """Vista informativa o página de ayuda (demo)."""
    return render_template("ayuda.html",
                           titulo=t("Ayuda", "Help", "幫助"))


# =========================================================
# ✅ CONFIRMACIÓN FINAL DE SISTEMA
# =========================================================

@app.route("/status")
def status():
    """Ruta interna para verificar el estado general del sistema."""
    estado = {
        "usuarios": len(seed_demo_users.__code__.co_consts),
        "publicaciones": len(PUBLICACIONES),
        "mensajes": len(MENSAJES),
        "idioma": session.get("lang", "es"),
        "estado": "OK ✅"
    }
    return estado
