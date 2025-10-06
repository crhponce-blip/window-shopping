# === app.py (parte 1/5) ===
import os
import uuid
from datetime import timedelta
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
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
        "usci": "US-9988-XY", "tax_id": "99-1234567"
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
    compras_vis = {
        "Packing": ["Planta", "Frigorífico"],
        "Frigorífico": ["Planta", "Packing"],
        "Exportador": ["Exportador", "Packing", "Frigorífico", "Planta"],
        "default": ["Productor", "Planta", "Packing", "Frigorífico", "Exportador"],
    }

    # --- VENTAS ---
    ventas_vis = {
        "Packing": ["Exportador", "Frigorífico", "Packing"],
        "Frigorífico": ["Packing", "Exportador"],
        "Exportador": ["Exportador", "Cliente extranjero"],
        "default": ["Exportador", "Packing", "Frigorífico", "Cliente extranjero"],
    }

    # --- SERVICIOS ---
    servicios_vis = {
        "Planta": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Packing": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Frigorífico": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
        "Exportador": ["Packing", "Frigorífico", "Transporte", "Extraportuario", "Agencia de Aduanas"],
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
# REGISTRO DE USUARIOS
# ---------------------------------------------------------
@app.route("/register_router")
def register_router():
    """Pantalla inicial de registro (elige nacionalidad y tipo)."""
    return render_template("register_router.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Formulario principal de registro (dinámico nacional/extranjero)."""
    error = None
    nacionalidad = request.args.get("nac")
    perfil_tipo = request.args.get("tipo")

    NACIONALIDAD_OPCIONES = ["nacional", "extranjero"]
    PERFIL_OPCIONES = ["compra_venta", "servicios"]
    ROLES_COMPRA_VENTA = ["Productor", "Planta", "Packing", "Frigorífico", "Exportador", "Cliente extranjero"]
    ROLES_SERVICIOS = ["Packing", "Frigorífico", "Transporte", "Agencia de Aduanas", "Extraportuario"]

    if request.method == "POST":
        nacionalidad = request.form.get("nacionalidad") or nacionalidad or "nacional"
        perfil_tipo = request.form.get("perfil_tipo") or perfil_tipo or "compra_venta"

        # Forzar cliente extranjero si aplica
        if nacionalidad == "extranjero":
            perfil_tipo = "compra_venta"

        username = (request.form.get("username", "") or "").strip().lower()
        password = (request.form.get("password", "") or "").strip()
        email = (request.form.get("email", "") or "").strip()
        telefono = (request.form.get("phone", "") or "").strip()
        direccion = (request.form.get("address", "") or "").strip()
        pais = (request.form.get("pais", "") or "").strip()
        rol = (request.form.get("rol", "") or "").strip()

        # Documentos
        rut = (request.form.get("rut", "") or "").strip() if nacionalidad == "nacional" else None
        usci = (request.form.get("usci", "") or "").strip() if nacionalidad == "extranjero" else None
        eori = (request.form.get("eori", "") or "").strip() if nacionalidad == "extranjero" else None
        tax_id = (request.form.get("tax_id", "") or "").strip() if nacionalidad == "extranjero" else None
        otros_id = (request.form.get("otros_id", "") or "").strip() if nacionalidad == "extranjero" else None

        # Archivo RUT
        rut_file_path = None
        if nacionalidad == "nacional" and "rut_file" in request.files:
            f = request.files["rut_file"]
            if f and f.filename and allowed_file(f.filename):
                fname = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
                f.save(os.path.join(UPLOAD_FOLDER, fname))
                rut_file_path = f"uploads/{fname}"

        # País por defecto
        if not pais:
            pais = "CL" if nacionalidad == "nacional" else "US"

        if not username or not password:
            error = t("Completa los campos obligatorios.", "Please fill required fields.")
        elif username in USERS:
            error = t("El usuario ya existe.", "User already exists.")
        else:
            if nacionalidad == "extranjero":
                rol = "Cliente extranjero"

            USERS[username] = {
                "password": password,
                "rol": rol,
                "perfil_tipo": perfil_tipo,
                "pais": pais,
            }
            USER_PROFILES[username] = {
                "empresa": username.split("@")[0].replace(".", " ").title(),
                "rut": rut,
                "rut_file": rut_file_path,
                "rol": rol,
                "perfil_tipo": perfil_tipo,
                "pais": pais,
                "email": email or username,
                "telefono": telefono or "",
                "direccion": direccion or "",
                "descripcion": "Nuevo perfil registrado.",
                "items": [],
                "usci": usci, "eori": eori, "tax_id": tax_id, "otros_id": otros_id
            }

            session["user"] = username
            flash(t("Registro exitoso", "Registration successful", "註冊完成"))
            return redirect(url_for("dashboard"))

    return render_template(
        "register.html",
        error=error,
        nacionalidad=nacionalidad,
        perfil_tipo=perfil_tipo,
        nacionalidad_opciones=NACIONALIDAD_OPCIONES,
        perfil_opciones=PERFIL_OPCIONES,
        roles_cv=[r for r in ROLES_COMPRA_VENTA if r != "Cliente extranjero"],
        roles_srv=ROLES_SERVICIOS,
        roles_all_cv=ROLES_COMPRA_VENTA,
    )# =========================================================
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
    Incluye un buscador avanzado para filtrar resultados.
    """
    tipo = tipo.lower()
    if tipo not in ("ventas", "compras", "servicios"):
        abort(404)

    roles_permitidos = None
    if is_logged():
        me = USERS.get(session["user"], {})
        roles_permitidos = set(targets_for(tipo, me.get("rol", "")))

    # Buscar por nombre o producto
    filtro_texto = request.args.get("q", "").lower()

    data = []
    if tipo == "servicios":
        for c in USER_PROFILES.values():
            if any(it.get("tipo") == "servicio" for it in c.get("items", [])):
                if roles_permitidos is None or c["rol"] in roles_permitidos:
                    if filtro_texto in c["empresa"].lower() or filtro_texto in c["descripcion"].lower():
                        data.append(c)
                    elif not filtro_texto:
                        data.append(c)
        tpl = "detalle_servicios.html"
    else:
        tag = "oferta" if tipo == "ventas" else "demanda"
        for c in USER_PROFILES.values():
            if any(it.get("tipo") == tag for it in c.get("items", [])):
                if roles_permitidos is None or c["rol"] in roles_permitidos:
                    if filtro_texto in c["empresa"].lower() or filtro_texto in c["descripcion"].lower():
                        data.append(c)
                    elif not filtro_texto:
                        data.append(c)
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
# PERFIL PERSONAL (Editar datos + Agregar ítems)
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

    return render_template("perfil.html", perfil=ViewObj(prof), mensaje=mensaje)


# =========================================================
# CARRITO DE COMPRAS
# =========================================================
@app.route("/carrito", methods=["GET", "POST"])
def carrito():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear":
            clear_cart()
            flash(t("Carrito vaciado", "Cart cleared"))
            return redirect(url_for("carrito"))
        if action and action.startswith("remove:"):
            idx = action.split(":", 1)[1]
            if remove_from_cart(idx):
                flash(t("Ítem eliminado", "Item removed"))
            return redirect(url_for("carrito"))
    return render_template("carrito.html", cart=get_cart())
# =========================================================
# AYUDA / SOPORTE
# =========================================================
@app.route("/ayuda")
def ayuda():
    temas = [
        {"titulo": "¿Cómo registrarme?", "detalle": "Selecciona tu tipo de usuario (nacional o extranjero) y completa los campos obligatorios. Puedes adjuntar tu RUT o documento de identificación."},
        {"titulo": "¿Cómo agregar productos o servicios?", "detalle": "Desde tu perfil, selecciona 'Agregar ítem' y completa la información. Podrás subir ofertas, demandas o servicios."},
        {"titulo": "¿Qué es el carrito?", "detalle": "Permite guardar productos o servicios que desees revisar más tarde o contactar a sus empresas."},
        {"titulo": "Idiomas disponibles", "detalle": "El sitio puede visualizarse en Español, Inglés o Chino Mandarín."},
    ]
    return render_template("ayuda.html", temas=temas)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/lang/<lang>")
def cambiar_idioma(lang):
    if lang not in ("es", "en", "zh"):
        abort(404)
    session["lang"] = lang
    flash(t("Idioma cambiado", "Language changed", "語言已變更"))
    return redirect(request.referrer or url_for("home"))


# =========================================================
# ERRORES PERSONALIZADOS
# =========================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        code=404,
        message=t("Página no encontrada", "Page not found", "找不到頁面"),
    ), 404


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        code=500,
        message=t("Error interno", "Internal server error", "內部伺服器錯誤"),
    ), 500

# =========================================================
# EJECUCIÓN PRINCIPAL
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
