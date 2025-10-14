# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 limpio) — BLOQUE 1
# Configuración, DB, Helpers, Caché USERS, Carrito, Visibilidad
# =========================================================

import os
import sqlite3
import uuid
from datetime import timedelta, datetime
from typing import List, Dict, Any

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

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
    """Verifica si el archivo tiene una extensión válida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# =========================================================
# 🌎 SISTEMA MULTI-IDIOMA — función global t()
# (Rutas de idioma se definen en bloques posteriores)
# =========================================================
def t(es, en="", zh=""):
    lang = session.get("lang", "es")
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

# Exponer t() a Jinja
app.jinja_env.globals.update(t=t)

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
    """Crea la tabla de usuarios si no existe."""
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
    """Agrega una columna a la tabla users si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {colname} TEXT")
        conn.commit()
        print(f"🛠️ Migración: columna '{colname}' agregada a users.")
    except sqlite3.OperationalError:
        # Ya existe
        pass
    finally:
        conn.close()

def migrate_add_rut_doc():
    migrate_add_column("rut_doc")

def migrate_add_contact_fields():
    migrate_add_column("direccion")
    migrate_add_column("telefono")

def get_user(email: str):
    """Obtiene un usuario por correo."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users() -> List[sqlite3.Row]:
    """Devuelve todos los usuarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(email, password_hashed, empresa, rol, tipo, pais,
             rut_doc=None, direccion=None, telefono=None):
    """
    Agrega un nuevo usuario a la base de datos.
    ⚠️ password_hashed debe venir ya hasheado (generate_password_hash).
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc, direccion, telefono)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, password_hashed, empresa, rol, tipo, pais, rut_doc, direccion, telefono))
        conn.commit()
        print(f"🆕 Usuario creado: {email}")
    except sqlite3.IntegrityError:
        print(f"⚠️ El usuario {email} ya existe.")
    finally:
        conn.close()

def update_user_fields(email: str, **fields):
    """Actualiza campos del usuario (empresa, rol, etc.)."""
    if not fields:
        return
    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values()) + [email]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {cols} WHERE email=?", vals)
    conn.commit()
    conn.close()

# =========================================================
# 👤 SEMILLA — Admin + Usuarios de demostración
# =========================================================
def create_admin_if_missing():
    """Crea un usuario administrador por defecto (password '1234')."""
    if not get_user("admin@ws.com"):
        add_user(
            email="admin@ws.com",
            password_hashed=generate_password_hash("1234"),
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
    """Crea usuarios de demostración por tipo y rol."""
    seeds = [
        # compraventa
        ("prod1@demo.cl","Productora Valle SpA","Productor(planta)","compraventa","CL","", "Curicó, CL","+56 9 1111 1111"),
        ("prod2@demo.cl","Agro Cordillera Ltda.","Productor(planta)","compraventa","CL","", "Rancagua, CL","+56 9 2222 2222"),
        ("pack1@demo.cl","Packing Maule SpA","Packing","compraventa","CL","", "Talca, CL","+56 9 3333 3333"),
        ("pack2@demo.cl","Packing Sur SpA","Packing","compraventa","CL","", "Osorno, CL","+56 9 4444 4444"),
        ("frio1@demo.cl","Frío Centro SpA","Frigorífico","compraventa","CL","", "San Fernando, CL","+56 9 5555 5555"),
        ("frio2@demo.cl","Patagonia Cold SA","Frigorífico","compraventa","CL","", "Punta Arenas, CL","+56 9 6666 6666"),
        ("exp1@demo.cl","Exportadora Andes","Exportador","compraventa","CL","", "Providencia, CL","+56 2 2345 6789"),
        ("exp2@demo.cl","Exportadora Pacífico","Exportador","compraventa","CL","", "Vitacura, CL","+56 2 2567 8901"),
        # servicios / mixto / compras
        ("aduana1@demo.cl","Agencia Andes","Agencia de aduana","servicios","CL","", "Valparaíso, CL","+56 32 222 2222"),
        ("trans1@demo.cl","Transporte Rápido","Transporte","servicios","CL","", "Santiago, CL","+56 2 2777 7777"),
        ("extra1@demo.cl","Extraportuario Norte","Extraportuario","servicios","CL","", "Antofagasta, CL","+56 55 2999 9999"),
        ("mixpack1@demo.cl","Mixto Packing Uno","Packing","mixto","CL","", "Talagante, CL","+56 2 2123 4567"),
        ("cliente1@ext.com","Importadora Asia Ltd.","Cliente extranjero","compras","US","", "Miami, US","+1 305 555 0101"),
    ]
    for email, empresa, rol, tipo, pais, rut_doc, direccion, telefono in seeds:
        if not get_user(email):
            add_user(
                email=email,
                password_hashed=generate_password_hash("1234"),
                empresa=empresa,
                rol=rol,
                tipo=tipo,
                pais=pais,
                rut_doc=rut_doc or None,
                direccion=direccion,
                telefono=telefono,
            )
            print(f"🧑‍💼 Usuario demo agregado: {email}")

# =========================================================
# 👥 CACHÉ DE USUARIOS PARA VISTAS (/clientes, mensajería)
# (Se carga desde la DB y se puede refrescar)
# =========================================================
USERS: Dict[str, Dict[str, Any]] = {}

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

def load_users_cache():
    """Carga USERS desde la DB (mínimo requerido por las vistas)."""
    USERS.clear()
    for row in get_all_users():
        USERS[row["email"]] = {
            "email": row["email"],
            "empresa": row["empresa"] or row["email"],
            "rol": row["rol"] or "",
            "tipo": row["tipo"] or "",
            "pais": row["pais"] or "",
            "direccion": row["direccion"] or "",
            "telefono": row["telefono"] or "",
            "descripcion": "",
            "items": [],  # opcional; se puede poblar desde otra fuente
        }

# =========================================================
# 🛒 CARRITO Y OCULTOS (helpers basados en sesión)
# =========================================================
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
# 🔐 PERMISOS DE VISIBILIDAD + FILTRO DE PUBLICACIONES
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
    tipo_pub = pub.get("tipo")
    rol_pub = pub.get("rol")
    if tipo_pub == "oferta":
        return rol_pub in PERMISOS["fruta_oferta_visible_por_rol"].get(rol_usuario, [])
    if tipo_pub == "demanda":
        return rol_pub in PERMISOS["fruta_demanda_visible_por_rol"].get(rol_usuario, [])
    if tipo_pub == "servicio":
        return rol_pub in PERMISOS["servicios_compra_de"].get(rol_usuario, [])
    return False

def publicaciones_visibles(usuario: Dict[str, Any], publicaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra publicaciones por permisos y ocultas en sesión."""
    hidden = set(session.get("hidden_items", []))
    rol = (usuario or {}).get("rol", "")
    out: List[Dict[str, Any]] = []
    for p in publicaciones:
        if p.get("id") in hidden:
            continue
        if publica_es_visible_para_rol(p, rol):
            out.append(p)
    return out

