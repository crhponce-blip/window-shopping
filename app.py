# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.8 Base Mejorada, Parte 1/4)
# Configuración, DB, Helpers, Caché USERS, Carrito, Visibilidad, Filtros
# =========================================================

import os
import sqlite3
import uuid
from datetime import timedelta, datetime
from typing import List, Dict, Any

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

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

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# =========================================================
# 🌎 MULTI-IDIOMA (función global t)
# =========================================================
def t(es, en="", zh=""):
    """
    Traductor universal: toma texto en español y opcionalmente versiones en inglés y chino.
    Si no hay traducción disponible, devuelve el texto original en español.
    """
    lang = session.get("lang", "es")
    if lang == "en" and en:
        return en
    elif lang == "zh" and zh:
        return zh
    return es

# 🔄 NUEVO: Extensión de traducciones dinámicas
def translate_dynamic(text: str) -> str:
    """
    Traduce textos dinámicos (como publicaciones, items o nombres de campos)
    para que todo el contenido visible sea coherente con el idioma actual.
    """
    lang = session.get("lang", "es")
    if not text:
        return text
    if lang == "en":
        reemplazos = {
            "oferta": "offer", "demanda": "demand", "servicio": "service",
            "precio": "price", "empresa": "company", "producto": "product",
            "publicación": "post", "carrito": "cart"
        }
    elif lang == "zh":
        reemplazos = {
            "oferta": "报价", "demanda": "需求", "servicio": "服务",
            "precio": "价格", "empresa": "公司", "producto": "产品",
            "publicación": "发布", "carrito": "购物车"
        }
    else:
        return text

    for es_word, tr_word in reemplazos.items():
        text = text.replace(es_word, tr_word)
    return text

app.jinja_env.globals.update(t=t, translate_dynamic=translate_dynamic)


# =========================================================
# 🧩 TIPOS Y ROLES
# =========================================================
TIPOS_VALIDOS = {"compras", "servicios", "mixto", "compraventa"}

ROLES_POR_TIPO: Dict[str, List[str]] = {
    "compras": ["Cliente extranjero"],
    "servicios": ["Agencia de aduana", "Transporte", "Extraportuario", "Packing", "Frigorífico"],
    "compraventa": ["Productor(planta)", "Packing", "Frigorífico", "Exportador"],
    "mixto": ["Packing", "Frigorífico"],
}


# =========================================================
# 🗄️ BASE DE DATOS (SQLite)
# =========================================================
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    """Crea la tabla de usuarios si no existe."""
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
            pais TEXT,
            rut_doc TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)
    conn.commit()
    conn.close()

def migrate_add_column(colname: str):
    """Agrega una columna nueva si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {colname} TEXT")
        conn.commit()
        print(f"🛠️ Migración: columna '{colname}' agregada.")
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

def migrate_add_rut_doc():
    migrate_add_column("rut_doc")

def migrate_add_contact_fields():
    migrate_add_column("direccion")
    migrate_add_column("telefono")

def get_user(email: str):
    """Obtiene un usuario por email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users() -> List[sqlite3.Row]:
    """Devuelve todos los usuarios existentes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(email, password_hashed, empresa, rol, tipo, pais,
             rut_doc=None, direccion=None, telefono=None):
    """Agrega un nuevo usuario a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (email, password, empresa, rol, tipo, pais, rut_doc, direccion, telefono)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, password_hashed, empresa, rol, tipo, pais, rut_doc, direccion, telefono))
        conn.commit()
        print(f"🆕 Usuario creado: {email}")
    except sqlite3.IntegrityError:
        print(f"⚠️ El usuario {email} ya existe.")
    finally:
        conn.close()

def update_user_fields(email: str, **fields):
    """Actualiza campos del usuario (empresa, rol, etc.)."""
    if not fields:
        return
    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values()) + [email]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {cols} WHERE email=?", vals)
    conn.commit()
    conn.close()
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.8 Base Mejorada, Parte 2/4)
# Autenticación, Registro, Idiomas, Errores
# =========================================================

