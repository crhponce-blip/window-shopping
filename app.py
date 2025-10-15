# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final) — PARTE 1/4
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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# =========================================================
# 🌎 MULTI-IDIOMA
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

def get_all_users() -> List[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(email, password_hashed, empresa, rol, tipo, pais,
             rut_doc=None, direccion=None, telefono=None):
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
# 👤 SEMILLAS Y CARGA DE USUARIOS
# =========================================================
def create_admin_if_missing():
    if not get_user("admin@ws.com"):
        add_user(
            "admin@ws.com", generate_password_hash("1234"),
            "Window Shopping Admin", "Exportador", "compraventa", "CL",
            direccion="Santiago CL", telefono="+56 2 2222 2222"
        )
        print("✅ Usuario admin creado (1234)")

def seed_demo_users():
    seeds = [
        ("prod1@demo.cl", "Productora Valle SpA", "Productor(planta)", "compraventa", "CL"),
        ("pack1@demo.cl", "Packing Maule SpA", "Packing", "compraventa", "CL"),
        ("frio1@demo.cl", "Frío Centro SpA", "Frigorífico", "compraventa", "CL"),
        ("exp1@demo.cl", "Exportadora Andes", "Exportador", "compraventa", "CL"),
        ("aduana1@demo.cl", "Agencia Andes", "Agencia de aduana", "servicios", "CL"),
        ("cliente1@ext.com", "Importadora Asia Ltd.", "Cliente extranjero", "compras", "US"),
    ]
    for email, empresa, rol, tipo, pais in seeds:
        if not get_user(email):
            add_user(email, generate_password_hash("1234"), empresa, rol, tipo, pais)

USERS: Dict[str, Dict[str, Any]] = {}

def load_users_cache():
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
# 🧩 HELPERS DE CLIENTES
# =========================================================
def _normaliza_items(items: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    out = []
    for it in items or []:
        out.append({
            "nombre": it.get("producto") or it.get("servicio") or "Item",
            "tipo": it.get("tipo") or "item",
            "detalle": it.get("descripcion") or it.get("detalle") or ""
        })
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
        "pais": data.get("pais", ""),
        "direccion": data.get("direccion", ""),
        "telefono": data.get("telefono", ""),
    }
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final) — PARTE 2/4
# Permisos por rol, publicaciones demo e inicialización
# =========================================================

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
# 🏁 INICIALIZACIÓN (orden correcto)
# =========================================================
init_db()
migrate_add_rut_doc()
migrate_add_contact_fields()
create_admin_if_missing()
seed_demo_users()
load_users_cache()
print(f"✅ USERS en caché: {len(USERS)} usuarios")
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final) — PARTE 3/4
# Rutas públicas, Login/Logout, Registro, Idioma, Errores
# =========================================================

# ---------------------------------------------------------
# 🗂️ Helper: guardar archivo subido (RUT/doc)
# ---------------------------------------------------------
def save_uploaded_file(file_storage):
    """
    Guarda un archivo subido en UPLOAD_FOLDER si su extensión es válida.
    Retorna la ruta relativa dentro de /static (ej: "uploads/archivo.pdf") o None.
    """
    if not file_storage or file_storage.filename == "":
        return None
    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename):
        return None
    # Evita colisiones
    base, ext = os.path.splitext(filename)
    final_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
    file_storage.save(dest)
    # Devolvemos ruta relativa desde /static
    return f"uploads/{final_name}"

# =========================================================
# 🏠 HOME
# =========================================================
@app.route("/")
def home():
    """Página principal"""
    titulo = t("Inicio", "Home", "主頁")
    return render_template("home.html", titulo=titulo)

# =========================================================
# 🔐 LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = get_user(email)
        if not user:
            flash(t("Usuario no encontrado", "User not found", "未找到用戶"), "error")
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash(t("Contraseña incorrecta", "Incorrect password", "密碼錯誤"), "error")
            return redirect(url_for("login"))

        # Guardamos solo el correo para evitar objetos no serializables
        session["user"] = email
        flash(t("Inicio de sesión correcto", "Login successful", "登入成功"), "success")
        return redirect(url_for("dashboard_ext"))

    titulo = t("Iniciar sesión", "Login", "登入")
    return render_template("login.html", titulo=titulo)

# =========================================================
# 🚪 LOGOUT
# =========================================================
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente", "Logged out", "登出成功"), "info")
    return redirect(url_for("home"))

# =========================================================
# 🧭 REGISTRO (router por tipo) + formulario
# =========================================================
@app.route("/register_router")
def register_router():
    """Página donde se elige tipo de registro."""
    return render_template("register_router.html", titulo=t("Registrarse", "Register", "註冊"))