# =========================================================
# 📦 PUBLICACIONES DEMO (en memoria)
# (Las rutas se definen en el bloque de vistas)
# =========================================================
PUBLICACIONES: List[Dict[str, Any]] = [
    {
        "id": "pub1",
        "usuario": "exp1@demo.cl",
        "tipo": "oferta",
        "rol": "Exportador",
        "empresa": "Exportadora Andes",
        "producto": "Cerezas Premium",
        "precio": "USD 7/kg",
        "descripcion": "Lapins 28+, condición exportación.",
        "fecha": "2025-10-01 09:00",
    },
    {
        "id": "pub2",
        "usuario": "pack1@demo.cl",
        "tipo": "servicio",
        "rol": "Packing",
        "empresa": "Packing Maule SpA",
        "producto": "Servicio de Embalaje",
        "precio": "USD 0.50/kg",
        "descripcion": "Clamshell y flowpack. BRC/IFS.",
        "fecha": "2025-10-02 10:00",
    },
    {
        "id": "pub3",
        "usuario": "frio1@demo.cl",
        "tipo": "servicio",
        "rol": "Frigorífico",
        "empresa": "Frío Centro SpA",
        "producto": "Almacenamiento Refrigerado",
        "precio": "USD 0.20/kg",
        "descripcion": "Cámaras -1 a 10 °C, AC, monitoreo 24/7.",
        "fecha": "2025-10-03 11:00",
    },
    {
        "id": "pub4",
        "usuario": "cliente1@ext.com",
        "tipo": "demanda",
        "rol": "Cliente extranjero",
        "empresa": "Importadora Asia Ltd.",
        "producto": "Demanda Fruta Chilena",
        "precio": "Consultar",
        "descripcion": "Cereza, arándano y uva, semanas 46-3.",
        "fecha": "2025-10-04 12:00",
    },
]

