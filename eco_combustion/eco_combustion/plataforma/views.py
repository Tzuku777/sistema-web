from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import (
    Producto,
    SolicitudRolComercial,
    Proveedor,
    Comuna,
    Servicio,
    PerfilUsuario,
    ContenidoEducativo,
)
from .forms import (
    ProductoForm,
    ServicioForm,
    RegistroUsuarioForm,
    SolicitudRolComercialForm,
    ContenidoEducativoForm,
    SolicitudRolAdminForm,
    PerfilForm,
)


# ================== HELPERS DE ROL ==================


def es_admin(user):
    return user.is_staff or user.is_superuser


def es_proveedor(user):
    """
    Es proveedor si tiene un registro Proveedor ACTIVO y marcado como proveedor de biocombustible.
    """
    return Proveedor.objects.filter(
        usuario=user,
        es_proveedor_biocombustible=True,
        estado=Proveedor.EstadoProveedor.ACTIVO,
    ).exists()


def es_prestador(user):
    """
    Es prestador de servicios si tiene un registro Proveedor ACTIVO y marcado como prestador de servicios.
    """
    return Proveedor.objects.filter(
        usuario=user,
        es_prestador_servicios=True,
        estado=Proveedor.EstadoProveedor.ACTIVO,
    ).exists()


# ================== VISTAS PÚBLICAS ==================


def home(request):
    return render(request, "plataforma/home.html")


def catalogo(request):
    productos = Producto.objects.filter(activo=True).select_related("proveedor").order_by("-id")
    servicios = Servicio.objects.filter(activo=True).select_related("proveedor").order_by("-id")

    return render(request, "plataforma/catalogo.html", {
        "productos": productos,
        "servicios": servicios,
    })



def detalle_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    productos = proveedor.productos.filter(activo=True)
    contexto = {"proveedor": proveedor, "productos": productos}
    return render(request, "plataforma/detalle_proveedor.html", contexto)


def educativo_lista(request):
    contenidos = ContenidoEducativo.objects.filter(activo=True)
    return render(
        request, "plataforma/educativo_lista.html", {"contenidos": contenidos}
    )


def educativo_detalle(request, slug):
    contenido = get_object_or_404(ContenidoEducativo, slug=slug, activo=True)
    return render(
        request,
        "plataforma/educativo_detalle.html",
        {"contenido": contenido},
    )


def quiz(request, slug):
    contenido = get_object_or_404(ContenidoEducativo, slug=slug, activo=True)
    preguntas = contenido.preguntas.prefetch_related("opciones")
    return render(
        request,
        "plataforma/quiz.html",
        {"contenido": contenido, "preguntas": preguntas},
    )


