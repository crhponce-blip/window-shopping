import os
import uuid
from datetime import timedelta
from typing import List, Dict, Any, Optional
import sqlite3

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, abort, flash, send_from_directory
)
from werkzeug.utils import secure_filename

# ---------------------------------------------------------
# 🔧 CONFIGURACIÓN BÁSICA
# ---------------------------------------------------------
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
    """Valida extensión de archivo subida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------------------------------------------------------
# 🧩 TIPOS Y ROLES (Reglas de creación de usuario)
# ---------------------------------------------------------
TIPOS_VALIDOS = {"compras", "servicios", "mixto", "compraventa"}

ROLES_POR_TIPO: Dict[str, List[str]] = {
    # Cliente extranjero = SOLO compras (no servicios)
    "compras": ["Cliente extranjero"],

    # Servicios únicos (no fruta)
    "servicios": [
        "Agencia de aduana", "Transporte", "Extraportuario",
        "Packing", "Frigorífico"
    ],

    # Nacional compraventa (fruta)
    "compraventa": [
        "Productor(planta)", "Packing", "Frigorífico", "Exportador"
    ],

    # Mixto (fruta + servicios)
    "mixto": ["Packing", "Frigorífico"],
}


# ---------------------------------------------------------
# 🗄️ BASE DE DATOS (SQLite) — Usuarios y autenticación
# ---------------------------------------------------------
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    """Crea la base de datos y tabla users si no existen."""
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
    """Crea un usuario admin por defecto si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", ("admin@ws.com",))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("admin@ws.com", "1234", "Window Shopping Admin", "Exportador", "compraventa", "CL"))
        conn.commit()
        print("✅ Usuario admin creado: admin@ws.com / 1234")
    conn.close()


def get_user(email: str):
    """Obtiene un usuario por email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user


def add_user(email, password, empresa, rol, tipo, pais):
    """Agrega un nuevo usuario a la base de datos."""
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


# ---------------------------------------------------------
# 🔒 LOGIN (con base de datos SQLite)
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión conectado a la base de datos SQLite."""
    if request.method == "POST":
        email = (request.form.get("username") or "").strip().lower()
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
            print(f"✅ Sesión iniciada por: {email}")
            return redirect(url_for("dashboard"))
        else:
            print("❌ Credenciales incorrectas")
            flash("Credenciales incorrectas")
            return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")


# ---------------------------------------------------------
# 🧾 VALIDADORES Y NORMALIZADORES
# ---------------------------------------------------------
def _normaliza_tipo(tipo: str) -> str:
    """Normaliza el tipo de cuenta."""
    tipo = (tipo or "").strip().lower()
    if tipo in {"compra-venta", "compra_venta", "cv"}:
        return "compraventa"
    return tipo if tipo in TIPOS_VALIDOS else ""


def _rol_valido_para_tipo(rol: str, tipo: str) -> bool:
    """Valida si el rol pertenece al tipo de cuenta."""
    return rol in ROLES_POR_TIPO.get(tipo, [])


