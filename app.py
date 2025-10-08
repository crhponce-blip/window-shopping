# === app.py (completo) ===
import os
import uuid
import json
from datetime import timedelta
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
            {"tipo": "oferta", "producto": "Arándano Duke", "bulto": "pallets", "cantidad": "60", "origen": "VI Región", "precio_caja": "$15"}
        ]
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
            {"tipo": "oferta", "producto": "Cajas plásticas 10kg", "bulto": "unidades", "cantidad": "20000", "origen": "R.M."}
        ]
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
            {"tipo": "oferta", "producto": "Ciruela Angeleno", "bulto": "pallets", "cantidad": "50", "origen": "R.M.", "precio_caja": "$11"}
        ]
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
            {"tipo": "servicio", "servicio": "Cámara fría", "capacidad": "1500 pallets", "ubicacion": "Valparaíso"}
        ]
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
            {"tipo": "demanda", "producto": "Uva Thompson", "bulto": "pallets", "cantidad": "80", "origen": "V Región"}
        ]
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
            {"tipo": "demanda", "producto": "Cereza Lapins", "bulto": "pallets", "cantidad": "300", "origen": "CL"}
        ],
        "eori": None, "otros_id": None  # Para extranjeros preferimos EORI y Otros
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
            {"tipo": "servicio", "servicio": "Flete marítimo local", "capacidad": "20 contenedores", "ubicacion": "Valparaíso"}
        ]
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
            {"tipo": "servicio", "servicio": "Asesoría logística", "capacidad": "Media", "ubicacion": "Valparaíso"}
        ]
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
            {"tipo": "servicio", "servicio": "Desconsolidado", "capacidad": "80/día", "ubicacion": "San Antonio"}
        ]
    }
}
# --- Fin de diccionario USER_PROFILES ---

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
    # (Quiénes puedo ver cuando QUIERO COMPRAR fruta)
    compras_vis = {
        # Packing compra a Planta y Frigorífico
        "Packing": ["Planta", "Frigorífico"],
        # Frigorífico compra a Planta y Packing
        "Frigorífico": ["Planta", "Packing"],
        # Exportador compra a Exportador/Planta/Packing/Frigorífico
        "Exportador": ["Exportador", "Packing", "Frigorífico", "Planta"],
        # Cliente extranjero: al entrar a "compras" quiere ver EXPORTADORES vendiendo (se maneja especial abajo)
        "Cliente extranjero": ["Exportador"],
        # Productor / Planta NO compran (se bloqueará con aviso en la vista)
        "Productor": [],
        "Planta": [],
        "default": ["Productor", "Planta", "Packing", "Frigorífico", "Exportador"],
    }

    # --- VENTAS ---
    # (A quiénes veo cuando QUIERO VENDER fruta)
    ventas_vis = {
        # Packing vende a Exportador y Frigorífico (y puede ver otros Packing)
        "Packing": ["Exportador", "Frigorífico", "Packing"],
        # Frigorífico vende a Packing y Exportador (NO a otros frigoríficos)
        "Frigorífico": ["Packing", "Exportador"],
        # Exportador vende a Cliente extranjero y a Exportadores
        "Exportador": ["Exportador", "Cliente extranjero"],
        # Productor/Planta venden a Exportadores, Packing, Frigorífico
        "Productor": ["Exportador", "Packing", "Frigorífico"],
        "Planta": ["Exportador", "Packing", "Frigorífico"],
        "default": ["Exportador", "Packing", "Frigorífico", "Cliente extranjero"],
    }

    # --- SERVICIOS ---
    # (A quiénes veo cuando QUIERO COMPRAR servicio)
    servicios_vis = {
        # Todos los compradores de servicio ven a los prestadores:
        # Packing, Frigorífico, Transporte, Extraportuario, Agencia de Aduanas
        "Planta": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Productor": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Packing": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Frigorífico": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Exportador": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        # Cliente extranjero típicamente no compra servicios locales -> vacío o restringido
        "Cliente extranjero": [],
        "default": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
    }

    mapping = {"compras": compras_vis, "ventas": ventas_vis, "servicios": servicios_vis}.get(tipo, {})
    return mapping.get(my_rol, mapping.get("default", []))

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
        # Fallback simple por si aún no subes el template
        return """
        <h1>Recuperar contraseña</h1>
        <form method="post">
          <input name="email" placeholder="Email"/><button>Enviar</button>
        </form>
        """, 200