# ================== AUTENTICACIÓN ==================


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect("plataforma:panel_admin")
            else:
                return redirect("plataforma:home")
    else:
        form = AuthenticationForm(request)

    return render(request, "plataforma/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("plataforma:home")


# ================== REGISTRO ==================

@transaction.atomic
def registro_view(request):
    if request.method == "POST":
        form_usuario = RegistroUsuarioForm(request.POST)
        if form_usuario.is_valid():
            usuario = form_usuario.save()
            PerfilUsuario.objects.get_or_create(usuario=usuario)
            login(request, usuario)
            messages.success(
                request,
                "Tu cuenta ha sido creada correctamente. "
                "Ahora puedes completar tu rol comercial en 'Configuración de cuenta'.",
            )
            return redirect("plataforma:panel_usuario")
    else:
        form_usuario = RegistroUsuarioForm()

    comunas = Comuna.objects.values("id", "nombre", "region_id")

    return render(
        request,
        "plataforma/registro.html",
        {
            "form_usuario": form_usuario,
            "comunas": list(comunas),
        },
    )




@login_required
@transaction.atomic
def configuracion_cuenta(request):
    usuario = request.user

    solicitud_existente = (
        SolicitudRolComercial.objects
        .filter(usuario=usuario)
        .order_by("-fecha_envio")
        .first()
        
    )

    if request.method == "POST":

        # ===== PERFIL =====
        if "guardar_perfil" in request.POST:
            form_perfil = PerfilForm(request.POST, instance=usuario)
            form_solicitud = SolicitudRolComercialForm(instance=solicitud_existente)

            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, "Datos de perfil actualizados correctamente.")
                return redirect("plataforma:configuracion_cuenta")

        # ===== ROL COMERCIAL =====
        elif "enviar_solicitud" in request.POST:
            form_perfil = PerfilForm(instance=usuario)
            form_solicitud = SolicitudRolComercialForm(
                request.POST,
                instance=solicitud_existente
            )

            if form_solicitud.is_valid():
                solicitud = form_solicitud.save(commit=False)
                solicitud.usuario = usuario
                solicitud.estado = SolicitudRolComercial.EstadoSolicitud.PENDIENTE
                solicitud.fecha_resolucion = None
                solicitud.comentario_admin = ""
                solicitud.save()

                desactivar_comercial(request.user)


                messages.success(
                    request,
                    "Tu solicitud de rol comercial fue enviada y quedó en estado PENDIENTE."
                )
                return redirect("plataforma:configuracion_cuenta")

    else:
        form_perfil = PerfilForm(instance=usuario)
        form_solicitud = SolicitudRolComercialForm(instance=solicitud_existente)

    return render(
        request,
        "plataforma/configuracion_cuenta.html",
        {
            "form_perfil": form_perfil,
            "form_solicitud": form_solicitud,
            "solicitud_actual": solicitud_existente,
            "puede_productos": es_proveedor(request.user),
            "puede_servicios": es_prestador(request.user),

        }
    )
def desactivar_comercial(usuario):
    """
    Corta acceso comercial:
    - Desactiva Proveedor (si existe)
    - Apaga flags proveedor/prestador
    - Despublica productos/servicios (activo=False)
    - Normaliza tipo_usuario
    """
    proveedor = Proveedor.objects.filter(usuario=usuario).first()
    if not proveedor:
        usuario.tipo_usuario = "usuario"
        usuario.save(update_fields=["tipo_usuario"])
        return

    proveedor.estado = Proveedor.EstadoProveedor.INACTIVO
    proveedor.es_proveedor_biocombustible = False
    proveedor.es_prestador_servicios = False
    proveedor.save(update_fields=["estado", "es_proveedor_biocombustible", "es_prestador_servicios"])

    Producto.objects.filter(proveedor=proveedor).update(activo=False)
    Servicio.objects.filter(proveedor=proveedor).update(activo=False)

    usuario.tipo_usuario = "usuario"
    usuario.save(update_fields=["tipo_usuario"])

# ================== API AUXILIAR COMUNAS ==================


def api_comunas_por_region(request, region_id):
    comunas = Comuna.objects.filter(region_id=region_id).order_by("nombre")
    data = [{"id": c.id, "nombre": c.nombre} for c in comunas]
    return JsonResponse(data, safe=False)


# ================== SOLICITUDES (ADMIN) ==================


@login_required
@user_passes_test(es_admin)
def solicitudes_proveedores_view(request):
    """
    Lista de solicitudes de proveedores / prestadores para el panel admin.
    Aquí se usa el modal para ver/gestionar cada solicitud.
    """
    solicitudes = SolicitudRolComercial.objects.all().order_by("-fecha_envio")
    return render(
        request,
        "plataforma/solicitudes_proveedores.html",
        {"solicitudes": solicitudes},
    )


