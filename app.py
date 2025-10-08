# === app.py (corregido y completo) ===
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, abort, flash, send_from_directory
)

# =========================================================
# CONFIGURACIÓN BÁSICA
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.permanent_session_lifetime = timedelta(days=14)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# =========================================================
# SISTEMA DE IDIOMAS (ES / EN / ZH)
# =========================================================
def t(es, en, zh=None):
    lang = session.get("lang", "es")
    if lang == "en":
        return en
    if lang == "zh" and zh:
        return zh
    return es


@app.context_processor
def inject_globals():
    return dict(
        t=t,
        LANGS=[("es", "ES"), ("en", "EN"), ("zh", "中文")]
    )


@app.route("/set_lang/<lang>")
def set_lang(lang):
    session["lang"] = lang if lang in ("es", "en", "zh") else "es"
    return redirect(request.referrer or url_for("home"))
# =========================================================
# USUARIOS Y PERFILES DE PRUEBA
# =========================================================
USERS: Dict[str, Dict[str, Any]] = {
    # Compra/Venta
    "productor@demo.cl": {"password": "1234", "rol": "Productor", "perfil_tipo": "compra_venta", "pais": "CL"},
    "planta@demo.cl": {"password": "1234", "rol": "Planta", "perfil_tipo": "compra_venta", "pais": "CL"},
    "packing@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "servicios", "pais": "CL"},
    "frigorifico@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "servicios", "pais": "CL"},
    "exportador@demo.cl": {"password": "1234", "rol": "Exportador", "perfil_tipo": "compra_venta", "pais": "CL"},
    "cliente@usa.com": {"password": "1234", "rol": "Cliente extranjero", "perfil_tipo": "compra_venta", "pais": "US"},
    # Otros roles de servicio
    "transporte@demo.cl": {"password": "1234", "rol": "Transporte", "perfil_tipo": "servicios", "pais": "CL"},
    "aduana@demo.cl": {"password": "1234", "rol": "Agencia de Aduanas", "perfil_tipo": "servicios", "pais": "CL"},
    "extraport@demo.cl": {"password": "1234", "rol": "Extraportuario", "perfil_tipo": "servicios", "pais": "CL"},
}

