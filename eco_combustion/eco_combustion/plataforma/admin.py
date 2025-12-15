from django.contrib import admin
from .models import (
    Region,
    Comuna,
    Usuario,
    SolicitudRolComercial,
    Proveedor,
    Producto,
    Servicio,
    TarifaEnvio,
    Resena,
    PerfilUsuario,
    ContenidoEducativo,
    QuizOpcion,
    QuizIntentoUsuario,
    QuizPregunta
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "region")



@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefono", "comuna", "recibe_boletin")
    search_fields = ("usuario__username", "telefono")


@admin.register(SolicitudRolComercial)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo_solicitud", "estado", "fecha_envio", "fecha_resolucion")
    list_filter = ("estado", "tipo_solicitud")
    search_fields = ("usuario__username",)
    readonly_fields = ("fecha_envio", "fecha_resolucion")



@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_comercial",
        "rut",
        "comuna",
        "es_proveedor_biocombustible",
        "es_prestador_servicios",
        "estado",
    )
    list_filter = ("estado", "es_proveedor_biocombustible", "es_prestador_servicios")
    search_fields = ("nombre_comercial", "rut")



@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "proveedor",
        "tipo_producto",
        "precio_unitario",
        "stock_disponible",
        "certificado_sncl",
        "activo",
    )
    list_filter = ("tipo_producto", "activo", "certificado_sncl")
    search_fields = ("proveedor__nombre_comercial", "especie")


# -----------------------------
# SERVICIOS
# -----------------------------

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "proveedor",
        "tipo_servicio",
        "nombre",
        "precio_base",
        "activo",
    )
    list_filter = ("tipo_servicio", "activo")
    search_fields = ("nombre", "proveedor__nombre_comercial")
    filter_horizontal = ("comunas_cobertura",)


# -----------------------------
# TARIFAS DE ENVÍO
# -----------------------------

@admin.register(TarifaEnvio)
class TarifaEnvioAdmin(admin.ModelAdmin):
    list_display = ("proveedor", "comuna", "tarifa_por_km", "tarifa_minima", "activo")
    list_filter = ("activo",)
    search_fields = ("proveedor__nombre_comercial",)


# -----------------------------
# RESEÑAS
# -----------------------------

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("proveedor", "usuario", "puntaje", "visible", "fecha_creacion")
    list_filter = ("visible", "puntaje")
    search_fields = ("proveedor__nombre_comercial", "usuario__username")


# -----------------------------
# CONTENIDO EDUCATIVO
# -----------------------------

@admin.register(ContenidoEducativo)
class ContenidoEducativoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tema", "activo", "fecha_publicacion", "autor_admin")
    list_filter = ("activo", "tema")
    search_fields = ("titulo", "tema", "autor_admin__username")
    prepopulated_fields = {"slug": ("titulo",)}


# -----------------------------
# QUIZ — PREGUNTAS
# -----------------------------

class QuizOpcionInline(admin.TabularInline):
    model = QuizOpcion
    extra = 1


@admin.register(QuizPregunta)
class QuizPreguntaAdmin(admin.ModelAdmin):
    list_display = ("contenido", "orden", "tipo_pregunta")
    list_filter = ("tipo_pregunta",)
    inlines = [QuizOpcionInline]


@admin.register(QuizIntentoUsuario)
class QuizIntentoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "contenido", "puntaje_obtenido", "total_preguntas", "fecha_intento")
    list_filter = ("fecha_intento",)
    search_fields = ("usuario__username", "contenido__titulo")