@login_required
@user_passes_test(es_admin)
def solicitud_proveedor_cambiar_estado(request, pk):
    """
    Vista tradicional (HTML) para aprobar o rechazar una solicitud.
    El flujo principal ahora irá por el modal + API, pero esta vista
    se deja como respaldo.
    """
    solicitud = get_object_or_404(SolicitudRolComercial, pk=pk)

    if request.method == "POST":
        accion = request.POST.get("accion")
        comentario = request.POST.get("comentario", "")
        messages.success(
            request,
            f"Solicitud aprobada. {solicitud.usuario} fue aprobado como: {solicitud.get_tipo_solicitud_display()}.",)
        if accion == "aprobar":
            solicitud.estado = SolicitudRolComercial.EstadoSolicitud.APROBADA
            solicitud.comentario_admin = comentario
            solicitud.fecha_resolucion = timezone.now()
            solicitud.save()

            if solicitud.tipo_solicitud == 'PROVEEDOR':
                solicitud.usuario.tipo_usuario = 'proveedor'
            elif solicitud.tipo_solicitud == 'PRESTADOR':
                solicitud.usuario.tipo_usuario = 'servicio'
            elif solicitud.tipo_solicitud == 'AMBOS':
                solicitud.usuario.tipo_usuario = 'ambos'

            solicitud.usuario.save()


            _crear_o_actualizar_proveedor_desde_solicitud(solicitud)

            messages.success(request, "Solicitud aprobada y proveedor actualizado/creado.")
        elif accion == "rechazar":
            solicitud.estado = SolicitudRolComercial.EstadoSolicitud.RECHAZADA
            solicitud.comentario_admin = comentario
            solicitud.fecha_resolucion = timezone.now()
            solicitud.save()

            desactivar_comercial(solicitud.usuario)


            messages.info(request, "Solicitud rechazada.")

        else:
            messages.error(request, "Acción no válida.")

        return redirect("plataforma:solicitudes_proveedores")
    

    # GET: mostrar detalle simple
    return render(
        request,
        "plataforma/solicitud_proveedor_detalle.html",
        {"solicitud": solicitud},
    )


@login_required
@user_passes_test(es_admin)
@require_http_methods(["GET", "POST"])
def api_solicitud_detalle(request, pk):
    """
    API JSON para:
    - GET: obtener detalle de la solicitud de rol comercial
    - POST: aprobar o rechazar la solicitud (accion=aprobar/rechazar, comentario opcional)

    Se usa desde un modal en solicitudes_proveedores.html
    """
    solicitud = get_object_or_404(SolicitudRolComercial, pk=pk)

    if request.method == "GET":
        data = {
            "id": solicitud.id,
            "usuario": solicitud.usuario.username,
            "email": solicitud.usuario.email,
            "tipo_solicitud": solicitud.get_tipo_solicitud_display(),
            "estado": solicitud.get_estado_display(),
            "fecha_envio": solicitud.fecha_envio.strftime("%Y-%m-%d %H:%M"),
            "fecha_resolucion": solicitud.fecha_resolucion.strftime("%Y-%m-%d %H:%M")
            if solicitud.fecha_resolucion
            else None,
            "nombre_comercio": solicitud.nombre_comercio,
            "giro_comercial": solicitud.giro_comercial,
            "direccion_punto_venta": solicitud.direccion_punto_venta,
            "acepta_ley_biocombustibles": solicitud.acepta_ley_biocombustibles,
            "ciudad": solicitud.ciudad,
            "datos_contacto": solicitud.datos_contacto,
            "tipo_servicios": solicitud.tipo_servicios,
            "acepta_terminos": solicitud.acepta_terminos,
            "comentario_admin": solicitud.comentario_admin or "",
        }
        return JsonResponse({"ok": True, "solicitud": data})

    # POST → aprobar o rechazar
    accion = request.POST.get("accion")
    comentario = request.POST.get("comentario", "").strip()

    if accion not in ["aprobar", "rechazar"]:
        return JsonResponse(
            {"ok": False, "mensaje": "Acción no válida."},
            status=400,
        )

    if accion == "aprobar":
        solicitud.estado = SolicitudRolComercial.EstadoSolicitud.APROBADA
    else:
        solicitud.estado = SolicitudRolComercial.EstadoSolicitud.RECHAZADA

    solicitud.comentario_admin = comentario
    solicitud.fecha_resolucion = timezone.now()
    solicitud.save()

    if accion == "aprobar":
        _crear_o_actualizar_proveedor_desde_solicitud(solicitud)

    return JsonResponse(
        {
            "ok": True,
            "mensaje": "Solicitud procesada correctamente.",
            "nuevo_estado": solicitud.get_estado_display(),
        }
    )


