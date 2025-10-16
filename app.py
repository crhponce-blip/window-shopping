# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.7 extendida, sin recortes)
# Autor: Christopher Ponce & GPT-5
# ---------------------------------------------------------
# Parte 1: Configuración · Traducción · Usuarios ficticios (completos)
#           Helper de saneo · Idioma · Home · Register Router · Register
#           (con subida de documento) · Login
# =========================================================

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# ---------------------------------------------------------
# App & Config
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = "windowshopping_secret_key_v3_7"

# Carpeta para subir documentos (RUT u otros)
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------
# Datos en memoria
# ---------------------------------------------------------
USERS = {}
PUBLICACIONES = []  # se populará en partes siguientes
OCULTOS = {}        # publicaciones ocultas por usuario (se usa luego)
MENSAJES = []       # mensajes internos (se usa luego)
HIDDEN_COMPANIES = {}  # empresas ocultas en listado (se usa luego)

# ---------------------------------------------------------
# Usuarios ficticios (completos: con username, país, dirección, teléfono, items)
# ---------------------------------------------------------
USERS = {
    "admin@ws.com": {
        "nombre": "Administrador General",
        "email": "admin@ws.com",
        "password": "admin",
        "tipo": "Nacional",
        "rol": "Administrador",
        "empresa": "Window Shopping",
        "descripcion": "Administrador principal de la plataforma WS.",
        "fecha": "2025-10-10 22:00:00",
        "username": "admin",
        "pais": "CL",
        "direccion": "Santiago, RM, Chile",
        "telefono": "+56 2 1234 5678",
        "rut_doc": "",  # se completa si sube archivo
        "items": []
    },
    "compra@ws.com": {
        "nombre": "Luis Mercado",
        "email": "compra@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Compraventa",
        "empresa": "Mercado Chile Ltda.",
        "descripcion": "Compra y venta de frutas chilenas al por mayor.",
        "fecha": "2025-10-10 09:30:00",
        "username": "compra",
        "pais": "CL",
        "direccion": "Av. Las Industrias 1020, Rancagua",
        "telefono": "+56 9 1111 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Servicio consolidación pallets", "detalle": "Consolidación y picking para exportaciones", "precio": "USD 250"}
        ]
    },
    "servicios@ws.com": {
        "nombre": "Ana Frío",
        "email": "servicios@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Servicios",
        "empresa": "FríoExpress SpA",
        "descripcion": "Almacenamiento y logística frigorífica.",
        "fecha": "2025-10-09 15:10:00",
        "username": "servicios",
        "pais": "CL",
        "direccion": "Camino a Noviciado 5500, Pudahuel",
        "telefono": "+56 9 2345 6789",
        "rut_doc": "",
        "items": [
            {"nombre": "Almacenaje en frío", "detalle": "Cámaras -1°C a +4°C", "precio": "USD 0.15/kg/día"},
            {"nombre": "Cross docking", "detalle": "Operación 24/7 con monitoreo", "precio": "USD 180/orden"}
        ]
    },
    "extranjero@ws.com": {
        "nombre": "David Wang",
        "email": "extranjero@ws.com",
        "password": "1234",
        "tipo": "Extranjero",
        "rol": "Cliente Extranjero",
        "empresa": "Shanghai Imports Co.",
        "descripcion": "Importador asiático de frescos chilenos.",
        "fecha": "2025-10-11 18:20:00",
        "username": "extranjero",
        "pais": "CN",
        "direccion": "Pudong, Shanghai, China",
        "telefono": "+86 21 5555 6666",
        "rut_doc": "",
        "items": []
    },
    "packing@ws.com": {
        "nombre": "María Campos",
        "email": "packing@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Packing",
        "empresa": "Packing Andes SpA",
        "descripcion": "Embalaje y control de calidad para exportadores.",
        "fecha": "2025-10-12 10:15:00",
        "username": "packing",
        "pais": "CL",
        "direccion": "Parcela 12, San Felipe",
        "telefono": "+56 9 3456 7890",
        "rut_doc": "",
        "items": [
            {"nombre": "Embalaje flowpack", "detalle": "Automático, certificación BRC", "precio": "USD 0.08/un"},
            {"nombre": "Reembalaje urgente", "detalle": "SLA 6 horas", "precio": "USD 0.12/kg"}
        ]
    },
    "frigorifico@ws.com": {
        "nombre": "Carlos Frías",
        "email": "frigorifico@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Frigorífico",
        "empresa": "Frigorífico Polar Sur",
        "descripcion": "Almacenamiento en frío para exportación.",
        "fecha": "2025-10-12 12:00:00",
        "username": "frigorifico",
        "pais": "CL",
        "direccion": "Ruta 5 Sur km 340, Talca",
        "telefono": "+56 9 4567 8901",
        "rut_doc": "",
        "items": [
            {"nombre": "Túnel de frío", "detalle": "Descenso rápido de temperatura", "precio": "USD 0.06/kg"},
            {"nombre": "Monitoreo T° IoT", "detalle": "Reporte por lote", "precio": "USD 25/lote"}
        ]
    },
    "aduana@ws.com": {
        "nombre": "Patricio Reyes",
        "email": "aduana@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Agencia de Aduana",
        "empresa": "SurLog Agencia Aduanera",
        "descripcion": "Gestión documental y trámites de exportación.",
        "fecha": "2025-10-12 16:40:00",
        "username": "aduana",
        "pais": "CL",
        "direccion": "Puerto de San Antonio, Galpón 3",
        "telefono": "+56 9 5678 9012",
        "rut_doc": "",
        "items": [
            {"nombre": "Despacho exportación", "detalle": "DUA + V°B° SAG", "precio": "USD 120"},
            {"nombre": "Asesoría certificaciones", "detalle": "China/USA/UE", "precio": "USD 90/h"}
        ]
    },
    "transporte@ws.com": {
        "nombre": "Javier Ruta",
        "email": "transporte@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Transporte Extraportuario",
        "empresa": "Transportes SurCargo",
        "descripcion": "Traslado de fruta desde campos a puertos.",
        "fecha": "2025-10-12 20:00:00",
        "username": "transporte",
        "pais": "CL",
        "direccion": "Av. Puerto 690, Valparaíso",
        "telefono": "+56 9 6789 0123",
        "rut_doc": "",
        "items": [
            {"nombre": "Camión refrigerado 28 pallets", "detalle": "GPS + Control T°", "precio": "USD 420/viaje"},
            {"nombre": "Traslado puerto", "detalle": "Valpo/San Antonio", "precio": "USD 250/viaje"}
        ]
    },
    # 👇 Extras para tener masa crítica de datos de prueba
    "exportador@ws.com": {
        "nombre": "Sofía Export",
        "email": "exportador@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Exportador",
        "empresa": "Exportadora Los Andes",
        "descripcion": "Exportadora de cerezas, arándanos y uva.",
        "fecha": "2025-10-13 08:30:00",
        "username": "exportador",
        "pais": "CL",
        "direccion": "Camino El Olivo 123, Curicó",
        "telefono": "+56 9 7123 4567",
        "rut_doc": "",
        "items": [
            {"nombre": "Cereza Lapins 9.5", "detalle": "Embalaje clamshell", "precio": "USD 6.20/kg"},
            {"nombre": "Arándano Duke", "detalle": "Export pack 12x125g", "precio": "USD 5.10/kg"}
        ]
    },
    "productor@ws.com": {
        "nombre": "Pedro Campo",
        "email": "productor@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Productor",
        "empresa": "Campos del Valle",
        "descripcion": "Productor de fruta de exportación.",
        "fecha": "2025-10-13 09:00:00",
        "username": "productor",
        "pais": "CL",
        "direccion": "Parcela 5, Molina",
        "telefono": "+56 9 7000 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Uva Red Globe campo", "detalle": "Granel para packing", "precio": "USD 1.00/kg"}
        ]
    },
    "mixto@ws.com": {
        "nombre": "Carolina Mix",
        "email": "mixto@ws.com",
        "password": "1234",
        "tipo": "Mixto",
        "rol": "Compraventa",
        "empresa": "Mixto Trade & Service",
        "descripcion": "Opera compra-venta y presta servicios logísticos.",
        "fecha": "2025-10-13 10:15:00",
        "username": "mixto",
        "pais": "CL",
        "direccion": "Av. Central 200, Mostazal",
        "telefono": "+56 9 7333 4444",
        "rut_doc": "",
        "items": [
            {"nombre": "Paletizado", "detalle": "Paletizado conforme NCh", "precio": "USD 0.05/kg"}
        ]
    },
}