# =========================================================
# 🏁 INICIALIZACIÓN (al importar app.py)
# =========================================================
init_db()
migrate_add_rut_doc()
migrate_add_contact_fields()
create_admin_if_missing()
seed_demo_users()
load_users_cache()
print(f"✅ USERS en caché: {len(USERS)} usuarios")
# =========================================================
# 🌐 WINDOW SHOPPING — BLOQUE 2
# Rutas públicas, login/logout, registro, idioma, errores
# =========================================================

# =========================================================
# 🏠 HOME
# =========================================================
@app.route("/")
def home():
    """Página principal"""
    titulo = t("Inicio", "Home", "主頁")
    return render_template("home.html", titulo=titulo)

# =========================================================
# 🔐 LOGIN / LOGOUT / REGISTRO
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión de usuario"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        user = get_user(email)

        if user and check_password_hash(user["password"], password):
            session["user"] = dict(user)
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"), "success")
            return redirect(url_for("dashboard_ext"))
        else:
            flash(t("Correo o contraseña incorrectos", "Invalid credentials", "電子郵件或密碼錯誤"), "error")

    return render_template("login.html", titulo=t("Iniciar sesión", "Login", "登入"))


@app.route("/logout")
def logout():
    """Cerrar sesión"""
    session.pop("user", None)
    flash(t("Has cerrado sesión", "You have logged out", "您已登出"), "info")
    return redirect(url_for("home"))


@app.route("/register_router")
def register_router():
    """Vista para elegir tipo de cuenta antes de registrarse"""
    return render_template("registro_tipo.html", titulo=t("Tipo de cuenta", "Account type", "帳戶類型"))


@app.route("/register/<tipo>", methods=["GET", "POST"])
def register(tipo):
    """Registro de nuevos usuarios según tipo de cuenta"""
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in
                ["email", "password", "empresa", "rol", "pais", "direccion", "telefono"]}
        file = request.files.get("rut_doc")
        rut_path = save_uploaded_file(file)

        # 🔹 Validación
        if not data["email"] or not data["password"]:
            flash(t("El correo y la contraseña son obligatorios.",
                    "Email and password are required.",
                    "必須輸入電子郵件和密碼"), "error")
            return redirect(request.url)

        # Hash de la contraseña
        password_hashed = generate_password_hash(data["password"])

        add_user(
            email=data["email"],
            password_hashed=password_hashed,
            empresa=data["empresa"],
            rol=data["rol"],
            tipo=tipo,
            pais=data["pais"],
            rut_doc=rut_path,
            direccion=data["direccion"],
            telefono=data["telefono"],
        )

        # Actualizar caché local
        load_users_cache()
        flash(t("Registro exitoso", "Registration successful", "註冊成功"), "success")
        return redirect(url_for("login"))

    roles = ROLES_POR_TIPO.get(tipo, [])
    return render_template("registro.html", tipo=tipo, roles=roles, titulo=t("Registro", "Register", "註冊"))


# =========================================================
# 🌍 CAMBIO DE IDIOMA (banderas)
# =========================================================
@app.route("/lang/<code>")
def cambiar_idioma(code):
    """Ruta rápida para cambiar idioma (banderas)."""
    session["lang"] = code if code in ["es", "en", "zh"] else "es"
    flash(t("Idioma actualizado correctamente.", "Language updated successfully.", "語言已成功更新"), "info")
    return redirect(request.referrer or url_for("home"))


@app.route("/set_lang/<lang>", methods=["GET", "POST"])
def set_lang(lang):
    """Alias más formal para cambio de idioma"""
    if lang not in ["es", "en", "zh"]:
        flash(t("Idioma no soportado.", "Unsupported language.", "不支援的語言"), "error")
        return redirect(request.referrer or url_for("home"))
    session["lang"] = lang
    flash(t("Idioma actualizado correctamente.", "Language updated successfully.", "語言已成功更新"), "info")
    return redirect(request.referrer or url_for("home"))


# =========================================================
# 🚨 ERRORES PERSONALIZADOS (404 / 500)
# =========================================================
@app.errorhandler(404)
def error_404(e):
    """Página no encontrada (Error 404)"""
    return render_template(
        "error.html",
        code=404,
        mensaje=t("Página no encontrada", "Page not found", "找不到頁面")
    ), 404


@app.errorhandler(500)
def error_500(e):
    """Error interno del servidor (Error 500)"""
    return render_template(
        "error.html",
        code=500,
        mensaje=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤")
    ), 500
