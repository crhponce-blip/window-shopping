# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 Estable) — PARTE 1/4
# Configuración, DB, Helpers, Caché USERS, Visibilidad
# =========================================================

import os, sqlite3, uuid
from datetime import timedelta, datetime
from typing import List, Dict, Any
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
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
def allowed_file(filename:str)->bool: return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXT

# =========================================================
# 🌎 MULTI-IDIOMA
# =========================================================
def t(es,en="",zh=""): lang=session.get("lang","es"); 
    return en if lang=="en" and en else zh if lang=="zh" and zh else es
app.jinja_env.globals.update(t=t)

# =========================================================
# 🧩 TIPOS Y ROLES
# =========================================================
TIPOS_VALIDOS={"compras","servicios","mixto","compraventa"}
ROLES_POR_TIPO={"compras":["Cliente extranjero"],"servicios":["Agencia de aduana","Transporte","Extraportuario","Packing","Frigorífico"],"compraventa":["Productor(planta)","Packing","Frigorífico","Exportador"],"mixto":["Packing","Frigorífico"]}

# =========================================================
# 🗄️ BASE DE DATOS (SQLite)
# =========================================================
DB_PATH=os.path.join(BASE_DIR,"users.db")
def init_db():
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,empresa TEXT,rol TEXT,tipo TEXT,pais TEXT,rut_doc TEXT,direccion TEXT,telefono TEXT)""")
    conn.commit(); conn.close()
def migrate_add_column(colname:str):
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    try: c.execute(f"ALTER TABLE users ADD COLUMN {colname} TEXT"); conn.commit()
    except sqlite3.OperationalError: pass
    finally: conn.close()
def migrate_add_rut_doc(): migrate_add_column("rut_doc")
def migrate_add_contact_fields(): [migrate_add_column(x) for x in ["direccion","telefono"]]
def get_user(email:str):
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; c=conn.cursor(); c.execute("SELECT * FROM users WHERE email=?",(email,)); u=c.fetchone(); conn.close(); return u
def get_all_users()->List[sqlite3.Row]:
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; c=conn.cursor(); c.execute("SELECT * FROM users"); r=c.fetchall(); conn.close(); return r
def add_user(email,pw,empresa,rol,tipo,pais,rut_doc=None,direccion=None,telefono=None):
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    try: c.execute("INSERT INTO users(email,password,empresa,rol,tipo,pais,rut_doc,direccion,telefono)VALUES(?,?,?,?,?,?,?,?,?)",(email,pw,empresa,rol,tipo,pais,rut_doc,direccion,telefono)); conn.commit(); print(f"🆕 Usuario creado: {email}")
    except sqlite3.IntegrityError: print(f"⚠️ El usuario {email} ya existe.")
    finally: conn.close()
def update_user_fields(email:str,**fields):
    if not fields: return
    cols=", ".join([f"{k}=?" for k in fields.keys()]); vals=list(fields.values())+[email]
    conn=sqlite3.connect(DB_PATH); c=conn.cursor(); c.execute(f"UPDATE users SET {cols} WHERE email=?",vals); conn.commit(); conn.close()

# =========================================================
# 👤 SEMILLAS Y CARGA DE USUARIOS
# =========================================================
def create_admin_if_missing():
    if not get_user("admin@ws.com"):
        add_user("admin@ws.com",generate_password_hash("1234"),"Window Shopping Admin","Exportador","compraventa","CL",direccion="Santiago CL",telefono="+56 2 2222 2222")
        print("✅ Usuario admin creado (1234)")

def seed_demo_users():
    seeds=[
        # Productor(planta)
        ("prod1@demo.cl","Productora Valle SpA","Productor(planta)","compraventa","CL"),
        ("prod2@demo.cl","Agrícola del Sol Ltda.","Productor(planta)","compraventa","CL"),
        # Packing
        ("pack1@demo.cl","Packing Maule SpA","Packing","mixto","CL"),
        ("pack2@demo.cl","Empaque Sur Ltda.","Packing","mixto","CL"),
        # Frigorífico
        ("frio1@demo.cl","Frío Centro SpA","Frigorífico","mixto","CL"),
        ("frio2@demo.cl","Frío Andes Ltda.","Frigorífico","mixto","CL"),
        # Exportador
        ("exp1@demo.cl","Exportadora Andes","Exportador","compraventa","CL"),
        ("exp2@demo.cl","Exportaciones del Maule","Exportador","compraventa","CL"),
        # Agencia de aduana
        ("aduana1@demo.cl","Agencia Andes","Agencia de aduana","servicios","CL"),
        ("aduana2@demo.cl","Agencia Pacífico","Agencia de aduana","servicios","CL"),
        # Transporte
        ("trans1@demo.cl","Transporte Sur S.A.","Transporte","servicios","CL"),
        ("trans2@demo.cl","Camiones del Valle","Transporte","servicios","CL"),
        # Extraportuario
        ("extra1@demo.cl","Depósito San Antonio","Extraportuario","servicios","CL"),
        ("extra2@demo.cl","Puerto Extrema SpA","Extraportuario","servicios","CL"),
        # Cliente extranjero
        ("cliente1@ext.com","Importadora Asia Ltd.","Cliente extranjero","compras","US"),
        ("cliente2@ext.com","Global Imports Co.","Cliente extranjero","compras","CN"),
    ]
    for e,em,ro,ti,pa in seeds:
        if not get_user(e): add_user(e,generate_password_hash("1234"),em,ro,ti,pa)

USERS:Dict[str,Dict[str,Any]]={}
def load_users_cache():
    USERS.clear()
    for r in get_all_users():
        USERS[r["email"]]={"email":r["email"],"empresa":r["empresa"] or r["email"],"rol":r["rol"] or "","tipo":r["tipo"] or "","pais":r["pais"] or "","direccion":r["direccion"] or "","telefono":r["telefono"] or "","descripcion":"","items":[]}

# =========================================================
# 🧩 HELPERS DE CLIENTES
# =========================================================
def _normaliza_items(items:List[Dict[str,Any]]|None)->List[Dict[str,Any]]:
    return [{"nombre":it.get("producto") or it.get("servicio") or "Item","tipo":it.get("tipo") or "item","detalle":it.get("descripcion") or it.get("detalle") or ""} for it in (items or [])]
def _armar_cliente_desde_users(username:str,data:Dict[str,Any])->Dict[str,Any]:
    return {"username":username,"empresa":data.get("empresa",username),"rol":data.get("rol",""),"tipo":data.get("tipo",""),"descripcion":data.get("descripcion",""),"items":_normaliza_items(data.get("items")),"email":data.get("email",username),"pais":data.get("pais",""),"direccion":data.get("direccion",""),"telefono":data.get("telefono","")}
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 Estable) — PARTE 2/4
# Rutas públicas, Login/Logout, Dashboards, Carrito
# =========================================================

# -- Helpers de sesión (compactos) --
def _row_to_dict(row): return dict(row) if row else None
def current_user():
    u = session.get("user")
    if not u: return None
    if isinstance(u, str): return _row_to_dict(get_user(u))
    if isinstance(u, dict): return u
    try:
        import sqlite3 as _s
        if isinstance(u, _s.Row): return dict(u)
    except Exception: pass
    return None
def login_required():
    if not current_user():
        flash(t("Debes iniciar sesión.","You must log in.","您必須登入"),"error")
        return redirect(url_for("login"))
    return None

# -- Redirección por rol a dashboard --
DASHBOARD_BY_ROLE={
    "Cliente extranjero":"dashboard_ext",
    "Productor(planta)":"dashboard",
    "Packing":"dashboard",
    "Frigorífico":"dashboard",
    "Exportador":"dashboard",
    "Agencia de aduana":"dashboard",
    "Transporte":"dashboard",
    "Extraportuario":"dashboard",
}
def dashboard_for(user):
    rol=(user or {}).get("rol","") or ""
    return DASHBOARD_BY_ROLE.get(rol,"dashboard")

# -- Login / Logout (corrige BuildError de 'dashboard_ext') --
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=(request.form.get("email","") or "").strip().lower()
        password=(request.form.get("password","") or "").strip()
        u=get_user(email)
        if not u:
            flash(t("Usuario no encontrado","User not found","未找到用戶"),"error"); return redirect(url_for("login"))
        if not check_password_hash(u["password"], password):
            flash(t("Contraseña incorrecta","Incorrect password","密碼錯誤"),"error"); return redirect(url_for("login"))
        session["user"]=email; flash(t("Inicio de sesión correcto","Login successful","登入成功"),"success")
        endpoint=dashboard_for(_row_to_dict(u))
        return redirect(url_for(endpoint))
    return render_template("login.html", titulo=t("Iniciar sesión","Login","登入"))

@app.route("/logout")
def logout():
    session.pop("user",None)
    flash(t("Sesión cerrada correctamente","Logged out","登出成功"),"info")
    return redirect(url_for("home"))

# -- Dashboards (cliente externo + genérico por rol) --
@app.route("/dashboard_ext")
def dashboard_ext():
    guard=login_required(); 
    if guard: return guard
    user=current_user()
    if (user or {}).get("rol")!="Cliente extranjero":
        flash(t("No tienes permiso para este panel.","You don't have permission for this panel.","你沒有此面板的權限"),"error")
        return redirect(url_for(dashboard_for(user)))
    visibles=publicaciones_visibles(user, PUBLICACIONES)
    return render_template("dashboard_ext.html", user=user, publicaciones=visibles, titulo=t("Panel Cliente Extranjero","External Client Dashboard","國際客戶面板"))

@app.route("/dashboard")
def dashboard():
    guard=login_required(); 
    if guard: return guard
    user=current_user()
    visibles=publicaciones_visibles(user, PUBLICACIONES)
    return render_template("dashboard.html", user=user, publicaciones=visibles, titulo=t("Panel","Dashboard","儀表板"))

# -- Carrito mínimo (evita BuildError por url_for('carrito')) --
@app.route("/carrito")
def carrito():
    guard=login_required(); 
    if guard: return guard
    user=current_user()
    cart=session.get("cart",[])
    return render_template("carrito.html", user=user, cart=cart, titulo=t("Carrito","Cart","購物車"))

@app.route("/carrito/add/<pub_id>", methods=["POST","GET"])
def carrito_add(pub_id):
    guard=login_required(); 
    if guard: return guard
    cart=session.get("cart",[])
    if pub_id and pub_id not in cart: cart.append(pub_id)
    session["cart"]=cart
    flash(t("Agregado al carrito.","Added to cart.","已加入購物車"),"success")
    return redirect(request.referrer or url_for("carrito"))

@app.route("/carrito/remove/<pub_id>", methods=["POST","GET"])
def carrito_remove(pub_id):
    guard=login_required(); 
    if guard: return guard
    cart=session.get("cart",[])
    if pub_id in cart: cart=[x for x in cart if x!=pub_id]
    session["cart"]=cart
    flash(t("Eliminado del carrito.","Removed from cart.","已從購物車移除"),"info")
    return redirect(request.referrer or url_for("carrito"))

# -- Home y auxiliares públicos (coherentes con Parte 1) --
@app.route("/")
def home():
    return render_template("home.html", titulo=t("Inicio","Home","主頁"))

@app.route("/register_router")
def register_router():
    return render_template("register_router.html", titulo=t("Registrarse","Register","註冊"))
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 Estable) — PARTE 3/4
# Registro, Subida de archivo, Idioma, Errores
# =========================================================

# -- Guardado de archivos subidos --
def save_uploaded_file(file_storage):
    if not file_storage or file_storage.filename=="": return None
    filename=secure_filename(file_storage.filename)
    if not allowed_file(filename): return None
    base,ext=os.path.splitext(filename); unique=f"{base}_{uuid.uuid4().hex[:8]}{ext}"
    dest=os.path.join(app.config["UPLOAD_FOLDER"],unique); file_storage.save(dest)
    return f"uploads/{unique}"

# -- Registro (router + formulario dinámico) --
@app.route("/register/<tipo>", methods=["GET","POST"])
def register(tipo):
    tipo=tipo.lower()
    if tipo not in TIPOS_VALIDOS: abort(404)
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","").strip()
        empresa=request.form.get("empresa","").strip(); rol=request.form.get("rol","").strip(); pais=request.form.get("pais","").strip()
        direccion=request.form.get("direccion","").strip() or None; telefono=request.form.get("telefono","").strip() or None
        rut_file=request.files.get("rut_doc"); rut_path=save_uploaded_file(rut_file)
        if not all([email,pw,empresa,rol,pais]):
            flash(t("Completa todos los campos requeridos","Complete all required fields","請填寫所有必填欄位"),"error")
            return redirect(url_for("register",tipo=tipo))
        if get_user(email):
            flash(t("El correo ya está registrado","Email already registered","郵箱已註冊"),"error")
            return redirect(url_for("register",tipo=tipo))
        hashed=generate_password_hash(pw)
        add_user(email,hashed,empresa,rol,tipo,pais,rut_doc=rut_path,direccion=direccion,telefono=telefono)
        load_users_cache()
        flash(t("Registro completado con éxito","Registration successful","註冊成功"),"success")
        return redirect(url_for("login"))
    roles=ROLES_POR_TIPO.get(tipo,[]); return render_template("register.html",tipo=tipo,roles=roles,titulo=t("Registro","Register","註冊"))

@app.route("/register_router")
def register_router():
    return render_template("register_router.html",titulo=t("Seleccionar tipo de registro","Select registration type","選擇註冊類型"))

# -- Cambio de idioma (3 rutas compatibles) --
@app.route("/lang/<code>")
def lang(code):
    if code in ["es","en","zh"]:
        session["lang"]=code; flash(t("Idioma actualizado correctamente.","Language updated successfully.","語言已成功更新"),"info")
    else:
        flash(t("Idioma no soportado.","Unsupported language.","不支援的語言"),"error")
    return redirect(request.referrer or url_for("home"))

@app.route("/set_lang/<lang>")
def set_lang_get(lang):
    if lang in ["es","en","zh"]:
        session["lang"]=lang; flash(t("Idioma actualizado correctamente.","Language updated successfully.","語言已成功更新"),"info")
    else:
        flash(t("Idioma no soportado.","Unsupported language.","不支援的語言"),"error")
    return redirect(request.referrer or url_for("home"))

@app.route("/set_lang", methods=["POST"])
def set_lang_post():
    lang=request.form.get("lang")
    if lang in ["es","en","zh"]:
        session["lang"]=lang; flash(t("Idioma actualizado correctamente.","Language updated successfully.","語言已成功更新"),"info")
    else:
        flash(t("Idioma no soportado.","Unsupported language.","不支援的語言"),"error")
    return redirect(request.referrer or url_for("home"))

# -- Errores personalizados --
@app.errorhandler(404)
def error_404(e):
    return render_template("error.html",code=404,message=t("Página no encontrada","Page not found","找不到頁面")),404

@app.errorhandler(500)
def error_500(e):
    return render_template("error.html",code=500,message=t("Error interno del servidor","Internal server error","伺服器內部錯誤")),500
# =========================================================
# 🌐 WINDOW SHOPPING — Flask App (v3.5 Estable) — PARTE 4/4
# Perfil, Mensajería, Clientes, Ayuda, Acerca, Status, Run
# =========================================================

# -- Perfil del usuario --
@app.route("/perfil", methods=["GET","POST"])
def perfil():
    user=current_user()
    if not user:
        flash(t("Debes iniciar sesión para ver tu perfil.","You must log in to view your profile.","您必須登入以檢視個人資料"),"error")
        return redirect(url_for("login"))
    if request.method=="POST":
        nueva_empresa=request.form.get("empresa","").strip(); nuevo_rol=request.form.get("rol","").strip()
        if nueva_empresa: user["empresa"]=nueva_empresa
        if nuevo_rol: user["rol"]=nuevo_rol
        update_user_fields(user["email"],empresa=user["empresa"],rol=user["rol"])
        session["user"]=user["email"]
        flash(t("Perfil actualizado correctamente.","Profile updated successfully.","個人資料已更新"),"success")
        return redirect(url_for("perfil"))
    return render_template("perfil.html",user=user,titulo=t("Tu Perfil","Your Profile","個人資料"))

# -- Mensajería básica entre usuarios --
MENSAJES=[]
@app.route("/mensajes", methods=["GET","POST"])
def mensajes():
    user=current_user()
    if not user:
        flash(t("Debes iniciar sesión.","You must log in.","您必須登入"),"error")
        return redirect(url_for("login"))
    if request.method=="POST":
        destino=request.form.get("destino","").strip().lower(); contenido=request.form.get("contenido","").strip()
        if not destino or not contenido:
            flash(t("Debes completar todos los campos.","All fields required.","請填寫所有欄位"),"error")
            return redirect(url_for("mensajes"))
        if destino not in USERS:
            flash(t("El destinatario no existe.","Recipient not found.","找不到收件人"),"error")
            return redirect(url_for("mensajes"))
        MENSAJES.append({"origen":user["email"],"destino":destino,"contenido":contenido,"fecha":datetime.now().strftime("%Y-%m-%d %H:%M")})
        flash(t("Mensaje enviado correctamente.","Message sent successfully.","訊息已發送"),"success")
        return redirect(url_for("mensajes"))
    recibidos=sorted([m for m in MENSAJES if m["destino"]==user["email"]],key=lambda x:x["fecha"],reverse=True)
    enviados=sorted([m for m in MENSAJES if m["origen"]==user["email"]],key=lambda x:x["fecha"],reverse=True)
    return render_template("mensajes.html",user=user,recibidos=recibidos,enviados=enviados,titulo=t("Mensajería","Messaging","訊息系統"))

# -- Listado y detalle de clientes --
@app.route("/clientes")
def clientes():
    data=[_armar_cliente_desde_users(u,info) for u,info in USERS.items()]
    return render_template("clientes.html",clientes=data,titulo=t("Empresas","Companies","公司"))

@app.route("/clientes/<username>")
def cliente_detalle(username):
    if username not in USERS: abort(404)
    c=_armar_cliente_desde_users(username,USERS[username])
    return render_template("cliente_detalle.html",c=c,titulo=c["empresa"])

# -- Secciones informativas --
@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html",titulo=t("Centro de Ayuda","Help Center","幫助中心"))

@app.route("/acerca")
def acerca():
    return render_template("acerca.html",titulo=t("Acerca de Window Shopping","About Window Shopping","關於 Window Shopping"))

@app.route("/status")
def status():
    estado={"usuarios":len(USERS),"publicaciones":len(PUBLICACIONES),"mensajes":len(MENSAJES),"idioma":session.get("lang","es"),"estado":"OK ✅"}
    return jsonify(estado)

# -- Inicialización ordenada (solo al importar o ejecutar) --
init_db(); migrate_add_rut_doc(); migrate_add_contact_fields(); create_admin_if_missing(); seed_demo_users(); load_users_cache()
print(f"✅ USERS en caché: {len(USERS)} usuarios cargados.")

# -- Ejecución local o en Render --
if __name__=="__main__":
    print("🌐 Servidor Flask ejecutándose en http://127.0.0.1:5000")
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)
