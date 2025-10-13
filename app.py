# =========================================================
# 🌐 WINDOW SHOPPING — Flask App Final (v3.1, Octubre 2025)
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
    """Crea un usuario administrador si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", ("admin@ws.com",))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("admin@ws.com", "1234", "Window Shopping Admin",
              "Exportador", "compraventa", "CL"))
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


# Inicialización automática
init_db()
create_admin_if_missing()
# =========================================================
# Parte 2 — Autenticación (Login, Registro) + Validadores
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
            # Mantener sesión permanente (respeta app.permanent_session_lifetime)
            session.permanent = True
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas", "error")
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


# ------------------------------
# 🧩 REGISTRO (SQLite) — con validaciones completas
# ------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios con validación por tipo/rol."""
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
        # Compatibilidad con tus templates: 'usuario' (email) o 'username'
        email = (
            (request.form.get("usuario") or request.form.get("username") or "")
            .strip()
            .lower()
        )
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        tipo = _normaliza_tipo(request.form.get("tipo") or "")
        # Si no envías pais en el form, cae en 'CL'
        pais = (request.form.get("pais") or "CL").strip().upper()

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

        # ¿Usuario ya existe?
        existing = get_user(email)
        if existing:
            flash("El usuario ya existe.", "error")
            return redirect(url_for("register"))

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
# 📦 PARTE 3 — Publicaciones, Visibilidad, Carrito, Permisos
# =========================================================

from typing import Any, Dict, List

# ---------------------------------------------------------
# 🧩 “ELIMINAR DE MI VISTA” (persistente en sesión)
# ---------------------------------------------------------
def get_hidden_items() -> List[str]:
    """Obtiene IDs de publicaciones ocultas por el usuario."""
    return session.setdefault("hidden_items", [])

def hide_item(item_id: str) -> None:
    """Oculta un ítem (lo añade a la lista de ocultos)."""
    hidden = get_hidden_items()
    if item_id not in hidden:
        hidden.append(item_id)
        session["hidden_items"] = hidden

def unhide_all() -> None:
    """Restaura todos los ítems ocultos."""
    session["hidden_items"] = []


# ---------------------------------------------------------
# 🧾 PUBLICACIONES DEMO (ofertas, servicios, demandas)
# ---------------------------------------------------------
PUBLICACIONES: List[Dict[str, Any]] = [
    # --- Fruta / Ofertas ---
    {
        "id": "pub1",
        "usuario": "export1@demo.cl",
        "tipo": "oferta",
        "rol": "Exportador",
        "empresa": "Exportadora Andes SpA",
        "producto": "Cerezas Premium",
        "precio": "USD 7/kg",
        "descripcion": "Cereza variedad Lapins, calibre 28+, condición exportación."
    },

    # --- Servicios ---
    {
        "id": "pub2",
        "usuario": "packingcv1@demo.cl",
        "tipo": "servicio",
        "rol": "Packing",
        "empresa": "Packing Maule SpA",
        "producto": "Servicio de Embalaje",
        "precio": "USD 0.50/kg",
        "descripcion": "Embalaje con clamshell y flowpack. Certificaciones BRC/IFS."
    },
    {
        "id": "pub3",
        "usuario": "frigorificocv1@demo.cl",
        "tipo": "servicio",
        "rol": "Frigorífico",
        "empresa": "Frío Centro SpA",
        "producto": "Almacenamiento Refrigerado",
        "precio": "USD 0.20/kg",
        "descripcion": "Cámaras -1 a 10°C, atmósfera controlada, monitoreo 24/7."
    },
    {
        "id": "pub4",
        "usuario": "aduana1@demo.cl",
        "tipo": "servicio",
        "rol": "Agencia de aduana",
        "empresa": "Agencia Andes",
        "producto": "Tramitación de Exportación",
        "precio": "USD 200/trámite",
        "descripcion": "Comex full: DUS, MIC/DTA, revisión documental y aforo."
    },

    # --- Demandas ---
    {
        "id": "pub5",
        "usuario": "clienteusa1@ext.com",
        "tipo": "demanda",
        "rol": "Cliente extranjero",
        "empresa": "Importadora Asia Ltd.",
        "producto": "Demanda de Fruta Chilena",
        "precio": "Consultar",
        "descripcion": "Buscamos cereza, arándano y uva sin semilla, semanas 46-3."
    },
]