USER_PROFILES: Dict[str, Dict[str, Any]] = {
    "productor@demo.cl": {
        "empresa": "Agro Los Andes",
        "rut": "76.000.111-2",
        "rol": "Productor",
        "perfil_tipo": "compra_venta",
        "pais": "CL",
        "email": "ventas@agroandes.cl",
        "telefono": "+56 9 6000 1111",
        "direccion": "Parcela 5, San Felipe",
        "descripcion": "Productores de uva de mesa y arándano.",
        "items": [
            {"tipo": "oferta", "producto": "Uva Red Globe", "bulto": "pallets", "cantidad": "100", "origen": "V Región", "precio_caja": "$12"},
            {"tipo": "oferta", "producto": "Arándano Duke", "bulto": "pallets", "cantidad": "60", "origen": "VI Región", "precio_caja": "$15"},
        ],
    },
    "planta@demo.cl": {
        "empresa": "Planta Frutal Rengo",
        "rut": "77.123.456-8",
        "rol": "Planta",
        "perfil_tipo": "compra_venta",
        "pais": "CL",
        "email": "contacto@planta.cl",
        "telefono": "+56 9 6000 2222",
        "direccion": "Camino Interior, Rengo",
        "descripcion": "Recepción y proceso de fruta fresca.",
        "items": [
            {"tipo": "demanda", "producto": "Ciruela D’Agen", "bulto": "pallets", "cantidad": "80", "origen": "VI Región"},
            {"tipo": "oferta", "producto": "Cajas plásticas 10kg", "bulto": "unidades", "cantidad": "20000", "origen": "R.M."},
        ],
    },
    "packing@demo.cl": {
        "empresa": "PackSmart SPA",
        "rut": "79.456.789-0",
        "rol": "Packing",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "info@packsmart.cl",
        "telefono": "+56 9 6000 3333",
        "direccion": "Ruta 5 km 185, Rancagua",
        "descripcion": "Servicios de embalaje y QA.",
        "items": [
            {"tipo": "servicio", "servicio": "Embalaje exportación", "capacidad": "25.000 cajas/día", "ubicacion": "Rancagua"},
            {"tipo": "oferta", "producto": "Ciruela Angeleno", "bulto": "pallets", "cantidad": "50", "origen": "R.M.", "precio_caja": "$11"},
        ],
    },
    "frigorifico@demo.cl": {
        "empresa": "FríoCenter Ltda.",
        "rut": "80.222.333-4",
        "rol": "Frigorífico",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "contacto@friocenter.cl",
        "telefono": "+56 9 6000 4444",
        "direccion": "Puerto Central, Valparaíso",
        "descripcion": "Almacenaje en frío y logística portuaria.",
        "items": [
            {"tipo": "servicio", "servicio": "Preenfriado", "capacidad": "6 túneles", "ubicacion": "Valparaíso"},
            {"tipo": "servicio", "servicio": "Cámara fría", "capacidad": "1500 pallets", "ubicacion": "Valparaíso"},
        ],
    },
    "exportador@demo.cl": {
        "empresa": "OCExport Chile",
        "rut": "78.345.678-9",
        "rol": "Exportador",
        "perfil_tipo": "compra_venta",
        "pais": "CL",
        "email": "export@ocexport.cl",
        "telefono": "+56 2 2345 6789",
        "direccion": "Av. Apoquindo 1234, Las Condes",
        "descripcion": "Exportador multiproducto a Asia, EU y EEUU.",
        "items": [
            {"tipo": "demanda", "producto": "Cereza Santina", "bulto": "pallets", "cantidad": "120", "origen": "VII Región"},
            {"tipo": "demanda", "producto": "Uva Thompson", "bulto": "pallets", "cantidad": "80", "origen": "V Región"},
        ],
    },
    "cliente@usa.com": {
        "empresa": "GlobalBuyer Co.",
        "rol": "Cliente extranjero",
        "perfil_tipo": "compra_venta",
        "pais": "US",
        "email": "contact@globalbuyer.com",
        "telefono": "+1 305 555 0100",
        "direccion": "Miami, FL, USA",
        "descripcion": "Importador y distribuidor de frutas frescas.",
        "items": [
            {"tipo": "demanda", "producto": "Ciruela D’Agen", "bulto": "pallets", "cantidad": "200", "origen": "CL"},
            {"tipo": "demanda", "producto": "Cereza Lapins", "bulto": "pallets", "cantidad": "300", "origen": "CL"},
        ],
        "eori": None,
        "otros_id": None,
    },
    "transporte@demo.cl": {
        "empresa": "TransVeloz SPA",
        "rut": "81.555.666-7",
        "rol": "Transporte",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "operaciones@transveloz.cl",
        "telefono": "+56 9 5000 1111",
        "direccion": "San Bernardo, RM",
        "descripcion": "Transporte nacional y refrigerado de fruta.",
        "items": [
            {"tipo": "servicio", "servicio": "Transporte reefer", "capacidad": "35 camiones", "ubicacion": "RM"},
            {"tipo": "servicio", "servicio": "Flete marítimo local", "capacidad": "20 contenedores", "ubicacion": "Valparaíso"},
        ],
    },
    "aduana@demo.cl": {
        "empresa": "AduanasFast Ltda.",
        "rut": "82.555.666-7",
        "rol": "Agencia de Aduanas",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "agencia@aduanasfast.cl",
        "telefono": "+56 2 2987 6543",
        "direccion": "Valparaíso",
        "descripcion": "Tramitación documental y asesoría exportadora.",
        "items": [
            {"tipo": "servicio", "servicio": "Despacho de exportación", "capacidad": "Alta", "ubicacion": "Valparaíso"},
            {"tipo": "servicio", "servicio": "Asesoría logística", "capacidad": "Media", "ubicacion": "Valparaíso"},
        ],
    },
    "extraport@demo.cl": {
        "empresa": "PortHelper SPA",
        "rut": "83.777.888-9",
        "rol": "Extraportuario",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "info@porthelper.cl",
        "telefono": "+56 9 7000 2222",
        "direccion": "San Antonio",
        "descripcion": "Consolidación, desconsolidación y contenedores.",
        "items": [
            {"tipo": "servicio", "servicio": "Consolidación de contenedores", "capacidad": "120/día", "ubicacion": "San Antonio"},
            {"tipo": "servicio", "servicio": "Desconsolidado", "capacidad": "80/día", "ubicacion": "San Antonio"},
        ],
    },
}
# --- Fin de diccionario USER_PROFILES —
# =========================================================
# CLASES Y FUNCIONES AUXILIARES
# =========================================================
class ViewObj:
    """Convierte un diccionario en objeto con atributos accesibles por punto."""
    def __init__(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)
        if hasattr(self, "items") and not isinstance(getattr(self, "items"), list):
            setattr(self, "items", data.get("items", []))


