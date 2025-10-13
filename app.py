# =========================================================
# 🌐 WINDOW SHOPPING — Flask App Final (v3.3, Octubre 2025)
# Autor: Christopher Ponce & GPT-5
# =========================================================

import os
import sqlite3
from datetime import timedelta
from typing import List, Dict, Any, Optional

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
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
    "servicios": [
        "Agencia de aduana", "Transporte", "Extraportuario",
        "Packing", "Frigorífico"
    ],
    "compraventa": [
        "Productor(planta)", "Packing", "Frigorífico", "Exportador"
    ],
    "mixto": ["Packing", "Frigorífico"],
}


# =========================================================
# 🗄️ BASE DE DATOS (SQLite) — Usuarios y autenticación
# =========================================================
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    """Crea la base de datos y la tabla de usuarios si no existen."""
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
            pais TEXT
        )
    """)
    conn.commit()
    conn.close()

def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def migrate_db():
    """Migraciones suaves (añadir columnas si faltan)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Añadir columna para almacenar el documento RUT si no existe
    if not _column_exists(c, "users", "rut_doc"):
        try:
            c.execute("ALTER TABLE users ADD COLUMN rut_doc TEXT")
            conn.commit()
            print("🛠️ Migración: columna 'rut_doc' agregada a users.")
        except Exception as e:
            print(f"⚠️ No se pudo migrar 'rut_doc': {e}")
    conn.close()

