# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.9 corregida)
# Autor: Christopher Ponce & GPT-5
# ---------------------------------------------------------
# Parte 1: Configuración · Traducción · Usuarios ficticios (2 por rol)
#          Estructuras · Idioma · Home · (stub) Perfil
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
    """Traducción automática según idioma activo en sesión."""
    lang = session.get("lang", "es")
    if lang == "es":
        return text
    # Soporta llamadas con traducciones inline
    if en or zh:
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
    session["lang"] = lang if lang in LANGS else "es"
    return redirect(request.referrer or url_for("home"))

# ---------------------------------------------------------
# 👥 USUARIOS FICTICIOS — 2 por rol real (conforme a tus reglas)
#    Perfiles:
#    - Compraventa: Productor, Packing, Frigorífico, Exportador
#    - Servicios: Transporte, Packing, Frigorífico, Extraportuarios, Agencia de Aduanas
#    - Mixto: Packing, Frigorífico
#    - Extranjero: Cliente Extranjero
#    - Administrador: (interno)
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

    # ===== COMPRAVENTA: PRODUCTOR (x2) =====
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

    # ===== COMPRAVENTA: PACKING (x2) =====
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
        "tipo": "compraventa",
        "rol": "Packing",
        "empresa": "AgroPacking Ltda.",
        "descripcion": "Packing con capacidad de compra/venta de fruta.",
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

    # ===== COMPRAVENTA: FRIGORÍFICO (x2) =====
    "frigorifico_cv1@ws.com": {
        "nombre": "Carlos Frías",
        "email": "frigorifico_cv1@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Frigorífico",
        "empresa": "Frigo Andes CV",
        "descripcion": "Frigorífico que compra y vende fruta.",
        "fecha": "2025-10-12 12:00",
        "username": "frigorifico_cv1",
        "pais": "CL",
        "direccion": "Talca, Maule",
        "telefono": "+56 9 4567 8901",
        "rut_doc": "",
        "items": [
            {"nombre": "Uva embalada", "detalle": "Calibre 20+ export", "precio": "USD 3.00/kg"}
        ]
    },
    "frigorifico_cv2@ws.com": {
        "nombre": "Andrea Vega",
        "email": "frigorifico_cv2@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Frigorífico",
        "empresa": "ColdTrade CV",
        "descripcion": "Opera como frigorífico compraventa.",
        "fecha": "2025-10-12 12:30",
        "username": "frigorifico_cv2",
        "pais": "CL",
        "direccion": "Los Andes, Valparaíso",
        "telefono": "+56 9 6789 4455",
        "rut_doc": "",
        "items": [
            {"nombre": "Arándano a Exportador", "detalle": "12x125g", "precio": "USD 5.00/kg"}
        ]
    },

    # ===== COMPRAVENTA: EXPORTADOR (x2) =====
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
            {"nombre": "Cereza Lapins 9.5", "Detalle": "Clamshell", "precio": "USD 6.20/kg"},
            {"nombre": "Arándano Duke", "detalle": "12x125g", "precio": "USD 5.10/kg"}
        ]
    },
    "exportador2@ws.com": {
        "nombre": "Juan Torres",
        "email": "exportador2@ws.com",
        "password": "1234",
        "tipo": "compraventa",
        "rol": "Exportador",
        "empresa": "ChileFruits Export",
        "descripcion": "Exporta fruta a Asia y Europa.",
        "fecha": "2025-10-13 08:15",
        "username": "exportador2",
        "pais": "CL",
        "direccion": "Quillota, Valparaíso",
        "telefono": "+56 9 7333 5566",
        "rut_doc": "",
        "items": [
            {"nombre": "Uva Thompson", "detalle": "Calibre grande", "precio": "USD 4.10/kg"}
        ]
    },

    # ===== SERVICIOS: TRANSPORTE (x2) =====
    "transporte1@ws.com": {
        "nombre": "Trans Andino",
        "email": "transporte1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Transporte",
        "empresa": "LogiTrans SpA",
        "descripcion": "Transporte refrigerado nacional.",
        "fecha": "2025-10-13 09:00",
        "username": "transporte1",
        "pais": "CL",
        "direccion": "Santiago",
        "telefono": "+56 9 8888 0001",
        "rut_doc": "",
        "items": [
            {"nombre": "Flete reefer 28 pallets", "detalle": "SCL → Valpo", "precio": "USD 480/viaje"}
        ]
    },
    "transporte2@ws.com": {
        "nombre": "Ruta Fría",
        "email": "transporte2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Transporte",
        "empresa": "RutaFría Ltda.",
        "descripcion": "Cobertura zona centro-sur.",
        "fecha": "2025-10-13 09:10",
        "username": "transporte2",
        "pais": "CL",
        "direccion": "Rancagua",
        "telefono": "+56 9 8888 0002",
        "rut_doc": "",
        "items": [
            {"nombre": "Flete full 30 pallets", "detalle": "Curicó → San Antonio", "precio": "USD 520/viaje"}
        ]
    },

    # ===== SERVICIOS: PACKING (x2) =====
    "packing_srv1@ws.com": {
        "nombre": "PackService 1",
        "email": "packing_srv1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Packing",
        "empresa": "PackService Ltda.",
        "descripcion": "Sólo venta de servicio de packing.",
        "fecha": "2025-10-13 09:20",
        "username": "packing_srv1",
        "pais": "CL",
        "direccion": "San Felipe",
        "telefono": "+56 9 4444 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Embalaje flowpack", "detalle": "BRC", "precio": "USD 0.09/un"}
        ]
    },
    "packing_srv2@ws.com": {
        "nombre": "PackService 2",
        "email": "packing_srv2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Packing",
        "empresa": "EmpaquePlus",
        "descripcion": "Servicio de empaque por kilo.",
        "fecha": "2025-10-13 09:25",
        "username": "packing_srv2",
        "pais": "CL",
        "direccion": "Quillota",
        "telefono": "+56 9 4444 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Reembalaje express", "detalle": "Turno noche", "precio": "USD 0.14/kg"}
        ]
    },

    # ===== SERVICIOS: FRIGORÍFICO (x2) =====
    "frigo_srv1@ws.com": {
        "nombre": "Frigo Service 1",
        "email": "frigo_srv1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Frigorífico",
        "empresa": "PolarService",
        "descripcion": "Solo servicio de frío.",
        "fecha": "2025-10-13 09:30",
        "username": "frigo_srv1",
        "pais": "CL",
        "direccion": "Talca",
        "telefono": "+56 9 5555 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Túnel de frío", "detalle": "Descenso rápido", "precio": "USD 0.06/kg"}
        ]
    },
    "frigo_srv2@ws.com": {
        "nombre": "Frigo Service 2",
        "email": "frigo_srv2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Frigorífico",
        "empresa": "FrescoCold",
        "descripcion": "Cámara fría y monitoreo.",
        "fecha": "2025-10-13 09:35",
        "username": "frigo_srv2",
        "pais": "CL",
        "direccion": "Los Andes",
        "telefono": "+56 9 5555 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Cámara 0–2°C", "detalle": "Monitoreo IoT", "precio": "USD 0.16/kg/día"}
        ]
    },

    # ===== SERVICIOS: EXTRAPORTUARIOS (x2) =====
    "extra1@ws.com": {
        "nombre": "Depot Extra 1",
        "email": "extra1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Extraportuarios",
        "empresa": "ExtraPort S.A.",
        "descripcion": "Servicios extraportuarios para exportador.",
        "fecha": "2025-10-13 09:40",
        "username": "extraport1",
        "pais": "CL",
        "direccion": "San Antonio",
        "telefono": "+56 9 6666 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Consolidación contenedor", "detalle": "Reefer 40'", "precio": "USD 180/ctr"}
        ]
    },
    "extra2@ws.com": {
        "nombre": "Depot Extra 2",
        "email": "extra2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Extraportuarios",
        "empresa": "DepotAndes",
        "descripcion": "Sólo a exportadores.",
        "fecha": "2025-10-13 09:45",
        "username": "extraport2",
        "pais": "CL",
        "direccion": "Valparaíso",
        "telefono": "+56 9 6666 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Pre-trip contenedor", "detalle": "PTI Reefer", "precio": "USD 95/ctr"}
        ]
    },

    # ===== SERVICIOS: AGENCIA DE ADUANAS (x2) =====
    "aduana1@ws.com": {
        "nombre": "Aduanas Pacífico",
        "email": "aduana1@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Agencia de Aduanas",
        "empresa": "Agencia Pacífico",
        "descripcion": "Despacho de exportación.",
        "fecha": "2025-10-13 09:50",
        "username": "aduana1",
        "pais": "CL",
        "direccion": "Santiago",
        "telefono": "+56 2 7777 1111",
        "rut_doc": "",
        "items": [
            {"nombre": "Tramitación DUS", "detalle": "Servicio a exportadores", "precio": "USD 120/embarque"}
        ]
    },
    "aduana2@ws.com": {
        "nombre": "Aduanas Andes",
        "email": "aduana2@ws.com",
        "password": "1234",
        "tipo": "servicios",
        "rol": "Agencia de Aduanas",
        "empresa": "AduAndes",
        "descripcion": "Trámites y coordinación.",
        "fecha": "2025-10-13 09:55",
        "username": "aduana2",
        "pais": "CL",
        "direccion": "Valparaíso",
        "telefono": "+56 2 7777 2222",
        "rut_doc": "",
        "items": [
            {"nombre": "Certificados origen", "detalle": "SAG/Chamber", "precio": "USD 75/doc"}
        ]
    },

    # ===== MIXTO: PACKING (x2) =====
    "packing_mx1@ws.com": {
        "nombre": "PackMix Uno",
        "email": "packing_mx1@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Packing",
        "empresa": "MixPack Uno",
        "descripcion": "Vende fruta y servicios de packing.",
        "fecha": "2025-10-13 10:10",
        "username": "packingmx1",
        "pais": "CL",
        "direccion": "San Felipe",
        "telefono": "+56 9 4444 3333",
        "rut_doc": "",
        "items": [
            {"nombre": "Venta Uva embalada", "detalle": "A frigorífico/exportador", "precio": "USD 3.10/kg"},
            {"nombre": "Servicio packing", "detalle": "Flowpack BRC", "precio": "USD 0.10/un"}
        ]
    },
    "packing_mx2@ws.com": {
        "nombre": "PackMix Dos",
        "email": "packing_mx2@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Packing",
        "empresa": "MixPack Dos",
        "descripcion": "Compra a productor y vende servicio.",
        "fecha": "2025-10-13 10:12",
        "username": "packingmx2",
        "pais": "CL",
        "direccion": "Rancagua",
        "telefono": "+56 9 4444 4444",
        "rut_doc": "",
        "items": [
            {"nombre": "Servicio reembalaje", "detalle": "Turno noche", "precio": "USD 0.13/kg"}
        ]
    },

    # ===== MIXTO: FRIGORÍFICO (x2) =====
    "frigo_mx1@ws.com": {
        "nombre": "FrigoMix Uno",
        "email": "frigo_mx1@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Frigorífico",
        "empresa": "FrigoMix Uno",
        "descripcion": "Vende fruta y servicio de frío.",
        "fecha": "2025-10-13 10:20",
        "username": "frigomx1",
        "pais": "CL",
        "direccion": "Talca",
        "telefono": "+56 9 5555 3333",
        "rut_doc": "",
        "items": [
            {"nombre": "Fruta refrigerada", "detalle": "Para exportación", "precio": "USD 3.25/kg"},
            {"nombre": "Cámara 0–2°C", "detalle": "IoT", "precio": "USD 0.15/kg/día"}
        ]
    },
    "frigo_mx2@ws.com": {
        "nombre": "FrigoMix Dos",
        "email": "frigo_mx2@ws.com",
        "password": "1234",
        "tipo": "mixto",
        "rol": "Frigorífico",
        "empresa": "FrigoMix Dos",
        "descripcion": "Compra a productor/packing y vende servicio.",
        "fecha": "2025-10-13 10:25",
        "username": "frigomx2",
        "pais": "CL",
        "direccion": "Los Andes",
        "telefono": "+56 9 5555 4444",
        "rut_doc": "",
        "items": [
            {"nombre": "Servicio túnel de frío", "detalle": "Descenso rápido", "precio": "USD 0.07/kg"}
        ]
    },

    # ===== EXTRANJERO: CLIENTE EXTRANJERO (x2) =====
    "cliente_ext1@ws.com": {
        "nombre": "Buyer Asia Ltd.",
        "email": "cliente_ext1@ws.com",
        "password": "1234",
        "tipo": "extranjero",
        "rol": "Cliente Extranjero",
        "empresa": "Buyer Asia Ltd.",
        "descripcion": "Cliente internacional (solo compra a Exportadores).",
        "fecha": "2025-10-13 11:00",
        "username": "extbuyer1",
        "pais": "CN",
        "direccion": "Shanghai",
        "telefono": "+86 21 5555 0001",
        "rut_doc": "",
        "items": []
    },
    "cliente_ext2@ws.com": {
        "nombre": "EuroFresh GmbH",
        "email": "cliente_ext2@ws.com",
        "password": "1234",
        "tipo": "extranjero",
        "rol": "Cliente Extranjero",
        "empresa": "EuroFresh GmbH",
        "descripcion": "Cliente internacional (solo compra a Exportadores).",
        "fecha": "2025-10-13 11:05",
        "username": "extbuyer2",
        "pais": "DE",
        "direccion": "Hamburg",
        "telefono": "+49 40 5555 0002",
        "rut_doc": "",
        "items": []
    },
}

