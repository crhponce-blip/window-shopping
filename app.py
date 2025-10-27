# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 FINAL)
# Autor: Christopher Ponce & GPT-5
# ---------------------------------------------------------
# Parte 1 · Configuración · Traducción · Usuarios · Home · Perfil
# =========================================================

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from datetime import datetime
import os
from uuid import uuid4
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
HIDDEN_COMPANIES = {}

# ---------------------------------------------------------
# 🌍 TRADUCCIÓN / i18n
# ---------------------------------------------------------
LANGS = ["es", "en", "zh"]
TRANSLATIONS = {
    "Bienvenido a Window Shopping": {"en": "Welcome to Window Shopping", "zh": "欢迎来到 Window Shopping"},
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
    "Empresas": {"en": "Companies", "zh": "企业"},
    "Carrito": {"en": "Cart", "zh": "购物车"},
    "Inicio": {"en": "Home", "zh": "首页"},
    "Panel Admin": {"en": "Admin Panel", "zh": "管理员面板"},
    "Panel Cliente": {"en": "Client Panel", "zh": "客户面板"},
    "Panel Servicio": {"en": "Service Panel", "zh": "服务面板"},
    "Panel Compraventa": {"en": "Trade Panel", "zh": "交易面板"},
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
    },
}

def t(text, en=None, zh=None):
    """Traducción automática según idioma activo."""
    lang = session.get("lang", "es")
    if lang == "es":
        return text
    if en or zh:
        if lang == "en" and en:
            return en
        if lang == "zh" and zh:
            return zh
    if text in TRANSLATIONS:
        return TRANSLATIONS[text].get(lang, text)
    return text

# Permitir que todos los textos se traduzcan dentro de plantillas
app.jinja_env.globals.update(t=t)
app.jinja_env.filters['t'] = t

# ---------------------------------------------------------
# 🌐 CONTROL DE IDIOMA
# ---------------------------------------------------------
@app.route("/set_lang/<lang>")
def set_lang(lang):
    session["lang"] = lang if lang in LANGS else "es"
    return redirect(request.referrer or url_for("home"))

