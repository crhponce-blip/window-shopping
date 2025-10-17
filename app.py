# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 corregida)
# Autor: Christopher Ponce & GPT-5
# ---------------------------------------------------------
# Parte 1: Configuración · Traducción · Usuarios ficticios (completos)
#           Helpers de saneo · Idioma · Home
# =========================================================

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# ---------------------------------------------------------
# 🔧 CONFIGURACIÓN INICIAL
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = "windowshopping_secret_key_v3_9"

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------
# 🧩 ESTRUCTURAS DE DATOS
# ---------------------------------------------------------
USERS = {}
PUBLICACIONES = []
MENSAJES = []
OCULTOS = {}
HIDDEN_COMPANIES = {}

# ---------------------------------------------------------
# 👥 USUARIOS FICTICIOS (completos, 2 por rol real)
# ---------------------------------------------------------
USERS = {
    # ===== ADMINISTRADOR =====
    "admin@ws.com": {
        "nombre": "Administrador General",
        "email": "admin@ws.com",
        "password": "admin",
        "tipo": "nacional",
        "rol": "Administrador",
        "empresa": "Window Shopping",
        "descripcion": "Administrador principal del sistema.",
        "fecha": "2025-10-10 09:00",
        "username": "admin",
        "pais": "CL",
        "direccion": "Santiago, RM",
        "telefono": "+56 2 1234 5678",
        "rut_doc": "",
        "items": []
    },
    "soporte@ws.com": {
        "nombre": "Soporte WS",
        "email": "soporte@ws.com",
        "password": "1234",
        "tipo": "nacional",
        "rol": "Administrador",
        "empresa": "WS Support Center",
        "descripcion": "Gestión de soporte técnico y cuentas.",
        "fecha": "2025-10-10 09:15",
        "username": "soporte",
        "pais": "CL",
        "direccion": "Providencia, Santiago",
        "telefono": "+56 9 4567 1111",
        "rut_doc": "",
        "items": []
    },

    # ===== PRODUCTORES =====
    "productor1@ws.com": {
        "nombre": "Pedro Campos",
        "email": "productor1@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Productor",
        "empresa": "Campos del Valle",
        "descripcion": "Productor de fruta fresca de exportación.",
        "fecha": "2025-10-12 10:00",
        "username": "productor1",
        "pais": "CL",
        "direccion": "Curicó, Maule",
        "telefono": "+56 9 7000 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Uva Red Globe", "detalle": "Granel para packing", "precio": "USD 1.10/kg"},
            {"nombre": "Durazno Diamante", "detalle": "Campo certificado GlobalGAP", "precio": "USD 0.90/kg"}
        ]
    },
    "productor2@ws.com": {
        "nombre": "Luis Morales",
        "email": "productor2@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Productor",
        "empresa": "Huertos del Sol",
        "descripcion": "Pequeño productor de cerezas premium.",
        "fecha": "2025-10-12 10:30",
        "username": "productor2",
        "pais": "CL",
        "direccion": "San Fernando, O’Higgins",
        "telefono": "+56 9 7333 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Cereza Lapins 9.5", "detalle": "Variedad exportable", "precio": "USD 6.00/kg"}
        ]
    },

    # ===== PACKING =====
    "packing1@ws.com": {
        "nombre": "María Campos",
        "email": "packing1@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Packing",
        "empresa": "Packing Andes SpA",
        "descripcion": "Procesamiento y embalaje para exportación.",
        "fecha": "2025-10-12 11:00",
        "username": "packing1",
        "pais": "CL",
        "direccion": "San Felipe, Valparaíso",
        "telefono": "+56 9 3456 7890",
        "rut_doc": "",
        "items": [
            {"nombre": "Embalaje flowpack", "detalle": "Automático con certificación BRC", "precio": "USD 0.08/un"},
            {"nombre": "Reembalaje urgente", "detalle": "Servicio en 6 horas", "precio": "USD 0.12/kg"}
        ]
    },
    "packing2@ws.com": {
        "nombre": "Felipe Rojas",
        "email": "packing2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Packing",
        "empresa": "AgroPacking Ltda.",
        "descripcion": "Packing mixto con servicios adicionales.",
        "fecha": "2025-10-12 11:15",
        "username": "packing2",
        "pais": "CL",
        "direccion": "Rancagua, O’Higgins",
        "telefono": "+56 9 4567 3344",
        "rut_doc": "",
        "items": [
            {"nombre": "Servicio de etiquetado", "detalle": "Etiquetas personalizadas exportación", "precio": "USD 0.03/un"}
        ]
    },

    # ===== FRIGORÍFICOS =====
    "frigorifico1@ws.com": {
        "nombre": "Carlos Frías",
        "email": "frigorifico1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Frigorífico",
        "empresa": "Frigorífico Polar Sur",
        "descripcion": "Almacenamiento y logística en cadena de frío.",
        "fecha": "2025-10-12 12:00",
        "username": "frigorifico1",
        "pais": "CL",
        "direccion": "Talca, Maule",
        "telefono": "+56 9 4567 8901",
        "rut_doc": "",
        "items": [
            {"nombre": "Túnel de frío", "detalle": "Descenso rápido de temperatura", "precio": "USD 0.06/kg"},
            {"nombre": "Monitoreo IoT", "detalle": "Control remoto de T°", "precio": "USD 25/lote"}
        ]
    },
    "frigorifico2@ws.com": {
        "nombre": "Andrea Vega",
        "email": "frigorifico2@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Frigorífico",
        "empresa": "ColdTrade SpA",
        "descripcion": "Opera como frigorífico mixto con venta de fruta y servicios.",
        "fecha": "2025-10-12 12:30",
        "username": "frigorifico2",
        "pais": "CL",
        "direccion": "Los Andes, Valparaíso",
        "telefono": "+56 9 6789 4455",
        "rut_doc": "",
        "items": [
            {"nombre": "Fruta refrigerada premium", "detalle": "Uva y arándano a exportadores", "precio": "USD 3.20/kg"},
            {"nombre": "Servicio cámara fría", "detalle": "Rango -1°C a 5°C", "precio": "USD 0.15/kg/día"}
        ]
    },

    # ===== EXPORTADORES =====
    "exportador1@ws.com": {
        "nombre": "Sofía Export",
        "email": "exportador1@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Exportador",
        "empresa": "Exportadora Los Andes",
        "descripcion": "Exportadora de cerezas y uvas de mesa.",
        "fecha": "2025-10-13 08:00",
        "username": "exportador1",
        "pais": "CL",
        "direccion": "Curicó, Maule",
        "telefono": "+56 9 7123 4567",
        "rut_doc": "",
        "items": [
            {"nombre": "Cereza Lapins 9.5", "detalle": "Embalaje clamshell", "precio": "USD 6.20/kg"},
            {"nombre": "Arándano Duke", "detalle": "Export pack 12x125g", "precio": "USD 5.10/kg"}
        ]
    },
    "exportador2@ws.com": {
        "nombre": "Juan Torres",
        "email": "exportador2@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Exportador",
        "empresa": "ChileFruits Export",
        "descripcion": "Exporta fruta chilena a Asia y Europa.",
        "fecha": "2025-10-13 08:15",
        "username": "exportador2",
        "pais": "CL",
        "direccion": "Quillota, Valparaíso",
        "telefono": "+56 9 7333 5566",
        "rut_doc": "",
        "items": [
            {"nombre": "Uva Thompson", "detalle": "Calibre grande premium", "precio": "USD 4.10/kg"}
        ]
    },
}
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 corregida)
# ---------------------------------------------------------
# Parte 2: Traducción · Helpers · Idioma · Home · Registro/Login
# =========================================================