# =========================================================
# 🔐 LOGIN / LOGOUT
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia sesión de usuario registrado."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = get_user(email)
        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user"] = email
            flash(t("Inicio de sesión correcto", "Login successful", "登入成功"), "success")
            return redirect(url_for("dashboard_ext"))

        flash(t("Credenciales inválidas", "Invalid credentials", "無效的登入資料"), "error")

    return render_template("login.html", titulo=t("Iniciar Sesión", "Login", "登入"))


@app.route("/logout")
def logout():
    """Cierra sesión y limpia variables de sesión."""
    session.clear()
    flash(t("Sesión cerrada correctamente", "Logged out successfully", "已登出"), "info")
    return redirect(url_for("home"))


# =========================================================
# 📝 REGISTRO DE USUARIOS
# =========================================================
@app.route("/register_router")
def register_router():
    """Pantalla que muestra tipos de usuario disponibles."""
    return render_template(
        "register_router.html",
        roles=ROLES_POR_TIPO,
        titulo=t("Registro", "Register", "註冊")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registra un nuevo usuario manualmente."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        empresa = request.form.get("empresa", "").strip()
        rol = request.form.get("rol", "").strip()
        tipo = request.form.get("tipo", "").strip()
        pais = request.form.get("pais", "CL").strip().upper()
        direccion = request.form.get("direccion", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not email or not password or not empresa:
            flash(
                t(
                    "Completa todos los campos obligatorios.",
                    "Complete all required fields.",
                    "請填寫所有必填欄位"
                ),
                "error"
            )
            return redirect(url_for("register"))

        if tipo not in TIPOS_VALIDOS:
            tipo = "compraventa"

        # ➕ Validación de rol según tipo
        roles_validos = ROLES_POR_TIPO.get(tipo, [])
        if rol not in roles_validos:
            flash(
                t(
                    "Rol no permitido para este tipo de usuario.",
                    "Role not allowed for this user type.",
                    "角色與類型不符"
                ),
                "error"
            )
            return redirect(url_for("register"))

        if get_user(email):
            flash(t("El usuario ya existe.", "User already exists.", "使用者已存在"), "warning")
            return redirect(url_for("login"))

        add_user(
            email=email,
            password_hashed=generate_password_hash(password),
            empresa=empresa,
            rol=rol,
            tipo=tipo,
            pais=pais,
            rut_doc=None,
            direccion=direccion,
            telefono=telefono,
        )
        load_users_cache()
        flash(t("Usuario registrado correctamente.", "User registered successfully.", "使用者已註冊"), "success")
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        tipos=TIPOS_VALIDOS,
        roles=ROLES_POR_TIPO,
        titulo=t("Registro", "Register", "註冊")
    )


# =========================================================
# 🏠 HOME
# =========================================================
@app.route("/")
def home():
    """Página principal."""
    return render_template("index.html", titulo="Window Shopping")


# =========================================================
# 🌍 GESTIÓN DE IDIOMA
# =========================================================
@app.route("/lang/<lang>")
def set_lang(lang):
    """Cambia el idioma desde el menú (por POST/GET)."""
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente", "Language updated", "語言已更新"), "info")
    else:
        flash(t("Idioma no soportado", "Unsupported language", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))


@app.route("/set_lang/<lang>")
def set_lang_get(lang):
    """Alias para cambiar idioma con /set_lang/<lang> (compatibilidad)."""
    if lang in ["es", "en", "zh"]:
        session["lang"] = lang
        flash(t("Idioma actualizado correctamente", "Language updated", "語言已更新"), "info")
    else:
        flash(t("Idioma no soportado", "Unsupported language", "不支援的語言"), "error")
    return redirect(request.referrer or url_for("home"))


# =========================================================
# ⚙️ RUTAS AUXILIARES / ERRORES
# =========================================================
@app.errorhandler(404)
def not_found_error(e):
    """Página 404 personalizada con traducción."""
    return (
        render_template(
            "404.html",
            titulo=t("Página no encontrada", "Page not found", "找不到頁面")
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(e):
    """Error interno del servidor."""
    return (
        render_template(
            "500.html",
            titulo=t("Error interno", "Internal error", "內部錯誤")
        ),
        500,
    )


# =========================================================
# 🚀 INICIALIZACIÓN AUTOMÁTICA
# =========================================================
with app.app_context():
    init_db()
    migrate_add_rut_doc()
    migrate_add_contact_fields()
    create_admin_if_missing()
    seed_demo_users()
    load_users_cache()
    print(f"✅ USERS en caché: {len(USERS)} usuarios cargados correctamente")
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.8 Base Mejorada, Parte 3/4)
# Dashboard, Carrito, Ocultos, Publicar, Eliminar
# =========================================================

# =========================================================
# 🧭 DASHBOARD PRINCIPAL
# =========================================================
PUBLICACIONES: List[Dict[str, Any]] = []

@app.route("/dashboard_ext", methods=["GET", "POST"])
def dashboard_ext():
    """Panel extendido del usuario con publicaciones y filtros por permisos."""
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    user = get_user(user_email)
    if not user:
        flash(t("Usuario no encontrado.", "User not found.", "未找到用戶"), "error")
        return redirect(url_for("logout"))

    rol = user["rol"]
    filtro = request.args.get("filtro", "oferta").lower()
    if filtro not in ["oferta", "demanda", "servicio"]:
        filtro = "oferta"

    visibles = [
        p for p in PUBLICACIONES
        if p["tipo"] == filtro
        and puede_ver_publicacion(rol, p["rol"], p["tipo"])
        and p["id"] not in get_hidden_items()
    ]
    visibles.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    propias = [p for p in PUBLICACIONES if p["usuario"] == user["email"]]
    propias.sort(key=lambda p: p.get("fecha", ""), reverse=True)

    return render_template(
        "dashboard.html",
        user=user,
        filtro=filtro,
        publicaciones=visibles,
        propias=propias,
        titulo=t("Panel de Usuario", "User Dashboard", "使用者主頁"),
    )


@app.route("/dashboard/filtro/<tipo>")
def dashboard_filtro(tipo):
    """Cambia el filtro del panel (oferta, demanda o servicio)."""
    tipo = tipo.lower()
    if tipo not in ["oferta", "demanda", "servicio"]:
        flash(t("Filtro inválido", "Invalid filter", "無效的篩選條件"), "error")
        return redirect(url_for("dashboard_ext"))
    return redirect(url_for("dashboard_ext", filtro=tipo))


# =========================================================
# 🧾 RUTA TEMPORAL — MIS PUBLICACIONES
# =========================================================
@app.route("/mis_publicaciones")
def mis_publicaciones():
    """Ruta temporal para compatibilidad con botones en dashboard/perfil."""
    flash(t("Sección en construcción.", "Section under construction.", "頁面建設中"), "info")
    return redirect(url_for("dashboard_ext"))


# =========================================================
# 🧺 CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito")
def carrito():
    user_email = session.get("user")
    if not user_email:
        flash(t("Debes iniciar sesión para ver el carrito.", "You must log in to view the cart.", "您必須登入以檢視購物車"), "error")
        return redirect(url_for("login"))

    cart = get_cart()
    if not cart:
        flash(t("Tu carrito está vacío.", "Your cart is empty.", "購物車是空的"), "info")

    return render_template("carrito.html", cart=cart, titulo=t("Carrito", "Cart", "購物車"))


@app.route("/carrito/agregar/<pub_id>", methods=["GET", "POST"])
def carrito_agregar(pub_id):
    """Agrega un ítem al carrito, evitando duplicados."""
    pub = next((p for p in PUBLICACIONES if p["id"] == pub_id), None)
    if not pub:
        flash(t("Publicación no encontrada", "Item not found", "找不到項目"), "error")
        return redirect(request.referrer or url_for("dashboard_ext"))

    add_to_cart(pub)
    flash(t("Agregado al carrito", "Added to cart", "已加入購物車"), "success")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito/eliminar/<int:index>", methods=["POST", "GET"])
def carrito_eliminar(index):
    """Elimina ítem por índice dentro del carrito."""
    if remove_from_cart(index):
        flash(t("Ítem eliminado del carrito", "Item removed from cart", "已刪除項目"), "info")
    else:
        flash(t("Ítem inexistente", "Item not found", "未找到項目"), "error")
    return redirect(url_for("carrito"))


@app.route("/carrito/vaciar", methods=["POST", "GET"])
def carrito_vaciar():
    """Vacia el carrito completo."""
    clear_cart()
    flash(t("Carrito vaciado correctamente", "Cart cleared", "購物車已清空"), "info")
    return redirect(url_for("carrito"))


# =========================================================
# 👁️‍🗨️ OCULTAR / RESTABLECER PUBLICACIONES
# =========================================================
@app.route("/ocultar/<pub_id>", methods=["POST", "GET"])
def ocultar_publicacion(pub_id):
    """Oculta temporalmente una publicación del panel."""
    hide_item(pub_id)
    flash(t("Publicación ocultada", "Item hidden", "項目已隱藏"), "info")
    return redirect(url_for("dashboard_ext"))


@app.route("/restablecer_ocultos", methods=["POST", "GET"])
def restablecer_ocultos():
    """Restaura todas las publicaciones ocultas."""
    unhide_all()
    flash(t("Publicaciones restauradas", "Items restored", "已恢復項目"), "success")
    return redirect(url_for("dashboard_ext"))


# =========================================================
# 🧾 NUEVA PUBLICACIÓN
# =========================================================
@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    """Permite a un usuario crear una publicación nueva."""
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
            flash(t("Tipo de publicación inválido", "Invalid post type", "無效的發布類型"), "error")
            return redirect(url_for("publicar"))

        if not producto or not descripcion:
            flash(t("Completa todos los campos requeridos", "Complete all required fields", "請填寫所有必填欄位"), "error")
            return redirect(url_for("publicar"))

        # ➕ Validación de permisos para publicar
        if not puede_publicar(user["rol"], tipo_pub):
            flash(t("No tienes permisos para crear este tipo de publicación.", "You are not allowed to post this type.", "無權限發布此類別"), "error")
            return redirect(url_for("dashboard_ext"))

        nueva_pub = {
            "id": f"pub_{uuid.uuid4().hex[:8]}",
            "usuario": user["email"],
            "tipo": tipo_pub,
            "rol": user["rol"],
            "empresa": user["empresa"],
            "producto": producto,
            "precio": precio,
            "descripcion": f"{subtipo.upper()} — {descripcion}" if subtipo else descripcion,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        PUBLICACIONES.append(nueva_pub)
        flash(t("Publicación creada correctamente", "Post created successfully", "發布已成功建立"), "success")
        return redirect(url_for("dashboard_ext"))

    return render_template("publicar.html", titulo=t("Nueva Publicación", "New Post", "新增發布"))


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
        flash(t("Publicación eliminada correctamente", "Post deleted successfully", "已刪除發布"), "success")
    else:
        flash(t("No se encontró la publicación o no tienes permiso", "Not found or unauthorized", "未找到或無權限"), "error")

    return redirect(url_for("dashboard_ext"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.8 Base Mejorada, Parte 4/4)
# Mensajería, Perfil, Clientes, Ayuda, Status, Run
# =========================================================

# =========================================================
# 🔄 UTILIDAD: obtener usuario desde sesión
# =========================================================
def _session_user_dict():
    """Devuelve un dict del usuario actual basado en session['user']."""
    user_email = session.get("user")
    if not user_email:
        return None
    row = get_user(user_email)
    return dict(row) if row else None


# =========================================================
# 💬 MENSAJERÍA ENTRE USUARIOS
# =========================================================
MENSAJES: List[Dict[str, Any]] = []

def puede_enviar_mensaje(origen: str, destino: str) -> bool:
    """Permite un mensaje por ítem cada 3 días entre los mismos usuarios."""
    now = datetime.now()
    recientes = [
        m for m in MENSAJES
        if m["origen"] == origen and m["destino"] == destino
    ]
    if not recientes:
        return True
    ultima_fecha = datetime.strptime(recientes[-1]["fecha"], "%Y-%m-%d %H:%M")
    return (now - ultima_fecha).days >= 3


@app.route("/mensajes", methods=["GET", "POST"])
def mensajes():
    """Sistema simple de mensajería interna."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión.", "You must log in.", "您必須登入"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        destino = request.form.get("destino", "").strip().lower()
        contenido = request.form.get("contenido", "").strip()

        if not destino or not contenido:
            flash(t("Debes completar todos los campos.", "All fields required.", "請填寫所有欄位"), "error")
            return redirect(url_for("mensajes"))

        if destino not in USERS:
            flash(t("El destinatario no existe.", "Recipient not found.", "找不到收件人"), "error")
            return redirect(url_for("mensajes"))

        # ➕ Control de frecuencia de envío
        if not puede_enviar_mensaje(user["email"], destino):
            flash(t(
                "Ya enviaste un mensaje a este usuario hace menos de 3 días.",
                "You already messaged this user less than 3 days ago.",
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
    """Visualiza o actualiza el perfil del usuario."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.", "You must log in to view your profile.", "您必須登入以檢視個人資料"), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        nueva_empresa = request.form.get("empresa", "").strip()
        nuevo_rol = request.form.get("rol", "").strip()
        nueva_dir = request.form.get("direccion", "").strip()
        nuevo_fono = request.form.get("telefono", "").strip()

        update_user_fields(
            user["email"],
            empresa=nueva_empresa or user["empresa"],
            rol=nuevo_rol or user["rol"],
            direccion=nueva_dir or user["direccion"],
            telefono=nuevo_fono or user["telefono"],
        )
        load_users_cache()
        flash(t("Perfil actualizado correctamente.", "Profile updated successfully.", "個人資料已更新"), "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user, titulo=t("Tu Perfil", "Your Profile", "個人資料"))


# =========================================================
# 🏢 CLIENTES / DETALLES
# =========================================================
def _armar_cliente_desde_users(username: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Arma un cliente para las vistas de /clientes."""
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": data.get("items", []),
        "email": data.get("email", username),
        "pais": data.get("pais", ""),
        "direccion": data.get("direccion", ""),
        "telefono": data.get("telefono", ""),
    }

@app.route("/clientes")
def clientes():
    """Lista todas las empresas visibles según el rol del usuario."""
    user = _session_user_dict()
    if not user:
        flash(t("Debes iniciar sesión para ver empresas.", "You must log in to view companies.", "您必須登入以查看公司"), "error")
        return redirect(url_for("login"))

    visibles = []
    for username, info in USERS.items():
        if info["email"] == user["email"]:
            continue  # no mostrarte a ti mismo
        if puede_ver_publicacion(user["rol"], info["rol"], "oferta") or puede_ver_publicacion(user["rol"], info["rol"], "servicio"):
            visibles.append(_armar_cliente_desde_users(username, info))

    # Filtro interactivo antes de mostrar resultados
    filtro_tipo = request.args.get("filtro", "todos").lower()
    if filtro_tipo in ["oferta", "demanda", "servicio"]:
        visibles = [v for v in visibles if v["tipo"] == filtro_tipo]

    # Paginación básica: 10 por vista
    pagina = int(request.args.get("page", 1))
    inicio = (pagina - 1) * 10
    fin = inicio + 10
    total_paginas = (len(visibles) + 9) // 10
    visibles_pagina = visibles[inicio:fin]

    return render_template(
        "clientes.html",
        clientes=visibles_pagina,
        pagina=pagina,
        total_paginas=total_paginas,
        filtro_tipo=filtro_tipo,
        titulo=t("Empresas", "Companies", "公司")
    )


@app.route("/clientes/<username>")
def cliente_detalle(username):
    """Muestra detalle individual del cliente."""
    if username not in USERS:
        abort(404)
    c = _armar_cliente_desde_users(username, USERS[username])
    puede_mensaje = False
    user = _session_user_dict()
    if user and puede_enviar_mensaje(user["email"], c["email"]):
        puede_mensaje = True
    return render_template("cliente_detalle.html", c=c, puede_mensaje=puede_mensaje, titulo=c["empresa"])


# =========================================================
# 💬 AYUDA / ACERCA / STATUS
# =========================================================
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo=t("Centro de Ayuda", "Help Center", "幫助中心"))


@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping", "About Window Shopping", "關於 Window Shopping"))


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
# 🚀 EJECUCIÓN LOCAL / DEPLOY
# =========================================================
if __name__ == "__main__":
    print("🌐 Servidor Flask ejecutándose en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
