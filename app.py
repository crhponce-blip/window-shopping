# === app.py (completo y corregido) ===
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
# RUTAS PRINCIPALES Y AUTENTICACIÓN
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = USERS.get(email)
        if not user or user["password"] != password:
            flash("Correo o contraseña incorrectos", "error")
            return redirect(url_for("login"))

        session["user"] = email
        session["rol"] = user["rol"]
        flash("Inicio de sesión exitoso", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        rol = request.form.get("rol")
        perfil_tipo = request.form.get("perfil_tipo")

        if email in USERS:
            flash("Este correo ya está registrado", "error")
            return redirect(url_for("register"))

        USERS[email] = {"password": password, "rol": rol, "perfil_tipo": perfil_tipo, "pais": "CL"}
        USER_PROFILES[email] = {
            "empresa": request.form.get("empresa"),
            "rut": request.form.get("rut"),
            "rol": rol,
            "perfil_tipo": perfil_tipo,
            "pais": "CL",
            "email": email,
            "telefono": request.form.get("telefono"),
            "direccion": request.form.get("direccion"),
            "descripcion": request.form.get("descripcion"),
            "items": [],
        }

        flash("Registro exitoso. Inicia sesión para continuar.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if not is_logged():
        return redirect(url_for("login"))

    user_email = session.get("user")
    profile = USER_PROFILES.get(user_email, {})
    rol = profile.get("rol")

    return render_template("dashboard.html", profile=profile, rol=rol)
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

    filtro_texto = (request.args.get("q", "") or "").lower().strip()
    data = []

    # Caso especial: Cliente extranjero en "compras" ve exportadores (oferta)
    if tipo == "compras" and my_rol == "Cliente extranjero":
        tag = "oferta"
        forced_roles = {"Exportador"}
        for uname, c in USER_PROFILES.items():
            if c.get("rol") in forced_roles and any(it.get("tipo") == tag for it in c.get("items", [])):
                if not filtro_texto or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion", "").lower()):
                    item = c.copy()
                    item["username"] = uname
                    data.append(item)
        return render_template("detalle_compras.html", data=wrap_list(data), tipo=tipo, query=filtro_texto)

    # --- Servicios ---
    if tipo == "servicios":
        for uname, c in USER_PROFILES.items():
            if any(it.get("tipo") == "servicio" for it in c.get("items", [])):
                if (roles_permitidos is None) or (c["rol"] in roles_permitidos):
                    if not filtro_texto or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion", "").lower()):
                        item = c.copy()
                        item["username"] = uname
                        data.append(item)
        return render_template("detalle_servicio.html", data=wrap_list(data), tipo=tipo, query=filtro_texto)

    # --- Compras y Ventas ---
    if tipo == "compras":
        tag = "oferta"      # comprador ve lo que se ofrece
    elif tipo == "ventas":
        tag = "demanda"     # vendedor ve lo que se solicita
    else:
        tag = "servicio"

    # Restricciones por rol
    if tipo == "compras" and my_rol in ("Productor", "Planta"):
        flash(t("Tu rol no puede comprar fruta. Revisa Ventas o Servicios.",
                "Your role cannot buy fruit. Check Sales or Services.",
                "你的角色不能購買水果。請查看銷售或服務。"))

    for uname, c in USER_PROFILES.items():
        if any(it.get("tipo") == tag for it in c.get("items", [])):
            if (roles_permitidos is None) or (c["rol"] in roles_permitidos):
                if not filtro_texto or filtro_texto in c["empresa"].lower() or filtro_texto in (c.get("descripcion", "").lower()):
                    item = c.copy()
                    item["username"] = uname
                    data.append(item)

    tpl = "detalle_ventas.html" if tipo == "ventas" else "detalle_compras.html"
    return render_template(tpl, data=wrap_list(data), tipo=tipo, query=filtro_texto)


# =========================================================
# MENSAJERÍA ENTRE EMPRESAS
# =========================================================
@app.route("/enviar_mensaje/<empresa>", methods=["GET", "POST"])
def enviar_mensaje(empresa):
    if not is_logged():
        return redirect(url_for("login"))

    if request.method == "POST":
        mensaje = request.form.get("mensaje")
        if not mensaje:
            flash("Debes escribir un mensaje antes de enviarlo.", "error")
            return redirect(request.url)

        flash("Mensaje enviado correctamente.", "success")
        return redirect(url_for("dashboard"))

    return render_template("mensaje_enviado.html", empresa=empresa)
# =========================================================
# CARRITO DE COMPRAS / SERVICIOS
# =========================================================

def get_cart():
    """Obtiene el carrito del usuario actual desde la sesión."""
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]


def save_cart(cart):
    """Guarda el carrito en la sesión."""
    session["cart"] = cart


@app.route("/carrito")
def carrito():
    """Muestra los ítems agregados al carrito."""
    if not is_logged():
        flash("Debes iniciar sesión para ver el carrito.", "error")
        return redirect(url_for("login"))

    cart = get_cart()
    return render_template("carrito.html", cart=cart)


@app.route("/cart_add", methods=["POST"])
def cart_add():
    """Agrega un elemento al carrito (ventas, compras o servicios)."""
    if not is_logged():
        flash("Debes iniciar sesión para agregar elementos al carrito.", "error")
        return redirect(url_for("login"))

    item = {
        "empresa": request.form.get("empresa"),
        "descripcion": request.form.get("descripcion"),
        "tipo": request.form.get("tipo"),
        "rol": request.form.get("rol"),
        "contacto": request.form.get("contacto"),
    }

    cart = get_cart()
    cart.append(item)
    save_cart(cart)
    flash("Elemento agregado al carrito.", "success")
    return redirect(request.referrer or url_for("carrito"))


@app.route("/cart_remove/<int:index>", methods=["POST"])
def cart_remove(index):
    """Elimina un elemento del carrito según su posición."""
    if not is_logged():
        return redirect(url_for("login"))

    cart = get_cart()
    if 0 <= index < len(cart):
        removed = cart.pop(index)
        save_cart(cart)
        flash(f"Se eliminó '{removed['empresa']}' del carrito.", "success")
    else:
        flash("Ítem no encontrado en el carrito.", "error")
    return redirect(url_for("carrito"))


@app.route("/cart_clear", methods=["POST"])
def cart_clear():
    """Vacía completamente el carrito."""
    if not is_logged():
        return redirect(url_for("login"))

    session.pop("cart", None)
    flash("Carrito vaciado correctamente.", "success")
    return redirect(url_for("carrito"))
# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def is_logged():
    """Verifica si el usuario está logeado."""
    return "user" in session


def wrap_list(data):
    """Asegura que los datos sean siempre una lista."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        return []


def t(es, en=None, zh=None):
    """
    Traductor simple por idioma.
    - Español (default)
    - Inglés
    - Chino
    """
    idioma = session.get("lang", "es")
    if idioma == "en" and en:
        return en
    elif idioma == "zh" and zh:
        return zh
    return es


# =========================================================
# RUTAS DE IDIOMA Y MENSAJES
# =========================================================

@app.route("/set_lang/<lang>")
def set_lang(lang):
    """Permite cambiar el idioma de la interfaz."""
    if lang not in ("es", "en", "zh"):
        lang = "es"
    session["lang"] = lang
    flash(f"Idioma cambiado a {lang.upper()}", "success")
    return redirect(request.referrer or url_for("home"))


@app.errorhandler(404)
def not_found(error):
    """Página personalizada para error 404."""
    return render_template("404.html"), 404


# =========================================================
# EJECUCIÓN LOCAL
# =========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