# =========================================================
# 🌐 WINDOW SHOPPING — BLOQUE 3
# Dashboard Extendido + Carrito + Ocultar Publicaciones
# =========================================================

# =========================================================
# 🧭 DASHBOARD EXTENDIDO
# =========================================================
@app.route("/dashboard_ext", methods=["GET", "POST"])
def dashboard_ext():
    """Panel extendido del usuario con filtros dinámicos"""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    filtro = request.args.get("filtro", "oferta").lower()

    # 🔹 Validar filtro
    if filtro not in ["oferta", "demanda", "servicio"]:
        flash(t("Filtro inválido", "Invalid filter", "無效的篩選條件"), "error")
        filtro = "oferta"

    # 🔹 Publicaciones visibles según permisos del rol
    visibles = [
        p for p in PUBLICACIONES
        if publica_es_visible_para_rol(p, rol) and p.get("tipo") == filtro
    ]
    visibles.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    # 🔹 Publicaciones propias del usuario
    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard.html",
        user=user,
        publicaciones=visibles,
        propias=propias,
        filtro=filtro,
        titulo=t("Panel de Usuario", "User Dashboard", "用戶主頁")
    )


@app.route("/dashboard/filtro/<tipo>")
def cambiar_filtro_dashboard(tipo):
    """Cambia el filtro de vista del panel (oferta/demanda/servicio)"""
    tipo = tipo.lower()
    if tipo not in ["oferta", "demanda", "servicio"]:
        flash(t("Filtro inválido", "Invalid filter", "無效的篩選條件"), "error")
        return redirect(url_for("dashboard_ext"))
    return redirect(url_for("dashboard_ext", filtro=tipo))


# =========================================================
# 🧺 CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito")
def carrito():
    """Muestra el carrito actual"""
    cart = get_cart()
    return render_template("carrito.html", cart=cart, titulo=t("Carrito", "Cart", "購物車"))


@app.route("/carrito/agregar/<pub_id>", methods=["POST", "GET"])
def carrito_agregar(pub_id):
    """Agrega una publicación al carrito"""
    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(request.referrer or url_for("dashboard_ext"))

    add_to_cart(pub)
    flash(t("Agregado al carrito", "Added to cart", "已加入購物車"), "success")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
def carrito_eliminar(index):
    """Elimina un ítem del carrito por índice"""
    if remove_from_cart(index):
        flash(t("Eliminado del carrito", "Removed from cart", "已刪除"), "info")
    else:
        flash(t("Ítem no válido o inexistente",
                "Invalid or missing item",
                "無效或不存在的項目"), "error")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar", methods=["POST"])
def carrito_vaciar():
    """Vacía el carrito completo"""
    clear_cart()
    flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"), "info")
    return redirect(url_for("carrito"))


