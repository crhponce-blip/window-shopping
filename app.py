# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final, Parte 1/4)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# =========================================================
# 🌎 MULTI-IDIOMA (función global t)
# =========================================================
def t(es, en="", zh=""):
    lang = session.get("lang", "es")
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

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
# 🗄️ BASE DE DATOS (SQLite)
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
    """Agrega una columna nueva si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {colname} TEXT")
        conn.commit()
        print(f"🛠️ Migración: columna '{colname}' agregada.")
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
    """Obtiene un usuario por email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users() -> List[sqlite3.Row]:
    """Devuelve todos los usuarios existentes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(email, password_hashed, empresa, rol, tipo, pais,
             rut_doc=None, direccion=None, telefono=None):
    """Agrega un nuevo usuario a la base de datos."""
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
# 👤 SEMILLA: Admin + Usuarios Demo
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
    """Carga usuarios demo (2 por rol)."""
    seeds = [
        ("prod1@demo.cl", "Productora Valle SpA", "Productor(planta)", "compraventa", "CL", "", "Curicó, CL", "+56 9 1111 1111"),
        ("prod2@demo.cl", "Agro Cordillera Ltda.", "Productor(planta)", "compraventa", "CL", "", "Rancagua, CL", "+56 9 2222 2222"),
        ("pack1@demo.cl", "Packing Maule SpA", "Packing", "compraventa", "CL", "", "Talca, CL", "+56 9 3333 3333"),
        ("pack2@demo.cl", "Packing Sur SpA", "Packing", "compraventa", "CL", "", "Osorno, CL", "+56 9 4444 4444"),
        ("frio1@demo.cl", "Frío Centro SpA", "Frigorífico", "compraventa", "CL", "", "San Fernando, CL", "+56 9 5555 5555"),
        ("frio2@demo.cl", "Patagonia Cold SA", "Frigorífico", "compraventa", "CL", "", "Punta Arenas, CL", "+56 9 6666 6666"),
        ("exp1@demo.cl", "Exportadora Andes", "Exportador", "compraventa", "CL", "", "Providencia, CL", "+56 2 2345 6789"),
        ("exp2@demo.cl", "Exportadora Pacífico", "Exportador", "compraventa", "CL", "", "Vitacura, CL", "+56 2 2567 8901"),
        ("aduana1@demo.cl", "Agencia Andes", "Agencia de aduana", "servicios", "CL", "", "Valparaíso, CL", "+56 32 222 2222"),
        ("trans1@demo.cl", "Transporte Rápido", "Transporte", "servicios", "CL", "", "Santiago, CL", "+56 2 2777 7777"),
        ("extra1@demo.cl", "Extraportuario Norte", "Extraportuario", "servicios", "CL", "", "Antofagasta, CL", "+56 55 2999 9999"),
        ("mixpack1@demo.cl", "Mixto Packing Uno", "Packing", "mixto", "CL", "", "Talagante, CL", "+56 2 2123 4567"),
        ("cliente1@ext.com", "Importadora Asia Ltd.", "Cliente extranjero", "compras", "US", "", "Miami, US", "+1 305 555 0101"),
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
# 👥 CARGA DE USUARIOS A CACHÉ
# =========================================================
USERS: Dict[str, Dict[str, Any]] = {}

def load_users_cache():
    """Carga USERS desde la base de datos a memoria."""
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
            "items": [],
        }

# =========================================================
# 🛒 CARRITO Y PUBLICACIONES OCULTAS (helpers)
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
# ➕ NUEVO — MATRICES DE PERMISOS Y PUBLICACIÓN
# =========================================================
PERMISOS = {
    "Productor(planta)": {
        "ver_demanda_fruta": ["Packing", "Frigorífico", "Exportador"],
        "comprar_servicios": ["Transporte", "Packing", "Frigorífico"],
        "vender_fruta": ["Packing", "Frigorífico", "Exportador"],
    },
    "Packing": {
        "comprar_fruta": ["Productor(planta)", "Frigorífico"],
        "vender_fruta": ["Frigorífico", "Exportador"],
        "comprar_servicios": ["Frigorífico", "Transporte"],
        "vender_servicios": ["Productor(planta)", "Frigorífico", "Exportador"],
    },
    "Frigorífico": {
        "comprar_fruta": ["Productor(planta)", "Packing"],
        "vender_fruta": ["Packing", "Exportador"],
        "comprar_servicios": ["Packing", "Transporte"],
        "vender_servicios": ["Productor(planta)", "Packing", "Exportador"],
    },
    "Exportador": {
        "comprar_fruta": ["Productor(planta)", "Packing", "Frigorífico"],
        "vender_fruta": ["Exportador", "Cliente extranjero"],
        "comprar_servicios": ["Transporte", "Agencia de aduana", "Packing", "Frigorífico", "Extraportuario"],
    },
    "Cliente extranjero": {
        "comprar_fruta": ["Exportador"],
    },
    "Agencia de aduana": {
        "vender_servicios": ["Exportador"],
    },
    "Transporte": {
        "vender_servicios": ["Productor(planta)", "Packing", "Frigorífico", "Exportador"],
    },
    "Extraportuario": {
        "vender_servicios": ["Exportador"],
    },
}

def puede_ver_publicacion(viewer_rol: str, pub_rol: str, pub_tipo: str) -> bool:
    """Evalúa si un rol puede ver una publicación de otro rol."""
    if viewer_rol not in PERMISOS:
        return False
    rules = PERMISOS[viewer_rol]
    if pub_tipo in ["oferta", "demanda"]:
        for key in ["comprar_fruta", "vender_fruta", "ver_demanda_fruta"]:
            if pub_rol in rules.get(key, []):
                return True
    if pub_tipo == "servicio":
        for key in ["comprar_servicios", "vender_servicios"]:
            if pub_rol in rules.get(key, []):
                return True
    return False

RESTRICCIONES_PUBLICAR = {
    "Productor(planta)": ["oferta"],
    "Packing": ["oferta", "demanda", "servicio"],
    "Frigorífico": ["oferta", "demanda", "servicio"],
    "Exportador": ["oferta", "demanda", "servicio"],
    "Cliente extranjero": [],
    "Agencia de aduana": ["servicio"],
    "Transporte": ["servicio"],
    "Extraportuario": ["servicio"],
}

def puede_publicar(rol: str, tipo_pub: str) -> bool:
    return tipo_pub in RESTRICCIONES_PUBLICAR.get(rol, [])
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final, Parte 2/4)
# Autenticación, Registro, Idiomas, Errores
# =========================================================

# =========================================================
# 🔐 LOGIN / LOGOUT
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia sesión de usuario registrado."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = get_user(email)
        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user"] = email
            flash(t("Inicio de sesión correcto", "Login successful", "登入成功"), "success")
            return redirect(url_for("dashboard_ext"))

        flash(t("Credenciales inválidas", "Invalid credentials", "無效的登入資料"), "error")

    return render_template("login.html", titulo=t("Iniciar Sesión", "Login", "登入"))


@app.route("/logout")
def logout():
    """Cierra sesión y limpia variables de sesión."""
    session.clear()
    flash(t("Sesión cerrada correctamente", "Logged out successfully", "已登出"), "info")
    return redirect(url_for("home"))


# =========================================================
# 📝 REGISTRO DE USUARIOS
# =========================================================
@app.route("/register_router")
def register_router():
    """Pantalla que muestra tipos de usuario disponibles."""
    return render_template(
        "register_router.html",
        roles=ROLES_POR_TIPO,
        titulo=t("Registro", "Register", "註冊")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registra un nuevo usuario manualmente."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        empresa = request.form.get("empresa", "").strip()
        rol = request.form.get("rol", "").strip()
        tipo = request.form.get("tipo", "").strip()
        pais = request.form.get("pais", "CL").strip().upper()
        direccion = request.form.get("direccion", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not email or not password or not empresa:
            flash(t("Completa todos los campos obligatorios.", "Complete all required fields.", "請填寫所有必填欄位"), "error")
            return redirect(url_for("register"))

        if tipo not in TIPOS_VALIDOS:
            tipo = "compraventa"

        # ➕ NUEVO — Validación de rol según tipo
        roles_validos = ROLES_POR_TIPO.get(tipo, [])
        if rol not in roles_validos:
            flash(t("Rol no permitido para este tipo de usuario.", "Role not allowed for this user type.", "角色與類型不符"), "error")
            return redirect(url_for("register"))

        if get_user(email):
            flash(t("El usuario ya existe.", "User already exists.", "使用者已存在"), "warning")
            return redirect(url_for("login"))

        add_user(
            email=email,
            password_hashed=generate_password_hash(password),
            empresa=empresa,
            rol=rol,
            tipo=tipo,
            pais=pais,
            rut_doc=None,
            direccion=direccion,
            telefono=telefono,
        )
        load_users_cache()
        flash(t("Usuario registrado correctamente.", "User registered successfully.", "使用者已註冊"), "success")
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        tipos=TIPOS_VALIDOS,
        roles=ROLES_POR_TIPO,
        titulo=t("Registro", "Register", "註冊")
    )


# =========================================================
# 🏠 HOME
# =========================================================
@app.route("/")
def home():
    """Página principal."""
    return render_template("index.html", titulo="Window Shopping")


# =========================================================
# 🌍 GESTIÓN DE IDIOMA
# =========================================================
@app.route("/lang/<lang>")
def set_lang(lang):
    """Cambia el idioma desde el menú (por POST/GET)."""
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente", "Language updated", "語言已更新"), "info")
    else:
        flash(t("Idioma no soportado", "Unsupported language", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))


@app.route("/set_lang/<lang>")
def set_lang_get(lang):
    """Alias para cambiar idioma con /set_lang/<lang> (compatibilidad)."""
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente", "Language updated", "語言已更新"), "info")
    else:
        flash(t("Idioma no soportado", "Unsupported language", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))


# =========================================================
# ⚙️ RUTAS AUXILIARES / ERRORES
# =========================================================
@app.errorhandler(404)
def not_found_error(e):
    return render_template("404.html", titulo=t("Página no encontrada", "Page not found", "找不到頁面")), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html", titulo=t("Error interno", "Internal error", "內部錯誤")), 500


# =========================================================
# 🚀 INICIALIZACIÓN
# =========================================================
with app.app_context():
    init_db()
    migrate_add_rut_doc()
    migrate_add_contact_fields()
    create_admin_if_missing()
    seed_demo_users()
    load_users_cache()
    print(f"✅ USERS en caché: {len(USERS)} usuarios")
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final, Parte 3/4)
# Dashboard, Carrito, Ocultos, Publicar, Eliminar
# =========================================================

# =========================================================
# 🧭 DASHBOARD PRINCIPAL
# =========================================================
PUBLICACIONES: List[Dict[str, Any]] = []

@app.route("/dashboard_ext", methods=["GET", "POST"])
def dashboard_ext():
    """Panel extendido del usuario con publicaciones y filtros."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    if not user:
        flash(t("Usuario no encontrado.", "User not found.", "未找到用戶"), "error")
        return redirect(url_for("logout"))

    rol = user["rol"]
    filtro = request.args.get("filtro", "oferta").lower()
    if filtro not in ["oferta", "demanda", "servicio"]:
        filtro = "oferta"

    visibles = [
        p for p in PUBLICACIONES
        if p["tipo"] == filtro
        and puede_ver_publicacion(rol, p["rol"], p["tipo"])  # ➕ NUEVO filtro por permisos
        and p["id"] not in get_hidden_items()
    ]
    visibles.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard.html",
        user=user,
        filtro=filtro,
        publicaciones=visibles,
        propias=propias,
        titulo=t("Panel de Usuario", "User Dashboard", "使用者主頁"),
    )


