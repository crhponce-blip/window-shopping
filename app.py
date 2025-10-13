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


def create_admin_if_missing():
    """Crea el usuario administrador y usuarios ficticios si no existen."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # === Admin principal ===
    c.execute("SELECT * FROM users WHERE email = ?", ("admin@ws.com",))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("admin@ws.com", "1234", "Window Shopping Admin",
              "Exportador", "compraventa", "CL"))
        conn.commit()
        print("✅ Usuario admin creado: admin@ws.com / 1234")

    # === Usuarios ficticios (por tipo y rol) ===

    usuarios_ficticios = [
        # --- COMPRAVENTA ---
        ("prod1@demo.cl", "1234", "Productores del Sur", "Productor(planta)", "compraventa", "CL"),
        ("prod2@demo.cl", "1234", "Agrícola Los Ríos", "Productor(planta)", "compraventa", "CL"),
        ("pack1@demo.cl", "1234", "Packing Andes SpA", "Packing", "compraventa", "CL"),
        ("pack2@demo.cl", "1234", "Packing Valle Central", "Packing", "compraventa", "CL"),
        ("frio1@demo.cl", "1234", "Frigorífico Los Andes", "Frigorífico", "compraventa", "CL"),
        ("frio2@demo.cl", "1234", "Frío Sur Ltda.", "Frigorífico", "compraventa", "CL"),
        ("exp1@demo.cl", "1234", "Exportadora Chile Global", "Exportador", "compraventa", "CL"),
        ("exp2@demo.cl", "1234", "Exportadora Andes SpA", "Exportador", "compraventa", "CL"),

        # --- SERVICIOS ---
        ("aduana1@demo.cl", "1234", "Agencia Andes", "Agencia de aduana", "servicios", "CL"),
        ("aduana2@demo.cl", "1234", "Agencia Pacífico", "Agencia de aduana", "servicios", "CL"),
        ("trans1@demo.cl", "1234", "Transporte del Maule", "Transporte", "servicios", "CL"),
        ("trans2@demo.cl", "1234", "Trans Andes Cargo", "Transporte", "servicios", "CL"),
        ("extra1@demo.cl", "1234", "Terminal Extraportuario Norte", "Extraportuario", "servicios", "CL"),
        ("extra2@demo.cl", "1234", "Centro Logístico Sur", "Extraportuario", "servicios", "CL"),

        # --- MIXTO ---
        ("mixpack1@demo.cl", "1234", "Packing Mixto Norte", "Packing", "mixto", "CL"),
        ("mixfrio1@demo.cl", "1234", "Frigorífico Integral SpA", "Frigorífico", "mixto", "CL"),

        # --- COMPRAS ---
        ("cliente1@ext.com", "1234", "Importadora Asia Ltd.", "Cliente extranjero", "compras", "CN"),
        ("cliente2@ext.com", "1234", "Hong Kong Fresh Co.", "Cliente extranjero", "compras", "HK"),
    ]

    for email, password, empresa, rol, tipo, pais in usuarios_ficticios:
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO users (email, password, empresa, rol, tipo, pais)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email, password, empresa, rol, tipo, pais))
            print(f"🧑‍💼 Usuario ficticio agregado: {email}")

    conn.commit()
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


def add_user(email, password, empresa, rol, tipo, pais):
    """Agrega un nuevo usuario al sistema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email, password, empresa, rol, tipo, pais))
        conn.commit()
        print(f"🆕 Usuario creado: {email}")
    except sqlite3.IntegrityError:
        print(f"⚠️ El usuario {email} ya existe.")
    finally:
        conn.close()


# =========================================================
# 📁 FUNCIÓN AUXILIAR PARA SUBIDA DE ARCHIVOS
# =========================================================
def save_uploaded_file(file_storage) -> str | None:
    """
    Guarda un archivo subido en la carpeta /static/uploads.
    Retorna la ruta relativa del archivo guardado o None si falla.
    """
    if not file_storage or file_storage.filename == "":
        return None

    if allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file_storage.save(save_path)
        print(f"📂 Archivo guardado: {save_path}")
        return f"uploads/{filename}"
    else:
        print("⚠️ Formato de archivo no permitido.")
        return None