# =========================================================
# 🧱 PUBLICACIONES: OCULTAR / RESTAURAR
# =========================================================
@app.route("/ocultar/<pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    """Oculta una publicación del panel"""
    hide_item(pub_id)
    flash(t("Publicación ocultada", "Item hidden", "項目已隱藏"), "info")
    return redirect(url_for("dashboard_ext"))


@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    """Restaura publicaciones ocultas"""
    unhide_all()
    flash(t("Publicaciones restauradas", "Hidden items restored", "已恢復隱藏項目"), "success")
    return redirect(url_for("dashboard_ext"))
# =========================================================
# 🌐 WINDOW SHOPPING — BLOQUE 4 FINAL
# Publicaciones, Mensajería, Perfil, Ayuda, Acerca, Estado
# =========================================================

# =========================================================
# 🧩 GESTIÓN DE PUBLICACIONES
# =========================================================
SUBTIPOS_POR_TIPO = {
    "oferta": ["Compra", "Venta", "Servicio"],
    "demanda": ["Compra", "Venta", "Servicio"],
}

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite crear una nueva publicación"""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para publicar.", "You must log in to post.", "您必須登入以發布"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo_pub = request.form.get("tipo_pub", "").lower().strip()
        subtipo = request.form.get("subtipo", "").lower().strip()
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip()

        # Validaciones
        if not all([tipo_pub, subtipo, producto, descripcion]):
            flash(t("Todos los campos son obligatorios.", "All fields are required.", "所有欄位都是必填的"), "error")
            return redirect(url_for("publicar"))

        if tipo_pub not in ["oferta", "demanda", "servicio"]:
            flash(t("Tipo inválido.", "Invalid type.", "無效的類型"), "error")
            return redirect(url_for("publicar"))

        if not precio:
            precio = "Consultar"

        pub_id = f"pub_{uuid.uuid4().hex[:8]}"
        nueva_pub = {
            "id": pub_id,
            "usuario": user.get("email"),
            "tipo": tipo_pub,
            "rol": user.get("rol"),
            "empresa": user.get("empresa"),
            "producto": producto,
            "precio": precio,
            "descripcion": f"{subtipo.upper()} — {descripcion}",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        PUBLICACIONES.append(nueva_pub)
        flash(t("Publicación agregada correctamente.", "Post added successfully.", "成功新增發布"), "success")
        return redirect(url_for("dashboard_ext"))

    return render_template(
        "publicar.html",
        subtipo_opciones=SUBTIPOS_POR_TIPO,
        titulo=t("Nueva Publicación", "New Post", "新增發布"),
        user=user
    )


@app.route("/publicacion/eliminar/<pub_id>", methods=["POST"])
def eliminar_publicacion(pub_id):
    """Elimina una publicación propia"""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    global PUBLICACIONES
    antes = len(PUBLICACIONES)
    PUBLICACIONES = [
        p for p in PUBLICACIONES if not (p["id"] == pub_id and p["usuario"] == user["email"])
    ]
    despues = len(PUBLICACIONES)

    if antes > despues:
        flash(t("Publicación eliminada correctamente.", "Post deleted successfully.", "已刪除發布"), "success")
    else:
        flash(t("No se encontró la publicación o no tienes permiso.", "Not found or no permission.", "未找到或無權限"), "error")

    return redirect(url_for("dashboard_ext"))


# =========================================================
# 💬 MENSAJERÍA ENTRE USUARIOS (DEMO)
# =========================================================
MENSAJES = []  # Memoria temporal

@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    """Envío y visualización de mensajes simples (demo)"""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        destino = request.form.get("destino", "").strip()
        contenido = request.form.get("contenido", "").strip()

        if not destino or not contenido:
            flash(t("Debes completar todos los campos.", "All fields required.", "請填寫所有欄位"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe.", "Recipient not found.", "找不到收件人"), "error")
            return redirect(url_for("mensajes"))

        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        flash(t("Mensaje enviado correctamente.", "Message sent successfully.", "訊息已發送"), "success")
        return redirect(url_for("mensajes"))

    # Mensajes recibidos/enviados
    recibidos = sorted([m for m in MENSAJES if m["destino"] == user["email"]],
                       key=lambda x: x["fecha"], reverse=True)
    enviados = sorted([m for m in MENSAJES if m["origen"] == user["email"]],
                      key=lambda x: x["fecha"], reverse=True)

    return render_template(
        "mensajes.html",
        user=user,
        recibidos=recibidos,
        enviados=enviados,
        titulo=t("Mensajería", "Messaging", "訊息系統"),
    )


# =========================================================
# 👤 PERFIL DE USUARIO
# =========================================================
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    """Visualiza y permite editar la información básica del usuario"""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.", "You must log in to view your profile.", "您必須登入以檢視個人資料"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        nueva_empresa = request.form.get("empresa", "").strip()
        nuevo_rol = request.form.get("rol", "").strip()

        if nueva_empresa:
            user["empresa"] = nueva_empresa
        if nuevo_rol:
            user["rol"] = nuevo_rol

        update_user_fields(user["email"], empresa=user["empresa"], rol=user["rol"])
        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Tu Perfil", "Your Profile", "個人資料"))


# =========================================================
# 🧭 AYUDA / ACERCA / STATUS
# =========================================================
@app.route("/ayuda")
def ayuda():
    """Centro de ayuda general."""
    return render_template("ayuda.html", titulo=t("Centro de Ayuda", "Help Center", "幫助中心"))


@app.route("/acerca")
def acerca():
    """Información del proyecto Window Shopping."""
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping", "About Window Shopping", "關於 Window Shopping"))


@app.route("/status")
def status():
    """Muestra información general del sistema."""
    estado = {
        "usuarios": len(USERS),
        "publicaciones": len(PUBLICACIONES),
        "mensajes": len(MENSAJES),
        "idioma": session.get("lang", "es"),
        "estado": "OK ✅",
    }
    return jsonify(estado)


# =========================================================
# 🚀 EJECUCIÓN LOCAL / DEPLOY
# =========================================================
if __name__ == "__main__":
    print("🌐 Servidor Flask ejecutándose en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
