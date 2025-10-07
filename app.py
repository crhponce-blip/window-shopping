from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
import os
import json

app = Flask(__name__)
app.secret_key = "clave_secreta"

# =========================================================
# CONFIGURACIÓN DE RUTAS Y CARPETAS
# =========================================================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =========================================================
# FUNCIONES DE IDIOMA Y SESIÓN
# =========================================================
def t(es, en, zh):
    lang = session.get("lang", "es")
    if lang == "en":
        return en
    elif lang == "zh":
        return zh
    return es

def is_logged():
    return "user" in session

def current_user_profile():
    user = session.get("user")
    if user and user in USER_PROFILES:
        return USER_PROFILES[user]
    return None

# =========================================================
# ESTRUCTURAS DE DATOS SIMULADAS (TEMPORALES)
# =========================================================
USERS = {
    "admin@example.com": {"password": "1234", "rol": "exportador"}
}

USER_PROFILES = {
    "admin@example.com": {
        "nombre": "Admin Exportaciones",
        "rol": "exportador",
        "descripcion": "Exportador de frutas frescas chilenas hacia Asia y Norteamérica.",
        "items": [
            {"tipo": "oferta", "producto": "Cereza", "variedad": "Regina", "cantidad": "500", "bulto": "cajas", "origen": "Curicó"},
            {"tipo": "servicio", "servicio": "Transporte frigorífico", "capacidad": "20 toneladas", "ubicacion": "Talca"}
        ]
    }
}

# =========================================================
# FUNCIONES DE CARRITO
# =========================================================
def get_cart():
    return session.get("cart", [])

def add_to_cart(item):
    cart = get_cart()
    cart.append(item)
    session["cart"] = cart

def clear_cart():
    session.pop("cart", None)

def remove_from_cart(index):
    cart = get_cart()
    try:
        idx = int(index)
        cart.pop(idx)
        session["cart"] = cart
        return True
    except Exception:
        return False
# =========================================================
# RUTA PRINCIPAL / LANDING
# =========================================================
@app.route("/")
def home():
    return render_template("landing.html")