# Inicialización automática
init_db()
create_admin_if_missing()
# =========================================================
# 🧭 PARTE 2 — Autenticación (Login, Registro) + Validadores
# =========================================================

from flask import request  # aseguramos disponibilidad

# ------------------------------
# 🧾 VALIDADORES Y NORMALIZADORES
# ------------------------------
def _normaliza_tipo(tipo: str) -> str:
    """Normaliza el tipo de cuenta (asegura formato uniforme)."""
    tipo = (tipo or "").strip().lower()
    if tipo in {"compra-venta", "compra_venta", "cv"}:
        return "compraventa"
    return tipo if tipo in TIPOS_VALIDOS else ""

def _rol_valido_para_tipo(rol: str, tipo: str) -> bool:
    """Valida si el rol pertenece al tipo de cuenta."""
    return rol in ROLES_POR_TIPO.get(tipo, [])


# ------------------------------
# 🔒 LOGIN (SQLite)
# ------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión conectado a la base de datos SQLite."""
    if request.method == "POST":
        email = (
            (request.form.get("username") or request.form.get("usuario") or "")
            .strip()
            .lower()
        )
        password = (request.form.get("password") or "").strip()

        user = get_user(email)
        if user and user["password"] == password:
            session["user"] = {
                "id": user["id"],
                "email": user["email"],
                "empresa": user["empresa"],
                "rol": user["rol"],
                "tipo": user["tipo"],
                "pais": user["pais"],
            }
            # Mantener sesión permanente
            session.permanent = True
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas", "error")
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


# ------------------------------
# 🧩 REGISTRO (SQLite) — con validaciones completas + archivo RUT
# ------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios con validación por tipo/rol y archivo RUT."""
    roles_catalogo = [
        "Cliente extranjero",
        "Productor(planta)",
        "Packing",
        "Frigorífico",
        "Exportador",
        "Agencia de aduana",
        "Extraportuario",
        "Transporte",
    ]
    tipos_catalogo = ["compras", "servicios", "mixto", "compraventa"]

    if request.method == "POST":
        # Campos del formulario
        email = (
            (request.form.get("usuario") or request.form.get("username") or "")
            .strip()
            .lower()
        )
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        tipo = _normaliza_tipo(request.form.get("tipo") or "")
        pais = (request.form.get("pais") or "CL").strip().upper()
        rut_file = request.files.get("rut_file")

        # Validaciones básicas
        if not all([email, password, empresa, rol, tipo]):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("register"))

        if not _rol_valido_para_tipo(rol, tipo):
            flash("El rol seleccionado no corresponde al tipo de cuenta.", "error")
            return redirect(url_for("register"))

        if rol == "Cliente extranjero" and tipo != "compras":
            flash("Cliente extranjero solo puede ser tipo 'compras'.", "error")
            return redirect(url_for("register"))

        if rol == "Exportador" and tipo not in {"compraventa"}:
            flash("Exportador debe ser tipo 'compraventa'.", "error")
            return redirect(url_for("register"))

        if len(pais) != 2:
            flash("El código de país debe tener 2 letras (ej: CL, US).", "error")
            return redirect(url_for("register"))

        # Validar existencia previa
        existing = get_user(email)
        if existing:
            flash("El usuario ya existe.", "error")
            return redirect(url_for("register"))

        # Subir archivo RUT
        if rut_file:
            saved_path = save_uploaded_file(rut_file)
            if not saved_path:
                flash("Error al subir el archivo RUT.", "error")
                return redirect(url_for("register"))
            else:
                print(f"📎 Archivo RUT recibido para {email}: {saved_path}")
        else:
            flash("Debe adjuntar el archivo RUT (PDF o imagen).", "error")
            return redirect(url_for("register"))

        # Agregar usuario
        add_user(email, password, empresa, rol, tipo, pais)
        flash("Usuario registrado exitosamente.", "success")
        return redirect(url_for("login"))

    # GET
    return render_template(
        "register.html",
        roles=roles_catalogo,
        tipos=tipos_catalogo,
        roles_por_tipo=ROLES_POR_TIPO,
    )