# ---------------------------------------------------------
# 🏠 PÁGINA PRINCIPAL (INDEX)
# ---------------------------------------------------------
@app.route("/")
def home():
    titulo = t("Bienvenido a Window Shopping")
    return render_template("index.html", titulo=titulo)

# ---------------------------------------------------------
# 🧷 STUB MÍNIMO: PERFIL
# (Evita el BuildError por url_for('perfil') en base.html)
# ---------------------------------------------------------
@app.route("/perfil")
def perfil():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("perfil.html", user=user, titulo=t("Perfil"))
# =========================================================
# 🌐 Parte 2: Login · Logout · Registro con filtros por tipo/rol
# =========================================================

from uuid import uuid4  # ya usado luego para publicaciones, no hace daño si se reusa

# ---------- Catálogo de tipos -> roles permitidos ----------
TIPOS_ROLES = {
    "compraventa": ["Productor", "Packing", "Frigorífico", "Exportador"],
    "servicio":    ["Transporte", "Packing", "Frigorífico", "Extraportuarios", "Agencia de Aduanas"],
    "mixto":       ["Packing", "Frigorífico"],
    "extranjero":  ["Cliente Extranjero"],
}

# Para mostrar títulos bonitos en UI
TIPO_TITULO = {
    "compraventa": "Compraventa",
    "servicio": "Servicios",
    "mixto": "Mixto",
    "extranjero": "Extranjero",
}