# ---------------------------------------------------------
# 🌍 FUNCIONES DE TRADUCCIÓN MULTI-IDIOMA
# ---------------------------------------------------------
LANGS = ["es", "en", "zh"]

TRANSLATIONS = {
    "Bienvenido a Window Shopping": {
        "en": "Welcome to Window Shopping",
        "zh": "欢迎来到 Window Shopping"
    },
    "Conectamos productores chilenos con compradores internacionales": {
        "en": "We connect Chilean producers with international buyers",
        "zh": "我们连接智利生产商与国际买家"
    },
    "Comienza ahora": {"en": "Start now", "zh": "立即开始"},
    "Explora empresas y servicios": {"en": "Explore companies and services", "zh": "探索公司和服务"},
    "Iniciar sesión": {"en": "Login", "zh": "登录"},
    "Contraseña": {"en": "Password", "zh": "密码"},
    "Correo electrónico": {"en": "Email", "zh": "电子邮件"},
    "Registrar": {"en": "Register", "zh": "注册"},
    "Registrarse": {"en": "Sign up", "zh": "注册"},
    "Perfil": {"en": "Profile", "zh": "用户资料"},
    "Salir": {"en": "Logout", "zh": "退出"},
    "Empresas": {"en": "Companies", "zh": "企业"},
    "Carrito": {"en": "Cart", "zh": "购物车"},
    "Inicio": {"en": "Home", "zh": "首页"},
    "Panel Admin": {"en": "Admin Panel", "zh": "管理员面板"},
    "Panel Cliente": {"en": "Client Panel", "zh": "客户面板"},
    "Panel Servicio": {"en": "Service Panel", "zh": "服务面板"},
    "Panel Compraventa": {"en": "Trade Panel", "zh": "交易面板"},
    "Panel Principal": {"en": "Main Panel", "zh": "主面板"},
    "Cerrar sesión": {"en": "Log out", "zh": "退出登录"},
    "Registro de Usuario": {"en": "User Registration", "zh": "用户注册"},
    "Empresa / Organización": {"en": "Company / Organization", "zh": "公司 / 组织"},
    "País (Código ISO)": {"en": "Country (ISO Code)", "zh": "国家代码 (ISO)"},
    "Dirección": {"en": "Address", "zh": "地址"},
    "Teléfono": {"en": "Phone", "zh": "电话"},
    "Rol": {"en": "Role", "zh": "角色"},
    "Versión 3.9 — Plataforma colaborativa de comercio internacional": {
        "en": "Version 3.9 — International trade collaborative platform",
        "zh": "版本 3.9 — 国际贸易协作平台"
    }
}