# =========================================================
# LOGIN / LOGOUT
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")
        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = email
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"))
            return redirect(url_for("dashboard"))
        else:
            flash(t("Credenciales inválidas", "Invalid credentials", "憑證無效"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash(t("Sesión cerrada", "Logged out", "登出"))
    return redirect(url_for("home"))

# =========================================================
# REGISTRO DE USUARIO
# =========================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "")
        nombre = request.form.get("nombre", "")
        descripcion = request.form.get("descripcion", "")
        tipo = request.form.get("tipo", "")
        subtipo = request.form.get("subtipo", "")
        nacionalidad = request.form.get("nacionalidad", "")
        doc = request.files.get("documento")

        if not email or not password or not rol:
            flash(t("Faltan datos obligatorios", "Missing required fields", "缺少必要欄位"))
            return redirect(url_for("register"))

        if email in USERS:
            flash(t("El usuario ya existe", "User already exists", "使用者已存在"))
            return redirect(url_for("register"))

        USERS[email] = {"password": password, "rol": rol}
        USER_PROFILES[email] = {
            "nombre": nombre,
            "rol": rol,
            "descripcion": descripcion,
            "tipo": tipo,
            "subtipo": subtipo,
            "nacionalidad": nacionalidad,
            "items": [],
        }

        if doc:
            path = os.path.join(app.config["UPLOAD_FOLDER"], doc.filename)
            doc.save(path)

        flash(t("Usuario registrado correctamente", "User registered successfully", "使用者成功註冊"))
        return redirect(url_for("login"))

    return render_template("register.html")

# =========================================================
# PANEL PRINCIPAL (DASHBOARD)
# =========================================================
@app.route("/dashboard")
def dashboard():
    if not is_logged():
        return redirect(url_for("login"))
    prof = current_user_profile()
    return render_template("dashboard.html", profile=prof)

# =========================================================
# CAMBIO DE IDIOMA
# =========================================================
@app.route("/lang/<lang>")
def cambiar_idioma(lang):
    if lang not in ("es", "en", "zh"):
        abort(404)
    session["lang"] = lang
    flash(t("Idioma cambiado", "Language changed", "語言已變更"))
    return redirect(request.referrer or url_for("home"))
# =========================================================
# CLIENTES (vista con filtros)
# =========================================================
@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if not is_logged():
        return redirect(url_for("login"))

    prof = current_user_profile()
    if not prof:
        abort(404)

    filtro = request.args.get("filtro", "ventas")
    data = []

    # Ejemplo simple: simulamos la carga según el filtro
    for user, p in USER_PROFILES.items():
        if user == session["user"]:
            continue  # omitir perfil propio

        # Lógica de filtro básica (luego se afina según tus reglas)
        if filtro == "ventas" and p["rol"] in ["exportador", "packing", "frigorífico"]:
            data.append({**p, "username": user})
        elif filtro == "compras" and p["rol"] in ["packing", "exportador", "frigorífico"]:
            data.append({**p, "username": user})
        elif filtro == "servicios" and p["rol"] in ["transporte", "aduana", "extraportuario"]:
            data.append({**p, "username": user})

    return render_template("clientes.html", perfil=prof, filtro=filtro, data=data)

# =========================================================
# AGREGAR ÍTEM AL PERFIL (compra, venta o servicio)
# =========================================================
@app.route("/agregar_item", methods=["POST"])
def agregar_item():
    if not is_logged():
        return redirect(url_for("login"))

    prof = current_user_profile()
    if not prof:
        abort(404)

    tipo = request.form.get("tipo")
    subtipo = request.form.get("subtipo")
    producto = request.form.get("producto")
    servicio = request.form.get("servicio")
    cantidad = request.form.get("cantidad")
    bulto = request.form.get("bulto")
    origen = request.form.get("origen")
    precio_caja = request.form.get("precio_caja")
    precio_kilo = request.form.get("precio_kilo")

    nuevo_item = {
        "tipo": tipo,
        "subtipo": subtipo,
        "producto": producto,
        "servicio": servicio,
        "cantidad": cantidad,
        "bulto": bulto,
        "origen": origen,
        "precio_caja": precio_caja,
        "precio_kilo": precio_kilo,
    }

    prof.setdefault("items", []).append(nuevo_item)
    flash(t("Ítem agregado correctamente", "Item added successfully", "已成功加入項目"))
    return redirect(url_for("dashboard"))

# =========================================================
# CARRITO (visualización y acciones)
# =========================================================
@app.route("/carrito", methods=["GET", "POST"])
def carrito():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear":
            clear_cart()
            flash(t("Carrito vaciado", "Cart cleared", "購物車已清空"))
            return redirect(url_for("carrito"))
        if action and action.startswith("remove:"):
            idx = action.split(":", 1)[1]
            if remove_from_cart(idx):
                flash(t("Ítem eliminado", "Item removed", "項目已刪除"))
            return redirect(url_for("carrito"))

    return render_template("carrito.html", cart=get_cart())

# =========================================================
# AYUDA / SOPORTE
# =========================================================
@app.route("/ayuda")
def ayuda():
    temas = [
        {"titulo": "¿Cómo registrarme?", "detalle": "Selecciona tu tipo de usuario (nacional o extranjero) y completa los campos obligatorios."},
        {"titulo": "¿Cómo agregar productos o servicios?", "detalle": "Desde tu panel selecciona 'Agregar ítem'."},
        {"titulo": "¿Qué es el carrito?", "detalle": "Permite guardar productos o servicios para contacto posterior."},
        {"titulo": "Idiomas disponibles", "detalle": "Español, Inglés y Chino Mandarín."},
    ]
    return render_template("ayuda.html", temas=temas)

# =========================================================
# ELIMINAR ÍTEM DESDE MI PANEL
# =========================================================
@app.route("/item_delete", methods=["POST"])
def item_delete():
    if not is_logged():
        return redirect(url_for("login"))
    prof = current_user_profile()
    if not prof:
        abort(404)
    try:
        idx = int(request.form.get("idx", "-1"))
    except:
        idx = -1
    items = prof.get("items", [])
    if 0 <= idx < len(items):
        items.pop(idx)
        prof["items"] = items
        flash(t("Ítem eliminado del perfil", "Item removed from profile", "已從檔案刪除"))
    else:
        flash(t("No se pudo eliminar el ítem", "Item could not be removed", "無法刪除項目"))
    return redirect(url_for("dashboard"))

# =========================================================
# RESTABLECER CONTRASEÑA (flujo básico)
# =========================================================
@app.route("/password_reset/request", methods=["GET", "POST"])
def password_reset_request():
    msg = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if email in USERS:
            session["pwd_reset_user"] = email
            flash(t("Enlace de restablecimiento enviado (demo).", "Reset link sent (demo).", "已發送重設連結（示範）"))
            return redirect(url_for("password_reset_form"))
        else:
            msg = t("El usuario no existe", "User not found", "用戶不存在")
    return render_template("password_reset_request.html", msg=msg)

@app.route("/password_reset/reset", methods=["GET", "POST"])
def password_reset_form():
    msg = None
    email = session.get("pwd_reset_user")
    if not email:
        flash(t("Primero solicita el enlace de restablecimiento.", "Request the reset link first.", "請先申請重設連結"))
        return redirect(url_for("password_reset_request"))
    if request.method == "POST":
        p1 = request.form.get("p1", "")
        p2 = request.form.get("p2", "")
        if not p1 or p1 != p2:
            msg = t("Las contraseñas no coinciden.", "Passwords do not match.", "密碼不一致")
        else:
            USERS[email]["password"] = p1
            flash(t("Contraseña actualizada", "Password updated", "密碼已更新"))
            session.pop("pwd_reset_user", None)
            return redirect(url_for("login"))
    return render_template("password_reset_form.html", msg=msg)

# =========================================================
# ERRORES PERSONALIZADOS
# =========================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, message=t("Página no encontrada", "Page not found", "找不到頁面")), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message=t("Error interno del servidor", "Internal server error", "內部伺服器錯誤")), 500

# =========================================================
# EJECUCIÓN LOCAL
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
