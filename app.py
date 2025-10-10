# =========================
# app.py — Parte 1/3
# Base estable: Config, i18n, sesión, semillas, auth, stubs seguros
# =========================
import os
import uuid
from datetime import timedelta
from typing import List, Dict, Any, Optional


from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, abort, flash, send_from_directory
)


# ---------------------------------------------------------
# CONFIGURACIÓN BÁSICA
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.permanent_session_lifetime = timedelta(days=14)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}




def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT




# ---------------------------------------------------------
# I18N / MULTI-IDIOMA (ES / EN / ZH)
# ---------------------------------------------------------
def is_logged() -> bool:
    return "user" in session




def t(es: str, en: str, zh: Optional[str] = None) -> str:
    """Devuelve texto según idioma de sesión."""
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
        LANGS=[("es", "ES"), ("en", "EN"), ("zh", "中文")],
        is_logged=is_logged
    )




@app.route("/set_lang/<lang>")
def set_lang(lang):
    """Cambia el idioma de la sesión (endpoint único)."""
    session["lang"] = lang if lang in ("es", "en", "zh") else "es"
    return redirect(request.referrer or url_for("home"))




# ---------------------------------------------------------
# SEMILLAS: USUARIOS / PERFILES / PUBLICACIONES
# (Consolidado y consistente; evita duplicados)
# ---------------------------------------------------------