def normaliza_tipo(t):
    """Normaliza alias desde URL o UI a nuestras claves de TIPOS_ROLES."""
    if not t:
        return None
    t = t.strip().lower()
    # admitir alias comunes
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
    """True si el rol (case-insensitive) pertenece al tipo elegido."""
    if not rol or not tipo_norm:
        return False
    roles = TIPOS_ROLES.get(tipo_norm, [])
    return any(rol.strip().lower() == r.lower() for r in roles)

def titulo_tipo(tipo_norm):
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
#   (muestra botones → cliente, servicio, compraventa, mixto)
# ---------------------------------------------------------
@app.route("/register_router")
def register_router():
    # Solo muestra la pantalla de selección (usa tu template register_router.html)
    return render_template("register_router.html", titulo=t("Selecciona el tipo de cuenta"))

# ---------------------------------------------------------
# 📝 REGISTRO: Formulario según tipo seleccionado
#   GET /register/<tipo>  → muestra register.html con SOLO los roles permitidos
# ---------------------------------------------------------
@app.route("/register/<tipo>", methods=["GET"])
def register_form(tipo):
    tipo_norm = normaliza_tipo(tipo)
    if not tipo_norm:
        flash(t("Tipo de cuenta inválido", "Invalid account type", "无效的帐户类型"), "error")
        return redirect(url_for("register_router"))

    # Guardamos el tipo elegido en sesión para validar en POST
    session["register_tipo"] = tipo_norm

    # Estructura que espera tu register.html: dict {Titulo Bonito: [roles...]}
    tipos_ctx = {titulo_tipo(tipo_norm): TIPOS_ROLES[tipo_norm]}
    return render_template(
        "register.html",
        titulo=t("Registro de Usuario"),
        tipos=tipos_ctx
    )