# ---------------------------------------------------------
# 🛒 CARRITO (helpers de sesión)
# ---------------------------------------------------------
def get_cart() -> List[Dict[str, Any]]:
    """Obtiene el carrito actual desde la sesión."""
    return session.setdefault("cart", [])

def save_cart(cart: List[Dict[str, Any]]) -> None:
    """Guarda el carrito actualizado en la sesión."""
    session["cart"] = cart

def add_to_cart(item: Dict[str, Any]) -> None:
    """Agrega un ítem al carrito si no está ya presente (por ID)."""
    cart = get_cart()
    if not any(i.get("id") == item.get("id") for i in cart):
        cart.append(item)
        save_cart(cart)

def remove_from_cart(index: int) -> bool:
    """Elimina un ítem del carrito por índice."""
    cart = get_cart()
    if 0 <= index < len(cart):
        cart.pop(index)
        save_cart(cart)
        return True
    return False

def clear_cart() -> None:
    """Vacía el carrito."""
    save_cart([])


# ---------------------------------------------------------
# 🧠 MATRIZ DE PERMISOS (ofertas, demandas, servicios)
# ---------------------------------------------------------
PERMISOS: Dict[str, Dict[str, List[str]]] = {
    # === FRUTA: quién puede ver OFERTAS publicadas por cada rol ===
    "fruta_oferta_visible_por_rol": {
        "Packing": ["Productor(planta)"],
        "Frigorífico": ["Productor(planta)", "Packing"],
        "Exportador": ["Productor(planta)", "Packing", "Frigorífico", "Exportador"],
        "Cliente extranjero": ["Exportador"],  # Solo ve exportadores
        "Productor(planta)": ["Packing", "Frigorífico", "Exportador"],

        # Servicios no ven fruta
        "Agencia de aduana": [],
        "Transporte": [],
        "Extraportuario": [],
    },

    # === FRUTA: quién puede ver DEMANDAS (quién compra fruta) ===
    "fruta_demanda_visible_por_rol": {
        "Productor(planta)": ["Exportador", "Packing", "Frigorífico", "Productor(planta)"],
        "Packing": ["Exportador", "Frigorífico", "Packing"],
        "Frigorífico": ["Exportador", "Packing", "Frigorífico"],
        "Exportador": ["Exportador"],
        "Cliente extranjero": ["Exportador"],

        # Servicios no participan en fruta
        "Agencia de aduana": [],
        "Transporte": [],
        "Extraportuario": [],
    },

    # === SERVICIOS: a quién pueden VENDER servicios cada rol ===
    "servicios_venta_a": {
        "Agencia de aduana": ["Exportador"],
        "Transporte": ["Exportador", "Packing", "Frigorífico", "Productor(planta)"],
        "Extraportuario": ["Exportador"],
        "Packing": ["Productor(planta)", "Frigorífico", "Exportador"],
        "Frigorífico": ["Packing", "Productor(planta)", "Exportador"],
        "Exportador": [],
        "Productor(planta)": [],
        "Cliente extranjero": [],
    },

    # === SERVICIOS: desde quién pueden COMPRAR servicios cada rol comprador ===
    "servicios_compra_de": {
        "Productor(planta)": ["Transporte", "Packing", "Frigorífico"],
        "Packing": ["Transporte", "Frigorífico"],
        "Frigorífico": ["Transporte", "Packing"],
        "Exportador": ["Agencia de aduana", "Transporte", "Extraportuario", "Packing", "Frigorífico"],
        "Cliente extranjero": [],

        # Proveedores de servicio normalmente no compran servicios
        "Agencia de aduana": [],
        "Transporte": [],
        "Extraportuario": [],
    },
}


# ---------------------------------------------------------
# 👁️ VISIBILIDAD DE PUBLICACIONES POR ROL
# ---------------------------------------------------------
def publica_es_visible_para_rol(pub: Dict[str, Any], rol_usuario: str) -> bool:
    """Evalúa si una publicación es visible para un rol dado (aplica PERMISOS)."""
    if not pub or not rol_usuario:
        return False

    tipo_pub = pub.get("tipo")
    rol_pub = pub.get("rol")

    if tipo_pub == "oferta":
        roles_v = PERMISOS["fruta_oferta_visible_por_rol"].get(rol_usuario, [])
        return rol_pub in roles_v

    if tipo_pub == "demanda":
        roles_v = PERMISOS["fruta_demanda_visible_por_rol"].get(rol_usuario, [])
        return rol_pub in roles_v

    if tipo_pub == "servicio":
        compra_de = PERMISOS["servicios_compra_de"].get(rol_usuario, [])
        return rol_pub in compra_de

    return False