def wrap_list(dict_list: List[Dict[str, Any]]) -> List[ViewObj]:
    return [ViewObj(d) for d in dict_list]


# ---------------------------------------------------------
# Sesión y carrito
# ---------------------------------------------------------
def is_logged() -> bool:
    return "user" in session


def current_user_profile() -> Optional[Dict[str, Any]]:
    u = session.get("user")
    return USER_PROFILES.get(u)


def get_cart() -> List[Dict[str, Any]]:
    return session.setdefault("cart", [])


def add_to_cart(item_dict: Dict[str, Any]) -> None:
    cart = get_cart()
    cart.append(item_dict)
    session["cart"] = cart


def remove_from_cart(index) -> bool:
    cart = get_cart()
    try:
        idx = int(index)
        if 0 <= idx < len(cart):
            cart.pop(idx)
            session["cart"] = cart
            return True
    except Exception:
        pass
    return False


def clear_cart() -> None:
    session["cart"] = []


# ---------------------------------------------------------
# Normalizador de dinero
# ---------------------------------------------------------
def norm_money(val: str) -> str:
    val = (val or "").strip()
    if not val:
        return "$0"
    if val.startswith("$"):
        return val
    return f"${val}"
# =========================================================
# REGLAS DE VISIBILIDAD ENTRE ROLES (según flujo definido)
# =========================================================
def targets_for(tipo: str, my_rol: str) -> List[str]:
    """
    Define a qué roles puede ver cada tipo de usuario
    según el flujo de compra, venta y servicios.
    """
    tipo = tipo.lower()

    # --- COMPRAS ---
    compras_vis = {
        "Productor": ["Packing"],
        "Planta": ["Packing"],
        "Packing": ["Frigorífico", "Exportador"],
        "Frigorífico": ["Exportador"],
        "Exportador": ["Cliente extranjero"],
        "Cliente extranjero": ["Exportador"],
    }

    # --- VENTAS ---
    ventas_vis = {
        "Productor": ["Packing", "Frigorífico"],
        "Planta": ["Packing"],
        "Packing": ["Exportador", "Frigorífico"],
        "Frigorífico": ["Exportador"],
        "Exportador": ["Cliente extranjero"],
        "Cliente extranjero": [],
    }

    # --- SERVICIOS ---
    servicios_vis = {
        "Packing": ["Exportador", "Frigorífico"],
        "Frigorífico": ["Exportador", "Packing"],
        "Exportador": ["Packing", "Frigorífico", "Cliente extranjero"],
        "Cliente extranjero": ["Exportador"],
        "Productor": ["Packing"],
        "Planta": ["Packing"],
    }

    # --- Lógica de retorno según tipo ---
    if tipo == "compras":
        return compras_vis.get(my_rol, [])
    elif tipo == "ventas":
        return ventas_vis.get(my_rol, [])
    elif tipo == "servicios":
        return servicios_vis.get(my_rol, [])
    else:
        # Valor por defecto: unión básica
        return list(set(ventas_vis.get(my_rol, []) + servicios_vis.get(my_rol, [])))

# =========================================================
# RUTAS PRINCIPALES
# =========================================================
@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/favicon.ico")
def favicon():
    return ("", 204)


# ---------------------------------------------------------
# LOGIN / LOGOUT
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form.get("username", "").strip().lower()
        pwd = request.form.get("password", "").strip()
        udata = USERS.get(user)
        if udata and udata["password"] == pwd:
            session["user"] = user
            session["usuario"] = user
            flash(t("Bienvenido/a", "Welcome", "歡迎"))
            return redirect(url_for("dashboard"))
        error = t("Credenciales inválidas", "Invalid credentials", "帳密錯誤")
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash(t("Sesión cerrada", "Session closed", "登出完成"))
    return redirect(url_for("home"))