# 👥 USUARIOS FICTICIOS — alineados a TIPOS_ROLES y PERMISOS
USERS = {
    # ======================================================
    # 🔹 ADMINISTRACIÓN (pueden crear usuarios)
    # ======================================================
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
        "nombre": "Centro de Soporte WS",
        "email": "soporte@ws.com",
        "password": "1234",
        "tipo": "nacional",
        "rol": "Administrador",
        "empresa": "WS Support Center",
        "descripcion": "Gestión de soporte técnico y validaciones de usuario.",
        "fecha": "2025-10-10 09:15",
        "username": "soporte",
        "pais": "CL",
        "direccion": "Providencia, Santiago",
        "telefono": "+56 9 4567 1111",
        "rut_doc": "",
        "items": []
    },

    # ======================================================
    # 🟢 COMPRAVENTA
    # ======================================================
    "productor@ws.com": {
        "nombre": "Campo Verde",
        "email": "productor@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Productor",
        "empresa": "Campo Verde Ltda.",
        "descripcion": "Producción de fruta de exportación.",
        "fecha": "2025-10-12 08:00",
        "username": "productor",
        "pais": "CL",
        "direccion": "Curicó, Maule",
        "telefono": "+56 9 7000 1111",
        "items": [
            {"nombre": "Cereza Lapins 9.5", "detalle": "Caja 5kg, calibre 28-30", "precio": "USD 8.20/kg"}
        ]
    },
    "packingcv@ws.com": {
        "nombre": "Packing del Sur",
        "email": "packingcv@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Packing",
        "empresa": "Packing del Sur SpA",
        "descripcion": "Empaque y calibrado de fruta exportable.",
        "fecha": "2025-10-12 09:00",
        "username": "packingcv",
        "pais": "CL",
        "direccion": "Rancagua, O'Higgins",
        "telefono": "+56 9 7100 1111",
        "items": [
            {"nombre": "Servicio de embalaje", "detalle": "Por kg procesado", "precio": "USD 0.35/kg"}
        ]
    },
    "frigorificocv@ws.com": {
        "nombre": "FríoAndes",
        "email": "frigorificocv@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Frigorífico",
        "empresa": "FríoAndes SpA",
        "descripcion": "Cámaras de frío y prefrío para fruta.",
        "fecha": "2025-10-12 10:00",
        "username": "frioandes",
        "pais": "CL",
        "direccion": "Talca, Maule",
        "telefono": "+56 9 7200 1111",
        "items": [
            {"nombre": "Almacenaje 7 días", "detalle": "Por pallet estándar", "precio": "USD 14.00"}
        ]
    },
    "exportador@ws.com": {
        "nombre": "Exportadora Andina",
        "email": "exportador@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Exportador",
        "empresa": "Exportadora Andina Ltda.",
        "descripcion": "Exportación de fruta fresca a Asia y EE.UU.",
        "fecha": "2025-10-12 11:00",
        "username": "exportadora",
        "pais": "CL",
        "direccion": "Valparaíso",
        "telefono": "+56 9 7300 1111",
        "items": [
            {"nombre": "Cerezas Premium", "detalle": "Caja 5kg", "precio": "USD 85.00/caja"}
        ]
    },

    # ======================================================
    # 🟣 SERVICIOS
    # ======================================================
    "transporte@ws.com": {
        "nombre": "RutaExpress",
        "email": "transporte@ws.com",
        "password": "1234",
        "tipo": "servicio",
        "rol": "Transporte",
        "empresa": "RutaExpress Ltda.",
        "descripcion": "Camiones refrigerados a nivel nacional.",
        "fecha": "2025-10-13 08:00",
        "username": "transporte",
        "pais": "CL",
        "direccion": "Talagante, RM",
        "telefono": "+56 9 7400 1111",
        "items": [
            {"nombre": "Flete RM–Valpo", "detalle": "Camión 28 pallets", "precio": "USD 420"}
        ]
    },
    "aduana@ws.com": {
        "nombre": "Agencia Portuaria Chile",
        "email": "aduana@ws.com",
        "password": "1234",
        "tipo": "servicio",
        "rol": "Agencia de Aduanas",
        "empresa": "Agencia Portuaria Chile Ltda.",
        "descripcion": "Gestión documental y despacho aduanero.",
        "fecha": "2025-10-13 09:30",
        "username": "aduana",
        "pais": "CL",
        "direccion": "San Antonio",
        "telefono": "+56 9 4444 4444",
        "items": [
            {"nombre": "Certificado de origen", "detalle": "Servicio por documento", "precio": "USD 8.00"}
        ]
    },
    "extraportuarios@ws.com": {
        "nombre": "Servicios Extraportuarios Chile",
        "email": "extraportuarios@ws.com",
        "password": "1234",
        "tipo": "servicio",
        "rol": "Extraportuarios",
        "empresa": "Servicios Extraportuarios SpA",
        "descripcion": "Custodia y consolidación post puerto.",
        "fecha": "2025-10-13 10:00",
        "username": "extraportuarios",
        "pais": "CL",
        "direccion": "Valparaíso",
        "telefono": "+56 9 8888 3333",
        "items": [
            {"nombre": "Consolidación pallet", "detalle": "Por unidad", "precio": "USD 25"}
        ]
    },

    # ======================================================
    # 🟠 MIXTO
    # ======================================================
    "mixtopacking@ws.com": {
        "nombre": "PackFrío",
        "email": "mixtopacking@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Packing",
        "empresa": "PackFrío Ltda.",
        "descripcion": "Packing con servicios logísticos integrados.",
        "fecha": "2025-10-14 08:00",
        "username": "mixtopacking",
        "pais": "CL",
        "direccion": "Requinoa, O'Higgins",
        "telefono": "+56 9 7777 1111",
        "items": [
            {"nombre": "Servicio integral packing", "detalle": "Embalaje + Frío + Paletizado", "precio": "USD 0.80/kg"}
        ]
    },
    "mixtofrigo@ws.com": {
        "nombre": "FrigoMix",
        "email": "mixtofrigo@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Frigorífico",
        "empresa": "FrigoMix SpA",
        "descripcion": "Frigorífico con operaciones de packing mixto.",
        "fecha": "2025-10-14 08:15",
        "username": "mixtofrigo",
        "pais": "CL",
        "direccion": "San Fernando, O'Higgins",
        "telefono": "+56 9 7777 2222",
        "items": [
            {"nombre": "Frío + selección", "detalle": "Servicio mixto integral", "precio": "USD 18/pallet"}
        ]
    },

    # ======================================================
    # 🌍 EXTRANJERO
    # ======================================================
    "cliente@ws.com": {
        "nombre": "Fruit Global HK",
        "email": "cliente@ws.com",
        "password": "1234",
        "tipo": "extranjero",
        "rol": "Cliente Extranjero",
        "empresa": "Fruit Global Hong Kong",
        "descripcion": "Importadora de frutas latinoamericanas.",
        "fecha": "2025-10-14 11:00",
        "username": "cliente",
        "pais": "HK",
        "direccion": "Hong Kong Central",
        "telefono": "+852 555 888 777",
        "items": []
    }
}

