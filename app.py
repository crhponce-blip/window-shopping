# === app.py (Parte 1/6) ===
# Configuración base, i18n y datos semilla (incluye clientes extranjeros con DEMANDA)

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
# SOPORTE DE ARCHIVOS Y FAVICON
# =========================================================
@app.route("/favicon.ico")
def favicon():
    """Evita errores 404 del navegador por el ícono"""
    ico_path = os.path.join(app.root_path, "static")
    try:
        return send_from_directory(ico_path, "favicon.ico", mimetype="image/vnd.microsoft.icon")
    except Exception:
        return ("", 204)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =========================================================
# I18N / MULTI-IDIOMA (ES / EN / ZH)
# =========================================================
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

# =========================================================
# UTILIDADES DE SESIÓN Y NORMALIZACIÓN
# =========================================================
def is_logged() -> bool:
    return "user" in session

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

def norm_money(val: str) -> str:
    val = (val or "").strip()
    if not val:
        return "$0"
    if val.startswith("$"):
        return val
    return f"${val}"
# =========================================================
# USUARIOS Y PERFILES (SEMILLA)
# Incluye 2 empresas por tipo/rol según tus reglas
# Cliente extranjero: items de tipo "demanda"
# Packing/Frigorífico mixtos incluidos
# =========================================================

USERS: Dict[str, Dict[str, Any]] = {
    # --- Compraventa nacionales ---
    "productor1@demo.cl": {"password": "1234", "rol": "Productor", "perfil_tipo": "compra_venta", "pais": "CL"},
    "productor2@demo.cl": {"password": "1234", "rol": "Productor", "perfil_tipo": "compra_venta", "pais": "CL"},

    "packingcv1@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "compra_venta", "pais": "CL"},
    "packingcv2@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "compra_venta", "pais": "CL"},

    "frigorificocv1@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "compra_venta", "pais": "CL"},
    "frigorificocv2@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "compra_venta", "pais": "CL"},

    "export1@demo.cl": {"password": "1234", "rol": "Exportador", "perfil_tipo": "compra_venta", "pais": "CL"},
    "export2@demo.cl": {"password": "1234", "rol": "Exportador", "perfil_tipo": "compra_venta", "pais": "CL"},

    # --- Servicios nacionales ---
    "packingserv1@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "servicios", "pais": "CL"},
    "packingserv2@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "servicios", "pais": "CL"},

    "frigorificoserv1@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "servicios", "pais": "CL"},
    "frigorificoserv2@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "servicios", "pais": "CL"},

    "aduana1@demo.cl": {"password": "1234", "rol": "Agencia de Aduanas", "perfil_tipo": "servicios", "pais": "CL"},
    "aduana2@demo.cl": {"password": "1234", "rol": "Agencia de Aduanas", "perfil_tipo": "servicios", "pais": "CL"},

    "extraport1@demo.cl": {"password": "1234", "rol": "Extraportuario", "perfil_tipo": "servicios", "pais": "CL"},
    "extraport2@demo.cl": {"password": "1234", "rol": "Extraportuario", "perfil_tipo": "servicios", "pais": "CL"},

    "transporte1@demo.cl": {"password": "1234", "rol": "Transporte", "perfil_tipo": "servicios", "pais": "CL"},
    "transporte2@demo.cl": {"password": "1234", "rol": "Transporte", "perfil_tipo": "servicios", "pais": "CL"},

    # --- Mixtos (solo Packing y Frigorífico) ---
    "packingmix1@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "ambos", "pais": "CL"},
    "packingmix2@demo.cl": {"password": "1234", "rol": "Packing", "perfil_tipo": "ambos", "pais": "CL"},
    "frigorificomix1@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "ambos", "pais": "CL"},
    "frigorificomix2@demo.cl": {"password": "1234", "rol": "Frigorífico", "perfil_tipo": "ambos", "pais": "CL"},

    # --- Clientes extranjeros (solo compras con DEMANDA) ---
    "clienteusa1@ext.com": {"password": "1234", "rol": "Cliente extranjero", "perfil_tipo": "compra_venta", "pais": "US"},
    "clienteusa2@ext.com": {"password": "1234", "rol": "Cliente extranjero", "perfil_tipo": "compra_venta", "pais": "US"},
}