# ---------------------------------------------------------
# RESET DE CONTRASEÑA (flujo simple local, sin email real)
# ---------------------------------------------------------
@app.route("/password_reset/request", methods=["GET", "POST"])
def password_reset_request():
    msg = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if email in USERS:
            session["pwd_reset_user"] = email
            flash(t("Te enviamos un enlace de restablecimiento (demo). Continúa abajo.",
                    "We sent you a reset link (demo). Continue below.",
                    "已發送重設連結（示範）。請繼續。"))
            return redirect(url_for("password_reset_form"))
        else:
            msg = t("Ese usuario no existe.", "That user does not exist.", "此用戶不存在")

    try:
        return render_template("password_reset_request.html", msg=msg)
    except TemplateNotFound:
        return """
        <h1>Recuperar contraseña</h1>
        <form method="post">
            <input name="email" placeholder="Email"/>
            <button>Enviar</button>
        </form>
        """, 200


@app.route("/password_reset/reset", methods=["GET", "POST"])
def password_reset_form():
    msg = None
    email = session.get("pwd_reset_user")

    if not email:
        flash(t("Primero solicita el enlace de restablecimiento.",
                "Request a reset link first.",
                "請先申請重設連結"))
        return redirect(url_for("password_reset_request"))

    if request.method == "POST":
        p1 = request.form.get("p1", "")
        p2 = request.form.get("p2", "")
        if not p1 or p1 != p2:
            msg = t("Las contraseñas no coinciden.", "Passwords do not match.", "密碼不一致")
        else:
            USERS[email]["password"] = p1
            flash(t("Contraseña actualizada.", "Password updated.", "已更新密碼"))
            session.pop("pwd_reset_user", None)
            return redirect(url_for("login"))

    try:
        return render_template("password_reset_form.html", msg=msg)
    except TemplateNotFound:
        return """
        <h1>Ingresar nueva contraseña</h1>
        <form method="post">
            <input type="password" name="p1" placeholder="Nueva contraseña"/>
            <input type="password" name="p2" placeholder="Repetir contraseña"/>
            <button>Actualizar</button>
        </form>
        """, 200
# =========================================================
# SELECCIÓN DE REGISTRO (Router Nacional / Extranjero / Ambos)
# =========================================================
@app.route("/register_router")
def register_router():
    """
    Pantalla intermedia para elegir el tipo de usuario antes del formulario.
    Se invoca desde el botón 'Registrarse' en landing.html.
    """
    opciones = [
        {
            "titulo": t("Registro Nacional", "National Registration", "國內註冊"),
            "descripcion": t("Para empresas chilenas: productores, plantas, packings, frigoríficos y exportadores.",
                             "For Chilean companies: producers, plants, packings, cold storages and exporters.",
                             "適用於智利公司：生產商、工廠、包裝廠及冷藏商。"),
            "url": url_for("register", tipo="compra_venta", nac="nacional"),
            "btn": t("Registro Nacional", "National", "國內")
        },
        {
            "titulo": t("Registro Extranjero", "Foreign Registration", "國際註冊"),
            "descripcion": t("Para compradores o importadores internacionales que buscan proveedores en Chile.",
                             "For international buyers or importers looking for suppliers in Chile.",
                             "適用於希望尋找智利供應商的國際買家或進口商。"),
            "url": url_for("register", tipo="compra_venta", nac="extranjero"),
            "btn": t("Registro Extranjero", "Foreign", "國際")
        },
        {
            "titulo": t("Registro de Servicios", "Service Registration", "服務註冊"),
            "descripcion": t("Para empresas chilenas que ofrecen servicios logísticos o complementarios.",
                             "For Chilean companies offering logistics or complementary services.",
                             "適用於提供物流或相關服務的智利公司。"),
            "url": url_for("register", tipo="servicios", nac="nacional"),
            "btn": t("Registro de Servicios", "Service", "服務")
        },
        {
            "titulo": t("Registro Mixto (Ambos)", "Mixed Registration (Both)", "混合註冊"),
            "descripcion": t("Solo para Packing y Frigoríficos: pueden operar tanto en compraventa como servicios.",
                             "Only for Packing and Cold Storages: can operate in both buy/sell and service profiles.",
                             "僅限包裝廠與冷藏商，可同時提供買賣與服務。"),
            "url": url_for("register", tipo="ambos", nac="nacional"),
            "btn": t("Registro Mixto", "Mixed", "混合")
        }
    ]
    return render_template("register_router.html", opciones=opciones)