# =========================================================
# 🧭 PARTE 3 — Dashboard, Publicaciones y Vistas Dinámicas
# =========================================================

# ------------------------------
# 🧱 SIMULADOR DE PUBLICACIONES (Datos iniciales)
# ------------------------------
PUBLICACIONES = [
    {
        "id": 1,
        "titulo": "Exportación de Trufas Negras",
        "empresa": "Exportadora Chile Global",
        "rol": "Exportador",
        "tipo": "compraventa",
        "descripcion": "Trufas negras frescas desde la Región del Maule, certificadas SAG y con envío aéreo.",
        "precio": 12000,
        "moneda": "USD/kg",
        "pais": "CL",
        "stock": "Disponible",
    },
    {
        "id": 2,
        "titulo": "Servicio de Transporte Refrigerado",
        "empresa": "Trans Andes Cargo",
        "rol": "Transporte",
        "tipo": "servicios",
        "descripcion": "Transporte nacional refrigerado para frutas y trufas con monitoreo GPS.",
        "precio": 850,
        "moneda": "USD/envío",
        "pais": "CL",
        "stock": "Disponible",
    },
    {
        "id": 3,
        "titulo": "Clientes internacionales buscan frutas frescas",
        "empresa": "Importadora Asia Ltd.",
        "rol": "Cliente extranjero",
        "tipo": "compras",
        "descripcion": "Buscamos exportadores chilenos de fruta fresca, especialmente ciruelas y cerezas.",
        "precio": 0,
        "moneda": "",
        "pais": "CN",
        "stock": "Abierto a cotizaciones",
    },
    {
        "id": 4,
        "titulo": "Servicio de Agencia de Aduana",
        "empresa": "Agencia Pacífico",
        "rol": "Agencia de aduana",
        "tipo": "servicios",
        "descripcion": "Gestión documental y tramitación de exportaciones e importaciones en puertos chilenos.",
        "precio": 350,
        "moneda": "USD/servicio",
        "pais": "CL",
        "stock": "Disponible",
    },
]

# ------------------------------
# 💼 DASHBOARD (Vista general)
# ------------------------------
@app.route("/dashboard")
def dashboard():
    """Panel principal del usuario según su tipo y rol."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    rol = user.get("rol", "")
    tipo = user.get("tipo", "")

    # Filtrar publicaciones según visibilidad lógica
    visibles = []
    for p in PUBLICACIONES:
        # Reglas de visibilidad simples y coherentes con los flujos reales:
        if tipo == "compras" and p["tipo"] == "compraventa":
            visibles.append(p)
        elif tipo == "compraventa" and p["tipo"] in {"servicios", "compras"}:
            visibles.append(p)
        elif tipo == "servicios" and p["tipo"] in {"compraventa"}:
            visibles.append(p)
        elif tipo == "mixto" and p["tipo"] in {"servicios", "compraventa"}:
            visibles.append(p)

    return render_template(
        "dashboard.html",
        user=user,
        publicaciones=visibles,
    )


# ------------------------------
# 🛒 CARRITO (Vista de compras o servicios seleccionados)
# ------------------------------
@app.route("/carrito")
def carrito():
    """Carrito de compras o solicitudes de servicio."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("carrito.html", user=user)


