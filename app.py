# === PATCH Parte 1: imports extra ===
import json

# =========================================================
# RESET DE CONTRASEÑA (flujo simple local, sin email real)
# =========================================================
@app.route("/password_reset/request", methods=["GET", "POST"])
def password_reset_request():
    """
    Flujo de solicitud de restablecimiento de contraseña.
    Muestra un formulario para ingresar el correo electrónico,
    y si existe, permite continuar al cambio de contraseña.
    """
    msg = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if email in USERS:
            # Guardamos en sesión el usuario a resetear y redirigimos
            session["pwd_reset_user"] = email
            flash(t("Te enviamos un enlace de restablecimiento (demo). Continúa abajo.", 
                    "We sent you a reset link (demo). Continue below.",
                    "已發送重設連結（示範）。請繼續。"))
            return redirect(url_for("password_reset_form"))
        else:
            msg = t("Ese usuario no existe.", "That user does not exist.", "此用戶不存在")
    return render_template("password_reset_request.html", msg=msg)


@app.route("/password_reset/reset", methods=["GET", "POST"])
def password_reset_form():
    """
    Segundo paso: formulario para ingresar nueva contraseña.
    """
    msg = None
    email = session.get("pwd_reset_user")
    if not email:
        flash(t("Primero solicita el enlace de restablecimiento.", 
                "Request a reset link first.", 
                "請先申請重設連結"))
        return redirect(url_for("password_reset_request"))

    if request.method == "POST":
        p1 = request.form.get("p1", "")
        p2 = request.form.get("p2", "")
        if not p1 or p1 != p2:
            msg = t("Las contraseñas no coinciden.", "Passwords do not match.", "密碼不一致")
        else:
            USERS[email]["password"] = p1
            flash(t("Contraseña actualizada.", "Password updated.", "已更新密碼"))
            session.pop("pwd_reset_user", None)
            return redirect(url_for("login"))

    return render_template("password_reset_form.html", msg=msg)
# === PATCH Parte 2: Ajuste dinámico de roles en registro ===