# =========================================================
# PERFILES DETALLADOS (USER_PROFILES)
# =========================================================

USER_PROFILES: Dict[str, Dict[str, Any]] = {
    # ======================================================
    # PRODUCTOR / PLANTA
    # ======================================================
    "productor1@demo.cl": {
        "empresa": "Productores del Valle SpA",
        "rut": "76.111.111-1",
        "rol": "Productor",
        "perfil_tipo": "compra_venta",
        "pais": "CL",
        "email": "productor1@demo.cl",
        "telefono": "+56 9 7000 1111",
        "direccion": "San Felipe, V Región",
        "descripcion": "Uva de mesa, arándano y ciruela. Exportación directa y vía packing.",
        "items": [
            {"tipo": "oferta", "producto": "Uva Red Globe", "variedad": "Red Globe", "cantidad": "120", "bulto": "pallets", "origen": "V Región", "precio_caja": "$12"},
            {"tipo": "oferta", "producto": "Arándano", "variedad": "Duke", "cantidad": "80", "bulto": "pallets", "origen": "VI Región", "precio_caja": "$15"},
            {"tipo": "servicio", "servicio": "Mano de obra cosecha", "capacidad": "10 cuadrillas", "ubicacion": "V-VI Región"}
        ],
    },
    "productor2@demo.cl": {
        "empresa": "Agro Cordillera Ltda.",
        "rut": "76.222.222-2",
        "rol": "Productor",
        "perfil_tipo": "compra_venta",
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

    # ======================================================
    # PACKING (compraventa)
    # ======================================================
    "packingcv1@demo.cl": {
        "empresa": "Packing Maule SpA",
        "rut": "77.333.333-3",
        "rol": "Packing",
        "perfil_tipo": "compra_venta",
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
        "perfil_tipo": "compra_venta",
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
   # ======================================================
    # FRIGORÍFICO (compraventa)
    # ======================================================
    "frigorificocv1@demo.cl": {
        "empresa": "Frío Centro SpA",
        "rut": "80.111.111-1",
        "rol": "Frigorífico",
        "perfil_tipo": "compra_venta",
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
        "perfil_tipo": "compra_venta",
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

    # ======================================================
    # EXPORTADORES (compraventa)
    # ======================================================
    "export1@demo.cl": {
        "empresa": "Exportadora Andes SpA",
        "rut": "78.111.111-1",
        "rol": "Exportador",
        "perfil_tipo": "compra_venta",
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
        "perfil_tipo": "compra_venta",
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

    # ======================================================
    # PACKING (servicios)
    # ======================================================
    "packingserv1@demo.cl": {
        "empresa": "PackSmart Servicios",
        "rut": "79.111.111-1",
        "rol": "Packing",
        "perfil_tipo": "servicios",
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
        "perfil_tipo": "servicios",
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

    # ======================================================
    # FRIGORÍFICO (servicios)
    # ======================================================
    "frigorificoserv1@demo.cl": {
        "empresa": "FríoPort Servicios",
        "rut": "80.333.333-3",
        "rol": "Frigorífico",
        "perfil_tipo": "servicios",
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
        "perfil_tipo": "servicios",
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

    # ======================================================
    # AGENCIA DE ADUANAS (servicios)
    # ======================================================
    "aduana1@demo.cl": {
        "empresa": "Agencia Andes",
        "rut": "82.111.111-1",
        "rol": "Agencia de Aduanas",
        "perfil_tipo": "servicios",
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
        "rol": "Agencia de Aduanas",
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "aduana2@demo.cl",
        "telefono": "+56 2 2900 2222",
        "direccion": "San Antonio",
        "descripcion": "Ventanilla única y asesoría OEA.",
        "items": [
            {"tipo": "servicio", "servicio": "Asesoría OEA", "capacidad": "Media", "ubicacion": "San Antonio"},
        ],
    },

    # ======================================================
    # EXTRAPORTUARIO (servicios)
    # ======================================================
    "extraport1@demo.cl": {
        "empresa": "Servicios Extraport Valpo",
        "rut": "83.111.111-1",
        "rol": "Extraportuario",
        "perfil_tipo": "servicios",
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
        "perfil_tipo": "servicios",
        "pais": "CL",
        "email": "extraport2@demo.cl",
        "telefono": "+56 9 7500 2222",
        "direccion": "San Antonio",
        "descripcion": "Servicios logísticos en puerto.",
        "items": [
            {"tipo": "servicio", "servicio": "Consolidación de contenedores", "capacidad": "50/día", "ubicacion": "San Antonio"},
        ],
    },
}
# =========================================================
# DATOS SIMULADOS: USUARIOS Y PUBLICACIONES
# =========================================================

USERS_SIM = {
    "cliente1": {"usuario": "cliente1", "rol": "Cliente extranjero", "tipo": "compras", "empresa": "Importadora Asia Ltd.", "password": "1234"},
    "export1": {"usuario": "export1", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora Andes SpA", "password": "1234"},
    "export2": {"usuario": "export2", "rol": "Exportador", "tipo": "compraventa", "empresa": "Exportadora del Pacífico", "password": "1234"},
    "packing1": {"usuario": "packing1", "rol": "Packing", "tipo": "compraventa", "empresa": "Packing Maule", "password": "1234"},
    "packing2": {"usuario": "packing2", "rol": "Packing", "tipo": "servicios", "empresa": "Servicios Packing Sur", "password": "1234"},
    "packing3": {"usuario": "packing3", "rol": "Packing", "tipo": "mixto", "empresa": "Packing Integral BioBio", "password": "1234"},
    "frig1": {"usuario": "frig1", "rol": "Frigorífico", "tipo": "compraventa", "empresa": "Frigorífico Valpo", "password": "1234"},
    "frig2": {"usuario": "frig2", "rol": "Frigorífico", "tipo": "servicios", "empresa": "Servicios Frío Sur", "password": "1234"},
    "frig3": {"usuario": "frig3", "rol": "Frigorífico", "tipo": "mixto", "empresa": "Frigorífico Integral del Maule", "password": "1234"},
    "prod1": {"usuario": "prod1", "rol": "Productor(planta)", "tipo": "ventas", "empresa": "Productores del Sur", "password": "1234"},
    "prod2": {"usuario": "prod2", "rol": "Productor(planta)", "tipo": "ventas", "empresa": "Plantas Maule Verde", "password": "1234"},
    "aduana1": {"usuario": "aduana1", "rol": "Agencia de aduana", "tipo": "servicios", "empresa": "Agencia Andes", "password": "1234"},
    "extra1": {"usuario": "extra1", "rol": "Extraportuario", "tipo": "servicios", "empresa": "Servicios Extraportuario Valpo", "password": "1234"},
    "trans1": {"usuario": "trans1", "rol": "Transporte", "tipo": "servicios", "empresa": "Transporte Global", "password": "1234"},
}

# =========================================================
# PUBLICACIONES SIMULADAS (ofertas, demandas, servicios)
# =========================================================

PUBLICACIONES = [
    {"usuario": "export1", "tipo": "oferta", "rol": "Exportador", "empresa": "Exportadora Andes SpA", "producto": "Trufas Negras Chilenas", "precio": "USD 800/kg"},
    {"usuario": "export2", "tipo": "oferta", "rol": "Exportador", "empresa": "Exportadora del Pacífico", "producto": "Cerezas Premium", "precio": "USD 7/kg"},
    {"usuario": "packing1", "tipo": "servicio", "rol": "Packing", "empresa": "Packing Maule", "producto": "Servicio de Embalaje de Fruta", "precio": "USD 0.50/kg"},
    {"usuario": "frig1", "tipo": "servicio", "rol": "Frigorífico", "empresa": "Frigorífico Valpo", "producto": "Almacenamiento Refrigerado", "precio": "USD 0.20/kg"},
    {"usuario": "aduana1", "tipo": "servicio", "rol": "Agencia de aduana", "empresa": "Agencia Andes", "producto": "Tramitación de Exportación", "precio": "USD 200/trámite"},
    {"usuario": "cliente1", "tipo": "demanda", "rol": "Cliente extranjero", "empresa": "Importadora Asia Ltd.", "producto": "Demanda de Fruta Chilena", "precio": "Consultar"},
]

# =========================================================
# FUNCIONES AUXILIARES (idioma, login, etc.)
# =========================================================

def get_lang() -> str:
    """Obtiene el idioma activo"""
    return session.get("lang", "es")

def t(es: str, en: str, zh: Optional[str] = None) -> str:
    """Traducción rápida según idioma"""
    lang = get_lang()
    if lang == "en":
        return en
    elif lang == "zh":
        return zh or es
    return es

def is_logged() -> bool:
    """Verifica si hay sesión activa"""
    return "user" in session

# =========================================================
# RUTAS PRINCIPALES Y AUTENTICACIÓN
# =========================================================

@app.route("/")
def home():
    """Página principal"""
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Se valida tanto con USERS como con USERS_SIM
        user_obj = USERS.get(username) or USERS_SIM.get(username)
        if user_obj and user_obj.get("password") == password:
            session["user"] = username
            flash(t("Inicio de sesión exitoso", "Login successful", "登入成功"))
            return redirect(url_for("home"))
        else:
            flash(t("Usuario o contraseña incorrecta", "Incorrect username or password", "用戶名或密碼錯誤"))
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Cerrar sesión"""
    session.pop("user", None)
    flash(t("Sesión cerrada correctamente", "Logged out successfully", "成功登出"))
    return redirect(url_for("home"))
# =========================================================
# RUTA DE REGISTRO (REGISTER + REGISTER_ROUTER)
# =========================================================

@app.route("/register", methods=["GET", "POST"])
@app.route("/register_router", methods=["GET", "POST"])
def register_router():
    """
    Registro de nuevos usuarios con subida opcional de archivo (logo, certificado, etc.)
    Se valida duplicado y se guarda localmente en /static/uploads
    """
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        empresa = request.form.get("empresa", "").strip()
        rol = request.form.get("rol", "").strip()
        tipo = request.form.get("tipo", "").strip()
        file = request.files.get("archivo")

        if not all([usuario, password, empresa, rol, tipo]):
            flash(t("Todos los campos son obligatorios", "All fields are required", "所有欄位均為必填"))
            return redirect(url_for("register_router"))

        if usuario in USERS or usuario in USERS_SIM:
            flash(t("El nombre de usuario ya existe", "Username already exists", "用戶名已存在"))
            return redirect(url_for("register_router"))

        # Guardado del archivo
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Agregar al diccionario global
        USERS[usuario] = {
            "usuario": usuario,
            "password": password,
            "empresa": empresa,
            "rol": rol,
            "tipo": tipo,
            "archivo": filename,
        }

        flash(t("Usuario registrado exitosamente", "User registered successfully", "用戶註冊成功"))
        return redirect(url_for("login"))

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

    return render_template("register.html", roles=roles, tipos=tipos)


# =========================================================
# RUTA PERFIL
# =========================================================
@app.route("/perfil")
def perfil():
    """Perfil del usuario actual"""
    if not is_logged():
        flash(t("Debes iniciar sesión para acceder al perfil", "You must log in to access the profile", "請先登入以訪問個人資料"))
        return redirect(url_for("login"))

    user = USERS.get(session["user"]) or USERS_SIM.get(session["user"])
    profile = USER_PROFILES.get(session["user"], {})
    return render_template("perfil.html", user=user, profile=profile)


# =========================================================
# DETALLES DE PUBLICACIONES (VENTAS / COMPRAS / SERVICIOS)
# =========================================================

@app.route("/detalles/<tipo>", methods=["GET", "POST"])
def detalles(tipo):
    """
    Muestra los detalles disponibles según el tipo y el rol del usuario logueado.
    Incluye buscador y filtro dinámico según las reglas de visibilidad.
    """
    tipo = tipo.lower()
    if tipo not in ("ventas", "compras", "servicios"):
        abort(404)

    if not is_logged():
        flash(t("Debes iniciar sesión para ver los detalles", "You must log in to view details", "請先登入以查看詳情"))
        return redirect(url_for("login"))

    me = USERS.get(session["user"]) or USERS_SIM.get(session["user"])
    my_rol = me.get("rol", "")
    filtro_texto = (request.args.get("q", "") or "").lower().strip()

    visibles = []
    for pub in PUBLICACIONES:
        p_rol = pub["rol"]
        p_tipo = pub["tipo"]
        p_empresa = pub["empresa"].lower()

        # Filtro de texto
        if filtro_texto and filtro_texto not in p_empresa:
            continue

        # Lógica de visibilidad según tipo y rol
        if tipo == "ventas":  # Ver demandas
            if my_rol == "Productor(planta)" and p_rol in ["Packing", "Frigorífico", "Exportador"]:
                visibles.append(pub)
            elif my_rol == "Packing" and p_rol in ["Frigorífico", "Exportador"]:
                visibles.append(pub)
            elif my_rol == "Frigorífico" and p_rol in ["Packing", "Exportador"]:
                visibles.append(pub)
            elif my_rol == "Exportador" and p_rol in ["Exportador", "Cliente extranjero"]:
                visibles.append(pub)

        elif tipo == "compras":  # Ver ofertas
            if my_rol == "Packing" and p_rol in ["Productor(planta)", "Frigorífico"]:
                visibles.append(pub)
            elif my_rol == "Frigorífico" and p_rol in ["Productor(planta)", "Packing"]:
                visibles.append(pub)
            elif my_rol == "Exportador" and p_rol in ["Productor(planta)", "Packing", "Frigorífico", "Exportador"]:
                visibles.append(pub)
            elif my_rol == "Cliente extranjero" and p_rol == "Exportador":
                visibles.append(pub)

        elif tipo == "servicios":  # Ver servicios disponibles
            if my_rol == "Productor(planta)" and p_rol in ["Packing", "Frigorífico", "Transporte"]:
                visibles.append(pub)
            elif my_rol == "Packing" and p_rol in ["Frigorífico", "Transporte"]:
                visibles.append(pub)
            elif my_rol == "Frigorífico" and p_rol in ["Packing", "Transporte"]:
                visibles.append(pub)
            elif my_rol == "Exportador" and p_rol in ["Agencia de aduana", "Transporte", "Extraportuario", "Packing", "Frigorífico"]:
                visibles.append(pub)
            elif my_rol == "Agencia de aduana" and p_rol == "Exportador":
                visibles.append(pub)
            elif my_rol == "Extraportuario" and p_rol == "Exportador":
                visibles.append(pub)
            elif my_rol == "Transporte" and p_rol in ["Exportador", "Packing", "Frigorífico", "Productor(planta)"]:
                visibles.append(pub)
            elif my_rol == "Packing" and me.get("tipo") == "mixto" and p_rol in ["Exportador", "Packing", "Productor(planta)"]:
                visibles.append(pub)
            elif my_rol == "Frigorífico" and me.get("tipo") == "mixto" and p_rol in ["Productor(planta)", "Packing", "Exportador"]:
                visibles.append(pub)

    # Selección de plantilla
    if tipo == "ventas":
        titulo = t("Detalle de Ventas", "Sales Details", "銷售詳情")
        plantilla = "detalle_ventas.html"
    elif tipo == "compras":
        titulo = t("Detalle de Compras", "Purchase Details", "採購詳情")
        plantilla = "detalle_compras.html"
    else:
        titulo = t("Detalle de Servicios", "Service Details", "服務詳情")
        plantilla = "detalle_servicio.html"

    return render_template(plantilla, titulo=titulo, publicaciones=visibles, tipo=tipo, query=filtro_texto)
# =========================================================
# SISTEMA DE CARRITO DE COMPRAS / SERVICIOS
# =========================================================

def get_cart():
    """Obtiene el carrito actual desde la sesión"""
    return session.get("cart", [])


def save_cart(cart):
    """Guarda el carrito actualizado en la sesión"""
    session["cart"] = cart


@app.route("/cart_add", methods=["POST"])
def cart_add():
    """Agrega un ítem al carrito"""
    if not is_logged():
        flash(t("Debes iniciar sesión para agregar al carrito", "You must log in to add to cart", "請先登入以新增至購物車"))
        return redirect(url_for("login"))

    cart = get_cart()
    empresa = request.form.get("empresa")
    rol = request.form.get("rol")
    tipo = request.form.get("tipo")

    if not all([empresa, rol, tipo]):
        flash(t("Error al agregar al carrito", "Error adding to cart", "新增至購物車時發生錯誤"))
        return redirect(request.referrer or url_for("home"))

    item = {"empresa": empresa, "rol": rol, "tipo": tipo}
    cart.append(item)
    save_cart(cart)

    flash(t("Agregado al carrito correctamente", "Added to cart successfully", "已成功加入購物車"))
    return redirect(request.referrer or url_for("carrito"))


@app.route("/carrito")
def carrito():
    """Muestra los ítems del carrito"""
    if not is_logged():
        flash(t("Debes iniciar sesión para ver el carrito", "You must log in to view the cart", "請先登入以查看購物車"))
        return redirect(url_for("login"))

    cart = get_cart()
    total_items = len(cart)
    return render_template("carrito.html", cart=cart, total_items=total_items)


@app.route("/cart_remove/<int:index>")
def cart_remove(index):
    """Elimina un ítem del carrito según su posición"""
    cart = get_cart()
    if 0 <= index < len(cart):
        eliminado = cart.pop(index)
        save_cart(cart)
        flash(t(f"Se eliminó {eliminado['empresa']} del carrito", f"Removed {eliminado['empresa']} from cart", f"已將 {eliminado['empresa']} 移出購物車"))
    else:
        flash(t("Ítem no encontrado", "Item not found", "找不到項目"))
    return redirect(url_for("carrito"))


@app.route("/cart_clear")
def cart_clear():
    """Vacía completamente el carrito"""
    save_cart([])
    flash(t("Carrito vaciado correctamente", "Cart cleared successfully", "購物車已清空"))
    return redirect(url_for("carrito"))


# =========================================================
# ERRORES PERSONALIZADOS CON TRADUCCIÓN
# =========================================================

@app.errorhandler(404)
def not_found(e):
    """Página no encontrada"""
    return render_template(
        "404.html",
        mensaje=t("Página no encontrada", "Page not found", "找不到頁面"),
        descripcion=t("La página que buscas no existe o fue movida.", "The page you are looking for does not exist or has been moved.", "您尋找的頁面不存在或已被移動。"),
    ), 404


@app.errorhandler(500)
def server_error(e):
    """Error interno del servidor"""
    return render_template(
        "500.html",
        mensaje=t("Error interno del servidor", "Internal server error", "伺服器內部錯誤"),
        descripcion=t("Ha ocurrido un error inesperado. Por favor, inténtalo más tarde.", "An unexpected error occurred. Please try again later.", "發生意外錯誤，請稍後再試。"),
    ), 500

# =========================================================
# ENDPOINTS FALTANTES: AYUDA, REGISTER_ROUTER, CLIENTES, RESET PASS, DASHBOARD, FAVICON
# (Pegar íntegro antes de la ejecución final)
# =========================================================

# Import extra (seguro aunque ya exista; Python lo permite)
from flask import send_from_directory

# ---------- FAVICON ----------
@app.route("/favicon.ico")
def favicon():
    """
    Sirve el favicon para evitar 404 y errores encadenados.
    Coloca tu archivo en: static/favicon.ico
    """
    try:
        return send_from_directory(os.path.join(STATIC_DIR), "favicon.ico")
    except Exception:
        # Si no existe, respondemos 204 (sin contenido) para no romper nada.
        return ("", 204)

# ---------- AYUDA ----------
@app.route("/ayuda")
def ayuda():
    """
    Página de ayuda (usada por el navbar en base.html).
    """
    return render_template("ayuda.html")

# ---------- REGISTER ROUTER ----------
@app.route("/register_router")
def register_router():
    """
    Pantalla para elegir tipo de registro (usa el template register_router.html).
    """
    return render_template("register_router.html")

# ---------- CLIENTES (LISTA) ----------
def _normaliza_items(items):
    """
    Convierte los items de USER_PROFILES a un formato estándar:
    [{'nombre': '...', 'tipo': 'oferta/servicio/demanda'}]
    """
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
        "tipo": profile.get("perfil_tipo") or profile.get("tipo") or "",
        "descripcion": profile.get("descripcion") or "",
        "items": _normaliza_items(profile.get("items")),
    }

def _armar_cliente_desde_users(username, data):
    # Fallback si no está en USER_PROFILES
    return {
        "username": username,
        "empresa": data.get("empresa", username),
        "rol": data.get("rol", ""),
        "tipo": data.get("perfil_tipo") or data.get("tipo") or "",
        "descripcion": data.get("descripcion", ""),
        "items": [],
    }

@app.route("/clientes")
def clientes():
    """
    Lista de empresas/usuarios para el template clientes.html
    - Prioriza USER_PROFILES por tener más datos (items, descripción).
    - Completa con USERS si algo no está en USER_PROFILES.
    """
    lista = []
    # 1) Desde USER_PROFILES (si existe en tu archivo)
    try:
        for u, profile in USER_PROFILES.items():
            lista.append(_armar_cliente_desde_profile(u, profile))
    except Exception:
        pass

    # 2) Completar con USERS faltantes
    try:
        ya = {c["username"] for c in lista}
        for u, data in USERS.items():
            if u not in ya:
                lista.append(_armar_cliente_desde_users(u, data))
    except Exception:
        pass

    # Orden simple por empresa
    lista.sort(key=lambda c: (c.get("empresa") or "").lower())
    return render_template("clientes.html", clientes=lista)

# ---------- CLIENTE DETALLE ----------
@app.route("/clientes/<username>")
def cliente_detalle(username):
    """
    Detalle de un cliente (usado por CLIENTE_DETALLE).
    """
    c = None
    # Buscar en USER_PROFILES
    try:
        if username in USER_PROFILES:
            c = _armar_cliente_desde_profile(username, USER_PROFILES[username])
    except Exception:
        pass

    # Fallback a USERS
    if not c:
        try:
            if username in USERS:
                c = _armar_cliente_desde_users(username, USERS[username])
        except Exception:
            pass

    if not c:
        abort(404)

    return render_template("cliente_detalle.html", c=c)

# ---------- ENVIAR MENSAJE A CLIENTE ----------
@app.route("/clientes/<username>/mensaje", methods=["POST"])
def enviar_mensaje(username):
    """
    Maneja el formulario de mensaje en CLIENTE_DETALLE.
    Solo simula el envío (flash) para esta demo.
    """
    if not is_logged():
        flash(t("Debes iniciar sesión para enviar mensajes",
                "You must log in to send messages",
                "請先登入以發送訊息"))
        return redirect(url_for("login"))

    mensaje = (request.form.get("mensaje") or "").strip()
    if not mensaje:
        flash(t("El mensaje no puede estar vacío",
                "Message cannot be empty",
                "訊息不可為空"))
        return redirect(url_for("cliente_detalle", username=username))

    flash(t("Mensaje enviado correctamente",
            "Message sent successfully",
            "訊息已成功發送"))
    return redirect(url_for("cliente_detalle", username=username))

# ---------- RESET DE CONTRASEÑA ----------
@app.route("/password_reset_request", methods=["GET", "POST"])
def password_reset_request():
    """
    Solicitud de reseteo de contraseña (renderiza password_reset_request.html).
    En POST solo simula que enviamos instrucciones y pasa al form de nuevo password.
    """
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        # Aquí podrías validar si usuario existe y generar token.
        flash(t("Si el usuario existe, enviaremos instrucciones a su correo.",
                "If the user exists, we'll email recovery instructions.",
                "若帳號存在，我們將寄出重設指示。"))
        return redirect(url_for("password_reset_form"))

    return render_template("password_reset_request.html")

@app.route("/password_reset_form", methods=["GET", "POST"])
def password_reset_form():
    """
    Formulario para establecer nueva contraseña (renderiza password_reset_form.html).
    En POST solo simula actualización y redirige a login.
    """
    if request.method == "POST":
        nueva_password = request.form.get("nueva_contraseña") or request.form.get("nueva_contrasena")
        if not (nueva_password or "").strip():
            flash(t("La nueva contraseña es obligatoria",
                    "New password is required",
                    "必須填寫新密碼"))
            return redirect(url_for("password_reset_form"))

        flash(t("Contraseña actualizada",
                "Password updated",
                "密碼已更新"))
        return redirect(url_for("login"))

    return render_template("password_reset_form.html")

# ---------- DASHBOARD (referido por PERFIL) ----------
@app.route("/dashboard")
def dashboard():
    """
    Enlace seguro desde PERFIL. Si no tienes template de dashboard,
    redirigimos al home para evitar TemplateNotFound.
    """
    return redirect(url_for("home"))

# ---------- (Opcional) Register con preselección por ?tipo= ----------
# Si quieres, puedes leer request.args.get("tipo") dentro de tu register() existente
# para preseleccionar roles/tipos en el template register.html.
# No lo sobreescribo aquí para respetar tu función actual.

# =========================================================
# EJECUCIÓN FINAL DE LA APLICACIÓN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