@app.route("/dashboard/filtro/<tipo>")
def dashboard_filtro(tipo):
    """Cambia el filtro del panel."""
    tipo = tipo.lower()
    if tipo not in ["oferta", "demanda", "servicio"]:
        flash(t("Filtro inválido", "Invalid filter", "無效的篩選條件"), "error")
        return redirect(url_for("dashboard_ext"))
    return redirect(url_for("dashboard_ext", filtro=tipo))


# =========================================================
# 🧾 RUTA TEMPORAL — MIS PUBLICACIONES
# (para compatibilidad con botones en dashboard/perfil)
# =========================================================
@app.route("/mis_publicaciones")
def mis_publicaciones():
    """Ruta temporal para compatibilidad con botones en dashboard/perfil."""
    flash(t("Sección en construcción.", "Section under construction.", "頁面建設中"), "info")
    return redirect(url_for("dashboard_ext"))


# =========================================================
# 🧺 CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito")
def carrito():
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para ver el carrito.", "You must log in to view the cart.", "您必須登入以檢視購物車"), "error")
        return redirect(url_for("login"))
    cart = get_cart()
    return render_template("carrito.html", cart=cart, titulo=t("Carrito", "Cart", "購物車"))


@app.route("/carrito/agregar/<pub_id>", methods=["GET", "POST"])
def carrito_agregar(pub_id):
    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(request.referrer or url_for("dashboard_ext"))

    add_to_cart(pub)
    flash(t("Agregado al carrito", "Added to cart", "已加入購物車"), "success")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>", methods=["POST", "GET"])