def create_admin_if_missing():
    """Crea un usuario administrador si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE email = ?", ("admin@ws.com",))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin@ws.com", "1234", "Window Shopping Admin",
              "Exportador", "compraventa", "CL", None))
        conn.commit()
        print("✅ Usuario admin creado: admin@ws.com / 1234")
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

def add_user(email, password, empresa, rol, tipo, pais, rut_doc: Optional[str] = None):
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
# 📁 FUNCIÓN AUXILIAR PARA SUBIDA DE ARCHIVOS
# =========================================================
def save_uploaded_file(file_storage) -> Optional[str]:
    """
    Guarda un archivo subido en la carpeta /static/uploads.
    Retorna la ruta relativa del archivo guardado (p.ej. 'uploads/archivo.pdf')
    o None si falla/si no hay archivo.
    """
    if not file_storage or getattr(file_storage, "filename", "") == "":
        return None
    if allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        # Evitar colisiones simples
        base, ext = os.path.splitext(filename)
        counter = 1
        final_name = filename
        while os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], final_name)):
            final_name = f"{base}_{counter}{ext}"
            counter += 1
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
        file_storage.save(save_path)
        rel = f"uploads/{final_name}"
        print(f"📂 Archivo guardado: {save_path}")
        return rel
    else:
        print("⚠️ Formato de archivo no permitido.")
        return None


# =========================================================
# 👤 SEED: USUARIOS FICTICIOS (2 por rol)
# =========================================================
def seed_demo_users():
    """
    Crea 2 usuarios por rol respetando TIPOS/ROLES.
    Contraseña por defecto: '1234'
    """
    demo: List[Dict[str, str]] = [
        # ——— COMPRAVENTA (Productor, Packing, Frigorífico, Exportador) ———
        {"email": "prod1@demo.cl",  "empresa": "Productora Valle 1", "rol": "Productor(planta)", "tipo": "compraventa", "pais": "CL"},
        {"email": "prod2@demo.cl",  "empresa": "Agro Campo 2",       "rol": "Productor(planta)", "tipo": "compraventa", "pais": "CL"},

        {"email": "pack1@demo.cl",  "empresa": "Packing Maule 1",    "rol": "Packing",           "tipo": "compraventa", "pais": "CL"},
        {"email": "pack2@demo.cl",  "empresa": "Packing Ñuble 2",    "rol": "Packing",           "tipo": "compraventa", "pais": "CL"},

        {"email": "frio1@demo.cl",  "empresa": "Frigorífico Sur 1",  "rol": "Frigorífico",       "tipo": "compraventa", "pais": "CL"},
        {"email": "frio2@demo.cl",  "empresa": "Frigorífico Norte 2","rol": "Frigorífico",       "tipo": "compraventa", "pais": "CL"},

        {"email": "exp1@demo.cl",   "empresa": "Exportadora Andes A","rol": "Exportador",        "tipo": "compraventa", "pais": "CL"},
        {"email": "exp2@demo.cl",   "empresa": "Exportadora Pacífico","rol": "Exportador",       "tipo": "compraventa", "pais": "CL"},

        # ——— SERVICIOS ———
        {"email": "aduana1@demo.cl","empresa": "Agencia Andes",      "rol": "Agencia de aduana", "tipo": "servicios", "pais": "CL"},
        {"email": "aduana2@demo.cl","empresa": "Agencia Pacífico",   "rol": "Agencia de aduana", "tipo": "servicios", "pais": "CL"},

        {"email": "trans1@demo.cl", "empresa": "Transporte Ruta 5",  "rol": "Transporte",        "tipo": "servicios", "pais": "CL"},
        {"email": "trans2@demo.cl", "empresa": "Logística Express",  "rol": "Transporte",        "tipo": "servicios", "pais": "CL"},

        {"email": "extra1@demo.cl", "empresa": "Depósito San A.",    "rol": "Extraportuario",    "tipo": "servicios", "pais": "CL"},
        {"email": "extra2@demo.cl", "empresa": "Depósito Los Andes", "rol": "Extraportuario",    "tipo": "servicios", "pais": "CL"},

        {"email": "packserv1@demo.cl","empresa": "Packing Service 1","rol": "Packing",           "tipo": "servicios", "pais": "CL"},
        {"email": "frioserv1@demo.cl","empresa": "Frigo Service 1",  "rol": "Frigorífico",       "tipo": "servicios", "pais": "CL"},

        # ——— MIXTO (solo Packing / Frigorífico permitidos) ———
        {"email": "mixpack1@demo.cl","empresa": "Packing Mixto Uno", "rol": "Packing",           "tipo": "mixto", "pais": "CL"},
        {"email": "mixfrio1@demo.cl","empresa": "Frigo Mixto Uno",   "rol": "Frigorífico",       "tipo": "mixto", "pais": "CL"},

        # ——— COMPRAS (cliente extranjero) ———
        {"email": "cliente1@ext.com","empresa": "Buyer Asia LTD",    "rol": "Cliente extranjero","tipo": "compras", "pais": "CN"},
        {"email": "cliente2@ext.com","empresa": "Import USA LLC",    "rol": "Cliente extranjero","tipo": "compras", "pais": "US"},
    ]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for u in demo:
        c.execute("SELECT 1 FROM users WHERE email = ?", (u["email"],))
        if not c.fetchone():
            try:
                c.execute("""
                    INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (u["email"], "1234", u["empresa"], u["rol"], u["tipo"], u["pais"], None))
                conn.commit()
                print(f"🧑‍💼 Usuario ficticio agregado: {u['email']}")
            except Exception as e:
                print(f"⚠️ No se pudo crear demo {u['email']}: {e}")
    conn.close()


# =========================================================
# 🔌 INICIALIZACIÓN (no borra tu flujo)
# =========================================================
init_db()
migrate_db()
create_admin_if_missing()
seed_demo_users()
# =========================================================
# 👥 AUTENTICACIÓN Y REGISTRO
# =========================================================

from flask import jsonify