# ---------------------------------------------------------
# 🧩 REGISTRO (con validaciones completas)
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios (validación por tipo/rol)."""
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
        email = (request.form.get("username") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        tipo = _normaliza_tipo(request.form.get("tipo") or "")
        pais = (request.form.get("pais") or "CL").strip().upper()

        # Validaciones básicas
        if not all([email, password, empresa, rol, tipo]):
            flash("Todos los campos son obligatorios")
            return redirect(url_for("register"))

        if not _rol_valido_para_tipo(rol, tipo):
            flash("El rol seleccionado no corresponde al tipo de cuenta.")
            return redirect(url_for("register"))

        if rol == "Cliente extranjero" and tipo != "compras":
            flash("Cliente extranjero solo puede ser tipo 'compras'.")
            return redirect(url_for("register"))

        if rol == "Exportador" and tipo not in {"compraventa"}:
            flash("Exportador debe ser tipo 'compraventa'.")
            return redirect(url_for("register"))

        if len(pais) != 2:
            flash("El código de país debe tener 2 letras (ej: CL, US).")
            return redirect(url_for("register"))

        existing = get_user(email)
        if existing:
            flash("El usuario ya existe")
            return redirect(url_for("register"))

        add_user(email, password, empresa, rol, tipo, pais)
        flash("Usuario registrado exitosamente")
        return redirect(url_for("login"))

    # GET
    return render_template(
        "register.html",
        roles=roles_catalogo,
        tipos=tipos_catalogo,
        roles_por_tipo=ROLES_POR_TIPO
    )
# ---------------------------------------------------------
# 🌱 SEMILLAS — Usuarios demo para pruebas
# ---------------------------------------------------------
USERS: Dict[str, Dict[str, Any]] = {
    # ---- Compraventa (fruta) ----
    "productor1@demo.cl": {
        "password": "1234", "rol": "Productor(planta)", "tipo": "compraventa",
        "empresa": "Productores del Valle SpA", "pais": "CL"
    },
    "packingcv1@demo.cl": {
        "password": "1234", "rol": "Packing", "tipo": "compraventa",
        "empresa": "Packing Maule SpA", "pais": "CL"
    },
    "frigorificocv1@demo.cl": {
        "password": "1234", "rol": "Frigorífico", "tipo": "compraventa",
        "empresa": "Frío Centro SpA", "pais": "CL"
    },
    "export1@demo.cl": {
        "password": "1234", "rol": "Exportador", "tipo": "compraventa",
        "empresa": "Exportadora Andes SpA", "pais": "CL"
    },

    # ---- Servicios ----
    "packingserv1@demo.cl": {
        "password": "1234", "rol": "Packing", "tipo": "servicios",
        "empresa": "PackSmart Servicios", "pais": "CL"
    },
    "frigorificoserv1@demo.cl": {
        "password": "1234", "rol": "Frigorífico", "tipo": "servicios",
        "empresa": "FríoPort Servicios", "pais": "CL"
    },
    "aduana1@demo.cl": {
        "password": "1234", "rol": "Agencia de aduana", "tipo": "servicios",
        "empresa": "Agencia Andes", "pais": "CL"
    },
    "transporte1@demo.cl": {
        "password": "1234", "rol": "Transporte", "tipo": "servicios",
        "empresa": "Transporte Global", "pais": "CL"
    },

    # ---- Cliente extranjero (solo compras) ----
    "clienteusa1@ext.com": {
        "password": "1234", "rol": "Cliente extranjero", "tipo": "compras",
        "empresa": "Importadora Asia Ltd.", "pais": "US"
    },
}


# ---------------------------------------------------------
# 🧩 “ELIMINAR DE MI VISTA” (persistente en sesión)
# ---------------------------------------------------------
def get_hidden_items() -> List[str]:
    """Obtiene IDs de publicaciones ocultas por el usuario."""
    return session.setdefault("hidden_items", [])


def hide_item(item_id: str):
    """Oculta un ítem (lo añade a la lista de ocultos)."""
    hidden = get_hidden_items()
    if item_id not in hidden:
        hidden.append(item_id)
        session["hidden_items"] = hidden


def unhide_all():
    """Restaura todos los ítems ocultos."""
    session["hidden_items"] = []


# ---------------------------------------------------------
# 🧾 PUBLICACIONES DEMO (ofertas, servicios, demandas)
# ---------------------------------------------------------
PUBLICACIONES: List[Dict[str, Any]] = [
    # --- Fruta / Ofertas ---
    {"id": "pub1", "usuario": "export1@demo.cl", "tipo": "oferta", "rol": "Exportador",
     "empresa": "Exportadora Andes SpA", "producto": "Cerezas Premium", "precio": "USD 7/kg"},
    # --- Servicios ---
    {"id": "pub2", "usuario": "packingcv1@demo.cl", "tipo": "servicio", "rol": "Packing",
     "empresa": "Packing Maule SpA", "producto": "Servicio de Embalaje", "precio": "USD 0.50/kg"},
    {"id": "pub3", "usuario": "frigorificocv1@demo.cl", "tipo": "servicio", "rol": "Frigorífico",
     "empresa": "Frío Centro SpA", "producto": "Almacenamiento Refrigerado", "precio": "USD 0.20/kg"},
    {"id": "pub4", "usuario": "aduana1@demo.cl", "tipo": "servicio", "rol": "Agencia de aduana",
     "empresa": "Agencia Andes", "producto": "Tramitación de Exportación", "precio": "USD 200/trámite"},
    # --- Demandas ---
    {"id": "pub5", "usuario": "clienteusa1@ext.com", "tipo": "demanda", "rol": "Cliente extranjero",
     "empresa": "Importadora Asia Ltd.", "producto": "Demanda de Fruta Chilena", "precio": "Consultar"},
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
    """Agrega un ítem al carrito si no está ya presente."""
    cart = get_cart()
    if item not in cart:
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
# 🧠 FILTRADO DE PUBLICACIONES SEGÚN ROL Y PERMISOS
# ---------------------------------------------------------
def filtrar_publicaciones_por_usuario(usuario: Dict[str, Any], permisos: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Devuelve solo las publicaciones visibles según el rol/tipo del usuario.
    Se filtra por permisos definidos en la Parte 3.
    """
    rol = usuario.get("rol", "")
    hidden = set(get_hidden_items())
    visibles = []

    for pub in PUBLICACIONES:
        if pub["id"] in hidden:
            continue

        tipo_pub = pub.get("tipo")

        # --- Ofertas ---
        if tipo_pub == "oferta":
            visibles_roles = permisos["fruta_oferta_visible_por_rol"].get(rol, [])
            if pub["rol"] in visibles_roles:
                visibles.append(pub)

        # --- Demandas ---
        elif tipo_pub == "demanda":
            visibles_roles = permisos["fruta_demanda_visible_por_rol"].get(rol, [])
            if pub["rol"] in visibles_roles:
                visibles.append(pub)

        # --- Servicios ---
        elif tipo_pub == "servicio":
            compradores = permisos["servicios_compra_de"].get(rol, [])
            if pub["rol"] in compradores or pub["rol"] == rol:
                visibles.append(pub)

    return visibles