# ---------------------------------------------------------
# 🏠 PÁGINA PRINCIPAL (INDEX)
# ---------------------------------------------------------
@app.route("/")
def home():
    titulo = t("Bienvenido a Window Shopping")
    return render_template("index.html", titulo=titulo)

# ---------------------------------------------------------
# 🧷 PERFIL (stub editable)
# ---------------------------------------------------------
def get_user():
    return session.get("user")

@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    user = get_user()
    if not user:
        flash(t("Debes iniciar sesión primero",
                "You must log in first", "您必須先登入"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        for campo in ["empresa", "pais", "direccion", "telefono", "descripcion"]:
            if campo in request.form:
                user[campo] = request.form.get(campo).strip()
        session["user"] = user
        flash(t("Perfil actualizado correctamente",
                "Profile updated successfully", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Perfil de Usuario"))
# =========================================================
# 🌐 Parte 2 · Login · Logout · Registro con filtros por tipo/rol
# =========================================================

# ---------- Catálogo de tipos -> roles permitidos ----------
TIPOS_ROLES = {
    "compraventa": ["Productor", "Packing", "Frigorífico", "Exportador"],
    "servicio": ["Transporte", "Packing", "Frigorífico", "Extraportuarios", "Agencia de Aduanas"],
    "mixto": ["Packing", "Frigorífico"],
    "extranjero": ["Cliente Extranjero"],
}

# Para mostrar títulos bonitos en UI
TIPO_TITULO = {
    "compraventa": "Compraventa",
    "servicio": "Servicios",
    "mixto": "Mixto",
    "extranjero": "Extranjero",
}

# ---------------------------------------------------------
# 🔄 FUNCIONES AUXILIARES DE REGISTRO
# ---------------------------------------------------------
def normaliza_tipo(t):
    """Normaliza alias desde URL o UI a nuestras claves de TIPOS_ROLES."""
    if not t:
        return None
    t = t.strip().lower()
    if t in ["servicios", "servicio"]:
        return "servicio"
    if t in ["compraventa", "compra-venta", "compra_venta"]:
        return "compraventa"
    if t in ["mixto"]:
        return "mixto"
    if t in ["extranjero", "cliente", "cliente_extranjero"]:
        return "extranjero"
    return None

def rol_valido_para_tipo(rol, tipo_norm):
    """True si el rol pertenece al tipo elegido."""
    if not rol or not tipo_norm:
        return False
    roles = TIPOS_ROLES.get(tipo_norm, [])
    return any(rol.strip().lower() == r.lower() for r in roles)

def titulo_tipo(tipo_norm):
    """Obtiene nombre legible para mostrar en templates."""
    return TIPO_TITULO.get(tipo_norm, tipo_norm.capitalize() if tipo_norm else "")

# ---------------------------------------------------------
# 🔐 LOGIN
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        user = USERS.get(email)

        if not user:
            flash(t("Usuario no encontrado", "User not found", "未找到用户"), "error")
        elif user.get("password") != password:
            flash(t("Contraseña incorrecta", "Incorrect password", "密码错误"), "error")
        else:
            session["user"] = user
            flash(t("Inicio de sesión exitoso", "Login successful", "登录成功"), "success")
            return redirect(url_for("dashboard_router"))
    return render_template("login.html", titulo=t("Iniciar sesión"))

# ---------------------------------------------------------
# 🚪 LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente", "Session closed", "已注销"), "success")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# 🧭 REGISTRO: Router de selección de tipo
# ---------------------------------------------------------
@app.route("/register_router")
def register_router():
    """Pantalla de selección de tipo de cuenta."""
    return render_template("register_router.html", titulo=t("Selecciona el tipo de cuenta"))

# ---------------------------------------------------------
# 📝 REGISTRO: Formulario según tipo seleccionado (GET)
# ---------------------------------------------------------
@app.route("/register/<tipo>", methods=["GET"])
def register_form(tipo):
    tipo_norm = normaliza_tipo(tipo)
    if not tipo_norm:
        flash(t("Tipo de cuenta inválido", "Invalid account type", "无效的帐户类型"), "error")
        return redirect(url_for("register_router"))

    # 🔧 Solución: fijar tipo de cuenta en sesión de forma persistente
    session["register_tipo"] = tipo_norm
    session.modified = True  # obliga a guardar en cookie
    
    tipos_ctx = {titulo_tipo(tipo_norm): TIPOS_ROLES[tipo_norm]}
    return render_template(
        "register.html",
        titulo=t("Registro de Usuario"),
        tipos=tipos_ctx,
        tipo_actual=tipo_norm
    )

# ---------------------------------------------------------
# ✅ REGISTRO FINAL: POST con validaciones estrictas
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    empresa = (request.form.get("empresa") or "").strip()
    rol = (request.form.get("rol") or "").strip()
    pais = (request.form.get("pais") or "CL").strip().upper()
    direccion = (request.form.get("direccion") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()

    # 📎 Nuevo: archivo de documento adjunto (RUT, USCI, etc.)
    rut_doc_path = ""
    if "rut_doc" in request.files:
        file = request.files["rut_doc"]
        if file and os.path.splitext(file.filename)[1].lower() in ALLOWED_DOC_EXTS:
            filename = secure_filename(f"{uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            rut_doc_path = f"uploads/{filename}"

    # 1️⃣ Validar email único
    if email in USERS:
        flash(t("El usuario ya existe", "User already exists", "用户已存在"), "error")
        return redirect(url_for("register_router"))

    # 2️⃣ Validar tipo desde sesión
    tipo_norm = session.get("register_tipo")
    if not tipo_norm:
        flash(t("Debes elegir un tipo de cuenta", "You must choose an account type", "请先选择帐户类型"), "error")
        return redirect(url_for("register_router"))

    # 3️⃣ Rol permitido para tipo
    if not rol_valido_para_tipo(rol, tipo_norm):
        flash(t("Rol no permitido para el tipo seleccionado",
                "Role not allowed for the selected type", "所选类型不允许该角色"), "error")
        return redirect(url_for("register_form", tipo=tipo_norm))

    # 4️⃣ Regla: Extranjero solo “Cliente Extranjero”
    if tipo_norm == "extranjero" and rol.lower() != "cliente extranjero":
        flash(t("Para perfil extranjero el rol debe ser 'Cliente Extranjero'",
                "Foreign profile must be 'Foreign Client'", "海外用户的角色必须为“客户（海外）”"), "error")
        return redirect(url_for("register_form", tipo=tipo_norm))

    # 5️⃣ Crear usuario
    new_user = {
        "nombre": empresa,
        "email": email,
        "password": password,
        "tipo": tipo_norm,
        "rol": rol,
        "empresa": empresa or email.split("@")[0],
        "descripcion": f"Cuenta nueva creada el {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "username": (empresa or email.split("@")[0]).lower().replace(" ", ""),
        "pais": pais,
        "direccion": direccion,
        "telefono": telefono,
        "rut_doc": "",
        "items": [],
    }
    USERS[email] = new_user

    session.pop("register_tipo", None)
    flash(t("Usuario registrado correctamente", "User registered successfully", "注册成功"), "success")
    return redirect(url_for("login"))
# =========================================================
# 🌐 Parte 3 · Permisos · Validaciones · Helpers · Middleware
# =========================================================

# ---------------------------------------------------------
# 🧩 MAPA DE PERMISOS SEGÚN PERFIL Y ROL
# ---------------------------------------------------------
PERMISOS = {
    "compraventa": {
        "Productor": {
            "puede_vender_a": ["Packing", "Frigorífico", "Exportador"],
            "puede_comprar_de": [],
            "puede_comprar_servicios": ["Transporte", "Packing", "Frigorífico"]
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
            "puede_comprar_servicios": [
                "Transporte", "Agencia de Aduanas", "Extraportuarios", "Packing", "Frigorífico"
            ]
        }
    },
    "servicio": {
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
# ⚙️ HELPERS DE LÓGICA GENERAL
# ---------------------------------------------------------
def puede_publicar(usuario):
    """Determina si el usuario puede publicar productos o servicios."""
    if not usuario:
        return False
    rol = usuario.get("rol", "")
    tipo = usuario.get("tipo", "")
    # Solo usuarios de compraventa o mixtos pueden publicar
    return tipo in ["compraventa", "mixto"] or rol in ["Exportador", "Productor"]

def puede_ver_publicacion(usuario, publicacion):
    """Valida si el usuario puede ver una publicación según su tipo y rol."""
    if not usuario or not publicacion:
        return False

    tipo_usuario = usuario.get("tipo", "")
    rol_usuario = usuario.get("rol", "")
    rol_publicador = publicacion.get("rol", "")
    tipo_publicador = publicacion.get("tipo", "")

    permisos_tipo = PERMISOS.get(tipo_usuario, {}).get(rol_usuario, {})

    # Caso 1: puede comprar productos
    if "puede_comprar_de" in permisos_tipo and rol_publicador in permisos_tipo["puede_comprar_de"]:
        return True

    # Caso 2: puede comprar servicios
    if "puede_comprar_servicios" in permisos_tipo and rol_publicador in permisos_tipo["puede_comprar_servicios"]:
        return True

    # Caso 3: cliente extranjero
    if tipo_usuario == "extranjero":
        return rol_publicador in ["Exportador"]

    # Caso 4: admin
    if rol_usuario == "Administrador":
        return True

    return False

def puede_mostrar_dashboard(usuario):
    """Determina qué dashboard mostrar según el tipo y rol."""
    if not usuario:
        return "home"

    rol = usuario.get("rol", "")
    tipo = usuario.get("tipo", "")

    if rol.lower() == "administrador":
        return "dashboard_admin"
    elif tipo == "extranjero":
        return "dashboard_extranjero"
    elif tipo == "servicio":
        return "dashboard_servicio"
    elif tipo == "compraventa":
        return "dashboard_compra"
    elif tipo == "mixto":
        return "dashboard_mixto"
    else:
        return "dashboard"

# ---------------------------------------------------------
# 🔄 MIDDLEWARE: Verificación de sesión válida
# ---------------------------------------------------------
@app.before_request
def check_session_integrity():
    """Verifica que el usuario logueado siga existiendo en USERS."""
    user = session.get("user")
    if user:
        email = user.get("email")
        if email not in USERS:
            session.pop("user", None)
            flash(
                t("Sesión expirada, por favor vuelva a iniciar sesión",
                  "Session expired, please log in again",
                  "会话已过期，请重新登录"),
                "error"
            )
            return redirect(url_for("login"))
# =========================================================
# 🌐 Parte 4 · Dashboards · Publicaciones · Carrito · Clientes · Mensajería
# =========================================================

from uuid import uuid4
from flask import abort

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
    rutas = {
        "dashboard_admin": "dashboard_admin",
        "dashboard_compra": "dashboard_compra",
        "dashboard_servicio": "dashboard_servicio",
        "dashboard_mixto": "dashboard_mixto",
        "dashboard_extranjero": "dashboard_extranjero",
    }
    return redirect(url_for(rutas.get(destino, "home")))

# ---------------------------------------------------------
# 📊 DASHBOARDS POR PERFIL
# ---------------------------------------------------------
@app.route("/dashboard_admin")
def dashboard_admin():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard_admin.html", user=user, titulo=t("Panel Administrador"))

# =========================================================
# 📦 Lógica de visibilidad de publicaciones por tipo de usuario
# =========================================================
def _publicaciones_visibles_para(user):
    """Filtra las publicaciones visibles según tipo y permisos del usuario."""
    tipo = user.get("tipo")
    rol = user.get("rol")
    visibles = []

    for p in PUBLICACIONES:
        autor_tipo = p.get("tipo")
        autor_rol = p.get("rol")

        # --- Productor ---
        if rol == "Productor" and tipo in ["compraventa"]:
            if p["categoria"] in ["servicio", "compra"]:
                visibles.append(p)

        # --- Exportador ---
        elif rol == "Exportador":
            if p["categoria"] in ["venta", "servicio", "compra"]:
                visibles.append(p)

        # --- Packing / Frigorífico ---
        elif rol in ["Packing", "Frigorífico"]:
            if p["categoria"] in ["servicio", "venta", "compra"]:
                visibles.append(p)

        # --- Mixto ---
        elif tipo == "mixto":
            visibles.append(p)

        # --- Servicio (transporte, aduana, etc.) ---
        elif tipo == "servicio":
            if p["categoria"] == "servicio":
                visibles.append(p)

        # --- Cliente extranjero: sólo ve exportadores con venta ---
        elif tipo == "extranjero":
            if autor_rol == "Exportador" and p["categoria"] == "venta":
                visibles.append(p)

    return visibles

# ---------------------------------------------------------
# 📊 DASHBOARDS POR PERFIL (corregidos)
# ---------------------------------------------------------
@app.route("/dashboard_compra")
def dashboard_compra():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = _publicaciones_visibles_para(user)
    return render_template("dashboard_compra.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel de Compraventa"))

@app.route("/dashboard_servicio")
def dashboard_servicio():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = [p for p in _publicaciones_visibles_para(user) if p.get("categoria") == "servicio"]
    return render_template("dashboard_servicio.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel de Servicios"))

@app.route("/dashboard_mixto")
def dashboard_mixto():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = _publicaciones_visibles_para(user)
    return render_template("dashboard_mixto.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel Mixto"))

@app.route("/dashboard_extranjero")
def dashboard_extranjero():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = _publicaciones_visibles_para(user)
    return render_template("dashboard_ext.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel Cliente Extranjero"))

@app.route("/dashboard_servicio")
def dashboard_servicio():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = [p for p in _publicaciones_visibles_para(user) if p.get("tipo") == "servicio"]
    return render_template("dashboard_servicio.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel de Servicios"))

@app.route("/dashboard_mixto")
def dashboard_mixto():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = _publicaciones_visibles_para(user)
    return render_template("dashboard_mixto.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel Mixto"))

@app.route("/dashboard_extranjero")
def dashboard_extranjero():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    pubs = _publicaciones_visibles_para(user)
    return render_template("dashboard_ext.html",
                           user=user,
                           publicaciones=pubs,
                           titulo=t("Panel Cliente Extranjero"))

# ---------------------------------------------------------
# 📰 PUBLICACIONES (crear / eliminar)
# ---------------------------------------------------------
@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    user = get_user()
    if not user:
        flash(t("Debes iniciar sesión primero",
                "You must log in first", "您必須先登入"), "error")
        return redirect(url_for("login"))

    # 🚫 Validación general de permisos
    if not puede_publicar(user):
        flash(t("No tienes permisos para publicar.",
                "You do not have permission to publish.",
                "無權限發布"), "error")
        return redirect(url_for("dashboard_router"))

    if request.method == "POST":
        subtipo = (request.form.get("subtipo") or "").strip().lower()      # oferta o demanda
        categoria = (request.form.get("tipo_publicacion") or "").strip().lower()  # compra, venta o servicio
        producto = (request.form.get("producto") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        precio = (request.form.get("precio") or "").strip() or "Consultar"

        if not subtipo or not categoria or not producto or not descripcion:
            flash(t("Completa todos los campos requeridos",
                    "Complete all required fields", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        rol = user.get("rol", "")
        tipo = user.get("tipo", "")

        # 🔒 Validaciones según tipo y rol
        valido = False

        # --- Productor ---
        if rol == "Productor" and tipo == "compraventa":
            if subtipo == "oferta" and categoria == "venta":
                valido = True
            elif subtipo == "demanda" and categoria == "servicio":
                valido = True

        # --- Packing / Frigorífico ---
        elif rol in ["Packing", "Frigorífico"]:
            if tipo in ["compraventa", "mixto"]:
                if subtipo == "oferta" and categoria in ["venta", "servicio"]:
                    valido = True
                elif subtipo == "demanda" and categoria in ["compra", "servicio"]:
                    valido = True

        # --- Exportador ---
        elif rol == "Exportador":
            if subtipo == "oferta" and categoria == "venta":
                valido = True
            elif subtipo == "demanda" and categoria == "servicio":
                valido = True

        # --- Mixtos: todo lo anterior permitido ---
        elif tipo == "mixto":
            valido = True

        if not valido:
            flash(t("Tu rol no permite publicar este tipo de anuncio.",
                    "Your role does not allow this publication type.",
                    "您的角色無法發布此類型的公告。"), "error")
            return redirect(url_for("dashboard_router"))

        # ✅ Crear publicación
        nueva = {
            "id": f"pub_{uuid4().hex[:8]}",
            "usuario": user["email"],
            "empresa": user.get("empresa"),
            "rol": rol,
            "tipo": tipo,
            "subtipo": subtipo,
            "categoria": categoria,
            "producto": producto,
            "descripcion": descripcion,
            "precio": precio,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        PUBLICACIONES.append(nueva)

        flash(t("Publicación creada correctamente",
                "Post created successfully", "發布成功"), "success")
        return redirect(url_for("dashboard_router"))

    # Si es GET: renderizar el formulario
    return render_template("publicar.html",
                           user=user,
                           titulo=t("Nueva Publicación"))

@app.route("/publicacion/eliminar/<pub_id>")
def eliminar_publicacion(pub_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    antes = len(PUBLICACIONES)
    PUBLICACIONES[:] = [
        p for p in PUBLICACIONES if not (p["id"] == pub_id and p["usuario"] == user["email"])
    ]
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
    return render_template("carrito.html", user=user, cart=carrito, titulo=t("Carrito de Compras"))

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)

    if not pub:
        if pub_id.startswith("direct-"):
            try:
                _, uname, idx_str = pub_id.split("-", 2)
                idx = int(idx_str) - 1
            except Exception:
                flash(t("Formato inválido", "Invalid format", "格式無效"), "error")
                return redirect(url_for("carrito"))

            email_map = {u["username"]: e for e, u in USERS.items()}
            email = email_map.get(uname)
            if not email or email not in USERS:
                flash(t("Empresa no encontrada", "Company not found", "找不到公司"), "error")
                return redirect(url_for("carrito"))

            c = USERS[email]
            if not c.get("items") or not (0 <= idx < len(c["items"])):
                flash(t("Ítem no disponible", "Item not available", "項目不可用"), "error")
                return redirect(url_for("carrito"))

            item = c["items"][idx]
            pub = {
                "id": pub_id,
                "usuario": email,
                "empresa": c.get("empresa"),
                "rol": c.get("rol"),
                "tipo": "oferta" if c.get("tipo") in ("compraventa", "mixto") else "servicio",
                "producto": item.get("nombre"),
                "descripcion": item.get("detalle"),
                "precio": item.get("precio", "Consultar"),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(url_for("dashboard_router"))

    if not puede_ver_publicacion(user, {"rol": pub["rol"], "tipo": pub["tipo"]}):
        flash(t("No tienes permiso para comprar este ítem",
                "You are not allowed to buy this item", "無權購買此項目"), "error")
        return redirect(url_for("dashboard_router"))

    carrito = user.setdefault("carrito", [])
    if any(item["id"] == pub["id"] for item in carrito):
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
# 🧾 CLIENTES / EMPRESAS VISIBLES SEGÚN PERMISOS
# ---------------------------------------------------------
@app.route("/clientes")
def clientes():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    # 🔽 Nuevo: filtro por tipo de empresa
    filtro = request.args.get("filtro", "").strip().lower()
    ocultos = HIDDEN_COMPANIES.get(user["email"], set())
    visibles = []

    for _, info in USERS.items():
        if info["email"] == user["email"]:
            continue
        username = info.get("username", "").lower()
        if username in ocultos:
            continue

        # Aplica filtro si está seleccionado
        if filtro:
            if filtro == "venta" and info["tipo"] not in ["compraventa", "mixto"]:
                continue
            if filtro == "compra" and info["rol"].lower() not in ["productor", "frigorífico", "packing"]:
                continue
            if filtro == "servicio" and info["tipo"] != "servicio":
                continue

        if puede_ver_publicacion(user, {"rol": info["rol"], "tipo": info["tipo"]}):
            visibles.append(info)

    return render_template(
        "clientes.html",
        user=user,
        clientes=visibles,
        titulo=t("Empresas Registradas"),
        filtro=filtro
    )

@app.route("/clientes/<username>")
def cliente_detalle(username):
    username = (username or "").lower().strip()
    email_map = {u["username"]: e for e, u in USERS.items()}
    email = email_map.get(username)
    if not email or email not in USERS:
        abort(404)

    c = USERS[email]
    user = get_user()
    return render_template(
        "cliente_detalle.html",
        user=user,
        c=c,
        titulo=c.get("empresa", username)
    )

# ---------------------------------------------------------
# 💬 MENSAJERÍA INTERNA
# ---------------------------------------------------------
@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        destino = (request.form.get("destino") or "").strip().lower()
        contenido = (request.form.get("contenido") or "").strip()

        # 🔹 Validaciones básicas
        if not destino or not contenido:
            flash(t("Completa destinatario y contenido",
                    "Fill recipient and content", "請填寫收件人與內容"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe",
                    "Recipient does not exist", "收件人不存在"), "error")
            return redirect(url_for("mensajes"))

        if destino == user["email"]:
            flash(t("No puedes enviarte mensajes a ti mismo",
                    "You cannot message yourself", "無法傳送訊息給自己"), "warning")
            return redirect(url_for("mensajes"))

        # 🕒 Cooldown: 3 días (72 horas)
        now = datetime.now()
        tres_dias = 3 * 24 * 3600  # segundos
        enviados_user = [m for m in MENSAJES
                         if m["origen"] == user["email"] and m["destino"] == destino]

        if enviados_user:
            ultimo_envio = max(datetime.strptime(m["fecha"], "%Y-%m-%d %H:%M")
                               for m in enviados_user)
            diferencia = (now - ultimo_envio).total_seconds()
            if diferencia < tres_dias:
                horas_rest = int((tres_dias - diferencia) / 3600)
                flash(t(f"Aún debes esperar {horas_rest}h para volver a contactar a esta empresa",
                        f"You must wait {horas_rest}h before messaging this company again",
                        f"您必須等待 {horas_rest} 小時才能再次聯絡此公司"), "warning")
                return redirect(url_for("mensajes"))

        # 📩 Registrar mensaje nuevo
        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": now.strftime("%Y-%m-%d %H:%M")
        })
        flash(t("Mensaje enviado correctamente",
                "Message sent successfully", "訊息已送出"), "success")
        return redirect(url_for("mensajes"))

    # 📬 Mostrar bandejas
    recibidos = [m for m in MENSAJES if m["destino"] == user["email"]]
    enviados = [m for m in MENSAJES if m["origen"] == user["email"]]

    return render_template("mensajes.html",
                           user=user,
                           recibidos=recibidos,
                           enviados=enviados,
                           titulo=t("Mensajería"))

# ---------------------------------------------------------
# 🧩 OCULTAR EMPRESAS DE LA VISTA
# ---------------------------------------------------------
@app.route("/ocultar/<username>", methods=["POST"])
def ocultar_publicacion(username):
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    if not username:
        return redirect(url_for("clientes"))

    key = user["email"]
    HIDDEN_COMPANIES.setdefault(key, set()).add(username.lower())
    flash(t("Elemento ocultado temporalmente de tu vista",
            "Item temporarily hidden from your view", "已暫時隱藏項目"), "info")
    return redirect(url_for("clientes"))


# 🔁 NUEVO: Mostrar nuevamente todas las empresas ocultas
@app.route("/mostrar_todo", methods=["POST"])
def mostrar_todo():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    key = user["email"]
    if key in HIDDEN_COMPANIES:
        HIDDEN_COMPANIES[key].clear()
        flash(t("Se han restaurado todas las empresas visibles",
                "All companies are now visible again", "所有公司已再次可見"), "success")
    else:
        flash(t("No había elementos ocultos",
                "There were no hidden items", "沒有隱藏的項目"), "info")

    return redirect(url_for("clientes"))

# ---------------------------------------------------------
# 💡 PÁGINAS INFORMATIVAS / STATUS
# ---------------------------------------------------------
@app.route("/ayuda")
def ayuda():
    user = get_user()
    if not user:
        return render_template("ayuda.html", titulo=t("Centro de Ayuda"))
    # Redirige correctamente al dashboard correspondiente
    return render_template(
        "ayuda.html",
        user=user,
        titulo=t("Centro de Ayuda"),
        volver=url_for(puede_mostrar_dashboard(user))
    )

@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping"))

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
# =========================================================
# 🚀 Parte 5 · Cierre Final y Ejecución del Servidor Flask
# =========================================================

import os

# ---------------------------------------------------------
# 🧩 CONFIGURACIÓN FINAL DE APP
# ---------------------------------------------------------
if not app.secret_key:
    app.secret_key = os.environ.get("SECRET_KEY", "clave_super_segura")

# Directorio base para recursos si hace falta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------
# 🪪 MANEJO DE ERRORES BÁSICOS
# ---------------------------------------------------------
@app.errorhandler(404)
def error_404(e):
    return render_template("error.html",
                           titulo=t("Página no encontrada"),
                           mensaje=t("La página solicitada no existe.",
                                     "The requested page does not exist.",
                                     "找不到請求的頁面")), 404

@app.errorhandler(500)
def error_500(e):
    return render_template("error.html",
                           titulo=t("Error interno del servidor"),
                           mensaje=t("Ha ocurrido un error inesperado.",
                                     "An unexpected error occurred.",
                                     "發生意外錯誤")), 500

# ---------------------------------------------------------
# 🧭 FUNCIÓN AUXILIAR PARA ARRANQUE LIMPIO
# ---------------------------------------------------------
def iniciar_app():
    print("\n🌐 Window Shopping iniciado correctamente\n")
    print(f"📦 Usuarios registrados: {len(USERS)}")
    print(f"📰 Publicaciones activas: {len(PUBLICACIONES)}")
    print(f"🕒 Servidor iniciado a las {datetime.now().strftime('%H:%M:%S')}")
    print("✅ Aplicación lista en http://127.0.0.1:5000/\n")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ---------------------------------------------------------
# ▶️ EJECUCIÓN FINAL
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        iniciar_app()
    except Exception as e:
        print(f"\n❌ Error al iniciar la app: {e}\n")