@app.route("/register/<tipo>", methods=["GET", "POST"])
def register(tipo):
    """Formulario de registro según tipo: compras, servicios, mixto o compraventa."""
    tipo = tipo.lower()
    if tipo not in TIPOS_VALIDOS:
        abort(404)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        empresa = request.form.get("empresa", "").strip()
        rol = request.form.get("rol", "").strip()
        pais = request.form.get("pais", "").strip()
        direccion = request.form.get("direccion", "").strip() or None
        telefono = request.form.get("telefono", "").strip() or None

        # Archivo (RUT/doc) desde <input type="file" name="rut_doc">
        rut_doc_file = request.files.get("rut_doc")
        rut_doc_path = save_uploaded_file(rut_doc_file)

        if not email or not password or not empresa or not rol or not pais:
            flash(t("Completa todos los campos requeridos",
                    "Complete all required fields",
                    "請填寫所有必填欄位"), "error")
            return redirect(url_for("register", tipo=tipo))

        if get_user(email):
            flash(t("El correo ya está registrado", "Email already registered", "郵箱已註冊"), "error")
            return redirect(url_for("register", tipo=tipo))

        hashed_pw = generate_password_hash(password)
        add_user(
            email=email,
            password_hashed=hashed_pw,
            empresa=empresa,
            rol=rol,
            tipo=tipo,
            pais=pais,
            rut_doc=rut_doc_path,
            direccion=direccion,
            telefono=telefono,
        )
        load_users_cache()

        flash(t("Registro completado con éxito", "Registration successful", "註冊成功"), "success")
        return redirect(url_for("login"))

    roles = ROLES_POR_TIPO.get(tipo, [])
    titulo = t("Registro", "Register", "註冊")
    return render_template("register.html", tipo=tipo, roles=roles, titulo=titulo)

# =========================================================
# 🌍 IDIOMA (compatibles con tu base.html y formularios)
# =========================================================
@app.route("/lang/<code>")
def lang(code):
    """Cambia el idioma a través de URL /lang/es /lang/en /lang/zh"""
    if code in ["es", "en", "zh"]:
        session["lang"] = code
        flash(t("Idioma actualizado correctamente.", "Language updated successfully.", "語言已成功更新"), "info")
    else:
        flash(t("Idioma no soportado.", "Unsupported language.", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))

# — ruta EXACTA que usa tu base.html (GET /set_lang/<lang>) —
@app.route("/set_lang/<lang>")
def set_lang_get(lang):
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente.", "Language updated successfully.", "語言已成功更新"), "info")
    else:
        flash(t("Idioma no soportado.", "Unsupported language.", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))

# — compatibilidad si decides usar <form method="post"> —
@app.route("/set_lang", methods=["POST"])
def set_lang_post():
    lang = request.form.get("lang")
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente.", "Language updated successfully.", "語言已成功更新"), "info")
    else:
        flash(t("Idioma no soportado.", "Unsupported language.", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))

# =========================================================
# 🚨 ERRORES PERSONALIZADOS (usa variables code y message)
# =========================================================
@app.errorhandler(404)
def error_404(e):
    return render_template(
        "error.html",
        code=404,
        message=t("Página no encontrada", "Page not found", "找不到頁面"),
    ), 404

@app.errorhandler(500)
def error_500(e):
    return render_template(
        "error.html",
        code=500,
        message=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤"),
    ), 500
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.4 Final) — PARTE 4/4
# Mensajería, Perfil, Clientes, Ayuda/Acerca/Status, Run
# =========================================================

def _session_user_dict():
    """Devuelve un dict de usuario actual desde session["user"]."""
    u = session.get("user")
    if not u:
        return None
    if isinstance(u, dict):
        return u
    try:
        import sqlite3 as _sqlite3
        if isinstance(u, _sqlite3.Row):
            return dict(u)
    except Exception:
        pass
    if isinstance(u, str):
        row = get_user(u)
        return dict(row) if row else None
    return None

# =========================================================
# 💬 MENSAJERÍA ENTRE USUARIOS
# =========================================================
MENSAJES: List[Dict[str, Any]] = []

@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
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

        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        flash(t("Mensaje enviado correctamente.", "Message sent successfully.", "訊息已發送"), "success")
        return redirect(url_for("mensajes"))

    recibidos = sorted(
        [m for m in MENSAJES if m["destino"] == user["email"]],
        key=lambda x: x["fecha"], reverse=True
    )
    enviados = sorted(
        [m for m in MENSAJES if m["origen"] == user["email"]],
        key=lambda x: x["fecha"], reverse=True
    )

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
    user = _session_user_dict()
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
        session["user"] = user
        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Tu Perfil", "Your Profile", "個人資料"))

# =========================================================
# 🏢 CLIENTES / DETALLE (USERS)
# =========================================================
@app.route("/clientes")
def clientes():
    data = [_armar_cliente_desde_users(username, info) for username, info in USERS.items()]
    return render_template("clientes.html", clientes=data, titulo=t("Empresas", "Companies", "公司"))

@app.route("/clientes/<username>")
def cliente_detalle(username):
    if username not in USERS:
        abort(404)
    cliente = _armar_cliente_desde_users(username, USERS[username])
    return render_template("cliente_detalle.html", c=cliente, titulo=cliente["empresa"])

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
