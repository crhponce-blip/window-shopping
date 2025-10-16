# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 estable y completa)
# Autor: Christopher Ponce & GPT-5
# ---------------------------------------------------------
# Contiene: Configuración · Traducción · Usuarios ficticios ·
# Registro · Login · Cambio de idioma
# =========================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "windowshopping_secret_key_v3_5"

# =========================================================
# 🔹 BASE DE DATOS EN MEMORIA
# =========================================================
USERS = {}
PUBLICACIONES = []

# =========================================================
# 🔹 USUARIOS FICTICIOS (para pruebas y desarrollo)
# =========================================================
USERS = {
    "admin@ws.com": {
        "nombre": "Administrador General",
        "email": "admin@ws.com",
        "password": "admin",
        "tipo": "Nacional",
        "rol": "Administrador",
        "empresa": "Window Shopping",
        "descripcion": "Administrador principal de la plataforma WS.",
        "fecha": "2025-10-10 22:00:00"
    },
    "compra@ws.com": {
        "nombre": "Luis Mercado",
        "email": "compra@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Compraventa",
        "empresa": "Mercado Chile Ltda.",
        "descripcion": "Empresa dedicada a la compra y venta de frutas chilenas al por mayor.",
        "fecha": "2025-10-10 09:30:00"
    },
    "servicios@ws.com": {
        "nombre": "Ana Frío",
        "email": "servicios@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Servicios",
        "empresa": "FríoExpress SpA",
        "descripcion": "Provee servicios de almacenamiento y logística frigorífica.",
        "fecha": "2025-10-09 15:10:00"
    },
    "extranjero@ws.com": {
        "nombre": "David Wang",
        "email": "extranjero@ws.com",
        "password": "1234",
        "tipo": "Extranjero",
        "rol": "Cliente Extranjero",
        "empresa": "Shanghai Imports Co.",
        "descripcion": "Cliente internacional interesado en productos frescos chilenos.",
        "fecha": "2025-10-11 18:20:00"
    },
    "packing@ws.com": {
        "nombre": "María Campos",
        "email": "packing@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Packing",
        "empresa": "Packing Andes SpA",
        "descripcion": "Ofrece servicios de embalaje y control de calidad para exportadores.",
        "fecha": "2025-10-12 10:15:00"
    },
    "frigorifico@ws.com": {
        "nombre": "Carlos Frías",
        "email": "frigorifico@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Frigorífico",
        "empresa": "Frigorífico Polar Sur",
        "descripcion": "Empresa de almacenamiento en frío para frutas exportadas.",
        "fecha": "2025-10-12 12:00:00"
    },
    "aduana@ws.com": {
        "nombre": "Patricio Reyes",
        "email": "aduana@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Agencia de Aduana",
        "empresa": "SurLog Agencia Aduanera",
        "descripcion": "Gestión documental y trámites de exportación para clientes WS.",
        "fecha": "2025-10-12 16:40:00"
    },
    "transporte@ws.com": {
        "nombre": "Javier Ruta",
        "email": "transporte@ws.com",
        "password": "1234",
        "tipo": "Nacional",
        "rol": "Transporte Extraportuario",
        "empresa": "Transportes SurCargo",
        "descripcion": "Servicios de traslado de fruta desde campos a puertos.",
        "fecha": "2025-10-12 20:00:00"
    }
}

# =========================================================
# 🔹 TRADUCCIONES BÁSICAS
# =========================================================
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

# =========================================================
# 🔹 FUNCIÓN DE TRADUCCIÓN UNIVERSAL
# =========================================================
def t(es, en=None, zh=None):
    lang = session.get("lang", "es")
    if isinstance(es, str) and es in TRAD:
        return TRAD[es].get(lang, es)
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

@app.context_processor
def inject_t():
    return dict(t=t)

# =========================================================
# 🔹 CAMBIO DE IDIOMA
# =========================================================
@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang not in ["es", "en", "zh"]:
        lang = "es"
    session["lang"] = lang
    flash(t("Idioma cambiado", "Language changed", "語言已更改"), "info")
    return redirect(request.referrer or url_for("home"))