# Semillas de acceso rápido (login por email o username)
USERS: Dict[str, Dict[str, Any]] = {
    # ---- Compraventa nacionales ----
    "productor1@demo.cl": {"password": "1234", "rol": "Productor(planta)", "tipo": "compraventa", "empresa": "Productores del Valle SpA", "pais": "CL"},
    "productor2@demo.cl": {"password": "1234", "rol": "Productor(planta)", "tipo": "compraventa", "empresa": "Agro Cordillera Ltda.", "pais": "CL"},


    "packingcv1@demo.cl": {"password": "1234", "rol": "Packing", "tipo": "compraventa", "empresa": "Packing Maule SpA", "pais": "CL"},
    "packingcv2@demo.cl": {"password": "1234", "rol": "Packing", "tipo": "compraventa", "empresa": "Packing Limarí Ltda.", "pais": "CL"},


    "frigorificocv1@demo.cl": {"password": "1234", "rol": "Frigorífico", "tipo": "compraventa", "empresa": "Frío Centro SpA", "pais": "CL"},
    "frigorificocv2@demo.cl": {"password": "1234", "rol": "Frigorífico", "tipo": "compraventa", "empresa": "Frío Pacífico Ltda.", "pais": "CL"},


    "export1@demo.cl": {"password": "1234", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora Andes SpA", "pais": "CL"},
    "export2@demo.cl": {"password": "1234", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora del Pacífico Ltda.", "pais": "CL"},


    # ---- Servicios nacionales ----
    "packingserv1@demo.cl": {"password": "1234", "rol": "Packing", "tipo": "servicios", "empresa": "PackSmart Servicios", "pais": "CL"},
    "packingserv2@demo.cl": {"password": "1234", "rol": "Packing", "tipo": "servicios", "empresa": "PackPro Services", "pais": "CL"},


    "frigorificoserv1@demo.cl": {"password": "1234", "rol": "Frigorífico", "tipo": "servicios", "empresa": "FríoPort Servicios", "pais": "CL"},
    "frigorificoserv2@demo.cl": {"password": "1234", "rol": "Frigorífico", "tipo": "servicios", "empresa": "Frío Andino Servicios", "pais": "CL"},


    "aduana1@demo.cl": {"password": "1234", "rol": "Agencia de aduana", "tipo": "servicios", "empresa": "Agencia Andes", "pais": "CL"},
    "aduana2@demo.cl": {"password": "1234", "rol": "Agencia de aduana", "tipo": "servicios", "empresa": "Aduanas Express", "pais": "CL"},


    "extraport1@demo.cl": {"password": "1234", "rol": "Extraportuario", "tipo": "servicios", "empresa": "Servicios Extraport Valpo", "pais": "CL"},
    "extraport2@demo.cl": {"password": "1234", "rol": "Extraportuario", "tipo": "servicios", "empresa": "Extraport San Antonio", "pais": "CL"},


    "transporte1@demo.cl": {"password": "1234", "rol": "Transporte", "tipo": "servicios", "empresa": "Transporte Global", "pais": "CL"},
    "transporte2@demo.cl": {"password": "1234", "rol": "Transporte", "tipo": "servicios", "empresa": "Ruta Andina", "pais": "CL"},


    # ---- Mixtos (Packing y Frigorífico) ----
    "packingmix1@demo.cl": {"password": "1234", "rol": "Packing", "tipo": "mixto", "empresa": "Packing Integral BioBio", "pais": "CL"},
    "frigorificomix1@demo.cl": {"password": "1234", "rol": "Frigorífico", "tipo": "mixto", "empresa": "Frigorífico Integral del Maule", "pais": "CL"},


    # ---- Clientes extranjeros (compras/demanda) ----
    "clienteusa1@ext.com": {"password": "1234", "rol": "Cliente extranjero", "tipo": "compras", "empresa": "Importadora Asia Ltd.", "pais": "US"},
    "clienteusa2@ext.com": {"password": "1234", "rol": "Cliente extranjero", "tipo": "compras", "empresa": "Gourmet Asia Ltd.", "pais": "US"},


    # ---- Aliases (usernames simples para pruebas) ----
    "export1": {"password": "1234", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora Andes SpA", "pais": "CL"},
    "export2": {"password": "1234", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora del Pacífico Ltda.", "pais": "CL"},
    "packing1": {"password": "1234", "rol": "Packing", "tipo": "compraventa", "empresa": "Packing Maule", "pais": "CL"},
    "frig1": {"password": "1234", "rol": "Frigorífico", "tipo": "compraventa", "empresa": "Frigorífico Valpo", "pais": "CL"},
    "aduana1": {"password": "1234", "rol": "Agencia de aduana", "tipo": "servicios", "empresa": "Agencia Andes", "pais": "CL"},
    "cliente1": {"password": "1234", "rol": "Cliente extranjero", "tipo": "compras", "empresa": "Importadora Asia Ltd.", "pais": "US"},
}


# Perfiles extendidos detallados (descripciones + items)
USER_PROFILES: Dict[str, Dict[str, Any]] = {
    "productor1@demo.cl": {
        "empresa": "Productores del Valle SpA",
        "rut": "76.111.111-1",
        "rol": "Productor(planta)",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "productor1@demo.cl",
        "telefono": "+56 9 7000 1111",
        "direccion": "San Felipe, V Región",
        "descripcion": "Uva de mesa, arándano y ciruela. Exportación directa y vía packing.",
        "items": [
            {"tipo": "oferta", "producto": "Uva Red Globe", "variedad": "Red Globe", "cantidad": "120", "bulto": "pallets", "origen": "V Región", "precio_caja": "$12"},
            {"tipo": "oferta", "producto": "Arándano", "variedad": "Duke", "cantidad": "80", "bulto": "pallets", "origen": "VI Región", "precio_caja": "$15"},
            {"tipo": "servicio", "servicio": "Mano de obra cosecha", "capacidad": "10 cuadrillas", "ubicacion": "V-VI Región"},
        ],
    },
    "productor2@demo.cl": {
        "empresa": "Agro Cordillera Ltda.",
        "rut": "76.222.222-2",
        "rol": "Productor(planta)",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "productor2@demo.cl",
        "telefono": "+56 9 7000 2222",
        "direccion": "Rengo, VI Región",
        "descripcion": "Cereza y ciruela D’Agen para fresco e industria.",
        "items": [
            {"tipo": "oferta", "producto": "Cereza", "variedad": "Santina", "cantidad": "150", "bulto": "pallets", "origen": "VI Región", "precio_caja": "$25"},
            {"tipo": "oferta", "producto": "Ciruela D’Agen", "variedad": "D’Agen", "cantidad": "100", "bulto": "pallets", "origen": "VI Región", "precio_kilo": "$1.2"},
        ],
    },


    # Packing CV
    "packingcv1@demo.cl": {
        "empresa": "Packing Maule SpA",
        "rut": "77.333.333-3",
        "rol": "Packing",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "packingcv1@demo.cl",
        "telefono": "+56 9 7100 3333",
        "direccion": "Curicó, VII Región",
        "descripcion": "Packing con línea de calibrado, también comercializamos fruta.",
        "items": [
            {"tipo": "oferta", "producto": "Ciruela Angeleno", "variedad": "Angeleno", "cantidad": "60", "bulto": "pallets", "origen": "VII Región", "precio_caja": "$11"},
            {"tipo": "servicio", "servicio": "Embalaje exportación", "capacidad": "20.000 cajas/día", "ubicacion": "Curicó"},
        ],
    },
    "packingcv2@demo.cl": {
        "empresa": "Packing Limarí Ltda.",
        "rut": "77.444.444-4",
        "rol": "Packing",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "packingcv2@demo.cl",
        "telefono": "+56 9 7100 4444",
        "direccion": "Ovalle, IV Región",
        "descripcion": "Packing multiproducto con frío propio.",
        "items": [
            {"tipo": "oferta", "producto": "Uva Thompson", "variedad": "Thompson", "cantidad": "50", "bulto": "pallets", "origen": "IV Región", "precio_caja": "$13"},
            {"tipo": "servicio", "servicio": "QA y etiquetado", "capacidad": "15.000 cajas/día", "ubicacion": "Ovalle"},
        ],
    },


    # Frigorífico CV
    "frigorificocv1@demo.cl": {
        "empresa": "Frío Centro SpA",
        "rut": "80.111.111-1",
        "rol": "Frigorífico",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "frigorificocv1@demo.cl",
        "telefono": "+56 9 7200 1111",
        "direccion": "Valparaíso",
        "descripcion": "Cámara fría y trading puntual de fruta.",
        "items": [
            {"tipo": "servicio", "servicio": "Preenfriado", "capacidad": "5 túneles", "ubicacion": "Valparaíso"},
            {"tipo": "oferta", "producto": "Manzana Fuji", "variedad": "Fuji", "cantidad": "40", "bulto": "pallets", "origen": "RM", "precio_caja": "$9"},
        ],
    },
    "frigorificocv2@demo.cl": {
        "empresa": "Frío Pacífico Ltda.",
        "rut": "80.222.222-2",
        "rol": "Frigorífico",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "frigorificocv2@demo.cl",
        "telefono": "+56 9 7200 2222",
        "direccion": "San Antonio",
        "descripcion": "Frigorífico multipropósito con zona extraport.",
        "items": [
            {"tipo": "servicio", "servicio": "Cámara fría", "capacidad": "1200 pallets", "ubicacion": "San Antonio"},
            {"tipo": "oferta", "producto": "Kiwi Hayward", "variedad": "Hayward", "cantidad": "70", "bulto": "pallets", "origen": "V Región", "precio_caja": "$10"},
        ],
    },


    # Exportadores
    "export1@demo.cl": {
        "empresa": "Exportadora Andes SpA",
        "rut": "78.111.111-1",
        "rol": "Exportador",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "export1@demo.cl",
        "telefono": "+56 2 2345 1111",
        "direccion": "Las Condes, RM",
        "descripcion": "Exportación a Asia y USA. Compramos cereza, uva y ciruela.",
        "items": [
            {"tipo": "demanda", "producto": "Cereza Santina", "variedad": "Santina", "cantidad": "120", "bulto": "pallets", "origen": "CL"},
            {"tipo": "demanda", "producto": "Uva Thompson", "variedad": "Thompson", "cantidad": "80", "bulto": "pallets", "origen": "CL"},
        ],
    },
    "export2@demo.cl": {
        "empresa": "Exportadora del Pacífico Ltda.",
        "rut": "78.222.222-2",
        "rol": "Exportador",
        "tipo": "compraventa",
        "pais": "CL",
        "email": "export2@demo.cl",
        "telefono": "+56 2 2345 2222",
        "direccion": "Providencia, RM",
        "descripcion": "FOB/CIF multi-mercado. Buscamos arándano y manzana.",
        "items": [
            {"tipo": "demanda", "producto": "Arándano Duke", "variedad": "Duke", "cantidad": "100", "bulto": "pallets", "origen": "CL"},
            {"tipo": "demanda", "producto": "Manzana Gala", "variedad": "Gala", "cantidad": "60", "bulto": "pallets", "origen": "CL"},
        ],
    },


    # Servicios: Packing
    "packingserv1@demo.cl": {
        "empresa": "PackSmart Servicios",
        "rut": "79.111.111-1",
        "rol": "Packing",
        "tipo": "servicios",
        "pais": "CL",
        "email": "packingserv1@demo.cl",
        "telefono": "+56 9 7300 1111",
        "direccion": "Rancagua",
        "descripcion": "Servicios de embalaje y QA.",
        "items": [
            {"tipo": "servicio", "servicio": "Embalaje exportación", "capacidad": "25.000 cajas/día", "ubicacion": "Rancagua"},
            {"tipo": "servicio", "servicio": "QA + etiquetado", "capacidad": "15.000 cajas/día", "ubicacion": "Rancagua"},
        ],
    },
    "packingserv2@demo.cl": {
        "empresa": "PackPro Services",
        "rut": "79.222.222-2",
        "rol": "Packing",
        "tipo": "servicios",
        "pais": "CL",
        "email": "packingserv2@demo.cl",
        "telefono": "+56 9 7300 2222",
        "direccion": "Talca",
        "descripcion": "Servicios para fruta de carozo y pomáceas.",
        "items": [
            {"tipo": "servicio", "servicio": "Reembalaje", "capacidad": "10.000 cajas/día", "ubicacion": "Talca"},
            {"tipo": "servicio", "servicio": "Clasificación óptica", "capacidad": "2 líneas", "ubicacion": "Talca"},
        ],
    },


    # Servicios: Frigorífico
    "frigorificoserv1@demo.cl": {
        "empresa": "FríoPort Servicios",
        "rut": "80.333.333-3",
        "rol": "Frigorífico",
        "tipo": "servicios",
        "pais": "CL",
        "email": "frigorificoserv1@demo.cl",
        "telefono": "+56 9 7400 1111",
        "direccion": "Valparaíso",
        "descripcion": "Prefrío, cámara y consolidado.",
        "items": [
            {"tipo": "servicio", "servicio": "Preenfriado", "capacidad": "6 túneles", "ubicacion": "Valparaíso"},
            {"tipo": "servicio", "servicio": "Cámara fría", "capacidad": "1500 pallets", "ubicacion": "Valparaíso"},
        ],
    },
    "frigorificoserv2@demo.cl": {
        "empresa": "Frío Andino Servicios",
        "rut": "80.444.444-4",
        "rol": "Frigorífico",
        "tipo": "servicios",
        "pais": "CL",
        "email": "frigorificoserv2@demo.cl",
        "telefono": "+56 9 7400 2222",
        "direccion": "Santiago",
        "descripcion": "Servicios integrales para exportación.",
        "items": [
            {"tipo": "servicio", "servicio": "Paletizado", "capacidad": "800 pallets/día", "ubicacion": "Santiago"},
            {"tipo": "servicio", "servicio": "Cross-docking", "capacidad": "Alta", "ubicacion": "Santiago"},
        ],
    },


    # Servicios: Aduana / Extraportuario
    "aduana1@demo.cl": {
        "empresa": "Agencia Andes",
        "rut": "82.111.111-1",
        "rol": "Agencia de aduana",
        "tipo": "servicios",
        "pais": "CL",
        "email": "aduana1@demo.cl",
        "telefono": "+56 2 2900 1111",
        "direccion": "Valparaíso",
        "descripcion": "Tramitación documental de exportación.",
        "items": [
            {"tipo": "servicio", "servicio": "Despacho de exportación", "capacidad": "Alta", "ubicacion": "Valparaíso"},
        ],
    },
    "aduana2@demo.cl": {
        "empresa": "Aduanas Express",
        "rut": "82.222.222-2",
        "rol": "Agencia de aduana",
        "tipo": "servicios",
        "pais": "CL",
        "email": "aduana2@demo.cl",
        "telefono": "+56 2 2900 2222",
        "direccion": "San Antonio",
        "descripcion": "Ventanilla única y asesoría OEA.",
        "items": [
            {"tipo": "servicio", "servicio": "Asesoría OEA", "capacidad": "Media", "ubicacion": "San Antonio"},
        ],
    },
    "extraport1@demo.cl": {
        "empresa": "Servicios Extraport Valpo",
        "rut": "83.111.111-1",
        "rol": "Extraportuario",
        "tipo": "servicios",
        "pais": "CL",
        "email": "extraport1@demo.cl",
        "telefono": "+56 9 7500 1111",
        "direccion": "Valparaíso",
        "descripcion": "Consolidado y desconsolidado.",
        "items": [
            {"tipo": "servicio", "servicio": "Consolidación de contenedores", "capacidad": "100/día", "ubicacion": "Valparaíso"},
        ],
    },
    "extraport2@demo.cl": {
        "empresa": "Extraport San Antonio",
        "rut": "83.222.222-2",
        "rol": "Extraportuario",
        "tipo": "servicios",
        "pais": "CL",
        "email": "extraport2@demo.cl",
        "telefono": "+56 9 7500 2222",
        "direccion": "San Antonio",
        "descripcion": "Servicios logísticos en puerto.",
        "items": [
            {"tipo": "servicio", "servicio": "Consolidación de contenedores", "capacidad": "50/día", "ubicacion": "San Antonio"},
        ],
    },


    # Clientes extranjeros
    "clienteusa1@ext.com": {
        "empresa": "Importadora Asia Ltd.",
        "rol": "Cliente extranjero",
        "tipo": "compras",
        "pais": "US",
        "email": "clienteusa1@ext.com",
        "telefono": "+1 415 555 0101",
        "direccion": "San Francisco, CA",
        "descripcion": "Compras de fruta chilena; foco cereza, uva y ciruela.",
        "items": [
            {"tipo": "demanda", "producto": "Cereza Santina", "variedad": "Santina", "cantidad": "80", "bulto": "pallets", "origen": "CL"},
        ],
    },
    "clienteusa2@ext.com": {
        "empresa": "Gourmet Asia Ltd.",
        "rol": "Cliente extranjero",
        "tipo": "compras",
        "pais": "US",
        "email": "clienteusa2@ext.com",
        "telefono": "+1 212 555 0199",
        "direccion": "New York, NY",
        "descripcion": "Compras de arándano y manzana premium.",
        "items": [
            {"tipo": "demanda", "producto": "Arándano Duke", "variedad": "Duke", "cantidad": "50", "bulto": "pallets", "origen": "CL"},
        ],
    },
}


# Dataset liviano de "publicaciones" genéricas (se usa en Parte 2)
PUBLICACIONES: List[Dict[str, Any]] = [
    {"usuario": "export1", "tipo": "oferta", "rol": "Exportador", "empresa": "Exportadora Andes SpA", "producto": "Trufas Negras Chilenas", "precio": "USD 800/kg"},
    {"usuario": "export2", "tipo": "oferta", "rol": "Exportador", "empresa": "Exportadora del Pacífico Ltda.", "producto": "Cerezas Premium", "precio": "USD 7/kg"},
    {"usuario": "packing1", "tipo": "servicio", "rol": "Packing", "empresa": "Packing Maule", "producto": "Servicio de Embalaje", "precio": "USD 0.50/kg"},
    {"usuario": "frig1", "tipo": "servicio", "rol": "Frigorífico", "empresa": "Frigorífico Valpo", "producto": "Almacenamiento Refrigerado", "precio": "USD 0.20/kg"},
    {"usuario": "aduana1", "tipo": "servicio", "rol": "Agencia de aduana", "empresa": "Agencia Andes", "producto": "Tramitación de Exportación", "precio": "USD 200/trámite"},
    {"usuario": "cliente1", "tipo": "demanda", "rol": "Cliente extranjero", "empresa": "Importadora Asia Ltd.", "producto": "Demanda de Fruta Chilena", "precio": "Consultar"},
]




# ---------------------------------------------------------
# CARRITO (helpers de sesión) — usado en Parte 2
# ---------------------------------------------------------
def get_cart() -> List[Dict[str, Any]]:
    return session.setdefault("cart", [])




def save_cart(cart: List[Dict[str, Any]]) -> None:
    session["cart"] = cart




def add_to_cart(item: Dict[str, Any]) -> None:
    cart = get_cart()
    cart.append(item)
    save_cart(cart)




def remove_from_cart(index: int) -> bool:
    cart = get_cart()
    if 0 <= index < len(cart):
        cart.pop(index)
        save_cart(cart)
        return True
    return False




def clear_cart() -> None:
    save_cart([])




# ---------------------------------------------------------
# AUTH Y RUTAS BASE
# ---------------------------------------------------------
@app.route("/")
def home():
    """Página principal (plantilla requiere base.html y enlace a /ayuda)."""
    return render_template("home.html")




@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión (permite email o username alias del seed)."""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()


        if username in USERS and USERS[username]["password"] == password:
            session["user"] = username
            session.permanent = True
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"))
            return redirect(url_for("home"))


        # Buscar por email si se ingresó un alias o viceversa
        # (Intento flexible de match)
        for u, data in USERS.items():
            if (u.lower() == username.lower() or data.get("empresa", "").lower() == username.lower()) and data.get("password") == password:
                session["user"] = u
                session.permanent = True
                flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"))
                return redirect(url_for("home"))


        flash(t("Usuario o contraseña incorrecta", "Incorrect username or password", "用戶名或密碼錯誤"))
        return redirect(url_for("login"))


    return render_template("login.html")




@app.route("/logout")
def logout():
    """Cierra sesión."""
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente", "Logged out successfully", "成功登出"))
    return redirect(url_for("home"))




@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registro de nuevos usuarios.
    Define: rol, tipo (compras, ventas, servicios, mixto, compraventa),
    agrega automáticamente a USERS (in-memory).
    """
    roles = [
        "Cliente extranjero",
        "Productor(planta)",
        "Packing",
        "Frigorífico",
        "Exportador",
        "Agencia de aduana",
        "Extraportuario",
        "Transporte",
    ]
    tipos = ["compras", "ventas", "servicios", "mixto", "compraventa"]


    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        password = (request.form.get("password") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        rol = (request.form.get("rol") or "").strip()
        tipo = (request.form.get("tipo") or "").strip()
        pais = (request.form.get("pais") or "CL").strip()


        if not all([usuario, password, empresa, rol, tipo]):
            flash(t("Todos los campos son obligatorios", "All fields are required", "所有欄位均為必填"))
            return redirect(url_for("register"))


        if usuario in USERS:
            flash(t("El nombre de usuario ya existe", "Username already exists", "用戶名已存在"))
            return redirect(url_for("register"))


        USERS[usuario] = {
            "password": password,
            "empresa": empresa,
            "rol": rol,
            "tipo": tipo,
            "pais": pais,
        }


        # Crear un perfil base (para vista de cliente_detalle)
        USER_PROFILES[usuario] = {
            "empresa": empresa,
            "rol": rol,
            "tipo": tipo,
            "pais": pais,
            "email": usuario,
            "telefono": "",
            "direccion": "",
            "descripcion": "",
            "items": [],
        }


        flash(t("Usuario registrado exitosamente", "User registered successfully", "用戶註冊成功"))
        # Redirige a login o a página de registro_ok (se añadirá en Parte 3)
        return redirect(url_for("login"))


    return render_template("register.html", roles=roles, tipos=tipos)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    # debug=True solo local. En Render se usa gunicorn app:app
    app.run(debug=True)
# =========================
# app.py — Parte 2/3
# Lógica de negocio, roles, vistas dinámicas y formularios
# =========================


# ---------------------------------------------------------
# HELPERS DE CLIENTES
# ---------------------------------------------------------
def _normaliza_items(items):
    out = []
    for it in items or []:
        nombre = it.get("producto") or it.get("servicio") or it.get("variedad") or "Item"
        tipo = it.get("tipo") or "item"
        out.append({"nombre": nombre, "tipo": tipo})
    return out




def _armar_cliente_desde_profile(username, profile):
    return {
        "username": username,
        "empresa": profile.get("empresa"),
        "rol": profile.get("rol"),
        "tipo": profile.get("tipo") or profile.get("perfil_tipo") or "",
        "descripcion": profile.get("descripcion") or "",
        "items": _normaliza_items(profile.get("items")),
    }




def _armar_cliente_desde_users(username, data):
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("tipo", ""),
        "descripcion": data.get("descripcion", ""),
        "items": [],
    }




# ---------------------------------------------------------
# CLIENTES / DETALLES / MENSAJES
# ---------------------------------------------------------
@app.route("/clientes")
def clientes():
    if not is_logged():
        flash(t("Debes iniciar sesión", "You must log in", "請先登入"))
        return redirect(url_for("login"))


    lista = []
    for u, profile in USER_PROFILES.items():
        lista.append(_armar_cliente_desde_profile(u, profile))
    ya = {c["username"] for c in lista}
    for u, data in USERS.items():
        if u not in ya:
            lista.append(_armar_cliente_desde_users(u, data))
    lista.sort(key=lambda c: (c.get("empresa") or "").lower())


    return render_template("clientes.html", clientes=lista)




@app.route("/clientes/<username>")
def cliente_detalle(username):
    if username in USER_PROFILES:
        c = _armar_cliente_desde_profile(username, USER_PROFILES[username])
    elif username in USERS:
        c = _armar_cliente_desde_users(username, USERS[username])
    else:
        abort(404)
    return render_template("cliente_detalle.html", c=c)




@app.route("/clientes/<username>/mensaje", methods=["POST"])
def enviar_mensaje(username):
    if not is_logged():
        flash(t("Debes iniciar sesión para enviar mensajes",
                "You must log in to send messages", "請先登入以發送訊息"))
        return redirect(url_for("login"))


    mensaje = (request.form.get("mensaje") or "").strip()
    if not mensaje:
        flash(t("El mensaje no puede estar vacío", "Message cannot be empty", "訊息不可為空"))
        return redirect(url_for("cliente_detalle", username=username))


    flash(t("Mensaje enviado correctamente",
            "Message sent successfully", "訊息已成功發送"))
    return redirect(url_for("cliente_detalle", username=username))




# ---------------------------------------------------------
# CARRITO / COMPRAS / VENTAS / SERVICIOS
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    if not is_logged():
        return redirect(url_for("login"))
    return render_template("carrito.html", cart=get_cart())




@app.route("/carrito/agregar/<int:pub_id>")
def carrito_agregar(pub_id):
    if not is_logged():
        flash(t("Debes iniciar sesión", "You must log in", "請先登入"))
        return redirect(url_for("login"))


    if 0 <= pub_id < len(PUBLICACIONES):
        add_to_cart(PUBLICACIONES[pub_id])
        flash(t("Agregado al carrito", "Added to cart", "已加入購物車"))
    return redirect(url_for("carrito"))




@app.route("/carrito/eliminar/<int:index>")
def carrito_eliminar(index):
    if remove_from_cart(index):
        flash(t("Eliminado del carrito", "Removed from cart", "已刪除"))
    else:
        flash(t("Ítem no encontrado", "Item not found", "找不到項目"))
    return redirect(url_for("carrito"))




@app.route("/compras")
def compras():
    return render_template("compras.html", publicaciones=[p for p in PUBLICACIONES if p["tipo"] in ("oferta", "servicio")])




@app.route("/ventas")
def ventas():
    return render_template("ventas.html", publicaciones=[p for p in PUBLICACIONES if p["tipo"] == "demanda"])




@app.route("/servicios")
def servicios():
    return render_template("servicios.html", publicaciones=[p for p in PUBLICACIONES if p["tipo"] == "servicio"])




# ---------------------------------------------------------
# PERFIL / DASHBOARD
# ---------------------------------------------------------
@app.route("/perfil")
def perfil():
    if not is_logged():
        flash(t("Debes iniciar sesión", "You must log in", "請先登入"))
        return redirect(url_for("login"))


    username = session["user"]
    user = USERS.get(username, {})
    return render_template("perfil.html", user=user)




@app.route("/dashboard")
def dashboard():
    if not is_logged():
        return redirect(url_for("login"))
    return render_template("dashboard.html")




# ---------------------------------------------------------
# REGISTER ROUTER
# ---------------------------------------------------------
@app.route("/register_router")
def register_router():
    return render_template("register_router.html")




# ---------------------------------------------------------
# PASSWORD RESET (2 PASOS)
# ---------------------------------------------------------
@app.route("/password_reset_request", methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        flash(t("Si el usuario existe, enviaremos instrucciones a su correo.",
                "If the user exists, we'll email recovery instructions.",
                "若帳號存在，我們將寄出重設指示。"))
        return redirect(url_for("password_reset_form"))
    return render_template("password_reset_request.html")




@app.route("/password_reset_form", methods=["GET", "POST"])
def password_reset_form():
    if request.method == "POST":
        nueva_password = request.form.get("nueva_contraseña") or request.form.get("nueva_contrasena")
        if not (nueva_password or "").strip():
            flash(t("La nueva contraseña es obligatoria",
                    "New password is required", "必須填寫新密碼"))
            return redirect(url_for("password_reset_form"))
        flash(t("Contraseña actualizada", "Password updated", "密碼已更新"))
        return redirect(url_for("login"))
    return render_template("password_reset_form.html")
# =========================
# app.py — Parte 3/3 (final)
# Rutas de ayuda, errores, registro_exitoso y manejo global
# =========================


# ---------------------------------------------------------
# AYUDA — versión completa (reemplaza stub de la Parte 1)
# ---------------------------------------------------------
@app.route("/ayuda")
def ayuda():
    """Centro de ayuda traducido con información básica."""
    return render_template("ayuda.html")




# ---------------------------------------------------------
# REGISTRO EXITOSO
# ---------------------------------------------------------
@app.route("/registro_exitoso")
def registro_exitoso():
    """Confirma creación de cuenta."""
    return render_template("registro_exitoso.html")




# ---------------------------------------------------------
# MANEJO DE ERRORES
# ---------------------------------------------------------
@app.errorhandler(404)
def not_found_error(e):
    """Página 404 personalizada."""
    return (
        render_template(
            "404.html",
            mensaje=t("Página no encontrada", "Page not found", "找不到頁面"),
            descripcion=t(
                "La página que buscas no existe o ha sido movida.",
                "The page you are looking for does not exist or has been moved.",
                "您尋找的頁面不存在或已被移動。",
            ),
        ),
        404,
    )




@app.errorhandler(500)
def server_error(e):
    """Página 500 personalizada."""
    return (
        render_template(
            "500.html",
            mensaje=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤"),
            descripcion=t(
                "Ha ocurrido un error inesperado. Por favor, inténtalo más tarde.",
                "An unexpected error occurred. Please try again later.",
                "發生意外錯誤，請稍後再試。",
            ),
        ),
        500,
    )




# ---------------------------------------------------------
# VALIDACIÓN FINAL — FAVICON ÚNICO
# ---------------------------------------------------------
@app.route("/favicon.ico")
def favicon():
    """Sirve el favicon sin duplicar endpoint."""
    icon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(icon_path):
        return send_from_directory(STATIC_DIR, "favicon.ico")
    return ("", 204)

# -----------------------------------------------------
# 🌐 SOPORTE MULTILENGUAJE (Español / English / 中文)
# -----------------------------------------------------
from flask import request, session, redirect, url_for

# 📘 Diccionario central de traducciones
TRANSLATIONS = {
    # --- Navegación ---
    "Inicio": {"en": "Home", "zh": "主頁"},
    "Empresas": {"en": "Companies", "zh": "公司"},
    "Servicios": {"en": "Services", "zh": "服務"},
    "Carrito": {"en": "Cart", "zh": "購物車"},
    "Perfil": {"en": "Profile", "zh": "個人資料"},
    "Ayuda": {"en": "Help", "zh": "幫助"},
    "Salir": {"en": "Logout", "zh": "登出"},
    "Iniciar Sesión": {"en": "Login", "zh": "登入"},
    "Registrarse": {"en": "Register", "zh": "註冊"},
    "Comercio Internacional": {"en": "International Trade", "zh": "國際貿易"},
    "Versión": {"en": "Version", "zh": "版本"},
    "Desarrollado en Flask": {"en": "Built with Flask", "zh": "使用 Flask 構建"},
    "Conectando productores y compradores del mundo": {
        "en": "Connecting global producers and buyers",
        "zh": "連接全球生產商與買家"
    },

    # --- HOME ---
    "Bienvenido a Window Shopping": {"en": "Welcome to Window Shopping", "zh": "歡迎來到 Window Shopping"},
    "La plataforma que conecta productores chilenos con compradores internacionales.": {
        "en": "The platform connecting Chilean producers with international buyers.",
        "zh": "連接智利生產商與國際買家的平台。"
    },
    "Comienza ahora": {"en": "Start now", "zh": "立即開始"},
    "Explora nuestros servicios": {"en": "Explore our services", "zh": "探索我們的服務"},
    "Compra y Venta": {"en": "Buy & Sell", "zh": "買賣"},
    "Encuentra productores, packing, exportadores y clientes internacionales.": {
        "en": "Find producers, packers, exporters and international clients.",
        "zh": "尋找生產商、包裝廠、出口商和國際客戶。"
    },
    "Servicios Logísticos": {"en": "Logistic Services", "zh": "物流服務"},
    "Accede a transporte, frigoríficos y agentes de aduana certificados.": {
        "en": "Access transport, cold storage, and certified customs agents.",
        "zh": "提供運輸、冷藏庫及報關行服務。"
    },
    "Sostenibilidad": {"en": "Sustainability", "zh": "永續發展"},
    "Promovemos comercio responsable con trazabilidad y economía circular.": {
        "en": "We promote responsible trade with traceability and circular economy.",
        "zh": "推動負責任的貿易、可追溯性與循環經濟。"
    },

    # --- LOGIN / REGISTER ---
    "Iniciar sesión": {"en": "Login", "zh": "登入"},
    "Correo electrónico": {"en": "Email", "zh": "電子郵件"},
    "Contraseña": {"en": "Password", "zh": "密碼"},
    "Entrar": {"en": "Sign in", "zh": "登入"},
    "¿No tienes una cuenta?": {"en": "Don't have an account?", "zh": "還沒有帳號？"},
    "Regístrate aquí": {"en": "Register here", "zh": "點此註冊"},
    "¿Ya tienes una cuenta?": {"en": "Already have an account?", "zh": "已經有帳號了？"},
    "Inicia sesión aquí": {"en": "Log in here", "zh": "點此登入"},
    "Registro de empresa o usuario": {"en": "Company or User Registration", "zh": "公司或用戶註冊"},
    "Nombre de la empresa o usuario": {"en": "Company or User Name", "zh": "公司或用戶名稱"},
    "Selecciona tu tipo de perfil": {"en": "Select your profile type", "zh": "選擇您的個人資料類型"},
    "Selecciona tu rol": {"en": "Select your role", "zh": "選擇您的角色"},
    "Crear cuenta": {"en": "Create Account", "zh": "建立帳號"},
    "Cliente extranjero (solo compras)": {"en": "Foreign client (only purchases)", "zh": "外國客戶（僅購買）"},
    "Nacional - Compra/Venta": {"en": "National - Buy/Sell", "zh": "國內 - 買賣"},
    "Nacional - Servicios": {"en": "National - Services", "zh": "國內 - 服務"},
    "Nacional - Mixto (Fruta y Servicios)": {"en": "National - Mixed (Fruit & Services)", "zh": "國內 - 混合（水果與服務）"},
    "Productor": {"en": "Producer", "zh": "生產商"},
    "Packing": {"en": "Packing", "zh": "包裝廠"},
    "Frigorífico": {"en": "Cold Storage", "zh": "冷藏庫"},
    "Exportador": {"en": "Exporter", "zh": "出口商"},
    "Agencia de aduana": {"en": "Customs Agency", "zh": "報關行"},
    "Extraportuario": {"en": "Extra-port Service", "zh": "港外服務"},
    "Transporte": {"en": "Transport", "zh": "運輸"},
    "Cliente extranjero": {"en": "Foreign Client", "zh": "外國客戶"},

    # --- REGISTRO EXITOSO ---
    "¡Registro Exitoso!": {"en": "Registration Successful!", "zh": "註冊成功！"},
    "Tu cuenta ha sido creada correctamente.": {
        "en": "Your account has been successfully created.",
        "zh": "您的帳戶已成功建立。"
    },
    "Ir al inicio de sesión": {"en": "Go to login", "zh": "前往登入"},

    # --- PERFIL ---
    "Tu Perfil": {"en": "Your Profile", "zh": "您的個人資料"},
    "Cerrar sesión": {"en": "Log out", "zh": "登出"},
    "Rol:": {"en": "Role:", "zh": "角色："},
    "Tipo de Cuenta:": {"en": "Account Type:", "zh": "帳戶類型："},

    # --- PASSWORD RESET ---
    "Recuperar Contraseña": {"en": "Recover Password", "zh": "重設密碼"},
    "Enviar enlace de recuperación": {"en": "Send recovery link", "zh": "發送重設連結"},
    "Nueva Contraseña": {"en": "New Password", "zh": "新密碼"},
    "Guardar contraseña": {"en": "Save password", "zh": "儲存密碼"},
    "Volver al inicio de sesión": {"en": "Back to login", "zh": "返回登入頁面"},

    # --- AYUDA ---
    "Centro de Ayuda": {"en": "Help Center", "zh": "幫助中心"},
    "Preguntas frecuentes": {"en": "Frequently Asked Questions", "zh": "常見問題"},
    "¿Cómo registro mi empresa?": {"en": "How do I register my company?", "zh": "如何註冊我的公司？"},
    "¿Puedo ofrecer servicios y productos a la vez?": {"en": "Can I offer both services and products?", "zh": "我可以同時提供服務和產品嗎？"},
    "¿Cómo contacto a un comprador extranjero?": {"en": "How do I contact a foreign buyer?", "zh": "如何聯繫外國買家？"},
    "¿Qué significa el perfil mixto?": {"en": "What does the mixed profile mean?", "zh": "什麼是混合型帳戶？"},
    "Si necesitas más ayuda, contáctanos a:": {"en": "If you need more help, contact us at:", "zh": "如需更多幫助，請聯繫我們："},

    # --- ERRORES ---
    "Página no encontrada": {"en": "Page not found", "zh": "找不到頁面"},
    "Error interno del servidor": {"en": "Internal server error", "zh": "伺服器內部錯誤"},
    "Volver al inicio": {"en": "Back to home", "zh": "返回主頁"},
}

# Función auxiliar t() disponible en templates
@app.context_processor
def inject_translator():
    def t(es, en=None, zh=None):
        """
        Traductor dinámico: usa el idioma activo (session['lang'])
        y busca coincidencias en TRANSLATIONS. Si no hay, devuelve el texto en español.
        """
        lang = session.get("lang", "es")
        if lang == "es":
            return es
        # Busca en el diccionario central
        if es in TRANSLATIONS and lang in TRANSLATIONS[es]:
            return TRANSLATIONS[es][lang]
        # Si no existe, usa el alternativo
        if lang == "en" and en:
            return en
        if lang == "zh" and zh:
            return zh
        return es  # fallback
    return dict(t=t)


# Ruta para cambiar idioma desde el selector del header
@app.route('/set_lang', methods=['POST'])
def set_lang():
    """Recibe el idioma desde el formulario base.html y lo guarda en sesión."""
    lang = request.form.get('lang', 'es')
    session['lang'] = lang
    print(f"🌍 Idioma establecido: {lang}")
    return redirect(request.referrer or url_for('home'))

# ---------------------------------------------------------
# ARRANQUE FINAL
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