# ---------------------------------------------------------
# Traducciones & helper t()
# ---------------------------------------------------------
TRAD = {
    "Inicio": {"en": "Home", "zh": "首頁"},
    "Iniciar sesión": {"en": "Login", "zh": "登入"},
    "Registrarse": {"en": "Register", "zh": "註冊"},
    "Empresas": {"en": "Companies", "zh": "公司"},
    "Carrito": {"en": "Cart", "zh": "購物車"},
    "Perfil": {"en": "Profile", "zh": "個人資料"},
    "Salir": {"en": "Logout", "zh": "登出"},
    "Panel de Usuario": {"en": "User Panel", "zh": "使用者面板"},
    "Bienvenido": {"en": "Welcome", "zh": "歡迎"},
    "Agregar al carrito": {"en": "Add to cart", "zh": "加入購物車"},
    "Restaurar ocultos": {"en": "Restore hidden", "zh": "恢復隱藏"},
    "Agregar ítem": {"en": "Add item", "zh": "新增項目"},
    "Panel de Compraventa": {"en": "Trade Panel", "zh": "貿易面板"},
    "Panel de Servicios": {"en": "Services Panel", "zh": "服務面板"},
    "Panel Cliente Extranjero": {"en": "Foreign Client Panel", "zh": "外國客戶面板"},
    "Panel Administrador": {"en": "Administrator Panel", "zh": "管理員面板"},
}