def publicaciones_visibles(usuario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filtra PUBLICACIONES según el rol del usuario + ítems ocultos."""
    hidden = set(session.get("hidden_items", []))
    rol = (usuario or {}).get("rol", "")
    out: List[Dict[str, Any]] = []

    for p in PUBLICACIONES:
        if p.get("id") in hidden:
            continue
        if publica_es_visible_para_rol(p, rol):
            out.append(p)

    return out


# ---------------------------------------------------------
# 👥 HELPERS DE CLIENTES (para vistas de lista/detalle)
# ---------------------------------------------------------
def _normaliza_items(items: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Normaliza productos o servicios dentro de perfiles."""
    out: List[Dict[str, Any]] = []
    for it in items or []:
        nombre = it.get("producto") or it.get("servicio") or it.get("variedad") or "Item"
        tipo = it.get("tipo") or "item"
        detalle = it.get("detalle") or it.get("descripcion") or ""
        out.append({"nombre": nombre, "tipo": tipo, "detalle": detalle})
    return out

def _armar_cliente_desde_users(username: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte datos de USERS (semilla o BD) a formato de cliente."""
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": _normaliza_items(data.get("items")),
    }
# =========================================================
# 🧭 PARTE 4 — RUTAS PRINCIPALES Y FUNCIONALIDAD DE NEGOCIO
# =========================================================

# ---------------------------------------------------------
# 🔐 LOGIN REQUERIDO (middleware simple)
# ---------------------------------------------------------
def login_requerido():
    """Valida que el usuario haya iniciado sesión."""
    if "user" not in session:
        flash("Debes iniciar sesión para acceder a esta sección.", "error")
        return False
    return True


# ---------------------------------------------------------
# 🏠 DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    """Panel principal del usuario (muestra publicaciones visibles)."""
    if not login_requerido():
        return redirect(url_for("login"))

    user = session.get("user", {})
    publicaciones = publicaciones_visibles(user)

    return render_template(
        "dashboard.html",
        user=user,
        publicaciones=publicaciones,
        rol=user.get("rol", ""),
        tipo=user.get("tipo", ""),
        empresa=user.get("empresa", ""),
        pais=user.get("pais", ""),
        titulo="Panel de Usuario",
    )


# ---------------------------------------------------------
# 🛍️ COMPRAS — Ofertas y Servicios visibles según rol
# ---------------------------------------------------------
@app.route("/compras")
def compras():
    """Vista de compras (ofertas + servicios visibles)."""
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] in ("oferta", "servicio")
        and publica_es_visible_para_rol(p, user["rol"])
    ]

    return render_template("compras.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 💰 VENTAS — Demandas visibles según rol
# ---------------------------------------------------------
@app.route("/ventas")
def ventas():
    """Vista de ventas (demandas visibles)."""
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] == "demanda"
        and publica_es_visible_para_rol(p, user["rol"])
    ]

    return render_template("ventas.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 🧰 SERVICIOS — Solo para roles que pueden comprar servicios
# ---------------------------------------------------------
@app.route("/servicios")
def servicios():
    """Vista de servicios filtrados según permisos de compra."""
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] == "servicio"
        and publica_es_visible_para_rol(p, user["rol"])
    ]

    return render_template("servicios.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 👥 CLIENTES — Listado general y detalle
# ---------------------------------------------------------
@app.route("/clientes")
def clientes():
    """Listado de empresas registradas o demo."""
    if not login_requerido():
        return redirect(url_for("login"))

    lista = []
    for username, data in USERS.items():
        lista.append(_armar_cliente_desde_users(username, data))
    lista.sort(key=lambda c: (c.get("empresa") or "").lower())

    return render_template("clientes.html", clientes=lista)


@app.route("/clientes/<username>")
def cliente_detalle(username):
    """Detalle de cliente individual."""
    if username not in USERS:
        abort(404)
    c = _armar_cliente_desde_users(username, USERS[username])
    return render_template("cliente_detalle.html", c=c)


# ---------------------------------------------------------
# 💬 MENSAJE A EMPRESA (simulado)
# ---------------------------------------------------------
@app.route("/clientes/<username>/mensaje", methods=["POST"])
def enviar_mensaje(username):
    """Envía mensaje simulado a otra empresa."""
    if not login_requerido():
        return redirect(url_for("login"))

    if username not in USERS:
        abort(404)

    mensaje = (request.form.get("mensaje") or "").strip()
    if not mensaje:
        flash("El mensaje no puede estar vacío.", "error")
        return redirect(url_for("cliente_detalle", username=username))

    flash("Mensaje enviado correctamente.", "success")
    return redirect(url_for("cliente_detalle", username=username))


# ---------------------------------------------------------
# 🛒 CARRITO — Visualización, agregar, eliminar, vaciar
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    """Carrito actual del usuario."""
    if not login_requerido():
        return redirect(url_for("login"))
    return render_template("carrito.html", cart=get_cart())


@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    """Agrega un ítem al carrito."""
    if not login_requerido():
        return redirect(url_for("login"))

    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if pub:
        add_to_cart(pub)
        flash("Agregado al carrito.", "success")
    else:
        flash("Publicación no encontrada.", "error")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>")
def carrito_eliminar(index):
    """Elimina ítem por índice."""
    if remove_from_cart(index):
        flash("Eliminado del carrito.", "success")
    else:
        flash("Ítem no encontrado.", "error")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar")
def carrito_vaciar():
    """Vacía completamente el carrito."""
    clear_cart()
    flash("Carrito vaciado.", "info")
    return redirect(url_for("carrito"))


# ---------------------------------------------------------
# 👁️ “ELIMINAR DE MI VISTA” / RESTAURAR
# ---------------------------------------------------------
@app.route("/ocultar/<pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    """Permite ocultar una publicación (no eliminarla)."""
    if not login_requerido():
        return redirect(url_for("login"))

    hide_item(pub_id)
    flash("Publicación ocultada.", "info")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    """Restaura todas las publicaciones ocultas."""
    if not login_requerido():
        return redirect(url_for("login"))

    unhide_all()
    flash("Publicaciones restauradas.", "success")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------
# 🙍 PERFIL DE USUARIO
# ---------------------------------------------------------
@app.route("/perfil")
def perfil():
    """Perfil del usuario actual."""
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    return render_template("perfil.html", user=user)


# ---------------------------------------------------------
# 🏠 HOME PAGE
# ---------------------------------------------------------
@app.route("/")
def home():
    """Página principal de Window Shopping."""
    return render_template("home.html")


# ---------------------------------------------------------
# 🧭 REGISTRO — Selector inicial
# ---------------------------------------------------------
@app.route("/register_router")
def register_router():
    """Vista para elegir tipo de registro antes del formulario."""
    return render_template("register_router.html")


# ---------------------------------------------------------
# 📖 AYUDA / FAQ
# ---------------------------------------------------------
@app.route("/ayuda")
def ayuda():
    """Centro de ayuda o preguntas frecuentes."""
    return render_template("ayuda.html")
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
        "en": "Welcome to Window Shopping", "zh": "歡迎來到 Window Shopping"
    },
    "Conectamos productores chilenos con compradores internacionales": {
        "en": "Connecting Chilean producers with international buyers",
        "zh": "連接智利生產商與國際買家"
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
    print(f"🌍 Idioma establecido: {lang}")
    return redirect(request.referrer or url_for("home"))

# --- Manejo de errores ---
@app.errorhandler(404)
def not_found_error(error):
    try:
        # Las plantillas 404.html/500.html usan {{ t(...) }} directamente
        return render_template("404.html"), 404
    except Exception as e:
        print(f"Error al renderizar 404: {e}")
        return "<h1>404</h1><p>Página no encontrada</p>", 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template("500.html"), 500
    except Exception as e:
        print(f"Error al renderizar 500: {e}")
        return "<h1>500</h1><p>Error interno del servidor</p>", 500

# --- Arranque local (Render usa: gunicorn app:app) ---
if __name__ == "__main__":
    print("🚀 Iniciando Window Shopping (v3.0)…")
    app.run(debug=True, host="0.0.0.0", port=5000)