# ---------------------------------------------------------
# REGISTRO DE USUARIOS
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    nacionalidad = request.args.get("nac")
    perfil_tipo = request.args.get("tipo")

    ROLES_COMPRA_VENTA = ["Productor", "Planta", "Packing", "Frigorífico", "Exportador"]
    ROLES_SERVICIOS = ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"]
    ROLES_AMBOS = ["Packing", "Frigorífico"]

    if request.method == "POST":
        nacionalidad = request.form.get("nacionalidad") or "nacional"
        perfil_tipo = request.form.get("perfil_tipo") or "compra_venta"

        username = (request.form.get("username") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        telefono = (request.form.get("phone") or "").strip()
        direccion = (request.form.get("address") or "").strip()
        pais = (request.form.get("pais") or "").strip()
        rol = (request.form.get("rol") or "").strip()

        if not username or not password:
            error = t("Completa los campos obligatorios.", "Please fill required fields.")
        elif username in USERS:
            error = t("El usuario ya existe.", "User already exists.")
        else:
            if nacionalidad == "extranjero":
                rol = "Cliente extranjero"
                perfil_tipo = "compra_venta"
            elif nacionalidad == "nacional":
                if perfil_tipo == "compra_venta" and rol not in ROLES_COMPRA_VENTA:
                    error = t("Rol inválido para perfil de compra/venta.", "Invalid role for buy/sell profile.")
                elif perfil_tipo == "servicios" and rol not in ROLES_SERVICIOS:
                    error = t("Rol inválido para perfil de servicios.", "Invalid role for services profile.")
                elif perfil_tipo == "ambos" and rol not in ROLES_AMBOS:
                    error = t("Solo Packing o Frigorífico pueden registrar ambos perfiles.",
                              "Only Packing or Cold Storage can register as both.")

        if not error:
            rut_file_path = None
            if nacionalidad == "nacional" and "rut_file" in request.files:
                f = request.files["rut_file"]
                if f and f.filename and allowed_file(f.filename):
                    fname = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
                    f.save(os.path.join(UPLOAD_FOLDER, fname))
                    rut_file_path = f"uploads/{fname}"

            rut = (request.form.get("rut") or "").strip() if nacionalidad == "nacional" else None
            eori = (request.form.get("eori") or "").strip() if nacionalidad == "extranjero" else None
            otros_id = (request.form.get("otros_id") or "").strip() if nacionalidad == "extranjero" else None
            if not pais:
                pais = "CL" if nacionalidad == "nacional" else "US"

            USERS[username] = {
                "password": password,
                "rol": rol,
                "perfil_tipo": perfil_tipo,
                "pais": pais,
            }

            USER_PROFILES[username] = {
                "empresa": empresa or username.split("@")[0].replace(".", " ").title(),
                "rut": rut,
                "rut_file": rut_file_path,
                "rol": rol,
                "perfil_tipo": perfil_tipo,
                "pais": pais,
                "email": username,
                "telefono": telefono,
                "direccion": direccion,
                "descripcion": "Nuevo perfil registrado.",
                "items": [],
                "eori": eori,
                "otros_id": otros_id,
            }

            session["user"] = username
            flash(t("Registro exitoso", "Registration successful", "註冊完成"))
            return render_template("registro_exitoso.html")

    return render_template(
        "register.html",
        error=error,
        nacionalidad=nacionalidad,
        perfil_tipo=perfil_tipo,
        roles_all_cv=["Productor", "Planta", "Packing", "Frigorífico", "Exportador", "Cliente extranjero"],
        roles_srv=["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
    )


# =========================================================
# DASHBOARD (Panel principal del usuario)
# =========================================================

@app.route("/dashboard")
def dashboard():
    """
    Muestra el panel principal con opciones según el rol del usuario.
    """
    if not is_logged():
        flash(t("Debes iniciar sesión para acceder al panel.",
                "You must log in to access the dashboard.",
                "您必須登入才能訪問主頁面。"))
        return redirect(url_for("login"))

    user_email = session["user"]
    user_data = USERS.get(user_email, {})
    perfil_data = USER_PROFILES.get(user_email, {})

    rol = user_data.get("rol", "Desconocido")
    nombre = user_data.get("nombre", "Usuario")
    empresa = perfil_data.get("empresa", "")
    descripcion = perfil_data.get("descripcion", "")
    cart = get_cart()

    # Opciones visibles según tipo de usuario
    acciones = [
        {"ruta": "detalles", "param": "compras", "nombre": t("Comprar", "Buy", "採購")},
        {"ruta": "detalles", "param": "ventas", "nombre": t("Vender", "Sell", "銷售")},
        {"ruta": "detalles", "param": "servicios", "nombre": t("Servicios", "Services", "服務")},
        {"ruta": "perfil", "param": "", "nombre": t("Mi Perfil", "My Profile", "我的資料")},
        {"ruta": "carrito", "param": "", "nombre": t(f"Carrito 🛒 ({len(cart)})", f"Cart 🛒 ({len(cart)})", f"購物車 🛒 ({len(cart)})")},
    ]

    return render_template(
        "dashboard.html",
        nombre=nombre,
        rol=rol,
        empresa=empresa,
        descripcion=descripcion,
        acciones=acciones,
    )

# =========================================================
# FILTROS Y DETALLES (Ventas / Compras / Servicios)
# =========================================================
@app.route("/detalles/<tipo>", methods=["GET", "POST"])
def detalles(tipo):
    """
    Muestra los detalles disponibles según el tipo y el rol del usuario logeado.
    Incluye buscador y checkboxes para agregar varios al carrito.
    """
    tipo = tipo.lower()
    if tipo not in ("ventas", "compras", "servicios"):
        abort(404)

    my_rol = None
    roles_permitidos = None
    if is_logged():
        me = USERS.get(session["user"], {})
        my_rol = me.get("rol", "")
        roles_permitidos = set(targets_for(tipo, my_rol))

    # Buscar por nombre o producto
    filtro_texto = (request.args.get("q", "") or "").lower().strip()
    data = []

    # --- Tipo: COMPRAS (ve ofertas de quienes venden) ---
    if tipo == "compras":
        tag = "oferta"

    # --- Tipo: VENTAS (ve demandas de quienes compran) ---
    elif tipo == "ventas":
        tag = "demanda"

    # --- Tipo: SERVICIOS (todos pueden verlos) ---
    else:
        tag = "servicio"

    # Búsqueda filtrada
    for uname, c in USER_PROFILES.items():
        if any(it.get("tipo") == tag for it in c.get("items", [])):
            if (roles_permitidos is None) or (c["rol"] in roles_permitidos):
                if (not filtro_texto) or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion", "").lower()):
                    item = c.copy()
                    item["username"] = uname
                    data.append(item)

    # Render según tipo
    tpl = (
        "detalle_ventas.html" if tipo == "ventas"
        else "detalle_compras.html" if tipo == "compras"
        else "detalle_servicio.html"
    )
    return render_template(tpl, data=wrap_list(data), tipo=tipo, query=filtro_texto)

# =========================================================
# CLIENTES Y DETALLES DE PERFIL PÚBLICO
# =========================================================
@app.route("/clientes")
def clientes():
    filtro = request.args.get("tipo")
    if filtro in ("compras", "ventas", "servicios"):
        return redirect(url_for("detalles", tipo=filtro))

    lista = []
    for uname, prof in USER_PROFILES.items():
        if "cliente" in (prof.get("rol") or "").lower():
            item = prof.copy()
            item["username"] = uname
            lista.append(item)

    return render_template("clientes.html", clientes=wrap_list(lista))


@app.route("/cliente/<username>")
def cliente_detalle(username):
    prof = USER_PROFILES.get(username)
    if not prof:
        abort(404)
    comp = {
        "nombre": prof.get("empresa"),
        "rut": prof.get("rut"),
        "pais": prof.get("pais"),
        "email": prof.get("email"),
        "telefono": prof.get("telefono"),
        "direccion": prof.get("direccion"),
        "descripcion": prof.get("descripcion"),
        "items": prof.get("items", []),
    }
    return render_template("cliente_detalle.html", comp=ViewObj(comp), username=username)


# =========================================================
# PERFIL PERSONAL (Editar datos + Agregar / Eliminar ítems)
# =========================================================
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if not is_logged():
        return redirect(url_for("login"))
    prof = current_user_profile()
    if not prof:
        abort(404)

    mensaje = None
    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_profile":
            prof["empresa"] = request.form.get("empresa", prof.get("empresa", "")).strip()
            prof["email"] = request.form.get("email", prof.get("email", "")).strip()
            prof["telefono"] = request.form.get("telefono", prof.get("telefono", "")).strip()
            prof["direccion"] = request.form.get("direccion", prof.get("direccion", "")).strip()
            prof["descripcion"] = request.form.get("descripcion", prof.get("descripcion", "")).strip()
            mensaje = t("Perfil actualizado.", "Profile updated.")

        elif action == "add_item":
            tipo_perfil_item = request.form.get("tipo_perfil_item", "").strip()
            if tipo_perfil_item == "servicios":
                servicio = request.form.get("servicio", "").strip()
                capacidad = request.form.get("capacidad", "").strip()
                ubicacion = request.form.get("ubicacion", "").strip()
                if servicio:
                    prof.setdefault("items", []).append({
                        "tipo": "servicio",
                        "servicio": servicio,
                        "capacidad": capacidad,
                        "ubicacion": ubicacion
                    })
                    mensaje = t("Servicio agregado.", "Service added.")
            else:
                subtipo = request.form.get("subtipo", "oferta")
                producto = request.form.get("producto", "").strip()
                variedad = request.form.get("variedad", "").strip()
                cantidad = request.form.get("cantidad", "").strip()
                bulto = request.form.get("bulto", "").strip()
                origen = request.form.get("origen", "").strip()
                precio_caja = norm_money(request.form.get("precio_caja", ""))
                precio_kilo = norm_money(request.form.get("precio_kilo", ""))
                if producto:
                    prof.setdefault("items", []).append({
                        "tipo": subtipo,
                        "producto": producto,
                        "variedad": variedad,
                        "cantidad": cantidad,
                        "bulto": bulto,
                        "origen": origen,
                        "precio_caja": precio_caja,
                        "precio_kilo": precio_kilo,
                    })
                    mensaje = t("Ítem agregado.", "Item added.")

        elif action and action.startswith("delete_item_"):
            try:
                idx = int(action.split("_")[-1])
            except Exception:
                idx = -1
            if 0 <= idx < len(prof.get("items", [])):
                prof["items"].pop(idx)
                mensaje = t("Ítem eliminado del perfil.", "Item removed from profile.")

    return render_template("perfil.html", perfil=ViewObj(prof), mensaje=mensaje)


# =========================================================
# PERFIL PÚBLICO Y MENSAJERÍA CON ENFRIAMIENTO (3 días)
# =========================================================
from datetime import datetime

def _msg_history() -> dict:
    return session.setdefault("msg_history", {})

def _can_message(username: str) -> tuple[bool, Optional[int]]:
    hist = _msg_history()
    ts = hist.get(username)
    if not ts:
        return True, None
    try:
        last = datetime.fromisoformat(ts)
    except Exception:
        return True, None
    delta = datetime.utcnow() - last
    if delta.days >= 3:
        return True, None
    restantes = int((3 * 24 * 60) - (delta.total_seconds() / 60))
    return False, max(restantes, 1)


@app.route("/cliente/<username>/mensaje", methods=["POST"])
def cliente_mensaje(username):
    prof = USER_PROFILES.get(username)
    if not prof:
        abort(404)

    puede, minutos = _can_message(username)
    if not puede:
        dias = minutos // (24*60)
        horas = (minutos % (24*60)) // 60
        mins = minutos % 60
        if dias > 0:
            restante_txt = f"{dias}d {horas}h {mins}m"
        elif horas > 0:
            restante_txt = f"{horas}h {mins}m"
        else:
            restante_txt = f"{mins}m"
        flash(t(
            f"Ya enviaste un mensaje reciente. Podrás escribir nuevamente en {restante_txt}.",
            f"You have sent a recent message. You can write again in {restante_txt}.",
            f"您最近已發送訊息，請於 {restante_txt} 後再試。"
        ))
        return redirect(url_for("cliente_detalle", username=username))

    hist = _msg_history()
    hist[username] = datetime.utcnow().isoformat()
    session["msg_history"] = hist

    contenido = (request.form.get("mensaje") or "").strip()
    if not contenido:
        contenido = t("Mensaje sin contenido", "Empty message")

    flash(t(
        f"Tu mensaje a {prof.get('empresa', username)} fue enviado correctamente.",
        f"Your message to {prof.get('empresa', username)} was sent."
    ))
    return redirect(url_for("cliente_detalle", username=username))


# =========================================================
# CARRITO DE COMPRAS / SERVICIOS
# =========================================================

@app.route("/carrito")
def carrito():
    """
    Muestra el contenido actual del carrito del usuario logeado.
    """
    if not is_logged():
        flash(t("Debes iniciar sesión para ver tu carrito.",
                "You must log in to view your cart.",
                "您必須登入才能查看購物車。"))
        return redirect(url_for("login"))

    cart = get_cart()
    return render_template("carrito.html", cart=cart)


@app.route("/cart_add", methods=["POST"])
def cart_add():
    """
    Agrega un ítem al carrito.
    """
    if not is_logged():
        flash(t("Debes iniciar sesión para agregar al carrito.",
                "You must log in to add to cart.",
                "您必須登入才能加入購物車。"))
        return redirect(url_for("login"))

    username = request.form.get("username")
    tipo = request.form.get("tipo")
    if not username or not tipo:
        flash(t("Error al agregar al carrito.",
                "Error adding to cart.",
                "加入購物車時出錯。"))
        return redirect(request.referrer or url_for("dashboard"))

    user = USER_PROFILES.get(username)
    if not user:
        flash(t("Usuario no encontrado.",
                "User not found.",
                "未找到使用者。"))
        return redirect(request.referrer or url_for("dashboard"))

    item = {
        "empresa": user.get("empresa"),
        "rol": user.get("rol"),
        "tipo": tipo,
        "username": username,
        "descripcion": user.get("descripcion", ""),
    }

    add_to_cart(item)
    flash(t("Agregado al carrito ✅",
            "Added to cart ✅",
            "已加入購物車 ✅"))
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/cart/remove/<int:index>", methods=["POST"])
def cart_remove(index):
    """
    Elimina un ítem del carrito.
    """
    if remove_from_cart(index):
        flash(t("Ítem eliminado", "Item removed", "已刪除"))
    else:
        flash(t("Error al eliminar el ítem.",
                "Error removing item.",
                "刪除項目時出錯。"))
    return redirect(url_for("carrito"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    """
    Vacía completamente el carrito.
    """
    clear_cart()
    flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"))
    return redirect(url_for("carrito"))


@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Simula el proceso de checkout / solicitud de compra.
    """
    items = get_cart()
    if not items:
        flash(t("Tu carrito está vacío.",
                "Your cart is empty.",
                "購物車是空的"))
        return redirect(url_for("carrito"))

    clear_cart()
    flash(t("Hemos recibido tu solicitud. Te contactaremos pronto ✅",
            "We've received your request. We'll contact you soon ✅",
            "我們已收到您的請求，稍後聯繫您 ✅"))
    return redirect(url_for("dashboard"))

# =========================================================
# CENTRO DE AYUDA
# =========================================================
@app.route("/ayuda")
def ayuda():
    temas = [
        {
            "titulo": t("Registro de usuario", "User Registration", "用戶註冊"),
            "detalle": t(
                "Aprende a crear tu cuenta como exportador o comprador internacional en pocos pasos.",
                "Learn how to create your account as an exporter or international buyer in just a few steps.",
                "了解如何在幾個步驟內創建出口商或國際買家帳戶。"
            ),
        },
        {
            "titulo": t("Gestión de productos y servicios", "Product and Service Management", "產品與服務管理"),
            "detalle": t(
                "Sube tus productos, publica tus servicios y edita tus ofertas directamente desde tu panel.",
                "Upload your products, post your services, and edit your offers directly from your dashboard.",
                "直接從儀表板上傳產品、發布服務並編輯報價。"
            ),
        },
        {
            "titulo": t("Compras y cotizaciones", "Purchases and Quotations", "購買與報價"),
            "detalle": t(
                "Los compradores pueden contactar a exportadores o proveedores de servicios mediante el botón 'Contactar'.",
                "Buyers can contact exporters or service providers through the 'Contact' button.",
                "買家可以通過「聯絡」按鈕聯繫出口商或服務供應商。"
            ),
        },
        {
            "titulo": t("Seguridad y soporte", "Security and Support", "安全與支援"),
            "detalle": t(
                "WS garantiza la confidencialidad de tus datos y ofrece soporte personalizado.",
                "WS ensures data confidentiality and provides personalized support.",
                "WS 確保您的數據保密並提供個性化支援。"
            ),
        },
    ]
    return render_template("ayuda.html", temas=temas, title=t("Centro de Ayuda", "Help Center", "幫助中心"))


# =========================================================
# MAIN (solo para pruebas locales)
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