def t(es, en=None, zh=None):
    """Traducción simple: clave en TRAD o textos ES/EN/ZH por parámetro."""
    lang = session.get("lang", "es")
    if isinstance(es, str) and es in TRAD:
        return TRAD[es].get(lang, es)
    if lang == "en" and en:
        return en
    if lang == "zh" and zh:
        return zh
    return es

@app.context_processor
def inject_t():
    return dict(t=t)

# ---------------------------------------------------------
# Helper: asegurar campos en USERS (por si no se cargan todos)
# ---------------------------------------------------------
def _ensure_user_fields():
    for email, u in USERS.items():
        u.setdefault("username", (email.split("@")[0]).lower())
        u.setdefault("pais", "CL")
        u.setdefault("direccion", "")
        u.setdefault("telefono", "")
        u.setdefault("tipo", u.get("tipo", "Nacional"))
        u.setdefault("items", [])
        u.setdefault("rut_doc", "")

_ensure_user_fields()

# ---------------------------------------------------------
# Rutas generales (idioma, home)
# ---------------------------------------------------------
@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang not in ["es", "en", "zh"]:
        lang = "es"
    session["lang"] = lang
    flash(t("Idioma cambiado", "Language changed", "語言已更改"), "info")
    return redirect(request.referrer or url_for("home"))

@app.route("/")
def home():
    lang = session.get("lang", "es")
    return render_template(
        "index.html",
        lang=lang,
        titulo=t("Inicio", "Home", "首頁")
    )

# ---------------------------------------------------------
# Registro — Router de selección y formulario
# ---------------------------------------------------------
# Roles disponibles para el <select> del formulario
ROLES_DISPONIBLES = [
    "Administrador",
    "Compraventa",
    "Productor",
    "Packing",
    "Frigorífico",
    "Exportador",
    "Servicios",
    "Transporte Extraportuario",
    "Agencia de Aduana",
    "Cliente Extranjero",
    "Mixto",
]

@app.route("/register_router", methods=["GET"])
def register_router():
    """Pantalla de selección de tipo de cuenta (usa REGISTER_ROUTER.HTML)."""
    return render_template(
        "register_router.html",
        titulo=t("Selecciona el tipo de cuenta", "Choose account type", "選擇帳戶類型")
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Formulario de registro (REGISTER.HTML).
    Acepta archivo 'rut_doc' y guarda en static/uploads.
    Pasa 'roles' para el <select>.
    """
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        pais = (request.form.get("pais") or "").strip().upper()[:2]
        direccion = (request.form.get("direccion") or "").strip()
        telefono = (request.form.get("telefono") or "").strip()

        # Nombre/tipo son opcionales en el form, normalizamos
        nombre = (request.form.get("nombre") or empresa or email.split("@")[0]).strip()
        tipo = (request.form.get("tipo") or "Nacional").strip()

        if not all([email, password, empresa, rol, pais, direccion, telefono]):
            flash(
                t("Por favor completa todos los campos",
                  "Please fill all fields",
                  "請填寫所有欄位"),
                "error"
            )
            return redirect(url_for("register"))

        if email in USERS:
            flash(t("El usuario ya existe", "User already exists", "使用者已存在"), "error")
            return redirect(url_for("register"))

        # Guardar documento si viene
        rut_path = ""
        file = request.files.get("rut_doc")
        if file and file.filename:
            fname = secure_filename(file.filename)
            ext = os.path.splitext(fname)[1].lower()
            if ext in ALLOWED_DOC_EXTS:
                # nombre único
                unique = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
                file.save(save_path)
                # almacenar como ruta relativa a static
                rut_path = f"uploads/{unique}"
            else:
                flash(
                    t("Formato de archivo no permitido.", "File type not allowed.", "檔案格式不允許"),
                    "error"
                )
                return redirect(url_for("register"))

        USERS[email] = {
            "nombre": nombre,
            "email": email,
            "password": password,
            "tipo": tipo,
            "rol": rol,
            "empresa": empresa,
            "descripcion": "",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": (email.split("@")[0]).lower(),
            "pais": pais or "CL",
            "direccion": direccion,
            "telefono": telefono,
            "rut_doc": rut_path,
            "items": []
        }

        flash(
            t("Registro exitoso. Ahora inicia sesión.",
              "Registration successful. Please log in.",
              "註冊成功，請登入"),
            "success"
        )
        return redirect(url_for("login"))

    # GET
    # rol sugerido según query ?tipo= (del selector), sólo para mostrar
    tipo_sel = (request.args.get("tipo") or "").lower().strip()
    rol_sugerido = None
    if tipo_sel == "compras":
        rol_sugerido = "Cliente Extranjero"
    elif tipo_sel == "servicios":
        rol_sugerido = "Servicios"
    elif tipo_sel == "compraventa":
        rol_sugerido = "Compraventa"
    elif tipo_sel == "mixto":
        rol_sugerido = "Mixto"

    return render_template(
        "register.html",
        roles=ROLES_DISPONIBLES,
        rol_sugerido=rol_sugerido,
        titulo=t("Registro de Usuario", "User Registration", "使用者註冊")
    )

# ---------------------------------------------------------
# Login
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        user = USERS.get(email)
        if user and user.get("password") == password:
            session["user"] = user
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"), "success")
            return redirect(url_for("dashboard_router"))
        else:
            flash(t("Credenciales incorrectas", "Incorrect credentials", "帳號或密碼錯誤"), "error")
            return redirect(url_for("login"))

    return render_template(
        "login.html",
        titulo=t("Iniciar sesión", "Login", "登入")
    )
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.7 extendida, sin recortes)
# ---------------------------------------------------------
# Parte 2: Dashboards por rol · Router unificado · Logout · Carrito inicial
# =========================================================

# ---------------------------------------------------------
# DASHBOARD ROUTER — Selección automática según tipo y rol
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard_router():
    """Redirige al dashboard correspondiente según rol o tipo."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión primero.",
                "You must log in first.",
                "您必須先登入"), "error")
        return redirect(url_for("login"))

    rol = (user.get("rol") or "").lower().strip()
    tipo = (user.get("tipo") or "").lower().strip()

    # Asignación prioritaria
    if rol in ["administrador", "admin"]:
        return redirect(url_for("dashboard_admin"))
    elif rol in ["compraventa", "productor", "packing", "frigorífico", "frigorifico", "exportador", "mixto"]:
        return redirect(url_for("dashboard_compra"))
    elif rol in ["servicios", "transporte extraportuario", "agencia de aduana", "servicio extraportuario"]:
        return redirect(url_for("dashboard_servicio"))
    elif rol in ["cliente extranjero", "extranjero"]:
        return redirect(url_for("dashboard_extranjero"))
    elif tipo == "servicio":
        return redirect(url_for("dashboard_servicio"))
    elif tipo == "extranjero":
        return redirect(url_for("dashboard_extranjero"))
    elif tipo == "mixto":
        return redirect(url_for("dashboard_compra"))
    else:
        flash(t("Rol no reconocido o sin panel asignado.",
                "Unrecognized role or no assigned dashboard.",
                "無法識別角色或未分配儀表板"), "warning")
        return redirect(url_for("home"))