def carrito_eliminar(index):
    if remove_from_cart(index):
        flash(t("Ítem eliminado del carrito", "Item removed from cart", "已刪除項目"), "info")
    else:
        flash(t("Ítem inexistente", "Item not found", "未找到項目"), "error")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar", methods=["POST", "GET"])
def carrito_vaciar():
    clear_cart()
    flash(t("Carrito vaciado correctamente", "Cart cleared", "購物車已清空"), "info")
    return redirect(url_for("carrito"))


# =========================================================
# 👁️‍🗨️ OCULTAR / RESTABLECER PUBLICACIONES
# =========================================================
@app.route("/ocultar/<pub_id>", methods=["POST", "GET"])
def ocultar_publicacion(pub_id):
    hide_item(pub_id)
    flash(t("Publicación ocultada", "Item hidden", "項目已隱藏"), "info")
    return redirect(url_for("dashboard_ext"))


@app.route("/restablecer_ocultos", methods=["POST", "GET"])
def restablecer_ocultos():
    unhide_all()
    flash(t("Publicaciones restauradas", "Items restored", "已恢復項目"), "success")
    return redirect(url_for("dashboard_ext"))


# =========================================================
# 🧾 NUEVA PUBLICACIÓN
# =========================================================
@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite a un usuario crear una publicación nueva."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para publicar.", "You must log in to post.", "您必須登入以發布"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)

    if request.method == "POST":
        tipo_pub = request.form.get("tipo_pub", "").lower().strip()
        subtipo = request.form.get("subtipo", "").strip()
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip() or "Consultar"

        if tipo_pub not in ["oferta", "demanda", "servicio"]:
            flash(t("Tipo de publicación inválido", "Invalid post type", "無效的發布類型"), "error")
            return redirect(url_for("publicar"))

        if not producto or not descripcion:
            flash(t("Completa todos los campos requeridos", "Complete all required fields", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        # ➕ NUEVO — Validación de permisos para publicar
        if not puede_publicar(user["rol"], tipo_pub):
            flash(t("No tienes permisos para crear este tipo de publicación.", "You are not allowed to post this type.", "無權限發布此類別"), "error")
            return redirect(url_for("dashboard_ext"))

        nueva_pub = {
            "id": f"pub_{uuid.uuid4().hex[:8]}",
            "usuario": user["email"],
            "tipo": tipo_pub,
            "rol": user["rol"],
            "empresa": user["empresa"],
            "producto": producto,
            "precio": precio,
            "descripcion": f"{subtipo.upper()} — {descripcion}" if subtipo else descripcion,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        PUBLICACIONES.append(nueva_pub)
        flash(t("Publicación creada correctamente", "Post created successfully", "發布已成功建立"), "success")
        return redirect(url_for("dashboard_ext"))

    return render_template("publicar.html", titulo=t("Nueva Publicación", "New Post", "新增發布"))


@app.route("/publicacion/eliminar/<pub_id>", methods=["POST", "GET"])
def eliminar_publicacion(pub_id):
    """Permite eliminar publicaciones propias."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    global PUBLICACIONES
    antes = len(PUBLICACIONES)
    PUBLICACIONES = [
        p for p in PUBLICACIONES if not (p["id"] == pub_id and p["usuario"] == user["email"])
    ]
    despues = len(PUBLICACIONES)

    if antes > despues:
        flash(t("Publicación eliminada correctamente", "Post deleted successfully", "已刪除發布"), "success")
    else:
        flash(t("No se encontró la publicación o no tienes permiso", "Not found or unauthorized", "未找到或無權限"), "error")

    return redirect(url_for("dashboard_ext"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final, Parte 4/4)
# Mensajería, Perfil, Clientes, Ayuda, Status, Run
# =========================================================

# =========================================================
# 🔄 UTILIDAD: obtener usuario desde sesión
# =========================================================
def _session_user_dict():
    """Devuelve un dict del usuario actual basado en session['user']."""
    user_email = session.get("user")
    if not user_email:
        return None
    row = get_user(user_email)
    return dict(row) if row else None


# =========================================================
# 💬 MENSAJERÍA ENTRE USUARIOS
# =========================================================
MENSAJES: List[Dict[str, Any]] = []

def puede_enviar_mensaje(origen: str, destino: str) -> bool:
    """Permite un mensaje por ítem cada 3 días entre mismos usuarios."""
    now = datetime.now()
    recientes = [
        m for m in MENSAJES
        if m["origen"] == origen and m["destino"] == destino
    ]
    if not recientes:
        return True
    ultima_fecha = datetime.strptime(recientes[-1]["fecha"], "%Y-%m-%d %H:%M")
    return (now - ultima_fecha).days >= 3


@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    """Sistema simple de mensajería interna."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        destino = request.form.get("destino", "").strip().lower()
        contenido = request.form.get("contenido", "").strip()

        if not destino or not contenido:
            flash(t("Debes completar todos los campos.", "All fields required.", "請填寫所有欄位"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe.", "Recipient not found.", "找不到收件人"), "error")
            return redirect(url_for("mensajes"))

        # ➕ NUEVO — Límite de envío
        if not puede_enviar_mensaje(user["email"], destino):
            flash(t(
                "Ya enviaste un mensaje a este usuario hace menos de 3 días.",
                "You already messaged this user less than 3 days ago.",
                "3天內無法再次發送訊息"
            ), "warning")
            return redirect(url_for("mensajes"))

        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        flash(t("Mensaje enviado correctamente.", "Message sent successfully.", "訊息已發送"), "success")
        return redirect(url_for("mensajes"))

    recibidos = [m for m in MENSAJES if m["destino"] == user["email"]]
    enviados = [m for m in MENSAJES if m["origen"] == user["email"]]
    recibidos.sort(key=lambda x: x["fecha"], reverse=True)
    enviados.sort(key=lambda x: x["fecha"], reverse=True)

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
    """Visualiza o actualiza el perfil del usuario."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.", "You must log in to view your profile.", "您必須登入以檢視個人資料"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        nueva_empresa = request.form.get("empresa", "").strip()
        nuevo_rol = request.form.get("rol", "").strip()
        nueva_dir = request.form.get("direccion", "").strip()
        nuevo_fono = request.form.get("telefono", "").strip()

        update_user_fields(
            user["email"],
            empresa=nueva_empresa or user["empresa"],
            rol=nuevo_rol or user["rol"],
            direccion=nueva_dir or user["direccion"],
            telefono=nuevo_fono or user["telefono"],
        )
        load_users_cache()
        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Tu Perfil", "Your Profile", "個人資料"))


# =========================================================
# 🏢 CLIENTES / DETALLES
# =========================================================
def _armar_cliente_desde_users(username: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Arma un cliente para las vistas de /clientes."""
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": data.get("items", []),
        "email": data.get("email", username),
        "pais": data.get("pais", ""),
        "direccion": data.get("direccion", ""),
        "telefono": data.get("telefono", ""),
    }

@app.route("/clientes")
def clientes():
    """Lista todas las empresas visibles según el rol del usuario."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión para ver empresas.", "You must log in to view companies.", "您必須登入以查看公司"), "error")
        return redirect(url_for("login"))

    visibles = []
    for username, info in USERS.items():
        if info["email"] == user["email"]:
            continue  # no mostrarte a ti mismo
        if puede_ver_publicacion(user["rol"], info["rol"], "oferta") or puede_ver_publicacion(user["rol"], info["rol"], "servicio"):
            visibles.append(_armar_cliente_desde_users(username, info))

    # Paginación básica: 10 por vista
    pagina = int(request.args.get("page", 1))
    inicio = (pagina - 1) * 10
    fin = inicio + 10
    total_paginas = (len(visibles) + 9) // 10
    visibles_pagina = visibles[inicio:fin]

    return render_template(
        "clientes.html",
        clientes=visibles_pagina,
        pagina=pagina,
        total_paginas=total_paginas,
        titulo=t("Empresas", "Companies", "公司")
    )


@app.route("/clientes/<username>")
def cliente_detalle(username):
    """Muestra detalle individual del cliente."""
    if username not in USERS:
        abort(404)
    c = _armar_cliente_desde_users(username, USERS[username])
    puede_mensaje = False
    user = _session_user_dict()
    if user and puede_enviar_mensaje(user["email"], c["email"]):
        puede_mensaje = True
    return render_template("cliente_detalle.html", c=c, puede_mensaje=puede_mensaje, titulo=c["empresa"])


# =========================================================
# 💬 AYUDA / ACERCA / STATUS
# =========================================================
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo=t("Centro de Ayuda", "Help Center", "幫助中心"))


@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping", "About Window Shopping", "關於 Window Shopping"))


@app.route("/status")
def status():
    """Devuelve estado del servidor en formato JSON."""
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