@app.route("/password_reset/reset", methods=["GET", "POST"])
def password_reset_form():
    msg = None
    email = session.get("pwd_reset_user")

    if not email:
        flash(t("Primero solicita el enlace de restablecimiento.", "Request a reset link first.", "請先申請重設連結"))
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
        # Fallback simple por si aún no subes el template
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
    return render_template("register_router.html")

# ---------------------------------------------------------
# REGISTRO DE USUARIOS (validación por nacionalidad, tipo y rol)
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    nacionalidad = request.args.get("nac")
    perfil_tipo = request.args.get("tipo")

    # --- Definición de roles según la lógica WS ---
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

        # --- Validación de campos obligatorios ---
        if not username or not password:
            error = t("Completa los campos obligatorios.", "Please fill required fields.")
        elif username in USERS:
            error = t("El usuario ya existe.", "User already exists.")
        else:
            # --- Asignar rol automático para extranjeros ---
            if nacionalidad == "extranjero":
                rol = "Cliente extranjero"
                perfil_tipo = "compra_venta"

            # --- Validación de roles según tipo de perfil ---
            elif nacionalidad == "nacional":
                if perfil_tipo == "compra_venta" and rol not in ROLES_COMPRA_VENTA:
                    error = t("Rol inválido para perfil de compra/venta.",
                              "Invalid role for buy/sell profile.")
                elif perfil_tipo == "servicios" and rol not in ROLES_SERVICIOS:
                    error = t("Rol inválido para perfil de servicios.",
                              "Invalid role for services profile.")
                elif perfil_tipo == "ambos" and rol not in ROLES_AMBOS:
                    error = t("Solo Packing o Frigorífico pueden registrar ambos perfiles.",
                              "Only Packing or Cold Storage can register as both.")

        # --- Si no hay error, registrar usuario ---
        if not error:
            # Guardar archivo RUT (solo nacionales)
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

            # --- Crear usuario y perfil ---
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
            # Mostrar pantalla visual de confirmación
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
# DASHBOARD
# =========================================================
@app.route("/dashboard")
def dashboard():
    if not is_logged():
        return redirect(url_for("login"))
    profile = current_user_profile()
    usuario = session.get("user")
    rol = USERS.get(usuario, {}).get("rol", "-")
    perfil_tipo = USERS.get(usuario, {}).get("perfil_tipo", "-")
    my_company_view = ViewObj(profile or {"items": []})

    return render_template(
        "dashboard.html",
        usuario=usuario,
        rol=rol,
        perfil_tipo=perfil_tipo,
        my_company=my_company_view,
        cart=get_cart(),
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
    # Caso especial Cliente extranjero en "compras":
    # quiere ver exportadores que ESTÁN VENDIENDO (oferta)
    if tipo == "compras" and my_rol == "Cliente extranjero":
        tag = "oferta"
        forced_roles = {"Exportador"}
        for uname, c in USER_PROFILES.items():
            if c.get("rol") in forced_roles and any(it.get("tipo") == tag for it in c.get("items", [])):
                if (not filtro_texto) or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion","").lower()):
                    item = c.copy()
                    item["username"] = uname
                    data.append(item)
        tpl = "detalle_compras.html"  # usamos plantilla de compras para mantener coherencia visual
        return render_template(tpl, data=wrap_list(data), tipo=tipo, query=filtro_texto)

    if tipo == "servicios":
        for uname, c in USER_PROFILES.items():
            if any(it.get("tipo") == "servicio" for it in c.get("items", [])):
                if (roles_permitidos is None) or (c["rol"] in roles_permitidos):
                    if (not filtro_texto) or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion","").lower()):
                        item = c.copy()
                        item["username"] = uname
                        data.append(item)
        tpl = "detalle_servicio.html"  # nombre correcto para evitar 500
    else:
        # ventas -> "oferta"; compras -> "demanda"
        tag = "oferta" if tipo == "ventas" else "demanda"

        # Bloqueo suave: Productor/Planta NO compran
        if tipo == "compras" and my_rol in ("Productor", "Planta"):
            flash(t("Tu rol no puede comprar fruta. Revisa Ventas o Servicios.",
                    "Your role cannot buy fruit. Check Sales or Services.",
                    "你的角色不能購買水果。請查看銷售或服務。"))
            # data quedará vacío, se muestran filtros sin resultados

        for uname, c in USER_PROFILES.items():
            if any(it.get("tipo") == tag for it in c.get("items", [])):
                if (roles_permitidos is None) or (c["rol"] in roles_permitidos):
                    if (not filtro_texto) or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion","").lower()):
                        item = c.copy()
                        item["username"] = uname
                        data.append(item)
        tpl = "detalle_ventas.html" if tipo == "ventas" else "detalle_compras.html"

    return render_template(tpl, data=wrap_list(data), tipo=tipo, query=filtro_texto)

# =========================================================
# CLIENTES Y DETALLES DE PERFIL PÚBLICO
# =========================================================
@app.route("/clientes")
def clientes():
    """
    Permite filtrar según tipo: ?tipo=compras|ventas|servicios
    """
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
# PERFIL PERSONAL (Editar datos + Agregar ítems + Eliminar ítems)
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
# CARRITO DE COMPRAS  ✅ (reemplazo/actualizado)
# =========================================================
from datetime import datetime  # import local permitido

def _hidden_keys() -> list:
    """Devuelve/crea la lista de claves ocultas en la sesión."""
    return session.setdefault("hidden_keys", [])

def _save_hidden(keys: list):
    session["hidden_keys"] = keys

def _msg_history() -> dict:
    """Historial de mensajes enviados por usuario destino."""
    return session.setdefault("msg_history", {})

def _can_message(username: str) -> tuple[bool, Optional[int]]:
    """
    True si han pasado >= 3 días desde el último mensaje a 'username'.
    Devuelve (puede, minutos_restantes_si_no).
    """
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
    # minutos restantes hasta completar 3 días
    restantes = int((3*24*60) - (delta.total_seconds() / 60))
    return False, max(restantes, 1)

@app.route("/carrito", methods=["GET", "POST"])
def carrito():
    """
    Vista del carrito con acciones:
    - POST action=clear
    - POST action=remove:<idx>
    - POST action=remove_selected con rm[]=idx,...
    """
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "clear":
            clear_cart()
            flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"))
            return redirect(url_for("carrito"))

        if action.startswith("remove:"):
            idx = action.split(":", 1)[1]
            if remove_from_cart(idx):
                flash(t("Ítem eliminado", "Item removed", "已刪除"))
            return redirect(url_for("carrito"))

        if action == "remove_selected":
            indices = [int(i) for i in request.form.getlist("rm")]
            indices = sorted(set([i for i in indices if i >= 0]), reverse=True)
            removed = 0
            cart = get_cart()
            for i in indices:
                if 0 <= i < len(cart):
                    cart.pop(i)
                    removed += 1
            session["cart"] = cart
            if removed:
                flash(t(f"{removed} ítem(s) eliminados", f"{removed} item(s) removed"))
            return redirect(url_for("carrito"))

    # GET
    return render_template("carrito.html", cart=get_cart())

# =========================================================
# AGREGAR AL CARRITO (Ítem único desde tarjetas)
# =========================================================
@app.route("/cart_add", methods=["POST"])
def cart_add():
    payload = {
        "empresa": (request.form.get("empresa") or "").strip(),
        "producto": (request.form.get("producto") or "").strip(),
        "servicio": (request.form.get("servicio") or "").strip(),
        "variedad": (request.form.get("variedad") or "").strip(),
        "cantidad": (request.form.get("cantidad") or "").strip(),
        "bulto": (request.form.get("bulto") or "").strip(),
        "origen": (request.form.get("origen") or "").strip(),
        "precio_caja": (request.form.get("precio_caja") or "").strip(),
        "precio_kilo": (request.form.get("precio_kilo") or "").strip(),
        "username": (request.form.get("username") or "").strip(),
        "key": (request.form.get("key") or "").strip(),  # opcional
    }
    clean = {k: v for k, v in payload.items() if v}
    if clean:
        add_to_cart(clean)
        flash(t("Agregado al carrito", "Added to cart", "已加入購物車"))
    else:
        flash(t("No se pudo agregar el ítem.", "Item could not be added.", "無法加入項目"))
    return redirect(request.referrer or url_for("carrito"))


# =========================================================
# NUEVO ENDPOINT ✅ para múltiples ítems (detalles_compras / ventas / servicios)
# =========================================================
@app.route("/cart_add_bulk", methods=["POST"])
def cart_add_bulk():
    """
    Permite agregar varios ítems seleccionados desde los formularios
    de detalle_compras, detalle_ventas o detalle_servicio.
    """
    seleccionados = request.form.getlist("sel") or request.form.getlist("selected")
    if not seleccionados:
        flash(t("No seleccionaste ningún producto.", "No items selected.", "未選擇任何項目"))
        return redirect(request.referrer or url_for("dashboard"))

    agregados = 0
    for raw in seleccionados:
        try:
            item = json.loads(raw)
            if isinstance(item, dict):
                add_to_cart(item)
                agregados += 1
        except Exception:
            continue

    if agregados:
        flash(t(f"Se agregaron {agregados} ítems al carrito 🛒",
                f"{agregados} items added to cart 🛒",
                f"已將 {agregados} 個項目加入購物車 🛒"))
    else:
        flash(t("No se pudo agregar ningún ítem.", "No items could be added.", "無法加入任何項目"))
    return redirect(request.referrer or url_for("dashboard"))

# =========================================================
# AGREGAR VARIOS AL CARRITO (checkbox de lista)
# - En el template, cada checkbox puede llevar value con un JSON del ítem
#   name="selected" value='{"empresa":"...", "producto":"...", ...}'
# =========================================================
@app.route("/cart/bulk_add", methods=["POST"])
def cart_bulk_add():
    selected = request.form.getlist("selected")
    ok = 0
    for raw in selected:
        try:
            item = json.loads(raw)
            if isinstance(item, dict) and any(item.values()):
                add_to_cart(item)
                ok += 1
        except Exception:
            # Si no viene JSON, ignoramos ese elemento
            continue
    if ok:
        flash(t(f"{ok} ítem(s) agregados al carrito",
                f"{ok} item(s) added to cart"))
    else:
        flash(t("No se seleccionó nada para agregar.",
                "Nothing selected to add."))
    return redirect(request.referrer or url_for("carrito"))

# =========================================================
# ELIMINAR DE VISTA (ocultar tarjetas seleccionadas)
# =========================================================
@app.route("/hide_from_view", methods=["POST"])
def hide_from_view():
    """
    Permite ocultar elementos temporalmente de la vista (detalle o lista),
    guardando sus claves en la sesión. Evita duplicados de endpoint.
    """
    keys = request.form.getlist("hide_keys") or request.form.getlist("selected_keys")
    if not keys:
        # fallback: si venían JSON, intentar extraer "key"
        for raw in request.form.getlist("selected"):
            try:
                obj = json.loads(raw)
                k = obj.get("key")
                if k:
                    keys.append(k)
            except Exception:
                pass

    if not keys:
        flash(t("No se seleccionó nada para ocultar.",
                "Nothing selected to hide.",
                "未選擇要隱藏的項目"))
        return redirect(request.referrer or url_for("home"))

    hidden = set(_hidden_keys())
    hidden.update(keys)
    _save_hidden(list(hidden))
    flash(t("Elementos ocultados en esta vista.",
            "Items hidden from this view.",
            "已隱藏這些項目"))
    return redirect(request.referrer or url_for("home"))

@app.route("/unhide_all", methods=["POST"])
def unhide_all():
    _save_hidden([])
    flash(t("Se restauraron todos los elementos ocultos.",
            "All hidden items were restored."))
    return redirect(request.referrer or url_for("home"))

# =========================================================
# PERFIL PÚBLICO Y MENSAJERÍA CON ENFRIAMIENTO (3 días)
# Enlázalo desde tarjetas con url_for('cliente_detalle', username=uname)
# y el formulario de mensaje a /cliente/<username>/mensaje
# =========================================================
@app.route("/cliente/<username>/mensaje", methods=["POST"])
def cliente_mensaje(username):
    prof = USER_PROFILES.get(username)
    if not prof:
        abort(404)

    puede, minutos = _can_message(username)
    if not puede:
        # tiempo restante legible
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

    # Guardamos el momento del envío (no persistente, solo sesión)
    hist = _msg_history()
    hist[username] = datetime.utcnow().isoformat()
    session["msg_history"] = hist

    # (Aquí iría el envío real por email/API si aplica)
    contenido = (request.form.get("mensaje") or "").strip()
    if not contenido:
        contenido = t("Mensaje sin contenido", "Empty message")

    flash(t(
        f"Tu mensaje a {prof.get('empresa', username)} fue enviado correctamente.",
        f"Your message to {prof.get('empresa', username)} was sent."
    ))
    return redirect(url_for("cliente_detalle", username=username))
# =========================================================
# RUTA: Enviar mensaje desde un perfil (limitado a 1 cada 3 días)
# =========================================================
from datetime import datetime, timedelta

ULTIMO_ENVIO = {}

@app.route("/enviar_mensaje", methods=["POST"])
def enviar_mensaje():
    if not is_logged():
        return redirect(url_for("login"))

    remitente = current_user_email()
    destinatario = (request.form.get("destinatario") or "").strip()
    mensaje = (request.form.get("mensaje") or "").strip()

    if not destinatario or not mensaje:
        flash(t("El mensaje está incompleto. Intenta nuevamente.",
                "The message is incomplete. Please try again.",
                "訊息不完整，請再試一次。"))
        return redirect(request.referrer or url_for("home"))

    ahora = datetime.now()
    limite = ULTIMO_ENVIO.get(remitente)

    if limite and (ahora - limite).days < 3:
        dias_restantes = 3 - (ahora - limite).days
        flash(t(f"Ya enviaste un mensaje recientemente. Podrás enviar otro en {dias_restantes} día(s).",
                f"You already sent a message recently. You can send another in {dias_restantes} day(s).",
                f"您最近已發送過訊息。您可以在 {dias_restantes} 天後再次發送。"))
        return redirect(request.referrer or url_for("home"))

    # Registrar nuevo envío
    ULTIMO_ENVIO[remitente] = ahora

    return render_template("mensaje_enviado.html",
                           destinatario=destinatario,
                           mensaje=mensaje,
                           fecha=ahora.strftime("%d/%m/%Y %H:%M"))
# =========================================================
# RUTA: Centro de Ayuda (multilenguaje)
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

    return render_template(
        "ayuda.html",
        temas=temas,
        title=t("Centro de Ayuda", "Help Center", "幫助中心")
    )