# ---------------------------------------------------------
# DASHBOARD: COMPRAVENTA
# ---------------------------------------------------------
@app.route("/dashboard_compra")
def dashboard_compra():
    """Panel para productores, packing, frigoríficos y exportadores."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "dashboard_compra.html",
        user=user,
        titulo=t("Panel de Compraventa",
                 "Trade Dashboard",
                 "貿易儀表板")
    )

# ---------------------------------------------------------
# DASHBOARD: SERVICIOS
# ---------------------------------------------------------
@app.route("/dashboard_servicio")
def dashboard_servicio():
    """Panel para empresas de servicios."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "dashboard_servicio.html",
        user=user,
        titulo=t("Panel de Servicios",
                 "Services Dashboard",
                 "服務儀表板")
    )

# ---------------------------------------------------------
# DASHBOARD: CLIENTE EXTRANJERO
# ---------------------------------------------------------
@app.route("/dashboard_extranjero")
def dashboard_extranjero():
    """Panel de clientes extranjeros."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "dashboard_extranjero.html",
        user=user,
        titulo=t("Panel Cliente Extranjero",
                 "Foreign Client Dashboard",
                 "外國客戶儀表板")
    )

# ---------------------------------------------------------
# DASHBOARD: ADMINISTRADOR
# ---------------------------------------------------------
@app.route("/dashboard_admin")
def dashboard_admin():
    """Panel general de administración."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "dashboard_admin.html",
        user=user,
        titulo=t("Panel Administrador",
                 "Admin Dashboard",
                 "管理員儀表板")
    )

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    """Cierra sesión y redirige al inicio."""
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente.",
            "Session closed successfully.",
            "已成功登出"), "success")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# CARRITO INICIAL (versión básica)
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    """Muestra el carrito actual del usuario (estructura inicial)."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver tu carrito.",
                "You must log in to view your cart.",
                "您必須登入以查看購物車"), "error")
        return redirect(url_for("login"))

    carrito_items = user.get("carrito", [])
    return render_template(
        "carrito.html",
        user=user,
        cart=carrito_items,
        titulo=t("Carrito", "Cart", "購物車")
    )
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.7 extendida, sin recortes)
# ---------------------------------------------------------
# Parte 3: Publicaciones · Permisos/Visibilidad · Ocultar/Restaurar
#          Carrito extendido (agregar/eliminar/vaciar, direct-username)
#          Alias /dashboard_ext · Defaults de contexto seguros
# =========================================================

from uuid import uuid4

# ---------------------------------------------------------
# Defaults de contexto para evitar errores en templates
# (si algún render no pasa publicaciones/propias, aquí van vacías)
# ---------------------------------------------------------
@app.context_processor
def _inject_safe_defaults():
    return dict(publicaciones=[], propias=[], filtro="oferta")

# ---------------------------------------------------------
# Normalización & saneo de usuarios ficticios (campos que
# esperan los templates: username, pais, direccion, telefono, items)
# ---------------------------------------------------------
def _ensure_user_fields():
    for email, u in USERS.items():
        u.setdefault("username", (email.split("@")[0]).lower())
        u.setdefault("pais", "CL")
        u.setdefault("direccion", "")
        u.setdefault("telefono", "")
        u.setdefault("items", [])
        u.setdefault("descripcion", u.get("descripcion", ""))

_ensure_user_fields()

# ---------------------------------------------------------
# Alias solicitado por templates: /dashboard_ext
# (se usa para “volver al panel” en varias vistas)
# ---------------------------------------------------------
@app.route("/dashboard_ext")
def dashboard_ext():
    # Si el usuario está logueado y es extranjero, lo llevamos ahí;
    # si no, usamos el router general.
    user = session.get("user")
    if user and (user.get("rol", "").lower().strip() in ["cliente extranjero", "extranjero"]):
        return redirect(url_for("dashboard_extranjero"))
    return redirect(url_for("dashboard_router"))

# ---------------------------------------------------------
# Matrices de permisos
# ---------------------------------------------------------
TRADE_CAN_SELL_TO = {
    "productor": {"packing", "frigorifico", "exportador"},
    "packing": {"frigorifico", "exportador"},
    "frigorifico": {"packing", "exportador"},
    "exportador": {"cliente_extranjero", "exportador"},
}

TRADE_SELLERS_FOR_BUYER = {
    "productor": set(),
    "packing": {"productor", "frigorifico"},
    "frigorifico": {"productor", "packing"},
    "exportador": {"productor", "packing", "frigorifico", "exportador"},
    "cliente_extranjero": {"exportador"},
}

SERVICE_CAN_SELL_TO = {
    "transporte_extraportuario": {"productor", "packing", "frigorifico", "exportador"},
    "servicio_extraportuario": {"exportador"},
    "agencia_aduana": {"exportador"},
    "packing": {"exportador", "frigorifico", "productor"},
    "frigorifico": {"exportador", "packing", "productor"},
}

FAMILY_COMPRAVENTA = {"productor", "packing", "frigorifico", "exportador"}
FAMILY_SERVICIO = {
    "transporte_extraportuario", "servicio_extraportuario", "agencia_aduana", "packing", "frigorifico"
}
FAMILY_CLIENTE = {"cliente_extranjero"}

OCULTOS = {}           # { email: [pub_id, ...] }
HIDDEN_COMPANIES = {}  # { email_viewer: [username, ...] }

# ---------------------------------------------------------
# Helpers de permisos/visibilidad
# ---------------------------------------------------------
def _norm(rol: str) -> str:
    # normaliza acentos y minúsculas
    return (rol or "").replace("í", "i").replace("Í", "I").lower().strip()

def puede_publicar(rol: str, tipo_pub: str) -> bool:
    r = _norm(rol)
    tipo = (tipo_pub or "").lower().strip()
    if tipo in {"oferta", "demanda"}:
        return r in FAMILY_COMPRAVENTA
    if tipo == "servicio":
        return r in FAMILY_SERVICIO
    return False

def puede_ver_publicacion(rol_viewer: str, rol_pub: str, tipo_pub: str) -> bool:
    v = _norm(rol_viewer)
    p = _norm(rol_pub)
    tipo = (tipo_pub or "").lower().strip()

    # Clientes extranjeros: SOLO ofertas de exportador
    if v in FAMILY_CLIENTE:
        return (tipo == "oferta") and (p == "exportador")

    # Ofertas: ¿el publicador puede venderle al viewer?
    if tipo == "oferta":
        return v in TRADE_CAN_SELL_TO.get(p, set())

    # Demandas: ¿el viewer puede venderle al publicador?
    if tipo == "demanda":
        sellers = TRADE_SELLERS_FOR_BUYER.get(p, set())
        return v in sellers

    # Servicios: ¿el prestador le vende al viewer?
    if tipo == "servicio":
        return v in SERVICE_CAN_SELL_TO.get(p, set())

    return False

# ---------------------------------------------------------
# Utilidades de publicaciones
# ---------------------------------------------------------
def _pub_base(user, tipo_pub, producto, descripcion, precio, subtipo=""):
    return {
        "id": f"pub_{uuid4().hex[:8]}",
        "usuario": user["email"],
        "empresa": user["empresa"],
        "rol": _norm(user["rol"]),
        "tipo": (tipo_pub or "").lower().strip(),      # "oferta" | "demanda" | "servicio"
        "producto": producto,
        "precio": precio if precio else "Consultar",
        "descripcion": f"{subtipo.upper()} — {descripcion}" if subtipo else descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

def _visibles_para(user, filtro):
    ocultas_ids = set(OCULTOS.get(user["email"], []))
    visibles = []
    for p in PUBLICACIONES:
        try:
            if p.get("tipo") != filtro:
                continue
            if p.get("id") in ocultas_ids:
                continue
            if puede_ver_publicacion(user.get("rol", ""), p.get("rol", ""), p.get("tipo", "")):
                visibles.append(p)
        except Exception:
            # ignora publicaciones corruptas
            continue
    visibles.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return visibles

def _propias_de(user):
    propias = [p for p in PUBLICACIONES if p.get("usuario") == user["email"]]
    propias.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return propias

def _username_index():
    return {u.get("username"): u.get("email") for _, u in USERS.items()}

def _company_is_hidden_for(viewer_email, company_username):
    return company_username in set(HIDDEN_COMPANIES.get(viewer_email, []))

# ---------------------------------------------------------
# Publicar
# ---------------------------------------------------------
@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Crear una publicación (oferta, demanda o servicio)."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para publicar.", "You must log in to post.", "您必須登入以發布"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo_pub = (request.form.get("tipo_pub") or "").lower().strip()
        subtipo = (request.form.get("subtipo") or "").strip()
        producto = (request.form.get("producto") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        precio = (request.form.get("precio") or "").strip()

        if tipo_pub not in {"oferta", "demanda", "servicio"}:
            flash(t("Tipo de publicación inválido.", "Invalid post type.", "無效的發布類型"), "error")
            return redirect(url_for("publicar"))

        if not producto or not descripcion:
            flash(t("Completa todos los campos requeridos.", "Complete all required fields.", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        if not puede_publicar(user.get("rol", ""), tipo_pub):
            flash(t("No tienes permisos para este tipo de publicación.", "You are not allowed to post this type.", "無權限發布此類別"), "error")
            return redirect(url_for("dashboard_router"))

        nueva = _pub_base(user, tipo_pub, producto, descripcion, precio, subtipo)
        PUBLICACIONES.append(nueva)
        flash(t("Publicación creada correctamente.", "Post created successfully.", "發布成功"), "success")
        return redirect(url_for("dashboard_router"))

    return render_template(
        "publicar.html",
        user=user,
        titulo=t("Nueva Publicación", "New Post", "新增發布")
    )

# ---------------------------------------------------------
# Eliminar publicación (solo propias)
# ---------------------------------------------------------
@app.route("/publicacion/eliminar/<pub_id>", methods=["POST", "GET"])
def eliminar_publicacion(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    antes = len(PUBLICACIONES)
    PUBLICACIONES[:] = [p for p in PUBLICACIONES if not (p.get("id") == pub_id and p.get("usuario") == user["email"])]
    despues = len(PUBLICACIONES)

    if despues < antes:
        flash(t("Publicación eliminada.", "Post deleted.", "發布已刪除"), "success")
    else:
        flash(t("No encontrada o sin permiso.", "Not found or unauthorized.", "未找到或無權限"), "warning")
    return redirect(url_for("dashboard_router"))

# ---------------------------------------------------------
# Ocultar publicación o empresa (según id recibido)
# - Si coincide con una publicación: oculta esa pub.
# - Si no, se trata como username de empresa y la oculta en /clientes.
# ---------------------------------------------------------
@app.route("/ocultar/<pub_id>", methods=["POST", "GET"])
def ocultar_publicacion(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    # 1) ¿Es una publicación?
    if any(p.get("id") == pub_id for p in PUBLICACIONES):
        ocultas = OCULTOS.setdefault(user["email"], [])
        if pub_id not in ocultas:
            ocultas.append(pub_id)
            flash(t("Publicación ocultada.", "Item hidden.", "項目已隱藏"), "info")
        return redirect(request.referrer or url_for("dashboard_router"))

    # 2) ¿Es un username de empresa?
    uname = (pub_id or "").lower().strip()
    idx = _username_index()
    if uname in idx:
        hidden = HIDDEN_COMPANIES.setdefault(user["email"], [])
        if uname not in hidden:
            hidden.append(uname)
            flash(t("Empresa ocultada de la lista.", "Company hidden from list.", "公司已隱藏"), "info")
        return redirect(request.referrer or url_for("clientes"))

    # Fallback
    flash(t("No se encontró el recurso a ocultar.", "Item to hide not found.", "找不到要隱藏的項目"), "warning")
    return redirect(request.referrer or url_for("dashboard_router"))

# ---------------------------------------------------------
# Restablecer ocultos (publicaciones)
# ---------------------------------------------------------
@app.route("/restablecer_ocultos", methods=["POST", "GET"])
def restablecer_ocultos():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    OCULTOS[user["email"]] = []
    flash(t("Se restauraron las publicaciones ocultas.", "Hidden items restored.", "已恢復隱藏項目"), "success")
    return redirect(url_for("dashboard_router"))

# =========================================================
# Carrito extendido (NO redefinimos /carrito: ya existe en Parte 2)
# - Agregar por pub_id (desde dashboards)
# - Agregar directo desde detalle empresa: direct-<username>-<loop.index>
# - Eliminar por índice (POST)
# - Vaciar (POST)
# =========================================================

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    cart = user.setdefault("carrito", [])

    # 1) Buscar publicación normal
    pub = next((p for p in PUBLICACIONES if p.get("id") == pub_id), None)

    # 2) Soporte "direct-<username>-<index>" desde CLIENTE_DETALLE.HTML
    if not pub and pub_id.startswith("direct-"):
        try:
            _, uname, idx_str = pub_id.split("-", 2)
            email_map = _username_index()
            email = email_map.get(uname)
            if email and email in USERS:
                c = USERS[email]
                i = int(idx_str) - 1  # loop.index inicia en 1
                if 0 <= i < len(c.get("items", [])):
                    it = c["items"][i]
                    pub = {
                        "id": pub_id,
                        "usuario": email,
                        "empresa": c.get("empresa"),
                        "rol": _norm(c.get("rol", "")),
                        "tipo": "oferta",
                        "producto": it.get("nombre", "Item"),
                        "precio": it.get("precio", "Consultar"),
                        "descripcion": it.get("detalle", ""),
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
        except Exception:
            pub = None

    if not pub:
        flash(t("Publicación no encontrada.", "Item not found.", "找不到項目"), "error")
        return redirect(request.referrer or url_for("dashboard_router"))

    # Evitar duplicados por id
    if any(item.get("id") == pub.get("id") for item in cart):
        flash(t("El ítem ya está en el carrito.", "Item already in cart.", "項目已在購物車中"), "warning")
    else:
        cart.append(pub)
        session["user"] = user
        flash(t("Agregado al carrito.", "Added to cart.", "已加入購物車"), "success")

    return redirect(url_for("carrito"))

@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
def carrito_eliminar(index):
    """El template usa loop.index0 como índice (POST)."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    cart = user.setdefault("carrito", [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session["user"] = user
        flash(t("Ítem eliminado del carrito.", "Item removed from cart.", "已刪除項目"), "info")
    else:
        flash(t("Índice inválido.", "Invalid index.", "索引無效"), "warning")
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar", methods=["POST"])
def carrito_vaciar():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    user["carrito"] = []
    session["user"] = user
    flash(t("Carrito vaciado.", "Cart cleared.", "購物車已清空"), "success")
    return redirect(url_for("carrito"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.7 extendida, sin recortes)
# ---------------------------------------------------------
# Parte 4: Mensajería · Perfil · Clientes/Empresas (paginado)
#          Ayuda/Acerca · Status JSON
# =========================================================

from datetime import timedelta
from flask import abort

# ----------------------- MENSAJERÍA INTERNA ---------------------------
MENSAJES = []   # [{origen, destino, contenido, fecha}]
_COOLDOWN_DIAS = 3  # 1 mensaje por par (origen->destino) cada 3 días

def puede_enviar_mensaje(origen: str, destino: str) -> bool:
    now = datetime.now()
    historial = [m for m in MENSAJES if m.get("origen") == origen and m.get("destino") == destino]
    if not historial:
        return True
    try:
        ultima = historial[-1]["fecha"]
        if isinstance(ultima, str):
            ultima = datetime.strptime(ultima, "%Y-%m-%d %H:%M")
    except Exception:
        return True
    return (now - ultima) >= timedelta(days=_COOLDOWN_DIAS)

@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        destino = (request.form.get("destino") or "").strip().lower()
        contenido = (request.form.get("contenido") or "").strip()

        if not destino or not contenido:
            flash(t("Completa todos los campos.", "Please fill all fields.", "請填寫所有欄位"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe.", "Recipient not found.", "找不到收件人"), "error")
            return redirect(url_for("mensajes"))

        if not puede_enviar_mensaje(user["email"], destino):
            flash(
                t(
                    "Ya enviaste un mensaje a este usuario hace menos de 3 días.",
                    "You already sent this user a message less than 3 days ago.",
                    "距上次傳送未滿 3 天，暫不可再傳送"
                ),
                "warning"
            )
            return redirect(url_for("mensajes"))

        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        flash(t("Mensaje enviado.", "Message sent.", "訊息已發送"), "success")
        return redirect(url_for("mensajes"))

    # GET: bandeja
    recibidos = [m for m in MENSAJES if m.get("destino") == user["email"]]
    enviados = [m for m in MENSAJES if m.get("origen") == user["email"]]
    recibidos.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    enviados.sort(key=lambda x: x.get("fecha", ""), reverse=True)

    # Sugerir destinatarios (todos menos yo)
    posibles = [info for _, info in USERS.items() if info.get("email") != user["email"]]

    return render_template(
        "mensajes.html",
        user=user,
        recibidos=recibidos,
        enviados=enviados,
        posibles=posibles,
        titulo=t("Mensajería", "Messaging", "訊息系統"),
    )

# --------------------------- PERFIL DE USUARIO -------------------------
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.", "You must log in to view your profile.", "您必須登入以檢視個人資料"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        empresa    = (request.form.get("empresa") or "").strip()
        descripcion= (request.form.get("descripcion") or "").strip()
        telefono   = (request.form.get("telefono") or "").strip()
        direccion  = (request.form.get("direccion") or "").strip()

        if empresa:
            user["empresa"] = empresa
            USERS[user["email"]]["empresa"] = empresa
        if descripcion:
            user["descripcion"] = descripcion
            USERS[user["email"]]["descripcion"] = descripcion
        if telefono:
            user["telefono"] = telefono
            USERS[user["email"]]["telefono"] = telefono
        if direccion:
            user["direccion"] = direccion
            USERS[user["email"]]["direccion"] = direccion

        session["user"] = user
        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template(
        "perfil.html",
        user=user,
        titulo=t("Tu Perfil", "Your Profile", "個人資料")
    )

# --------------------------- CLIENTES / EMPRESAS -----------------------
@app.route("/clientes")
def clientes():
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver empresas.", "You must log in to view companies.", "您必須登入以查看公司"), "error")
        return redirect(url_for("login"))

    # Filtro del template: todos/oferta/demanda/servicio
    filtro_tipo = (request.args.get("filtro") or "todos").lower().strip()
    if filtro_tipo not in {"todos", "oferta", "demanda", "servicio"}:
        filtro_tipo = "todos"

    empresas = []
    for _, info in USERS.items():
        if info["email"] == user["email"]:
            continue  # no me muestro

        uname = info.get("username", "")
        if uname and _company_is_hidden_for(user["email"], uname):
            continue  # empresa oculta por el viewer

        # Ver si existe al menos una publicación visible desde mi rol
        tiene_visible = False
        items = []

        for p in PUBLICACIONES:
            if p.get("empresa") == info.get("empresa"):
                if filtro_tipo != "todos" and p.get("tipo") != filtro_tipo:
                    continue
                if puede_ver_publicacion(user.get("rol", ""), p.get("rol", ""), p.get("tipo", "")):
                    tiene_visible = True
                    items.append({
                        "nombre": p.get("producto"),
                        "detalle": p.get("descripcion", ""),
                        "precio": p.get("precio", "Consultar"),
                        "id": p.get("id")
                    })

        # Si no hay publicaciones pero es relevante por rol, mostrar en "todos"
        if filtro_tipo == "todos" and not tiene_visible:
            if puede_ver_publicacion(user.get("rol",""), info.get("rol",""), "servicio") \
               or puede_ver_publicacion(user.get("rol",""), info.get("rol",""), "oferta"):
                tiene_visible = True

        if tiene_visible:
            empresa_card = dict(info)
            empresa_card["items"] = items
            empresas.append(empresa_card)

    # Paginación: 10 por página
    page = int(request.args.get("page", 1))
    page_size = 10
    total = len(empresas)
    total_paginas = max((total + page_size - 1) // page_size, 1)
    page = max(1, min(page, total_paginas))
    start = (page - 1) * page_size
    end = start + page_size
    page_empresas = empresas[start:end]

    return render_template(
        "clientes.html",
        user=user,
        clientes=page_empresas,
        pagina=page,
        total_paginas=total_paginas,
        filtro_tipo=filtro_tipo,
        titulo=t("Empresas Registradas", "Registered Companies", "註冊公司")
    )

@app.route("/clientes/<username>")
def cliente_detalle(username):
    username = (username or "").lower().strip()
    idx = _username_index()
    email = idx.get(username)
    if not email or email not in USERS:
        abort(404)

    c = USERS[email]
    user = session.get("user")
    puede_mensaje = bool(user) and puede_enviar_mensaje(user["email"], c["email"])

    # Si no hay items precargados, intentar generarlos desde PUBLICACIONES
    if not c.get("items"):
        c["items"] = []
        for p in PUBLICACIONES:
            if p.get("empresa") == c.get("empresa"):
                c["items"].append({
                    "nombre": p.get("producto"),
                    "detalle": p.get("descripcion", ""),
                    "precio": p.get("precio", "Consultar"),
                    "id": p.get("id")
                })

    return render_template(
        "cliente_detalle.html",
        user=user,
        c=c,
        puede_mensaje=puede_mensaje,
        titulo=c.get("empresa", username)
    )

# ------------------------------ AYUDA / ACERCA -------------------------
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo=t("Centro de Ayuda", "Help Center", "幫助中心"))

@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping", "About Window Shopping", "關於 Window Shopping"))

# ------------------------------ STATUS JSON ----------------------------
@app.route("/status")
def status():
    estado = {
        "usuarios": len(USERS),
        "publicaciones": len(PUBLICACIONES),
        "mensajes": len(MENSAJES),
        "idioma": session.get("lang", "es"),
        "estado": "OK ✅",
        "hora_servidor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return jsonify(estado)

# ------------------------------ NOTA RUN -------------------------------
# Ejecutar localmente:
# if __name__ == "__main__":
#     print("🌐 Servidor Flask en http://127.0.0.1:5000")
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