def _crear_o_actualizar_proveedor_desde_solicitud(solicitud: SolicitudRolComercial):
    usuario = solicitud.usuario

    proveedor, _ = Proveedor.objects.get_or_create(
        usuario=usuario,
        defaults={
            "razon_social": solicitud.nombre_comercio or usuario.get_full_name() or usuario.username,
            "rut": usuario.rut or "11.111.111-1",
            "nombre_comercial": solicitud.nombre_comercio or usuario.username,
            "email_contacto": usuario.email or "",
            "telefono_contacto": solicitud.datos_contacto or "",
            "direccion_texto": solicitud.direccion_punto_venta or "",
            "comuna": usuario.comuna,
            "numero_sncl": (solicitud.datos_adicionales or {}).get("numero_sncl", ""),
        },
    )

    # ---- Actualizar campos si vienen vacíos o si hay info nueva ----
    if solicitud.nombre_comercio:
        proveedor.nombre_comercial = solicitud.nombre_comercio
        if not proveedor.razon_social:
            proveedor.razon_social = solicitud.nombre_comercio

    if usuario.email:
        proveedor.email_contacto = usuario.email

    if solicitud.datos_contacto:
        proveedor.telefono_contacto = solicitud.datos_contacto

    if solicitud.direccion_punto_venta:
        proveedor.direccion_texto = solicitud.direccion_punto_venta

    if usuario.comuna:
        proveedor.comuna = usuario.comuna

    # ---- Flags según tipo ----
    proveedor.es_proveedor_biocombustible = solicitud.tipo_solicitud in ["PROVEEDOR", "AMBOS"]
    proveedor.es_prestador_servicios = solicitud.tipo_solicitud in ["PRESTADOR", "AMBOS"]

    proveedor.fecha_aprobacion = timezone.now()
    proveedor.estado = Proveedor.EstadoProveedor.ACTIVO
    proveedor.save()



# ================== PANELES (USUARIO / PROVEEDOR / ADMIN) ==================


@login_required
def panel_usuario(request):
    return render(request, "plataforma/panel_usuario.html")


@login_required
@user_passes_test(es_admin)
def panel_admin(request):
    return render(request, "plataforma/panel_admin.html")


@login_required
def panel_proveedor(request):
    if not es_proveedor(request.user) and not es_prestador(request.user):
        return redirect("plataforma:home")

    productos = Producto.objects.filter(proveedor__usuario=request.user)
    servicios = Servicio.objects.filter(proveedor__usuario=request.user)

    return render(
        request,
        "plataforma/panel_proveedor.html",
        {"productos": productos, "servicios": servicios},
    )


# ================== CRUD PRODUCTOS / SERVICIOS ==================


@login_required
def producto_crear(request):
    if not es_proveedor(request.user):
        return redirect("plataforma:home")

    if request.method == "POST":
        form = ProductoForm(request.POST or None, user=request.user)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.proveedor = request.user.proveedor
            producto.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("plataforma:panel_proveedor")
    else:
        form = ProductoForm()

    return render(
        request,
        "plataforma/producto_form.html",
        {"form": form, "titulo": "Crear producto"},
    )