# ---------------------------------------------------------
# ✅ REGISTRO: POST con validaciones estrictas de tipo/rol
# ---------------------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    empresa = (request.form.get("empresa") or "").strip()
    rol = (request.form.get("rol") or "").strip()
    pais = (request.form.get("pais") or "CL").strip().upper()
    direccion = (request.form.get("direccion") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()

    # 1) Email único
    if email in USERS:
        flash(t("El usuario ya existe", "User already exists", "用户已存在"), "error")
        return redirect(url_for("register_router"))

    # 2) Tipo debe venir de la selección anterior
    tipo_norm = session.get("register_tipo")
    if not tipo_norm:
        # Si no viene, forzamos a pasar por el router
        flash(t("Debes elegir un tipo de cuenta", "You must choose an account type", "请先选择帐户类型"), "error")
        return redirect(url_for("register_router"))

    # 3) Validar que el rol pertenece al tipo seleccionado
    if not rol_valido_para_tipo(rol, tipo_norm):
        flash(
            t("Rol no permitido para el tipo seleccionado",
              "Role not allowed for the selected type",
              "所选类型不允许该角色"),
            "error"
        )
        return redirect(url_for("register_form", tipo=tipo_norm))

    # 4) Reglas específicas ligeras (p. ej. Extranjero)
    if tipo_norm == "extranjero" and rol.lower() != "cliente extranjero":
        flash(t("Para perfil extranjero el rol debe ser 'Cliente Extranjero'",
                "Foreign profile must be 'Foreign Client'",
                "海外用户的角色必须为“客户（海外）”"), "error")
        return redirect(url_for("register_form", tipo=tipo_norm))

    # 5) Crear usuario
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

    # Limpia el tipo elegido para no contaminar otro registro
    session.pop("register_tipo", None)

    flash(t("Usuario registrado correctamente", "User registered successfully", "注册成功"), "success")
    return redirect(url_for("login"))
# =========================================================
# 🌐 Parte 3: Permisos · Validaciones · Helpers · Middleware
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
# ⚙️ HELPERS DE LÓGICA
# ---------------------------------------------------------
def get_user():
    """Devuelve el usuario logueado o None."""
    return session.get("user")

def puede_publicar(usuario):
    """Determina si el usuario puede publicar productos o servicios."""
    if not usuario:
        return False
    rol = usuario.get("rol", "")
    tipo = usuario.get("tipo", "")
    # Solo usuarios de compraventa o mixtos pueden publicar productos
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
    """Verifica que el usuario en sesión siga existiendo."""
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
# 🌐 Parte 4: Dashboards · Publicaciones · Carrito · Clientes
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
        producto = request.form.get("producto", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "").strip() or "Consultar"
        tipo_pub = user.get("tipo", "compraventa")

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
            "precio": precio,
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

    # validación permiso de compra
    if not puede_ver_publicacion(user, {"rol": pub["rol"], "tipo": pub["tipo"]}):
        flash(t("No tienes permiso para comprar este ítem",
                "You are not allowed to buy this item", "無權購買此項目"), "error")
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
# 🧾 CLIENTES / EMPRESAS VISIBLES SEGÚN PERMISOS
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
        # Verificación: solo mostrar empresas que puede comprar/ver
        if puede_ver_publicacion(user, {"rol": info["rol"], "tipo": info["tipo"]}):
            visibles.append(info)

    return render_template(
        "clientes.html",
        user=user,
        clientes=visibles,
        titulo=t("Empresas Registradas")
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
# ⚙️ STATUS JSON (debug / salud del servidor)
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
# 💡 PÁGINAS INFORMATIVAS (Ayuda / Acerca de)
# ---------------------------------------------------------
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo=t("Centro de Ayuda"))

@app.route("/acerca")
def acerca():
    return render_template("acerca.html", titulo=t("Acerca de Window Shopping"))

# ---------------------------------------------------------
# 🏁 EJECUCIÓN LOCAL
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🌐 Servidor Flask corriendo en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
