# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 CORREGIDO FINAL) — PARTE 1/4
# Configuración · Traducción · Usuarios Demo · Login/Logout · Dashboards
# =========================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
import os
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4
from types import SimpleNamespace

# =========================================================
# ⚙️ CONFIGURACIÓN BÁSICA
# =========================================================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_segura")

# =========================================================
# 🌎 TRADUCCIÓN GLOBAL
# =========================================================
def t(es: str, en: str = "", zh: str = "") -> str:
    """Traducción simple según idioma actual en sesión."""
    lang = session.get("lang", "es")
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

# Registrar función t en Jinja global
app.jinja_env.globals.update(t=t)

@app.context_processor
def inject_globals():
    """Variables globales disponibles en todos los templates."""
    return {
        "t": t,
        "current_lang": session.get("lang", "es"),
        "year_now": datetime.now().year,
        "user_session": session.get("user")
    }

@app.before_request
def ensure_lang():
    """Asegura idioma por defecto."""
    if "lang" not in session:
        session["lang"] = "es"

@app.route("/set_lang/<lang>")
def set_lang(lang):
    """Cambia idioma y vuelve a la vista anterior."""
    if lang not in ["es", "en", "zh"]:
        flash("Idioma no disponible.", "error")
        return redirect(request.referrer or url_for("home"))
    session["lang"] = lang
    flash(t("Idioma cambiado correctamente.", "Language changed successfully.", "語言已變更"), "success")
    return redirect(request.referrer or url_for("home"))

# Alias antiguo (/lang/<lang>) por compatibilidad
@app.route("/lang/<lang>")
def set_lang_alias(lang):
    return set_lang(lang)

# =========================================================
# 🧠 "BASE DE DATOS" SIMPLIFICADA (en memoria)
# =========================================================
USERS: Dict[str, Dict[str, Any]] = {}
PUBLICACIONES: List[Dict[str, Any]] = []
OCULTOS: Dict[str, List[str]] = {}
MENSAJES: List[Dict[str, Any]] = []

# =========================================================
# 🔧 FUNCIONES DE USUARIO
# =========================================================
def load_users_cache():
    """Carga usuarios base de demostración."""
    global USERS
    if USERS:
        return

    demo_users = [
        {
            "email": "admin@windowshopping.cl",
            "password": "admin123",
            "rol": "administrador",
            "tipo": "admin",
            "empresa": "Window Shopping Admin",
            "descripcion": "Administrador del sistema.",
        },
        {
            "email": "cliente@windowshopping.cl",
            "password": "cliente123",
            "rol": "cliente_extranjero",
            "tipo": "cliente",
            "empresa": "Importadora Global",
            "descripcion": "Cliente extranjero que compra fruta chilena.",
        },
        {
            "email": "productor@windowshopping.cl",
            "password": "productor123",
            "rol": "productor",
            "tipo": "compraventa",
            "empresa": "Frutas del Valle",
            "descripcion": "Productor que vende fruta y compra servicios.",
        },
        {
            "email": "packing@windowshopping.cl",
            "password": "packing123",
            "rol": "packing",
            "tipo": "mixto",
            "empresa": "Packing Andes",
            "descripcion": "Packing que compra y vende fruta y servicios.",
        },
        {
            "email": "frigorifico@windowshopping.cl",
            "password": "frigo123",
            "rol": "frigorifico",
            "tipo": "mixto",
            "empresa": "Frigorífico Polar",
            "descripcion": "Frigorífico que almacena y vende servicios.",
        },
        {
            "email": "exportador@windowshopping.cl",
            "password": "exportador123",
            "rol": "exportador",
            "tipo": "compraventa",
            "empresa": "Exportadora Sur",
            "descripcion": "Exportador de frutas chilenas a mercados internacionales.",
        },
        {
            "email": "aduana@windowshopping.cl",
            "password": "aduana123",
            "rol": "agencia_aduana",
            "tipo": "servicio",
            "empresa": "Agencia Aduanera SurLog",
            "descripcion": "Agencia de aduana que ofrece servicios documentales.",
        },
        {
            "email": "transporte@windowshopping.cl",
            "password": "transporte123",
            "rol": "transporte_extraportuario",
            "tipo": "servicio",
            "empresa": "Transporte Extraportuario Chile",
            "descripcion": "Transporte terrestre para cargas exportadoras.",
        },
        {
            "email": "extraportuario@windowshopping.cl",
            "password": "extra123",
            "rol": "servicio_extraportuario",
            "tipo": "servicio",
            "empresa": "Servicios Portuarios Global",
            "descripcion": "Servicios logísticos y portuarios para exportadores.",
        },
    ]

    for u in demo_users:
        u.setdefault("items", [])
        u.setdefault("carrito", [])
        USERS[u["email"].lower()] = u
        print(f"🆕 Usuario creado: {u['email']}")

    print(f"✅ USERS en caché: {len(USERS)} usuarios listos.")