# =========================================================
# 🔹 PÁGINA INICIO
# =========================================================
@app.route("/")
def home():
    lang = session.get("lang", "es")
    return render_template("index.html",
                           lang=lang,
                           titulo=t("Inicio", "Home", "首頁"))

# =========================================================
# 🔹 REGISTRO
# =========================================================
@app.route("/register", methods=["GET", "POST"])
def register_router():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        tipo = request.form.get("tipo")
        rol = request.form.get("rol")
        empresa = request.form.get("empresa")

        if not all([nombre, email, password, tipo, rol, empresa]):
            flash(t("Por favor completa todos los campos",
                    "Please fill all fields",
                    "請填寫所有欄位"), "error")
            return redirect(url_for("register_router"))

        if email in USERS:
            flash(t("El usuario ya existe", "User already exists", "使用者已存在"), "error")
            return redirect(url_for("register_router"))

        USERS[email] = {
            "nombre": nombre,
            "email": email,
            "password": password,
            "tipo": tipo,
            "rol": rol,
            "empresa": empresa,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        flash(t("Registro exitoso. Ahora inicia sesión.",
                "Registration successful. Please log in.",
                "註冊成功，請登入"), "success")
        return redirect(url_for("login"))

    return render_template("register.html",
                           titulo=t("Registrarse", "Register", "註冊"))

# =========================================================
# 🔹 LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = user
            flash(t("Inicio de sesión exitoso",
                    "Login successful",
                    "登入成功"), "success")
            return redirect(url_for("dashboard_router"))
        else:
            flash(t("Credenciales incorrectas",
                    "Incorrect credentials",
                    "帳號或密碼錯誤"), "error")
            return redirect(url_for("login"))

    return render_template("login.html",
                           titulo=t("Iniciar sesión", "Login", "登入"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 estable)
# ---------------------------------------------------------
# Parte 2: Dashboards por rol · Logout · Carrito inicial
# =========================================================

# =========================================================
# 🔹 DASHBOARD ROUTER — según rol
# =========================================================
@app.route("/dashboard")
def dashboard_router():
    """Redirige al dashboard según el rol del usuario."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión primero.",
                "You must log in first.",
                "您必須先登入"), "error")
        return redirect(url_for("login"))

    rol = user.get("rol", "").lower()

    if rol == "administrador":
        return redirect(url_for("dashboard_admin"))
    elif rol in ["compraventa", "productor", "packing", "frigorífico", "frigorifico", "exportador"]:
        return redirect(url_for("dashboard_compra"))
    elif rol in ["servicios", "transporte extraportuario", "agencia de aduana", "servicio extraportuario"]:
        return redirect(url_for("dashboard_servicio"))
    elif rol in ["cliente extranjero", "extranjero"]:
        return redirect(url_for("dashboard_extranjero"))
    else:
        flash(t("Rol no reconocido o sin panel asignado.",
                "Unrecognized role or no assigned dashboard.",
                "無法識別角色或未分配儀表板"), "warning")
        return redirect(url_for("home"))

# =========================================================
# 🔹 DASHBOARD: COMPRAVENTA
# =========================================================
@app.route("/dashboard_compra")
def dashboard_compra():
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

# =========================================================
# 🔹 DASHBOARD: SERVICIOS
# =========================================================
@app.route("/dashboard_servicio")
def dashboard_servicio():
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

# =========================================================
# 🔹 DASHBOARD: CLIENTE EXTRANJERO
# =========================================================
@app.route("/dashboard_extranjero")
def dashboard_extranjero():
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

# =========================================================
# 🔹 DASHBOARD: ADMINISTRADOR
# =========================================================
@app.route("/dashboard_admin")
def dashboard_admin():
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

# =========================================================
# 🔹 LOGOUT
# =========================================================
@app.route("/logout")
def logout():
    """Cierra sesión y redirige al inicio."""
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente.",
            "Session closed successfully.",
            "已成功登出"), "success")
    return redirect(url_for("home"))

# =========================================================
# 🔹 CARRITO (vista inicial)
# =========================================================
@app.route("/carrito")
def carrito():
    """Muestra el carrito actual (estructura básica)."""
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver tu carrito.",
                "You must log in to view your cart.",
                "您必須登入以查看購物車"), "error")
        return redirect(url_for("login"))

    # A futuro aquí se cargarán los ítems reales
    carrito_items = PUBLICACIONES[:3] if PUBLICACIONES else []

    return render_template(
        "carrito.html",
        user=user,
        carrito=carrito_items,
        titulo=t("Carrito", "Cart", "購物車")
    )
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 estable)
# ---------------------------------------------------------
# Parte 3: Publicaciones · Permisos/Visibilidad · Carrito
#                  Ocultar/Restaurar · Dashboards con data
# =========================================================

from uuid import uuid4
from datetime import datetime
from flask import request, redirect, url_for, render_template, flash, session, jsonify, abort

# --------- MATRICES DE PERMISOS SEGÚN TU ESPECIFICACIÓN ---------

# Quien PUEDE VENDER fruta A quién (para publicaciones tipo "oferta")
TRADE_CAN_SELL_TO = {
    "productor": {"packing", "frigorifico", "exportador"},
    "packing": {"frigorifico", "exportador"},
    "frigorifico": {"packing", "exportador"},
    "exportador": {"cliente_extranjero", "exportador"},
}

# Quién PUEDE COMPRAR fruta A quién (para publicaciones tipo "demanda")
# -> vendedores que pueden vender al demandante
TRADE_SELLERS_FOR_BUYER = {
    "productor": set(),  # un productor no "compra" fruta, así que vacío
    "packing": {"productor", "frigorifico"},
    "frigorifico": {"productor", "packing"},
    "exportador": {"productor", "packing", "frigorifico", "exportador"},
    "cliente_extranjero": {"exportador"},  # por si en algún flujo publica "demanda"
}

# QUIÉN PUEDE VENDER SERVICIOS A QUIÉN (publicaciones tipo "servicio")
SERVICE_CAN_SELL_TO = {
    "transporte_extraportuario": {"productor", "packing", "frigorifico", "exportador"},
    "servicio_extraportuario": {"exportador"},
    "agencia_aduana": {"exportador"},
    "packing": {"exportador", "frigorifico", "productor"},   # como prestador de servicio
    "frigorifico": {"exportador", "packing", "productor"},   # como prestador de servicio
}

# Roles “agrupados” por familia (para validaciones suaves)
FAMILY_COMPRAVENTA = {"productor", "packing", "frigorifico", "exportador"}
FAMILY_SERVICIO = {
    "transporte_extraportuario", "servicio_extraportuario", "agencia_aduana", "packing", "frigorifico"
}
FAMILY_CLIENTE = {"cliente_extranjero"}


# ----------------- FUNCIONES DE PERMISOS Y VISIBILIDAD -----------------

def _norm(rol: str) -> str:
    return rol.replace("í", "i").replace("Í", "I").lower().strip()

def puede_publicar(rol: str, tipo_pub: str) -> bool:
    """Quién puede publicar cada tipo según reglas."""
    r = _norm(rol)
    tipo = (tipo_pub or "").lower().strip()

    if tipo in {"oferta", "demanda"}:
        # Solo compraventa y exportador pueden publicar fruta
        return r in FAMILY_COMPRAVENTA
    if tipo == "servicio":
        # Prestadores de servicios (incluye packing y frigorífico como servicio)
        return r in FAMILY_SERVICIO
    return False

def puede_ver_publicacion(rol_viewer: str, rol_pub: str, tipo_pub: str) -> bool:
    """Visibilidad entre roles según tipo de publicación."""
    v = _norm(rol_viewer)
    p = _norm(rol_pub)
    tipo = (tipo_pub or "").lower().strip()

    # Clientes extranjeros ven SOLO ofertas de exportadores
    if v in FAMILY_CLIENTE:
        return tipo == "oferta" and p == "exportador"

    # Ofertas de fruta: ¿el publicador puede venderle al viewer?
    if tipo == "oferta":
        return v in TRADE_CAN_SELL_TO.get(p, set())

    # Demandas de fruta: ¿el viewer puede venderle al publicador?
    if tipo == "demanda":
        sellers = TRADE_SELLERS_FOR_BUYER.get(p, set())
        return v in sellers

    # Servicios: ¿el prestador le vende servicio al viewer?
    if tipo == "servicio":
        return v in SERVICE_CAN_SELL_TO.get(p, set())

    return False


# --------------------- UTILIDADES DE PUBLICACIONES ---------------------

def _pub_base(user, tipo_pub, producto, descripcion, precio, subtipo=""):
    return {
        "id": f"pub_{uuid4().hex[:8]}",
        "usuario": user["email"],
        "empresa": user["empresa"],
        "rol": _norm(user["rol"]),
        "tipo": tipo_pub,  # "oferta" | "demanda" | "servicio"
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
            if p["tipo"] != filtro:
                continue
            if p["id"] in ocultas_ids:
                continue
            if puede_ver_publicacion(user["rol"], p["rol"], p["tipo"]):
                visibles.append(p)
        except Exception:
            # Si hubo alguna clave faltante, se ignora esa publicación corrupta
            continue
    visibles.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return visibles

def _propias_de(user):
    propias = [p for p in PUBLICACIONES if p.get("usuario") == user["email"]]
    propias.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return propias


# -------------------------- RUTAS: PUBLICAR ----------------------------

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite crear una publicación nueva (oferta, demanda o servicio)."""
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

        if not puede_publicar(user["rol"], tipo_pub):
            flash(t("No tienes permisos para este tipo de publicación.", "You are not allowed to post this type.", "無權限發布此類別"), "error")
            return redirect(url_for("dashboard_router"))

        nueva = _pub_base(user, tipo_pub, producto, descripcion, precio, subtipo)
        PUBLICACIONES.append(nueva)
        flash(t("Publicación creada correctamente.", "Post created successfully.", "發布成功"), "success")
        # Redirige al dashboard adecuado
        return redirect(url_for("dashboard_router"))

    return render_template(
        "publicar.html",
        user=user,
        titulo=t("Nueva Publicación", "New Post", "新增發布")
    )


@app.route("/publicacion/eliminar/<pub_id>", methods=["POST", "GET"])
def eliminar_publicacion(pub_id):
    """Eliminar publicación propia."""
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    antes = len(PUBLICACIONES)
    # solo elimina si es del usuario
    PUBLICACIONES[:] = [p for p in PUBLICACIONES if not (p.get("id") == pub_id and p.get("usuario") == user["email"])]
    despues = len(PUBLICACIONES)

    if despues < antes:
        flash(t("Publicación eliminada.", "Post deleted.", "發布已刪除"), "success")
    else:
        flash(t("No encontrada o sin permiso.", "Not found or unauthorized.", "未找到或無權限"), "warning")
    return redirect(url_for("dashboard_router"))


# ---------------------- RUTAS: OCULTAR / RESTAURAR ---------------------

@app.route("/ocultar/<pub_id>", methods=["POST", "GET"])
def ocultar_publicacion(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    ocultas = OCULTOS.setdefault(user["email"], [])
    if pub_id not in ocultas:
        ocultas.append(pub_id)
        flash(t("Publicación ocultada.", "Item hidden.", "項目已隱藏"), "info")
    return redirect(url_for("dashboard_router"))

@app.route("/restablecer_ocultos", methods=["POST", "GET"])
def restablecer_ocultos():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    OCULTOS[user["email"]] = []
    flash(t("Se restauraron las publicaciones ocultas.", "Hidden items restored.", "已恢復隱藏項目"), "success")
    return redirect(url_for("dashboard_router"))


# ----------------------------- RUTAS: CARRITO --------------------------

@app.route("/carrito")
def carrito():
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión para ver el carrito.", "You must log in to view the cart.", "您必須登入以檢視購物車"), "error")
        return redirect(url_for("login"))

    cart = user.setdefault("carrito", [])
    return render_template(
        "carrito.html",
        user=user,
        cart=cart,
        titulo=t("Carrito", "Cart", "購物車")
    )

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    pub = next((p for p in PUBLICACIONES if p.get("id") == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada.", "Item not found.", "找不到項目"), "error")
        return redirect(url_for("dashboard_router"))

    cart = user.setdefault("carrito", [])
    if any(item.get("id") == pub_id for item in cart):
        flash(t("El ítem ya está en el carrito.", "Item already in cart.", "項目已在購物車中"), "warning")
    else:
        cart.append(pub)
        # Persistimos en sesión
        session["user"] = user
        flash(t("Agregado al carrito.", "Added to cart.", "已加入購物車"), "success")

    return redirect(url_for("carrito"))

@app.route("/carrito/eliminar/<pub_id>")
def carrito_eliminar(pub_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    cart = user.setdefault("carrito", [])
    nuevo = [p for p in cart if p.get("id") != pub_id]
    user["carrito"] = nuevo
    session["user"] = user
    flash(t("Ítem eliminado del carrito.", "Item removed from cart.", "已刪除項目"), "info")
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar")
def carrito_vaciar():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    user["carrito"] = []
    session["user"] = user
    flash(t("Carrito vaciado.", "Cart cleared.", "購物車已清空"), "success")
    return redirect(url_for("carrito"))


# ------------------- DASHBOARDS CON PUBLICACIONES REALES ----------------

def _dashboard_contexto(user, filtro_default="oferta"):
    filtro = (request.args.get("filtro") or filtro_default).lower().strip()
    if filtro not in {"oferta", "demanda", "servicio"}:
        filtro = filtro_default
    return {
        "user": user,
        "filtro": filtro,
        "publicaciones": _visibles_para(user, filtro),
        "propias": _propias_de(user),
    }

@app.route("/dashboard_compra")
def dashboard_compra():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    ctx = _dashboard_contexto(user, "oferta")
    return render_template(
        "dashboard_compra.html",
        **ctx,
        titulo=t("Panel de Compraventa", "Trade Panel", "貿易面板")
    )

@app.route("/dashboard_servicio")
def dashboard_servicio():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    ctx = _dashboard_contexto(user, "servicio")
    return render_template(
        "dashboard_servicio.html",
        **ctx,
        titulo=t("Panel de Servicios", "Service Panel", "服務面板")
    )

@app.route("/dashboard_extranjero")
def dashboard_extranjero():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    ctx = _dashboard_contexto(user, "oferta")
    return render_template(
        "dashboard_extranjero.html",
        **ctx,
        titulo=t("Panel Cliente Extranjero", "Foreign Client Panel", "外國客戶面板")
    )

@app.route("/dashboard_admin")
def dashboard_admin():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    # El admin ve todo (sin filtro por visibilidad), pero mantenemos estructura
    filtro = (request.args.get("filtro") or "oferta").lower().strip()
    if filtro not in {"oferta", "demanda", "servicio"}:
        filtro = "oferta"
    visibles = [p for p in PUBLICACIONES if p.get("tipo") == filtro]
    visibles.sort(key=lambda x: x.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard_admin.html",
        user=user,
        filtro=filtro,
        publicaciones=visibles,
        propias=_propias_de(user),
        titulo=t("Panel Administrador", "Admin Panel", "管理面板")
    )
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 estable)
# ---------------------------------------------------------
# Parte 4: Router de dashboards · Mensajería · Perfil
#          Clientes/Empresas · Ayuda/Acerca · Status · Run
# =========================================================

from datetime import datetime, timedelta
from flask import request, redirect, url_for, render_template, flash, session, jsonify, abort

# ----------------------- DASHBOARD ROUTER -----------------------------

@app.route("/dashboard")
def dashboard_router():
    """
    Redirecciona al panel correcto según el rol/tipo del usuario.
    - cliente_extranjero -> dashboard_extranjero
    - tipo == 'compraventa' o rol en FAMILY_COMPRAVENTA -> dashboard_compra
    - tipo == 'servicio' o rol en FAMILY_SERVICIO -> dashboard_servicio
    - admin -> dashboard_admin
    """
    user = session.get("user")
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    rol = (user.get("rol") or "").lower().strip()
    tipo = (user.get("tipo") or "").lower().strip()

    if rol == "administrador" or rol == "admin":
        return redirect(url_for("dashboard_admin"))

    if rol == "cliente_extranjero" or tipo == "cliente":
        return redirect(url_for("dashboard_extranjero"))

    # Si es mixto o está en compraventa, por defecto abre el de compraventa
    if tipo in {"compraventa", "mixto"} or rol in FAMILY_COMPRAVENTA:
        return redirect(url_for("dashboard_compra"))

    # Si es de servicio puro
    if tipo == "servicio" or rol in FAMILY_SERVICIO:
        return redirect(url_for("dashboard_servicio"))

    # Fallback
    return redirect(url_for("dashboard_compra"))


# ----------------------- MENSAJERÍA INTERNA --------------------------

MENSAJES = []  # [{origen, destino, contenido, fecha}]

_COOLDOWN_DIAS = 3  # 1 mensaje por par (origen->destino) cada 3 días

def puede_enviar_mensaje(origen: str, destino: str) -> bool:
    now = datetime.now()
    historial = [m for m in MENSAJES if m.get("origen") == origen and m.get("destino") == destino]
    if not historial:
        return True
    # último mensaje
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

    # Sugerimos destinatarios visibles (no a uno mismo)
    posibles = [
        info for _, info in USERS.items()
        if info.get("email") != user["email"]
    ]

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
        empresa = (request.form.get("empresa") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

        if empresa:
            user["empresa"] = empresa
            # sincroniza con USERS
            if user["email"] in USERS:
                USERS[user["email"]]["empresa"] = empresa
        if descripcion:
            user["descripcion"] = descripcion
            if user["email"] in USERS:
                USERS[user["email"]]["descripcion"] = descripcion

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

    visibles = []
    for _, info in USERS.items():
        if info["email"] == user["email"]:
            continue  # no incluirme a mí mismo
        # Si puedo verles una oferta o un servicio, es una empresa relevante
        if puede_ver_publicacion(user["rol"], info["rol"], "oferta") or puede_ver_publicacion(user["rol"], info["rol"], "servicio"):
            visibles.append(info)

    # Filtro opcional por tipo (cliente / compraventa / servicio / mixto)
    filtro_tipo = (request.args.get("tipo") or "").lower().strip()
    if filtro_tipo in {"cliente", "compraventa", "servicio", "mixto"}:
        visibles = [c for c in visibles if (c.get("tipo") or "").lower().strip() == filtro_tipo]

    return render_template(
        "clientes.html",
        user=user,
        clientes=visibles,
        titulo=t("Empresas Registradas", "Registered Companies", "註冊公司")
    )

@app.route("/clientes/<email>")
def cliente_detalle(email):
    c = USERS.get(email.lower().strip())
    if not c:
        abort(404)
    user = session.get("user")
    puede_mensaje = bool(user) and puede_enviar_mensaje(user["email"], c["email"])
    return render_template(
        "cliente_detalle.html",
        user=user,
        c=c,
        puede_mensaje=puede_mensaje,
        titulo=c.get("empresa", email)
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


# ------------------------------ RUN FINAL ------------------------------

# IMPORTANTE:
# Asegúrate de que SOLO exista **un** bloque `if __name__ == "__main__":`
# en el archivo final. Si ya está definido en la Parte 1, NO dupliques este.
# De lo contrario, descomenta el siguiente bloque para ejecutar localmente:
#
# if __name__ == "__main__":
#     load_users_cache()
#     print("🌐 Servidor Flask ejecutándose en http://127.0.0.1:5000")
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