# ------------------------------
# 📦 DETALLES DE PUBLICACIÓN (según tipo)
# ------------------------------
@app.route("/detalle/<int:pub_id>")
def detalle(pub_id):
    """Detalle de una publicación según el tipo de usuario."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    publicacion = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not publicacion:
        abort(404)

    tipo = publicacion["tipo"]
    if tipo == "compraventa":
        template = "detalle_compras.html"
    elif tipo == "servicios":
        template = "detalle_servicios.html"
    elif tipo == "compras":
        template = "detalle_ventas.html"
    else:
        template = "detalle_generico.html"

    return render_template(template, user=user, publicacion=publicacion)


# ------------------------------
# ❌ CIERRE DE SESIÓN
# ------------------------------
@app.route("/logout")
def logout():
    """Cierra la sesión actual."""
    session.pop("user", None)
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))
# =========================================================
# 🧭 PARTE 4 — Búsqueda, Carrito, Ocultar publicaciones y Errores
# =========================================================

# ------------------------------
# 🛒 CARRITO — Lógica funcional completa
# ------------------------------
def get_cart():
    """Obtiene el carrito actual desde la sesión."""
    return session.setdefault("cart", [])


def save_cart(cart):
    """Guarda el carrito actualizado."""
    session["cart"] = cart


@app.route("/carrito/agregar/<int:pub_id>")
def carrito_agregar(pub_id):
    """Agrega una publicación al carrito."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    cart = get_cart()
    publicacion = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)

    if publicacion and publicacion not in cart:
        cart.append(publicacion)
        save_cart(cart)
        flash("✅ Publicación agregada al carrito.", "success")
    else:
        flash("⚠️ Esta publicación ya está en tu carrito o no existe.", "info")

    return redirect(url_for("carrito"))


@app.route("/carrito/eliminar/<int:pub_id>")
def carrito_eliminar(pub_id):
    """Elimina una publicación específica del carrito."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    cart = get_cart()
    cart = [p for p in cart if p["id"] != pub_id]
    save_cart(cart)
    flash("🗑️ Publicación eliminada del carrito.", "info")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar")
def carrito_vaciar():
    """Vacía completamente el carrito."""
    session["cart"] = []
    flash("🧺 Carrito vaciado correctamente.", "info")
    return redirect(url_for("carrito"))


# ------------------------------
# 🔍 BÚSQUEDA DE PUBLICACIONES
# ------------------------------
@app.route("/buscar", methods=["GET", "POST"])
def buscar():
    """Permite buscar publicaciones por palabra clave."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    query = (request.form.get("q") or request.args.get("q") or "").strip().lower()
    resultados = []

    if query:
        for p in PUBLICACIONES:
            if (
                query in p["titulo"].lower()
                or query in p["empresa"].lower()
                or query in p["descripcion"].lower()
                or query in p["rol"].lower()
            ):
                resultados.append(p)

    return render_template("buscar.html", user=user, query=query, resultados=resultados)


# ------------------------------
# 👁️ OCULTAR Y RESTAURAR PUBLICACIONES
# ------------------------------
def get_hidden_items():
    """Obtiene IDs de publicaciones ocultas."""
    return session.setdefault("hidden_items", [])