def get_user(email: str) -> Dict[str, Any] | None:
    return USERS.get(email.lower())

def validate_login(email: str, password: str) -> bool:
    user = get_user(email)
    return bool(user and user["password"] == password)

# =========================================================
# 🏠 RUTAS PRINCIPALES
# =========================================================
@app.route("/", endpoint="home")
@app.route("/index", endpoint="index")
def index():
    load_users_cache()
    lang = session.get("lang", "es")
    return render_template("index.html", titulo=t("Inicio", "Home", "首頁"), lang=lang)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash(t("Completa todos los campos.", "Please fill in all fields.", "請填寫所有欄位"), "error")
            return render_template("login.html", titulo=t("Iniciar Sesión", "Login", "登入"))

        if validate_login(email, password):
            session["user"] = email
            flash(t("Inicio de sesión exitoso.", "Login successful.", "登入成功"), "success")

            rol = USERS[email]["rol"]
            if rol == "cliente_extranjero":
                return redirect(url_for("dashboard_ext"))
            elif rol in ["productor", "packing", "frigorifico", "exportador"]:
                return redirect(url_for("dashboard_compra"))
            elif rol in ["transporte_extraportuario", "agencia_aduana", "servicio_extraportuario"]:
                return redirect(url_for("dashboard_servicio"))
            elif rol == "administrador":
                return redirect(url_for("dashboard_admin"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash(t("Correo o contraseña incorrectos.", "Invalid credentials.", "帳號或密碼錯誤"), "error")

    return render_template("login.html", titulo=t("Iniciar Sesión", "Login", "登入"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente.", "Logged out successfully.", "登出成功"), "success")
    return redirect(url_for("home"))

# =========================================================
# 🌐 DASHBOARDS SEPARADOS (por rol)
# =========================================================
@app.route("/dashboard_ext")
def dashboard_ext():
    return render_template("dashboard_ext.html", titulo=t("Panel Cliente Extranjero", "Foreign Client Panel", "外國客戶面板"))

@app.route("/dashboard_compra")
def dashboard_compra():
    return render_template("dashboard_compra.html", titulo=t("Panel de Compraventa", "Trade Panel", "貿易面板"))

@app.route("/dashboard_servicio")
def dashboard_servicio():
    return render_template("dashboard_servicio.html", titulo=t("Panel de Servicios", "Service Panel", "服務面板"))

@app.route("/dashboard_admin")
def dashboard_admin():
    return render_template("dashboard_admin.html", titulo=t("Panel Administrador", "Admin Panel", "管理面板"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 CORREGIDO FINAL) — PARTE 2/4
# Registro · Roles · Validación · Enrutamiento de registro
# =========================================================

# =========================================================
# 🧩 DEFINICIÓN DE TIPOS Y ROLES DISPONIBLES
# =========================================================
TIPOS_DISPONIBLES = {
    "cliente": ["cliente_extranjero"],
    "compraventa": ["productor", "packing", "frigorifico", "exportador"],
    "servicio": ["transporte_extraportuario", "agencia_aduana", "servicio_extraportuario"],
    "mixto": ["packing", "frigorifico"],
}

ROL_DESCRIPCIONES = {
    "cliente_extranjero": "Cliente extranjero que compra fruta chilena.",
    "productor": "Produce y vende fruta a packing, frigoríficos y exportadores.",
    "packing": "Compra y vende fruta, y ofrece servicios de embalaje.",
    "frigorifico": "Ofrece almacenamiento y servicios de refrigeración.",
    "exportador": "Compra fruta local y la exporta a clientes internacionales.",
    "transporte_extraportuario": "Transporte terrestre desde y hacia puertos.",
    "agencia_aduana": "Ofrece gestión documental y trámites aduaneros.",
    "servicio_extraportuario": "Servicios logísticos portuarios y externos.",
}

# =========================================================
# 🧾 FORMULARIO DE REGISTRO
# =========================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    """Permite crear una nueva cuenta según tipo y rol."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        empresa = request.form.get("empresa", "").strip()
        tipo = request.form.get("tipo", "").strip()
        rol = request.form.get("rol", "").strip()

        # Validación de campos vacíos
        if not email or not password or not empresa:
            flash(t("Completa todos los campos obligatorios.", "Please fill all required fields.", "請填寫所有必填欄位"), "error")
            return redirect(url_for("register"))

        # Validación de tipo
        if tipo not in TIPOS_DISPONIBLES:
            flash(t("Tipo de usuario inválido.", "Invalid user type.", "無效的使用者類型"), "error")
            return redirect(url_for("register"))

        # Validación de rol permitido
        roles_validos = TIPOS_DISPONIBLES[tipo]
        if rol not in roles_validos:
            flash(t("Rol no permitido para este tipo de usuario.", "Role not allowed for this type.", "角色與類型不符"), "error")
            return redirect(url_for("register"))

        # Verificación de duplicados
        if get_user(email):
            flash(t("El usuario ya existe.", "User already exists.", "使用者已存在"), "warning")
            return redirect(url_for("login"))

        # Crear usuario
        descripcion = ROL_DESCRIPCIONES.get(rol, "")
        USERS[email] = {
            "email": email,
            "password": password,
            "rol": rol,
            "tipo": tipo,
            "empresa": empresa,
            "descripcion": descripcion,
            "items": [],
            "carrito": [],
        }

        flash(t("Usuario registrado correctamente.", "User registered successfully.", "註冊成功"), "success")
        return redirect(url_for("login"))

    # Render normal del formulario
    return render_template(
        "register.html",
        tipos=TIPOS_DISPONIBLES,
        titulo=t("Registro de Usuario", "User Registration", "用戶註冊"),
    )

# =========================================================
# 💡 DATOS AUXILIARES PARA FORMULARIO (AJAX)
# =========================================================
@app.route("/roles_por_tipo/<tipo>")
def roles_por_tipo(tipo):
    """Devuelve roles válidos según el tipo (para dropdown dinámico)."""
    tipo = tipo.strip().lower()
    if tipo not in TIPOS_DISPONIBLES:
        return jsonify({"roles": []})
    return jsonify({"roles": TIPOS_DISPONIBLES[tipo]})

# =========================================================
# 🧠 PERMISOS POR ROL (QUIÉN PUEDE PUBLICAR O VER)
# =========================================================
def puede_publicar(rol: str, tipo_pub: str) -> bool:
    """Determina si el usuario puede publicar cierto tipo."""
    if rol == "cliente_extranjero":
        return False
    if tipo_pub == "servicio" and rol in ["transporte_extraportuario", "agencia_aduana", "servicio_extraportuario"]:
        return True
    if tipo_pub in ["oferta", "demanda"] and rol in ["productor", "packing", "frigorifico", "exportador"]:
        return True
    return False

def puede_ver_publicacion(rol_origen: str, rol_destino: str, tipo: str) -> bool:
    """Controla visibilidad entre roles."""
    # Clientes extranjeros solo ven ofertas
    if rol_origen == "cliente_extranjero" and tipo == "oferta":
        return True

    # Compraventa entre productores, packings, frigoríficos y exportadores
    if rol_origen in ["productor", "packing", "frigorifico", "exportador"]:
        return rol_destino in ["productor", "packing", "frigorifico", "exportador"]

    # Servicios entre agencias, transporte, extraportuarios, frigoríficos, packings
    if rol_origen in ["agencia_aduana", "transporte_extraportuario", "servicio_extraportuario"]:
        return rol_destino in ["agencia_aduana", "transporte_extraportuario", "servicio_extraportuario", "frigorifico", "packing"]

    return False

# =========================================================
# 🧩 RUTA DEMO: SELECCIÓN DE TIPO DE REGISTRO
# =========================================================
@app.route("/register_router")
def register_router():
    """Pantalla inicial para elegir tipo de registro."""
    return render_template(
        "register_router.html",
        tipos=list(TIPOS_DISPONIBLES.keys()),
        titulo=t("Seleccionar tipo de registro", "Select registration type", "選擇註冊類型"),
    )
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 CORREGIDO FINAL) — PARTE 3/4
# Dashboard · Publicaciones · Carrito · Ocultar / Restaurar
# =========================================================

# =========================================================
# 🧭 DASHBOARD PRINCIPAL (común)
# =========================================================
@app.route("/dashboard")
def dashboard():
    """Panel principal de usuario (según su rol y publicaciones visibles)."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    if not user:
        flash(t("Usuario no encontrado.", "User not found.", "找不到使用者"), "error")
        return redirect(url_for("logout"))

    # Filtrado de publicaciones
    filtro = request.args.get("filtro", "oferta").lower()
    if filtro not in ["oferta", "demanda", "servicio"]:
        filtro = "oferta"

    visibles = [
        p for p in PUBLICACIONES
        if p["tipo"] == filtro
        and puede_ver_publicacion(user["rol"], p["rol"], p["tipo"])
        and p["id"] not in OCULTOS.get(user["email"], [])
    ]
    visibles.sort(key=lambda x: x.get("fecha", ""), reverse=True)

    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda x: x.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard.html",
        user=user,
        filtro=filtro,
        publicaciones=visibles,
        propias=propias,
        titulo=t("Panel de Usuario", "User Dashboard", "使用者主頁"),
    )

# =========================================================
# 🧾 CREAR NUEVA PUBLICACIÓN
# =========================================================
@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite crear una nueva publicación según el rol."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para publicar.", "You must log in to post.", "您必須登入以發布"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)

    if request.method == "POST":
        tipo_pub = request.form.get("tipo_pub", "").lower().strip()
        subtipo = request.form.get("subtipo", "").strip()
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip() or "Consultar"

        if tipo_pub not in ["oferta", "demanda", "servicio"]:
            flash(t("Tipo de publicación inválido.", "Invalid post type.", "無效的發布類型"), "error")
            return redirect(url_for("publicar"))

        if not producto or not descripcion:
            flash(t("Completa todos los campos requeridos.", "Complete all required fields.", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        if not puede_publicar(user["rol"], tipo_pub):
            flash(t("No tienes permiso para publicar este tipo.", "You cannot publish this type.", "無權限發布此類別"), "error")
            return redirect(url_for("dashboard"))

        nueva_pub = {
            "id": f"pub_{uuid4().hex[:8]}",
            "usuario": user["email"],
            "empresa": user["empresa"],
            "rol": user["rol"],
            "tipo": tipo_pub,
            "producto": producto,
            "precio": precio,
            "descripcion": f"{subtipo.upper()} — {descripcion}" if subtipo else descripcion,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        PUBLICACIONES.append(nueva_pub)
        flash(t("Publicación creada correctamente.", "Post created successfully.", "發布成功"), "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "publicar.html",
        titulo=t("Nueva Publicación", "New Post", "新增發布")
    )

# =========================================================
# 🧹 ELIMINAR PUBLICACIÓN
# =========================================================
@app.route("/publicacion/eliminar/<pub_id>", methods=["POST", "GET"])
def eliminar_publicacion(pub_id):
    """Permite eliminar publicaciones propias."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    global PUBLICACIONES
    antes = len(PUBLICACIONES)
    PUBLICACIONES = [
        p for p in PUBLICACIONES if not (p["id"] == pub_id and p["usuario"] == user["email"])
    ]
    despues = len(PUBLICACIONES)

    if antes > despues:
        flash(t("Publicación eliminada correctamente.", "Post deleted successfully.", "發布已刪除"), "success")
    else:
        flash(t("No se encontró la publicación o no tienes permiso.", "Not found or unauthorized.", "未找到或無權限"), "error")

    return redirect(url_for("dashboard"))

# =========================================================
# 👁️‍🗨️ OCULTAR / RESTAURAR PUBLICACIONES
# =========================================================
@app.route("/ocultar/<pub_id>")
def ocultar_publicacion(pub_id):
    """Permite ocultar temporalmente una publicación visible."""
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("login"))

    ocultos = OCULTOS.setdefault(user_email, [])
    if pub_id not in ocultos:
        ocultos.append(pub_id)
        flash(t("Publicación ocultada.", "Item hidden.", "項目已隱藏"), "info")
    return redirect(url_for("dashboard"))

@app.route("/restablecer_ocultos")
def restablecer_ocultos():
    """Restaura todas las publicaciones ocultas."""
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("login"))
    OCULTOS[user_email] = []
    flash(t("Publicaciones restauradas.", "Items restored.", "項目已恢復"), "success")
    return redirect(url_for("dashboard"))

# =========================================================
# 🛒 CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito")
def carrito():
    """Muestra el carrito de compras actual."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para ver el carrito.", "You must log in to view the cart.", "您必須登入以檢視購物車"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    cart = user.get("carrito", [])
    if not cart:
        flash(t("Tu carrito está vacío.", "Your cart is empty.", "購物車是空的"), "info")

    return render_template("carrito.html", cart=cart, titulo=t("Carrito", "Cart", "購物車"))

@app.route("/carrito/agregar/<pub_id>")
def carrito_agregar(pub_id):
    """Agrega una publicación al carrito si no está ya agregada."""
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("login"))
    user = get_user(user_email)

    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada.", "Item not found.", "找不到項目"), "error")
        return redirect(url_for("dashboard"))

    cart = user.setdefault("carrito", [])
    if any(p["id"] == pub_id for p in cart):
        flash(t("El ítem ya está en el carrito.", "Item already in cart.", "項目已在購物車中"), "warning")
    else:
        cart.append(pub)
        flash(t("Agregado al carrito.", "Added to cart.", "已加入購物車"), "success")

    return redirect(url_for("carrito"))

@app.route("/carrito/eliminar/<pub_id>")
def carrito_eliminar(pub_id):
    """Elimina un ítem del carrito."""
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("login"))
    user = get_user(user_email)
    cart = user.get("carrito", [])
    user["carrito"] = [p for p in cart if p["id"] != pub_id]
    flash(t("Ítem eliminado del carrito.", "Item removed from cart.", "已刪除項目"), "info")
    return redirect(url_for("carrito"))

@app.route("/carrito/vaciar")
def carrito_vaciar():
    """Vacía completamente el carrito."""
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("login"))
    user = get_user(user_email)
    user["carrito"] = []
    flash(t("Carrito vaciado correctamente.", "Cart cleared.", "購物車已清空"), "success")
    return redirect(url_for("carrito"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 CORREGIDO FINAL) — PARTE 4/4
# Mensajería · Perfil · Clientes · Ayuda · Status · Run Final
# =========================================================

# =========================================================
# 💬 MENSAJERÍA INTERNA ENTRE USUARIOS
# =========================================================
MENSAJES = []


def puede_enviar_mensaje(origen: str, destino: str) -> bool:
    """Evita spam: máximo un mensaje por usuario cada 3 días."""
    now = datetime.now()
    recientes = [m for m in MENSAJES if m["origen"] == origen and m["destino"] == destino]
    if not recientes:
        return True
    ultima_fecha = datetime.strptime(recientes[-1]["fecha"], "%Y-%m-%d %H:%M")
    return (now - ultima_fecha).days >= 3


@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    """Vista de bandeja de entrada y envío de mensajes."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)

    if request.method == "POST":
        destino = request.form.get("destino", "").strip().lower()
        contenido = request.form.get("contenido", "").strip()

        if not destino or not contenido:
            flash(t("Completa todos los campos.", "Please fill all fields.", "請填寫所有欄位"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe.", "Recipient not found.", "找不到收件人"), "error")
            return redirect(url_for("mensajes"))

        if not puede_enviar_mensaje(user["email"], destino):
            flash(t(
                "Ya enviaste un mensaje a este usuario hace menos de 3 días.",
                "You already sent a message less than 3 days ago.",
                "3天內無法再次發送訊息"
            ), "warning")
            return redirect(url_for("mensajes"))

        MENSAJES.append({
            "origen": user["email"],
            "destino": destino,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        flash(t("Mensaje enviado correctamente.", "Message sent successfully.", "訊息已發送"), "success")
        return redirect(url_for("mensajes"))

    recibidos = [m for m in MENSAJES if m["destino"] == user["email"]]
    enviados = [m for m in MENSAJES if m["origen"] == user["email"]]
    recibidos.sort(key=lambda x: x["fecha"], reverse=True)
    enviados.sort(key=lambda x: x["fecha"], reverse=True)

    return render_template(
        "mensajes.html",
        user=user,
        recibidos=recibidos,
        enviados=enviados,
        titulo=t("Mensajería", "Messaging", "訊息系統"),
    )


# =========================================================
# 👤 PERFIL DE USUARIO
# =========================================================
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    """Permite editar la información del perfil."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para ver tu perfil.", "You must log in to view your profile.", "您必須登入以檢視個人資料"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)

    if request.method == "POST":
        empresa = request.form.get("empresa", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if empresa:
            user["empresa"] = empresa
        if descripcion:
            user["descripcion"] = descripcion

        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Tu Perfil", "Your Profile", "個人資料"))


# =========================================================
# 🏢 CLIENTES / EMPRESAS
# =========================================================
@app.route("/clientes")
def clientes():
    """Lista de empresas visibles por el usuario autenticado."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para ver empresas.", "You must log in to view companies.", "您必須登入以查看公司"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    visibles = []

    for _, info in USERS.items():
        if info["email"] == user["email"]:
            continue  # no mostrarte a ti mismo
        if (puede_ver_publicacion(user["rol"], info["rol"], "oferta")
                or puede_ver_publicacion(user["rol"], info["rol"], "servicio")):
            visibles.append(info)

    filtro_tipo = request.args.get("filtro", "todos").lower()
    if filtro_tipo in ["cliente", "compraventa", "servicio", "mixto", "admin"]:
        visibles = [v for v in visibles if v.get("tipo") == filtro_tipo]

    return render_template(
        "clientes.html",
        clientes=visibles,
        titulo=t("Empresas Registradas", "Registered Companies", "註冊公司")
    )


@app.route("/clientes/<email>")
def cliente_detalle(email):
    """Detalle de una empresa en particular."""
    c = get_user(email)
    if not c:
        abort(404)
    user_email = session.get("user")
    puede_mensaje = bool(user_email) and puede_enviar_mensaje(user_email, c["email"])
    return render_template(
        "cliente_detalle.html",
        c=c,
        puede_mensaje=puede_mensaje,
        titulo=c["empresa"]
    )


# =========================================================
# 📘 AYUDA Y ACERCA DE
# =========================================================
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo=t("Centro de Ayuda", "Help Center", "幫助中心"))


@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping", "About Window Shopping", "關於 Window Shopping"))


# =========================================================
# ⚙️ STATUS DEL SERVIDOR
# =========================================================
@app.route("/status")
def status():
    """Devuelve estado del servidor en formato JSON."""
    estado = {
        "usuarios": len(USERS),
        "publicaciones": len(PUBLICACIONES),
        "mensajes": len(MENSAJES),
        "idioma": session.get("lang", "es"),
        "estado": "OK ✅",
        "hora_servidor": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify(estado)


# =========================================================
# 🚀 RUN FINAL (protección por si ejecutas app.py directamente)
# =========================================================
if __name__ == "__main__":
    load_users_cache()
    print("🌐 Servidor Flask ejecutándose en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