# ---------------------------------------------------------
# 🔐 LOGIN
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")

        user = get_user(email)
        if not user or user["password"] != password:
            return render_template("login.html", error="❌ Credenciales incorrectas")

        # Crear sesión persistente
        session.permanent = True
        session["user"] = {
            "email": user["email"],
            "empresa": user["empresa"],
            "rol": user["rol"],
            "tipo": user["tipo"],
            "pais": user["pais"],
        }

        flash(f"👋 Bienvenido {user['empresa']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------------------------------------------------
# 🚪 LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("👋 Sesión cerrada correctamente.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------
# 📝 REGISTRO DE NUEVOS USUARIOS
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    tipos = sorted(list(TIPOS_VALIDOS))
    roles_default = sorted({r for roles in ROLES_POR_TIPO.values() for r in roles})

    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")
        empresa = request.form.get("empresa")
        tipo = request.form.get("tipo")
        rol = request.form.get("rol")
        pais = request.form.get("pais", "CL").upper()

        if not all([email, password, empresa, tipo, rol]):
            flash("⚠️ Todos los campos son obligatorios.", "warning")
            return render_template("register.html", tipos=tipos, roles=roles_default)

        if tipo not in TIPOS_VALIDOS:
            flash("⚠️ Tipo de cuenta no válido.", "error")
            return render_template("register.html", tipos=tipos, roles=roles_default)

        if rol not in ROLES_POR_TIPO[tipo]:
            flash("⚠️ El rol no coincide con el tipo seleccionado.", "error")
            return render_template("register.html", tipos=tipos, roles=roles_default)

        # Guardar documento RUT (opcional)
        rut_doc_path = None
        file = request.files.get("rut_doc")
        if file and allowed_file(file.filename):
            rut_doc_path = save_uploaded_file(file)

        add_user(email, password, empresa, rol, tipo, pais, rut_doc_path)
        flash("✅ Cuenta creada correctamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", tipos=tipos, roles=roles_default)


# ---------------------------------------------------------
# 🔄 API INTERNA PARA ACTUALIZAR ROLES POR TIPO
# ---------------------------------------------------------
@app.route("/api/roles/<tipo>")
def api_roles_por_tipo(tipo):
    """Devuelve los roles válidos según el tipo elegido (para uso dinámico en el front)."""
    roles = ROLES_POR_TIPO.get(tipo, [])
    return jsonify({"roles": roles})


# =========================================================
# 🔒 FUNCIONES AUXILIARES DE SESIÓN
# =========================================================
def usuario_actual():
    """Devuelve el usuario actualmente logueado (objeto sqlite Row o None)."""
    if "user" not in session:
        return None
    data = session["user"]
    return get_user(data["email"])

def login_requerido(func):
    """Decorador para rutas que exigen sesión activa."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("⚠️ Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper
# =========================================================
# 🧭 DASHBOARD Y SECCIONES PRINCIPALES
# =========================================================
@app.route("/dashboard")
@login_requerido
def dashboard():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Simulación: publicaciones relevantes (según tipo)
    publicaciones = []
    if user["tipo"] == "compras":
        c.execute("SELECT * FROM users WHERE tipo='compraventa'")
    elif user["tipo"] == "servicios":
        c.execute("SELECT * FROM users WHERE tipo='compras' OR tipo='compraventa'")
    elif user["tipo"] in ("compraventa", "mixto"):
        c.execute("SELECT * FROM users WHERE tipo!='compras'")
    publicaciones = c.fetchall()
    conn.close()

    return render_template("dashboard.html", user=user, publicaciones=publicaciones)


# =========================================================
# 🛒 COMPRAS (solo clientes extranjeros)
# =========================================================
@app.route("/compras", methods=["GET"])
@login_requerido
def compras():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    query = request.args.get("q", "").lower()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE tipo='compraventa'")
    data = [d for d in c.fetchall() if query in d["empresa"].lower() or query in d["rol"].lower()]
    conn.close()

    return render_template("detalle_compras.html", data=data)


# =========================================================
# 💰 VENTAS (solo nacional o mixto)
# =========================================================
@app.route("/ventas", methods=["GET"])
@login_requerido
def ventas():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    query = request.args.get("q", "").lower()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE tipo='compras'")
    demandas = [d for d in c.fetchall() if query in d["empresa"].lower() or query in d["rol"].lower()]
    conn.close()

    return render_template("detalle_ventas.html", demandas=demandas)


# =========================================================
# 🧰 SERVICIOS (packing, frigorífico, transporte, aduana)
# =========================================================
@app.route("/servicios", methods=["GET"])
@login_requerido
def servicios():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE tipo='servicios'")
    servicios_data = c.fetchall()
    conn.close()

    return render_template("detalle_servicios.html", data=servicios_data)


# =========================================================
# 🧾 CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito")
@login_requerido
def carrito():
    cart = session.get("cart", [])
    return render_template("carrito.html", cart=cart)

@app.route("/carrito/agregar/<pub_id>", methods=["POST"])
@login_requerido
def carrito_agregar(pub_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (pub_id,))
    pub = c.fetchone()
    conn.close()

    if not pub:
        flash("⚠️ Publicación no encontrada.", "warning")
        return redirect(url_for("dashboard"))

    cart = session.get("cart", [])
    cart.append({
        "empresa": pub["empresa"],
        "rol": pub["rol"],
        "descripcion": f"Oferta de {pub['empresa']} ({pub['rol']})",
        "tipo": pub["tipo"]
    })
    session["cart"] = cart
    flash(f"🛒 {pub['empresa']} agregado al carrito.", "success")
    return redirect(url_for("carrito"))

@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
@login_requerido
def carrito_eliminar(index):
    cart = session.get("cart", [])
    if 0 <= index < len(cart):
        eliminado = cart.pop(index)
        session["cart"] = cart
        flash(f"🗑️ {eliminado['empresa']} eliminado del carrito.", "info")
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar", methods=["POST"])
@login_requerido
def carrito_vaciar():
    session["cart"] = []
    flash("🧺 Carrito vaciado correctamente.", "info")
    return redirect(url_for("carrito"))

@app.route("/carrito/confirmar", methods=["POST"])
@login_requerido
def carrito_confirmar():
    session["cart"] = []
    flash("✅ Pedido confirmado y enviado.", "success")
    return redirect(url_for("dashboard"))


# =========================================================
# 🔍 DETALLES GENERALES
# =========================================================
@app.route("/detalle/<tipo>/<int:uid>")
@login_requerido
def detalle_generico(tipo, uid):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    comp = c.fetchone()
    conn.close()

    if not comp:
        abort(404)

    if tipo == "compras":
        template = "detalle_compras.html"
    elif tipo == "ventas":
        template = "detalle_ventas.html"
    elif tipo == "servicios":
        template = "detalle_servicios.html"
    else:
        template = "detalle.html"

    return render_template(template, comp=comp)


# =========================================================
# 🌍 MULTILENGUAJE Y HOME
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
    "Página no encontrada": {"en": "Page not found", "zh": "找不到頁面"},
    "Error interno del servidor": {"en": "Internal server error", "zh": "伺服器內部錯誤"},
}

@app.context_processor
def inject_translator():
    def t(es: str, en: str = None, zh: str = None) -> str:
        lang = session.get("lang", "es")
        if lang == "en":
            return TRANSLATIONS.get(es, {}).get("en", en or es)
        if lang == "zh":
            return TRANSLATIONS.get(es, {}).get("zh", zh or es)
        return es
    return dict(t=t)

@app.route("/set_lang", methods=["POST"])
def set_lang():
    lang = request.form.get("lang", "es")
    session["lang"] = lang
    flash("🌍 Idioma cambiado correctamente.", "info")
    return redirect(request.referrer or url_for("home"))

@app.route("/")
def home():
    return render_template("home.html")

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


# =========================================================
# 🚀 EJECUCIÓN
# =========================================================
if __name__ == "__main__":
    print("🚀 Iniciando Window Shopping (v3.3) — Flask server listo.")
    app.run(debug=True, host="0.0.0.0", port=5000)