@app.route("/ocultar/<int:pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    """Oculta una publicación del dashboard."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    hidden = get_hidden_items()
    if pub_id not in hidden:
        hidden.append(pub_id)
        session["hidden_items"] = hidden
        flash("👁️ Publicación ocultada de tu vista.", "info")

    return redirect(request.referrer or url_for("dashboard"))


@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    """Restaura todas las publicaciones ocultas."""
    session["hidden_items"] = []
    flash("🔄 Publicaciones restauradas correctamente.", "success")
    return redirect(url_for("dashboard"))


# ------------------------------
# ⚠️ MANEJO DE ERRORES PERSONALIZADO
# ------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Página no encontrada."""
    try:
        return render_template("404.html"), 404
    except Exception:
        return "<h1>404</h1><p>Página no encontrada</p>", 404


@app.errorhandler(500)
def internal_error(error):
    """Error interno del servidor."""
    try:
        return render_template("500.html"), 500
    except Exception:
        return "<h1>500</h1><p>Error interno del servidor</p>", 500
# =========================================================
# 🌍 PARTE 5 — MULTILENGUAJE, ERRORES Y ARRANQUE
# =========================================================

# --- Diccionario base de traducciones ---
TRANSLATIONS = {
    # Navegación / header
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

    # Home / Hero
    "Bienvenido a Window Shopping": {
        "en": "Welcome to Window Shopping",
        "zh": "歡迎來到 Window Shopping",
    },
    "Conectamos productores chilenos con compradores internacionales": {
        "en": "Connecting Chilean producers with international buyers",
        "zh": "連接智利生產商與國際買家",
    },
    "Comienza ahora": {"en": "Start now", "zh": "立即開始"},
    "Explora nuestros servicios": {"en": "Explore our services", "zh": "探索我們的服務"},
    "Compra y Venta": {"en": "Buy & Sell", "zh": "買賣"},
    "Servicios Logísticos": {"en": "Logistic Services", "zh": "物流服務"},
    "Sostenibilidad": {"en": "Sustainability", "zh": "永續發展"},

    # Dashboard / acciones
    "Ver Demandas": {"en": "View Demands", "zh": "查看需求"},
    "Explorar Ofertas": {"en": "Browse Offers", "zh": "瀏覽商品"},
    "Explorar Servicios": {"en": "Explore Services", "zh": "探索服務"},
    "Panel de Usuario": {"en": "User Dashboard", "zh": "用戶主頁"},

    # Carrito / botones genéricos
    "Agregado al carrito": {"en": "Added to cart", "zh": "已加入購物車"},
    "Eliminado del carrito": {"en": "Removed from cart", "zh": "已刪除"},
    "Carrito vaciado": {"en": "Cart cleared", "zh": "購物車已清空"},
    "Publicación no encontrada": {"en": "Item not found", "zh": "找不到項目"},
    "Publicación ocultada": {"en": "Item hidden", "zh": "項目已隱藏"},
    "Publicaciones restauradas": {"en": "Hidden items restored", "zh": "已恢復隱藏項目"},

    # Errores
    "Página no encontrada": {"en": "Page not found", "zh": "找不到頁面"},
    "Error interno del servidor": {"en": "Internal server error", "zh": "伺服器內部錯誤"},
}

# --- Inyección del traductor `t()` ---
@app.context_processor
def inject_translator():
    def t(es: str, en: str = None, zh: str = None) -> str:
        """
        Traductor dinámico:
        - Usa session['lang'] (por defecto 'es').
        - Prioridad: diccionario central -> parámetros en/en zh -> texto ES.
        """
        lang = session.get("lang", "es")
        if lang == "en":
            return TRANSLATIONS.get(es, {}).get("en") or (en if en else es)
        if lang == "zh":
            return TRANSLATIONS.get(es, {}).get("zh") or (zh if zh else es)
        return es

    return dict(t=t)


# --- Selector de idioma ---
@app.route("/set_lang", methods=["POST"])
def set_lang():
    lang = request.form.get("lang", "es")
    session["lang"] = lang
    flash("🌍 Idioma cambiado correctamente.", "info")
    print(f"🌍 Idioma establecido: {lang}")
    return redirect(request.referrer or url_for("home"))


# --- Rutas globales de ayuda y home ---
@app.route("/")
def home():
    """Página principal de Window Shopping."""
    return render_template("home.html")


@app.route("/ayuda")
def ayuda():
    """Centro de ayuda o preguntas frecuentes."""
    return render_template("ayuda.html")


# --- Registro Router (para elegir tipo antes del formulario) ---
@app.route("/register_router")
def register_router():
    """Vista para elegir tipo de registro antes del formulario."""
    return render_template("register_router.html")


# --- Errores de respaldo ---
@app.errorhandler(404)
def not_found_error(error):
    """Página no encontrada (backup general)."""
    try:
        return render_template("404.html"), 404
    except Exception as e:
        print(f"Error 404: {e}")
        return "<h1>404</h1><p>Página no encontrada</p>", 404


@app.errorhandler(500)
def internal_error(error):
    """Error interno del servidor (backup general)."""
    try:
        return render_template("500.html"), 500
    except Exception as e:
        print(f"Error 500: {e}")
        return "<h1>500</h1><p>Error interno del servidor</p>", 500


# =========================================================
# 🚀 ARRANQUE DE LA APLICACIÓN
# =========================================================
if __name__ == "__main__":
    print("🚀 Iniciando Window Shopping (v3.3)…")
    app.run(debug=True, host="0.0.0.0", port=5000)