@login_required
def producto_editar(request, pk):
    if not es_proveedor(request.user):
        return redirect("plataforma:home")

    producto = get_object_or_404(Producto, pk=pk, proveedor__usuario=request.user)

    if request.method == "POST":
        form = ProductoForm(request.POST or None, instance=producto, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado.")
            return redirect("plataforma:panel_proveedor")
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        "plataforma/producto_form.html",
        {"form": form, "titulo": "Editar producto"},
    )


@login_required
def producto_eliminar(request, pk):
    if not es_proveedor(request.user):
        return redirect("plataforma:home")

    producto = get_object_or_404(Producto, pk=pk, proveedor__usuario=request.user)

    if request.method == "POST":
        producto.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("plataforma:panel_proveedor")

    return render(
        request,
        "plataforma/producto_confirm_delete.html",
        {"producto": producto},
    )




@login_required
def servicio_crear(request):
    if not es_prestador(request.user):
        return redirect("plataforma:home")

    if request.method == "POST":
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.proveedor = request.user.proveedor
            servicio.save()
            messages.success(request, "Servicio creado correctamente.")
            return redirect("plataforma:panel_proveedor")
    else:
        form = ServicioForm()

    return render(
        request,
        "plataforma/servicio_form.html",
        {"form": form, "titulo": "Crear servicio"},
    )


@login_required
def servicio_editar(request, pk):
    if not es_prestador(request.user):
        return redirect("plataforma:home")

    servicio = get_object_or_404(Servicio, pk=pk, proveedor__usuario=request.user)

    if request.method == "POST":
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio actualizado.")
            return redirect("plataforma:panel_proveedor")
    else:
        form = ServicioForm(instance=servicio)

    return render(
        request,
        "plataforma/servicio_form.html",
        {"form": form, "titulo": "Editar servicio"},
    )


@login_required
@require_POST
def servicio_eliminar(request, pk):
    if not es_prestador(request.user):
        return redirect("plataforma:home")

    servicio = get_object_or_404(Servicio, pk=pk, proveedor__usuario=request.user)
    servicio.delete()
    messages.success(request, "Servicio eliminado.")
    return redirect("plataforma:panel_proveedor")



# ================== CONTENIDO EDUCATIVO (ADMIN) ==================


@login_required
@user_passes_test(es_admin)
def educativo_admin_lista(request):
    contenidos = ContenidoEducativo.objects.all().order_by("-fecha_publicacion")
    return render(
        request,
        "plataforma/educativo_admin_lista.html",
        {"contenidos": contenidos},
    )


@login_required
@user_passes_test(es_admin)
def educativo_admin_crear(request):
    if request.method == "POST":
        form = ContenidoEducativoForm(request.POST)
        if form.is_valid():
            contenido = form.save(commit=False)
            contenido.autor_admin = request.user
            contenido.save()
            messages.success(request, "Contenido educativo creado.")
            return redirect("plataforma:educativo_admin_lista")
    else:
        form = ContenidoEducativoForm()

    return render(
        request,
        "plataforma/educativo_admin_form.html",
        {"form": form, "titulo": "Crear contenido educativo"},
    )


@login_required
@user_passes_test(es_admin)
def educativo_admin_editar(request, pk):
    contenido = get_object_or_404(ContenidoEducativo, pk=pk)

    if request.method == "POST":
        form = ContenidoEducativoForm(request.POST, instance=contenido)
        if form.is_valid():
            form.save()
            messages.success(request, "Contenido educativo actualizado.")
            return redirect("plataforma:educativo_admin_lista")
    else:
        form = ContenidoEducativoForm(instance=contenido)

    return render(
        request,
        "plataforma/educativo_admin_form.html",
        {"form": form, "titulo": "Editar contenido educativo"},
    )


@login_required
@user_passes_test(es_admin)
@require_POST
def educativo_admin_eliminar(request, pk):
    contenido = get_object_or_404(ContenidoEducativo, pk=pk)
    contenido.delete()
    messages.success(request, "Contenido eliminado correctamente.")
    return redirect("plataforma:educativo_admin_lista")