def t(text, en=None, zh=None):
    """Traducción automática según idioma activo en sesión"""
    lang = session.get("lang", "es")
    if lang == "es":
        return text
    if en or zh:  # Si vienen traducciones manuales
        if lang == "en" and en:
            return en
        if lang == "zh" and zh:
            return zh
    if text in TRANSLATIONS:
        return TRANSLATIONS[text].get(lang, text)
    return text

app.jinja_env.globals.update(t=t)

# ---------------------------------------------------------
# 🌐 CONTROL DE IDIOMA
# ---------------------------------------------------------
@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in LANGS:
        session["lang"] = lang
    else:
        session["lang"] = "es"
    return redirect(request.referrer or url_for("home"))

# ---------------------------------------------------------
# 🏠 PÁGINA PRINCIPAL (INDEX)
# ---------------------------------------------------------
@app.route("/")
def home():
    titulo = t("Bienvenido a Window Shopping")
    return render_template("index.html", titulo=titulo)

# ---------------------------------------------------------
# 🔐 LOGIN Y REGISTRO DE USUARIOS
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = USERS.get(email)

        if not user:
            flash(t("Usuario no encontrado", "User not found", "未找到用户"), "error")
        elif user["password"] != password:
            flash(t("Contraseña incorrecta", "Incorrect password", "密码错误"), "error")
        else:
            session["user"] = user
            flash(t("Inicio de sesión exitoso", "Login successful", "登录成功"), "success")
            return redirect(url_for("home"))
    return render_template("login.html", titulo=t("Iniciar sesión"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente", "Session closed", "已注销"), "success")
    return redirect(url_for("home"))

@app.route("/register_router")
def register_router():
    # Lógica: redirige según tipo de perfil seleccionado
    tipos = {
        "Compraventa": ["Productor", "Packing", "Frigorífico", "Exportador"],
        "Servicios": ["Transporte", "Packing", "Frigorífico", "Extraportuarios", "Agencia de Aduanas"],
        "Mixto": ["Packing", "Frigorífico"],
        "Extranjero": ["Cliente Extranjero"]
    }
    return render_template("register.html", titulo=t("Registro de Usuario"), tipos=tipos)

@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email").strip().lower()
    if email in USERS:
        flash(t("El usuario ya existe", "User already exists", "用户已存在"), "error")
        return redirect(url_for("register_router"))

    new_user = {
        "email": email,
        "password": request.form.get("password"),
        "empresa": request.form.get("empresa"),
        "rol": request.form.get("rol"),
        "pais": request.form.get("pais", "CL").upper(),
        "direccion": request.form.get("direccion", ""),
        "telefono": request.form.get("telefono", ""),
        "descripcion": f"Cuenta nueva creada el {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tipo": "extranjero" if "extranjero" in request.form.get("rol", "").lower() else "compraventa",
        "items": []
    }

    USERS[email] = new_user
    flash(t("Usuario registrado correctamente", "User registered successfully", "注册成功"), "success")
    return redirect(url_for("login"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 corregida)
# ---------------------------------------------------------
# Parte 3: Permisos, validaciones y helpers
# =========================================================

# ---------------------------------------------------------
# 🧩 MAPA DE PERMISOS SEGÚN PERFIL Y ROL
# ---------------------------------------------------------
PERMISOS = {
    "compraventa": {
        "Productor": {
            "puede_vender_a": ["Packing", "Frigorífico", "Exportador"],
            "puede_comprar_de": [],
            "puede_comprar_servicios": ["Transporte"]
        },
        "Packing": {
            "puede_vender_a": ["Frigorífico", "Exportador"],
            "puede_comprar_de": ["Productor", "Frigorífico"],
            "puede_comprar_servicios": ["Transporte", "Frigorífico"]
        },
        "Frigorífico": {
            "puede_vender_a": ["Packing", "Exportador"],
            "puede_comprar_de": ["Productor", "Packing"],
            "puede_comprar_servicios": ["Transporte", "Packing"]
        },
        "Exportador": {
            "puede_vender_a": ["Exportador", "Cliente Extranjero"],
            "puede_comprar_de": ["Productor", "Packing", "Frigorífico", "Exportador"],
            "puede_comprar_servicios": ["Transporte", "Agencia de Aduanas", "Extraportuarios", "Packing", "Frigorífico"]
        }
    },
    "servicios": {
        "Transporte": {
            "puede_vender_a": ["Productor", "Packing", "Frigorífico", "Exportador"],
            "puede_comprar_de": []
        },
        "Packing": {
            "puede_vender_a": ["Productor", "Frigorífico", "Exportador"],
            "puede_comprar_servicios": ["Transporte", "Frigorífico"]
        },
        "Frigorífico": {
            "puede_vender_a": ["Productor", "Packing", "Exportador"],
            "puede_comprar_servicios": ["Transporte", "Packing"]
        },
        "Extraportuarios": {
            "puede_vender_a": ["Exportador"]
        },
        "Agencia de Aduanas": {
            "puede_vender_a": ["Exportador"]
        }
    },
    "mixto": {
        "Packing": {
            "puede_vender_a": ["Frigorífico", "Exportador"],
            "puede_comprar_de": ["Productor", "Frigorífico"],
            "puede_vender_servicios_a": ["Productor", "Frigorífico", "Exportador"],
            "puede_comprar_servicios": ["Transporte", "Frigorífico"]
        },
        "Frigorífico": {
            "puede_vender_a": ["Packing", "Exportador"],
            "puede_comprar_de": ["Productor", "Packing"],
            "puede_vender_servicios_a": ["Productor", "Packing", "Exportador"],
            "puede_comprar_servicios": ["Transporte", "Packing"]
        }
    },
    "extranjero": {
        "Cliente Extranjero": {
            "puede_comprar_de": ["Exportador"],
            "puede_vender_a": []
        }
    }
}

# ---------------------------------------------------------
# ⚙️ HELPERS DE LÓGICA
# ---------------------------------------------------------
def get_user():
    """Devuelve el usuario logueado o None"""
    return session.get("user")

def puede_publicar(usuario):
    """Determina si el usuario puede publicar productos o servicios"""
    if not usuario:
        return False
    rol = usuario.get("rol", "")
    tipo = usuario.get("tipo", "")
    # Solo usuarios de compraventa o mixtos pueden publicar productos
    return tipo in ["compraventa", "mixto"] or rol in ["Exportador", "Productor"]

def puede_ver_publicacion(usuario, publicacion):
    """Valida si el usuario tiene permiso para ver una publicación según su tipo y rol"""
    if not usuario or not publicacion:
        return False

    tipo_usuario = usuario.get("tipo", "")
    rol_usuario = usuario.get("rol", "")
    rol_publicador = publicacion.get("rol", "")
    tipo_publicador = publicacion.get("tipo", "")

    permisos_tipo = PERMISOS.get(tipo_usuario, {}).get(rol_usuario, {})

    # Caso 1: comprador compraventa
    if "puede_comprar_de" in permisos_tipo:
        if rol_publicador in permisos_tipo["puede_comprar_de"]:
            return True

    # Caso 2: comprador de servicios
    if "puede_comprar_servicios" in permisos_tipo:
        if rol_publicador in permisos_tipo["puede_comprar_servicios"]:
            return True

    # Caso 3: compradores extranjeros
    if tipo_usuario == "extranjero":
        return rol_publicador in ["Exportador"]

    # Caso 4: visibilidad general (admins)
    if rol_usuario == "Administrador":
        return True

    return False

def puede_mostrar_dashboard(usuario):
    """Determina qué dashboard debe mostrarse según el tipo y rol"""
    if not usuario:
        return "home"

    rol = usuario.get("rol", "")
    tipo = usuario.get("tipo", "")

    if rol.lower() == "administrador":
        return "dashboard_admin"
    elif tipo == "extranjero":
        return "dashboard_ext"
    elif tipo == "servicios":
        return "dashboard_servicio"
    elif tipo == "compraventa":
        return "dashboard_compra"
    elif tipo == "mixto":
        return "dashboard_mixto"
    else:
        return "dashboard"

# ---------------------------------------------------------
# 🔄 MIDDLEWARE PARA VERIFICAR SESIÓN
# ---------------------------------------------------------
@app.before_request
def check_session_integrity():
    """Verifica que el usuario en sesión siga siendo válido"""
    user = session.get("user")
    if user:
        email = user.get("email")
        if email not in USERS:
            session.pop("user", None)
            flash(t("Sesión expirada, por favor vuelva a iniciar sesión",
                    "Session expired, please log in again", "会话已过期，请重新登录"), "error")
            return redirect(url_for("login"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 corregida)
# ---------------------------------------------------------
# Parte 4: Dashboards · Publicaciones · Carrito · Clientes
# =========================================================

from uuid import uuid4

# ---------------------------------------------------------
# 🧭 DASHBOARD ROUTER
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard_router():
    user = get_user()
    if not user:
        flash(t("Debes iniciar sesión primero",
                "You must log in first", "您必須先登入"), "error")
        return redirect(url_for("login"))

    destino = puede_mostrar_dashboard(user)
    if destino == "dashboard_admin":
        return redirect(url_for("dashboard_admin"))
    elif destino == "dashboard_servicio":
        return redirect(url_for("dashboard_servicio"))
    elif destino == "dashboard_compra":
        return redirect(url_for("dashboard_compra"))
    elif destino == "dashboard_mixto":
        return redirect(url_for("dashboard_mixto"))
    elif destino == "dashboard_ext":
        return redirect(url_for("dashboard_extranjero"))
    return redirect(url_for("home"))

# ---------------------------------------------------------
# 📊 DASHBOARDS POR PERFIL
# ---------------------------------------------------------
@app.route("/dashboard_admin")
def dashboard_admin():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_admin.html", user=user, titulo=t("Panel Administrador"))

@app.route("/dashboard_compra")
def dashboard_compra():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_compra.html", user=user, titulo=t("Panel de Compraventa"))

@app.route("/dashboard_servicio")
def dashboard_servicio():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_servicio.html", user=user, titulo=t("Panel de Servicios"))

@app.route("/dashboard_mixto")
def dashboard_mixto():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_mixto.html", user=user, titulo=t("Panel Mixto"))

@app.route("/dashboard_extranjero")
def dashboard_extranjero():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_extranjero.html", user=user, titulo=t("Panel Cliente Extranjero"))

# ---------------------------------------------------------
# 📰 PUBLICACIONES (crear / listar / eliminar)
# ---------------------------------------------------------
PUBLICACIONES = []

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo_pub = request.form.get("tipo_pub", "").lower()
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip()

        if not producto or not descripcion:
            flash(t("Completa todos los campos requeridos",
                    "Complete all required fields", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        if not puede_publicar(user):
            flash(t("No tienes permiso para publicar",
                    "You are not allowed to post", "無權限發布"), "error")
            return redirect(url_for("dashboard_router"))

        nueva = {
            "id": f"pub_{uuid4().hex[:8]}",
            "usuario": user["email"],
            "empresa": user["empresa"],
            "rol": user["rol"],
            "tipo": tipo_pub,
            "producto": producto,
            "descripcion": descripcion,
            "precio": precio or "Consultar",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        PUBLICACIONES.append(nueva)
        flash(t("Publicación creada correctamente",
                "Post created successfully", "發布成功"), "success")
        return redirect(url_for("dashboard_router"))

    return render_template("publicar.html", user=user, titulo=t("Nueva Publicación"))

@app.route("/publicacion/eliminar/<pub_id>")
def eliminar_publicacion(pub_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    antes = len(PUBLICACIONES)
    PUBLICACIONES[:] = [p for p in PUBLICACIONES if not (p["id"] == pub_id and p["usuario"] == user["email"])]
    if len(PUBLICACIONES) < antes:
        flash(t("Publicación eliminada", "Post deleted", "發布已刪除"), "success")
    else:
        flash(t("No encontrada o sin permiso", "Not found or unauthorized", "未找到或無權限"), "warning")
    return redirect(url_for("dashboard_router"))

# ---------------------------------------------------------
# 🛒 CARRITO DE COMPRAS
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    carrito = user.setdefault("carrito", [])
    return render_template("carrito.html", user=user, cart=carrito, titulo=t("Carrito"))

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(url_for("dashboard_router"))

    carrito = user.setdefault("carrito", [])
    if any(item["id"] == pub_id for item in carrito):
        flash(t("El ítem ya está en el carrito", "Item already in cart", "項目已在購物車中"), "warning")
    else:
        carrito.append(pub)
        flash(t("Agregado al carrito", "Added to cart", "已加入購物車"), "success")
    session["user"] = user
    return redirect(url_for("carrito"))

@app.route("/carrito/eliminar/<int:index>", methods=["POST"])
def carrito_eliminar(index):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    carrito = user.setdefault("carrito", [])
    if 0 <= index < len(carrito):
        carrito.pop(index)
        flash(t("Ítem eliminado", "Item removed", "已刪除項目"), "info")
    else:
        flash(t("Índice inválido", "Invalid index", "索引無效"), "warning")
    session["user"] = user
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar", methods=["POST"])
def carrito_vaciar():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    user["carrito"] = []
    session["user"] = user
    flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"), "success")
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# 🧾 CLIENTES / EMPRESAS
# ---------------------------------------------------------
@app.route("/clientes")
def clientes():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    visibles = []
    for _, info in USERS.items():
        if info["email"] == user["email"]:
            continue
        if puede_ver_publicacion(user, {"rol": info["rol"], "tipo": "oferta"}):
            visibles.append(info)

    return render_template("clientes.html",
                           user=user,
                           clientes=visibles,
                           titulo=t("Empresas Registradas"))

@app.route("/clientes/<username>")
def cliente_detalle(username):
    username = (username or "").lower().strip()
    email_map = {u["username"]: e for e, u in USERS.items()}
    email = email_map.get(username)
    if not email or email not in USERS:
        abort(404)

    c = USERS[email]
    user = get_user()
    return render_template("cliente_detalle.html",
                           user=user,
                           c=c,
                           titulo=c.get("empresa", username))

# ---------------------------------------------------------
# ⚙️ STATUS JSON
# ---------------------------------------------------------
@app.route("/status")
def status():
    estado = {
        "usuarios": len(USERS),
        "publicaciones": len(PUBLICACIONES),
        "idioma": session.get("lang", "es"),
        "hora_servidor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": "OK ✅"
    }
    return jsonify(estado)

# ---------------------------------------------------------
# 🏁 EJECUCIÓN LOCAL
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🌐 Servidor Flask en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