# ---------------------------------------------------------
# 🧩 MATRIZ DE PERMISOS (ofertas, demandas, servicios)
# ---------------------------------------------------------
PERMISOS: Dict[str, Dict[str, List[str]]] = {
    # === FRUTA: quién puede ver OFERTAS publicadas por cada rol ===
    "fruta_oferta_visible_por_rol": {
        # Productor vende a Packing, Frigorífico, Exportador
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
# 🧱 ROLES POR TIPO DE CUENTA (helpers para registro)
# ---------------------------------------------------------
ROLES_SERVICIO_PUROS = ["Agencia de aduana", "Transporte", "Extraportuario"]
ROLES_FRUTA = ["Productor(planta)", "Packing", "Frigorífico", "Exportador"]
ROLES_TODOS = ROLES_FRUTA + ROLES_SERVICIO_PUROS + ["Cliente extranjero"]

def roles_permitidos_por_tipo(tipo: str) -> List[str]:
    """
    Devuelve los roles válidos para el tipo de cuenta seleccionado.
    - 'compras'     -> Cliente extranjero
    - 'servicios'   -> Perfiles de servicio puros (+ Packing/Frigorífico)
    - 'compraventa' -> Productor, Packing, Frigorífico, Exportador
    - 'mixto'       -> Packing, Frigorífico (ambos tipos)
    """
    tipo = (tipo or "").strip().lower()
    if tipo == "compras":
        return ["Cliente extranjero"]
    if tipo == "servicios":
        return ROLES_SERVICIO_PUROS + ["Packing", "Frigorífico"]
    if tipo == "compraventa":
        return ROLES_FRUTA
    if tipo == "mixto":
        return ["Packing", "Frigorífico"]
    return ROLES_TODOS


# ---------------------------------------------------------
# 👁️‍🗨️ VISIBILIDAD DE PUBLICACIONES POR ROL
# ---------------------------------------------------------
def publica_es_visible_para_rol(pub: Dict[str, Any], rol_usuario: str) -> bool:
    """Evalúa si una publicación es visible para un rol dado."""
    if not pub or not rol_usuario:
        return False

    tipo = pub.get("tipo")
    rol_pub = pub.get("rol")

    if tipo == "oferta":
        roles_v = PERMISOS["fruta_oferta_visible_por_rol"].get(rol_usuario, [])
        return rol_pub in roles_v

    if tipo == "demanda":
        roles_v = PERMISOS["fruta_demanda_visible_por_rol"].get(rol_usuario, [])
        return rol_pub in roles_v

    if tipo == "servicio":
        compra_de = PERMISOS["servicios_compra_de"].get(rol_usuario, [])
        return rol_pub in compra_de

    return False


def publicaciones_visibles(usuario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filtra PUBLICACIONES según el rol/tipo del usuario + ítems ocultos."""
    hidden = set(session.get("hidden_items", []))
    rol = usuario.get("rol", "")
    visibles = []
    for p in PUBLICACIONES:
        if p.get("id") in hidden:
            continue
        if publica_es_visible_para_rol(p, rol):
            visibles.append(p)
    return visibles


# ---------------------------------------------------------
# 👥 HELPERS DE CLIENTES (para vistas de lista/detalle)
# ---------------------------------------------------------
def _normaliza_items(items):
    """Normaliza productos o servicios dentro de perfiles."""
    out = []
    for it in items or []:
        nombre = it.get("producto") or it.get("servicio") or it.get("variedad") or "Item"
        tipo = it.get("tipo") or "item"
        out.append({"nombre": nombre, "tipo": tipo})
    return out


def _armar_cliente_desde_profile(username: str, profile: Dict[str, Any]):
    """Convierte un perfil extendido en un formato estándar para mostrar."""
    return {
        "username": username,
        "empresa": profile.get("empresa"),
        "rol": profile.get("rol"),
        "tipo": profile.get("tipo") or profile.get("perfil_tipo") or "",
        "descripcion": profile.get("descripcion") or "",
        "items": _normaliza_items(profile.get("items")),
    }


def _armar_cliente_desde_users(username: str, data: Dict[str, Any]):
    """Convierte datos de USERS (semilla o BD) a formato de cliente."""
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": [],
    }
from flask import render_template, redirect, url_for, request, flash, abort, session

# ---------------------------------------------------------
# 🔐 LOGIN REQUERIDO (middleware simple)
# ---------------------------------------------------------
def login_requerido():
    """Valida que el usuario haya iniciado sesión."""
    if "user" not in session:
        flash("Debes iniciar sesión para acceder a esta sección.")
        return False
    return True


# ---------------------------------------------------------
# 🏠 DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    """Panel principal del usuario."""
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
        titulo="Panel de Usuario"
    )


# ---------------------------------------------------------
# 🛍️ COMPRAS — Ofertas y servicios visibles según rol
# ---------------------------------------------------------
@app.route("/compras")
def compras():
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] in ("oferta", "servicio") and publica_es_visible_para_rol(p, user["rol"])
    ]
    return render_template("compras.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 💰 VENTAS — Demandas visibles según rol
# ---------------------------------------------------------
@app.route("/ventas")
def ventas():
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] == "demanda" and publica_es_visible_para_rol(p, user["rol"])
    ]
    return render_template("ventas.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 🧰 SERVICIOS — Filtrados según rol comprador
# ---------------------------------------------------------
@app.route("/servicios")
def servicios():
    if not login_requerido():
        return redirect(url_for("login"))

    user = session["user"]
    publicaciones = [
        p for p in PUBLICACIONES
        if p["tipo"] == "servicio" and publica_es_visible_para_rol(p, user["rol"])
    ]
    return render_template("servicios.html", publicaciones=publicaciones)


# ---------------------------------------------------------
# 👥 CLIENTES — Listado general y detalle
# ---------------------------------------------------------
@app.route("/clientes")
def clientes():
    if not login_requerido():
        return redirect(url_for("login"))

    lista = []
    for username, data in USERS.items():
        lista.append(_armar_cliente_desde_users(username, data))
    lista.sort(key=lambda c: (c.get("empresa") or "").lower())

    return render_template("clientes.html", clientes=lista)


@app.route("/clientes/<username>")
def cliente_detalle(username):
    """Detalle de un cliente específico."""
    if username not in USERS:
        abort(404)
    cliente = _armar_cliente_desde_users(username, USERS[username])
    return render_template("cliente_detalle.html", c=cliente)


# ---------------------------------------------------------
# 🛒 CARRITO — Visualización, agregar, eliminar, vaciar
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    if not login_requerido():
        return redirect(url_for("login"))
    return render_template("carrito.html", cart=get_cart())


@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    if not login_requerido():
        return redirect(url_for("login"))

    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if pub:
        add_to_cart(pub)
        flash("Agregado al carrito.")
    else:
        flash("Publicación no encontrada.")
    return redirect(url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>")
def carrito_eliminar(index):
    if remove_from_cart(index):
        flash("Eliminado del carrito.")
    else:
        flash("Ítem no encontrado.")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar")
def carrito_vaciar():
    clear_cart()
    flash("Carrito vaciado.")
    return redirect(url_for("carrito"))


# ---------------------------------------------------------
# 🧹 “ELIMINAR DE MI VISTA” / RESTAURAR
# ---------------------------------------------------------
@app.route("/ocultar/<pub_id>", methods=["POST"])
def ocultar_publicacion(pub_id):
    """Permite ocultar una publicación (no eliminarla del sistema)."""
    if not login_requerido():
        return redirect(url_for("login"))

    hide_item(pub_id)
    flash("Publicación ocultada.")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/restablecer_ocultos", methods=["POST"])
def restablecer_ocultos():
    """Restaura todas las publicaciones ocultas."""
    if not login_requerido():
        return redirect(url_for("login"))

    unhide_all()
    flash("Publicaciones restauradas.")
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
# ------------------------------
# 🌐 MULTILENGUAJE (ES / EN / 中文)
# ------------------------------
from flask import request

# Diccionario base; si falta una clave, el traductor hace fallback al texto en ES.
TRANSLATIONS = {
    # Navegación y acciones
    "Inicio": {"en": "Home", "zh": "主頁"},
    "Compras": {"en": "Purchases", "zh": "購買"},
    "Ventas": {"en": "Sales", "zh": "銷售"},
    "Servicios": {"en": "Services", "zh": "服務"},
    "Carrito": {"en": "Cart", "zh": "購物車"},
    "Perfil": {"en": "Profile", "zh": "個人資料"},
    "Ayuda": {"en": "Help", "zh": "幫助"},
    "Cerrar sesión": {"en": "Log out", "zh": "登出"},
    "Iniciar sesión": {"en": "Log in", "zh": "登入"},
    "Registrarse": {"en": "Register", "zh": "註冊"},

    # Home
    "Bienvenido a Window Shopping": {
        "en": "Welcome to Window Shopping", "zh": "歡迎來到 Window Shopping"
    },
    "Conectamos productores chilenos con compradores internacionales": {
        "en": "Connecting Chilean producers with international buyers",
        "zh": "連接智利生產商與國際買家"
    },
    "Ver demandas": {"en": "View demands", "zh": "查看需求"},
    "Explorar ofertas": {"en": "Explore offers", "zh": "查看報價"},
    "Explorar servicios": {"en": "Explore services", "zh": "探索服務"},

    # Mensajes comunes
    "Debes iniciar sesión para acceder a esta sección.": {
        "en": "You must log in to access this section.", "zh": "請先登入以存取此區域。"
    },
    "Agregado al carrito": {"en": "Added to cart", "zh": "已加入購物車"},
    "Eliminado del carrito": {"en": "Removed from cart", "zh": "已從購物車移除"},
    "Carrito vaciado": {"en": "Cart cleared", "zh": "購物車已清空"},
    "Publicación no encontrada": {"en": "Item not found", "zh": "找不到項目"},
    "Publicación ocultada": {"en": "Item hidden", "zh": "項目已隱藏"},
    "Publicaciones restauradas": {"en": "Hidden items restored", "zh": "已恢復隱藏項目"},
    "Panel de Usuario": {"en": "User Dashboard", "zh": "用戶主頁"},

    # Errores
    "Página no encontrada": {"en": "Page not found", "zh": "找不到頁面"},
    "Error interno del servidor": {"en": "Internal server error", "zh": "伺服器內部錯誤"},
}

@app.context_processor
def inject_translator():
    def t(es: str, en: str = None, zh: str = None) -> str:
        """
        Traductor dinámico:
        - Usa session['lang'] (por defecto 'es')
        - Busca en TRANSLATIONS; si no existe, usa los alternativos 'en'/'zh' pasados a la función
        - Si aún así no hay, retorna el texto en español.
        """
        lang = session.get("lang", "es")
        if lang == "en":
            # 1) diccionario central -> 2) parámetro 'en' -> 3) fallback ES
            return (TRANSLATIONS.get(es, {}).get("en")) or (en if en else es)
        if lang == "zh":
            return (TRANSLATIONS.get(es, {}).get("zh")) or (zh if zh else es)
        return es
    return dict(t=t)

@app.route("/set_lang", methods=["POST"])
def set_lang():
    """Selector de idioma: guarda el idioma en sesión y regresa a la página previa."""
    lang = request.form.get("lang", "es")
    session["lang"] = lang
    print(f"🌍 Idioma establecido: {lang}")
    return redirect(request.referrer or url_for("home"))


# ------------------------------
# 🧯 MANEJO DE ERRORES
# ------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Página no encontrada (404)."""
    try:
        return render_template(
            "404.html",
            mensaje=t("Página no encontrada", "Page not found", "找不到頁面")
        ), 404
    except Exception as e:
        # Fallback minimalista si falla el template
        print(f"Error al renderizar 404: {e}")
        return "<h1>404</h1><p>Página no encontrada</p>", 404


@app.errorhandler(500)
def server_error(error):
    """Error interno del servidor (500)."""
    try:
        return render_template(
            "500.html",
            mensaje=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤")
        ), 500
    except Exception as e:
        print(f"Error al renderizar 500: {e}")
        return "<h1>500</h1><p>Error interno del servidor</p>", 500


# ------------------------------
# 🚀 ARRANQUE LOCAL
# (En Render se usa: gunicorn app:app)
# ------------------------------
if __name__ == "__main__":
    print("🚀 Iniciando Window Shopping...")
    app.run(debug=True, host="0.0.0.0", port=5000)