@app.route("/register_dynamic", methods=["GET", "POST"])
def register_dynamic():
    """
    Versión mejorada del registro, con reglas ajustadas:
      - Si nacionalidad = extranjero → perfil = compra_venta, rol = Cliente extranjero.
      - Si nacionalidad = nacional y tipo = servicios → solo roles Packing, Frigorífico, Transporte, Aduana, Extraportuario.
      - Si nacionalidad = nacional y tipo = compra_venta → roles Productor, Planta, Packing, Frigorífico, Exportador.
      - Si nacionalidad = nacional y tipo = ambos → Packing y Frigorífico (únicos con doble perfil).
    """
    error = None
    nacionalidad = request.args.get("nac")
    perfil_tipo = request.args.get("tipo")

    # Listas maestras
    ROLES_NACIONAL_CV = ["Productor", "Planta", "Packing", "Frigorífico", "Exportador"]
    ROLES_NACIONAL_SRV = ["Packing", "Frigorífico", "Transporte", "Agencia de Aduanas", "Extraportuario"]
    ROLES_AMBOS = ["Packing", "Frigorífico"]

    if request.method == "POST":
        nacionalidad = (request.form.get("nacionalidad") or nacionalidad or "nacional").lower()
        perfil_tipo = (request.form.get("perfil_tipo") or perfil_tipo or "compra_venta").lower()

        # --- Validación de roles según nacionalidad/tipo ---
        if nacionalidad == "extranjero":
            rol = "Cliente extranjero"
            perfil_tipo = "compra_venta"
        else:
            if perfil_tipo == "servicios":
                roles_validos = ROLES_NACIONAL_SRV
            elif perfil_tipo == "ambos":
                roles_validos = ROLES_AMBOS
            else:
                roles_validos = ROLES_NACIONAL_CV

            rol = request.form.get("rol", "")
            if rol not in roles_validos:
                error = t("Rol no válido para el tipo seleccionado.", "Invalid role for this type.", "該類型角色無效")

        username = (request.form.get("username") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        email = (request.form.get("email") or "").strip()
        telefono = (request.form.get("phone") or "").strip()
        direccion = (request.form.get("address") or "").strip()
        pais = (request.form.get("pais") or "").strip() or ("CL" if nacionalidad == "nacional" else "US")

        # Documentos
        rut = (request.form.get("rut") or "").strip() if nacionalidad == "nacional" else None
        usci = (request.form.get("usci") or "").strip() if nacionalidad == "extranjero" else None
        eori = (request.form.get("eori") or "").strip() if nacionalidad == "extranjero" else None
        tax_id = (request.form.get("tax_id") or "").strip() if nacionalidad == "extranjero" else None
        otros_id = (request.form.get("otros_id") or "").strip() if nacionalidad == "extranjero" else None

        # Validaciones principales
        if not username or not password:
            error = t("Completa todos los campos obligatorios.", "Please fill required fields.", "請填寫所有必要欄位")
        elif username in USERS:
            error = t("El usuario ya existe.", "User already exists.", "用戶已存在")

        if not error:
            USERS[username] = {
                "password": password,
                "rol": rol,
                "perfil_tipo": perfil_tipo,
                "pais": pais,
            }
            USER_PROFILES[username] = {
                "empresa": username.split("@")[0].replace(".", " ").title(),
                "rut": rut,
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

    # Render dinámico
    return render_template(
        "register.html",
        error=error,
        nacionalidad=nacionalidad,
        perfil_tipo=perfil_tipo,
        roles_cv=ROLES_NACIONAL_CV,
        roles_srv=ROLES_NACIONAL_SRV,
        roles_ambos=ROLES_AMBOS,
        roles_all=["Cliente extranjero"] + ROLES_NACIONAL_CV + ROLES_NACIONAL_SRV,
    )
# === PATCH Parte 3: Ajuste de login y dashboard ===

@app.route("/login_v2", methods=["GET", "POST"])
def login_v2():
    """
    Nueva versión del login con manejo robusto de errores,
    soporte multilenguaje y compatibilidad con el registro dinámico.
    """
    error = None
    if request.method == "POST":
        user = (request.form.get("username") or "").strip().lower()
        pwd = (request.form.get("password") or "").strip()
        udata = USERS.get(user)

        if udata and udata.get("password") == pwd:
            session["user"] = user
            session["usuario"] = user
            flash(t("Bienvenido/a", "Welcome", "歡迎"))
            return redirect(url_for("dashboard_v2"))
        else:
            error = t("Credenciales inválidas o usuario no registrado.", 
                      "Invalid credentials or unregistered user.",
                      "帳號或密碼錯誤")

    return render_template("login.html", error=error)


@app.route("/dashboard_v2")
def dashboard_v2():
    """
    Panel principal mejorado. 
    Evita errores si el usuario no tiene perfil o tiene items vacíos.
    """
    if not is_logged():
        flash(t("Primero inicia sesión.", "Please log in first.", "請先登入"))
        return redirect(url_for("login_v2"))

    usuario = session.get("user")
    user_data = USERS.get(usuario, {})
    profile_data = USER_PROFILES.get(usuario, {})

    rol = user_data.get("rol", "Sin rol")
    perfil_tipo = user_data.get("perfil_tipo", "N/A")
    pais = user_data.get("pais", "CL")

    my_company = ViewObj({
        "empresa": profile_data.get("empresa", "—"),
        "email": profile_data.get("email", "—"),
        "telefono": profile_data.get("telefono", "—"),
        "direccion": profile_data.get("direccion", "—"),
        "descripcion": profile_data.get("descripcion", "—"),
        "rol": rol,
        "pais": pais,
        "items": profile_data.get("items", []),
    })

    # Determinar tipo de dashboard visual
    dashboard_tipo = (
        "servicios" if perfil_tipo == "servicios"
        else "compra_venta" if perfil_tipo == "compra_venta"
        else "mixto"
    )

    return render_template(
        "dashboard.html",
        usuario=usuario,
        rol=rol,
        pais=pais,
        perfil_tipo=perfil_tipo,
        my_company=my_company,
        dashboard_tipo=dashboard_tipo,
        cart=get_cart(),
    )
# === PATCH Parte 4: Filtros mejorados para Compras / Ventas / Servicios ===

@app.route("/buscar", methods=["GET"])
def buscar():
    """
    Búsqueda avanzada global.
    Permite buscar por empresa, producto o servicio, 
    en cualquiera de los tres módulos (compras, ventas o servicios).
    """
    query = (request.args.get("q") or "").strip().lower()
    tipo = (request.args.get("tipo") or "todos").lower()
    resultados = []

    if not query:
        flash(t("Debes ingresar un término de búsqueda.", 
                "Please enter a search term.", 
                "請輸入搜尋詞"))
        return redirect(request.referrer or url_for("dashboard_v2"))

    # Filtros por tipo
    for uname, prof in USER_PROFILES.items():
        items = prof.get("items", [])
        for it in items:
            # Verificamos coincidencias por texto
            if (
                query in prof.get("empresa", "").lower()
                or query in prof.get("descripcion", "").lower()
                or query in it.get("producto", "").lower()
                or query in it.get("servicio", "").lower()
            ):
                if tipo == "compras" and it.get("tipo") != "demanda":
                    continue
                if tipo == "ventas" and it.get("tipo") != "oferta":
                    continue
                if tipo == "servicios" and it.get("tipo") != "servicio":
                    continue

                r = prof.copy()
                r["username"] = uname
                resultados.append(r)
                break

    return render_template("busqueda_resultados.html", resultados=wrap_list(resultados), query=query, tipo=tipo)


@app.route("/filtrar_roles/<tipo>")
def filtrar_roles(tipo):
    """
    Endpoint auxiliar para el front-end (AJAX o HTML clásico),
    devuelve qué roles pueden visualizar un tipo de módulo.
    Ejemplo: /filtrar_roles/servicios
    """
    tipo = tipo.lower()
    if tipo not in ("compras", "ventas", "servicios"):
        return json.dumps({"error": "Tipo inválido"}), 400

    usuario = session.get("user")
    if not usuario:
        return json.dumps({"error": "No autenticado"}), 403

    rol = USERS.get(usuario, {}).get("rol", "default")
    visibles = targets_for(tipo, rol)
    return json.dumps({"tipo": tipo, "rol": rol, "visibles": visibles})


@app.route("/servicios_avanzado", methods=["GET"])
def servicios_avanzado():
    """
    Visualización avanzada de servicios, con agrupación por tipo (packing, frío, transporte, etc.)
    """
    filtro_texto = (request.args.get("q") or "").lower()
    agrupados = {
        "Packing": [],
        "Frigorífico": [],
        "Transporte": [],
        "Agencia de Aduanas": [],
        "Extraportuario": [],
    }

    for uname, prof in USER_PROFILES.items():
        for item in prof.get("items", []):
            if item.get("tipo") == "servicio":
                if filtro_texto and not (
                    filtro_texto in prof.get("empresa", "").lower() or
                    filtro_texto in item.get("servicio", "").lower()
                ):
                    continue
                rol = prof.get("rol", "Otro")
                if rol in agrupados:
                    entry = prof.copy()
                    entry["username"] = uname
                    entry["servicio_detalle"] = item
                    agrupados[rol].append(entry)

    return render_template("servicios_avanzado.html", agrupados=agrupados, query=filtro_texto)
# === PATCH Parte 5: Idioma global, errores y helpers adicionales ===

# ---------------------------------------------------------
# Cambio de idioma global (versión mejorada)
# ---------------------------------------------------------
@app.route("/idioma/<lang>")
def idioma(lang):
    """Cambia el idioma global del sitio (es/en/zh)."""
    lang = lang.lower()
    if lang not in ("es", "en", "zh"):
        flash(t("Idioma inválido.", "Invalid language.", "語言無效"))
        return redirect(url_for("home"))
    session["lang"] = lang
    flash(t("Idioma cambiado correctamente.", "Language changed successfully.", "語言已更新"))
    return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------
# Errores mejorados
# ---------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    mensaje = t("Página no encontrada", "Page not found", "找不到頁面")
    return render_template("error.html", code=404, message=mensaje), 404


@app.errorhandler(500)
def internal_error(e):
    mensaje = t("Error interno del servidor", "Internal server error", "內部伺服器錯誤")
    return render_template("error.html", code=500, message=mensaje), 500


@app.errorhandler(403)
def forbidden(e):
    mensaje = t("Acceso denegado", "Access denied", "拒絕訪問")
    return render_template("error.html", code=403, message=mensaje), 403


# ---------------------------------------------------------
# Idioma por defecto si la sesión expira
# ---------------------------------------------------------
@app.before_request
def set_default_lang():
    if "lang" not in session:
        session["lang"] = "es"

# ---------------------------------------------------------
# Helper para mostrar los idiomas en la barra superior
# ---------------------------------------------------------
@app.context_processor
def globals_context():
    return dict(
        current_lang=session.get("lang", "es"),
        langs=[("es", "ES"), ("en", "EN"), ("zh", "中文")],
    )
