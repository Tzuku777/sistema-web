from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from .validador import validar_rut_chileno
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class Region(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"

    def __str__(self):
        return self.nombre


class Comuna(models.Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='comunas',
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Comuna"
        verbose_name_plural = "Comunas"

    def __str__(self):
        return f"{self.nombre} ({self.region.nombre})"


class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('consumidor', 'Consumidor'),
        ('proveedor', 'Proveedor de leña'),
        ('servicio', 'Prestador de servicios'),
        ('ambos', 'Ambos (leña y servicios)'),
    ]

    email_verificado = models.BooleanField(default=False)
    email_verificado_en = models.DateTimeField(null=True, blank=True)
    bloqueado = models.BooleanField(default=False)
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='consumidor'
    )
    # RUT de la persona usuaria (no del comercio)
    rut = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        validators=[validar_rut_chileno],
        help_text="Formato: 12.345.678-5",
    )
    # Región/comuna base del usuario (se usan en el formulario y no se repiten)
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )
    comuna = models.ForeignKey(
        Comuna,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    def __str__(self):
        return self.username
    def verificacion_vencida(self):
        if self.email_verificado:
            return False
        return timezone.now() > (self.date_joined + timedelta(days=7))


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    telefono = models.CharField(max_length=20, blank=True)
    direccion_texto = models.CharField(max_length=255, blank=True)
    comuna = models.ForeignKey(
        Comuna, on_delete=models.SET_NULL, null=True, blank=True, related_name="perfiles"
    )
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    recibe_boletin = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class SolicitudRolComercial(models.Model):
    class TipoSolicitud(models.TextChoices):
        PROVEEDOR = "PROVEEDOR", _("Proveedor de biocombustibles")
        PRESTADOR = "PRESTADOR", _("Prestador de servicios")
        AMBOS = "AMBOS", _("Proveedor y prestador")

    class EstadoSolicitud(models.TextChoices):
        PENDIENTE = "PENDIENTE", _("Pendiente")
        APROBADA = "APROBADA", _("Aprobada")
        RECHAZADA = "RECHAZADA", _("Rechazada")

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solicitudes_rol",
    )
    tipo_solicitud = models.CharField(
        max_length=20,
        choices=TipoSolicitud.choices,
        default=TipoSolicitud.PROVEEDOR,
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE,
    )
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    comentario_admin = models.TextField(blank=True)

    # -----------------------------
    # Campos estructurados para el formulario de registro comercial
    # -----------------------------
    # BLOQUE "DATOS PARA VENDER LEÑA CERTIFICADA"
    nombre_comercio = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nombre del comercio para venta de biocombustibles",
    )
    giro_comercial = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ej: Venta de leña seca",
    )
    direccion_punto_venta = models.CharField(
        max_length=255,
        blank=True,
        help_text="Dirección o punto de venta",
    )
    acepta_ley_biocombustibles = models.BooleanField(
        default=False,
        help_text="Marca si declara cumplir la Ley de Biocombustibles",
    )

    # BLOQUE "DATOS PARA OFRECER SERVICIOS"
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ciudad principal donde presta servicios",
    )
    datos_contacto = models.CharField(
        max_length=255,
        blank=True,
        help_text="Teléfono y/o correo de contacto",
    )
    tipo_servicios = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ej: Transporte, instalación de calefactor, limpieza de cañones",
    )
    acepta_terminos = models.BooleanField(
        default=False,
        help_text="Acepta los términos y condiciones del sitio",
    )

    # Campo genérico para extensiones futuras
    datos_adicionales = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Solicitud de rol comercial"
        verbose_name_plural = "Solicitudes de rol comercial"

    def __str__(self):
        return f"{self.usuario} - {self.tipo_solicitud} ({self.estado})"


class Proveedor(models.Model):
    class EstadoProveedor(models.TextChoices):
        ACTIVO = "ACTIVO", _("Activo")
        SUSPENDIDO = "SUSPENDIDO", _("Suspendido")
        INACTIVO = "INACTIVO", _("Inactivo")

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proveedor",
    )
    razon_social = models.CharField(max_length=255)
    rut = models.CharField(
        max_length=12,
        unique=True,
        help_text="Formato: 12.345.678-5",
        validators=[validar_rut_chileno],
    )
    nombre_comercial = models.CharField(max_length=255)
    email_contacto = models.EmailField()
    telefono_contacto = models.CharField(max_length=20)
    direccion_texto = models.CharField(max_length=255)
    comuna = models.ForeignKey(
        Comuna, on_delete=models.SET_NULL, null=True, related_name="proveedores"
    )
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    numero_sncl = models.CharField(max_length=50, help_text="Número de registro SNCL")
    es_proveedor_biocombustible = models.BooleanField(default=False)
    es_prestador_servicios = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=20,
        choices=EstadoProveedor.choices,
        default=EstadoProveedor.ACTIVO,
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Proveedor / Prestador"
        verbose_name_plural = "Proveedores / Prestadores"

    def __str__(self):
        return self.nombre_comercial


class Producto(models.Model):
    class TipoProducto(models.TextChoices):
        LENA = "LENA", _("Leña")
        PELLET = "PELLET", _("Pellet")
        BRIQUETA = "BRIQUETA", _("Briqueta")
        CARBON = "CARBON", _("Carbón")

    # 👉 NUEVO: choices normalizados
    class FormatoProducto(models.TextChoices):
        METRO_RUMA = "METRO_RUMA", _("Metro ruma")
        M3_GRANEL = "M3_GRANEL", _("m³ a granel")
        SACO_15 = "SACO_15", _("Saco 15 kg")
        SACO_20 = "SACO_20", _("Saco 20 kg")
        SACO_25 = "SACO_25", _("Saco 25 kg")
        BOLSA = "BOLSA", _("Bolsa")
        OTRO = "OTRO", _("Otro")

    class UnidadMedida(models.TextChoices):
        M3 = "m3", _("m³")
        SACO = "saco", _("Saco")
        KG = "kg", _("Kilogramo")
        BOLSA = "bolsa", _("Bolsa")
        PALLET = "pallet", _("Pallet")

    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="productos"
    )
    tipo_producto = models.CharField(max_length=20, choices=TipoProducto.choices)
    especie = models.CharField(max_length=100, blank=True)
    contenido_humedad = models.FloatField(
        null=True, blank=True, help_text="Porcentaje aproximado de humedad"
    )

    # 👉 SOLO aquí se modifica: se agregan choices
    formato = models.CharField(
        max_length=20,
        choices=FormatoProducto.choices,
        help_text="Presentación del producto"
    )
    unidad_medida = models.CharField(
        max_length=20,
        choices=UnidadMedida.choices,
        help_text="Unidad de cobro"
    )

    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField(blank=True)
    comuna = models.ForeignKey(
        Comuna, on_delete=models.SET_NULL, null=True, related_name="productos"
    )
    stock_disponible = models.IntegerField(null=True, blank=True)
    certificado_sncl = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def precio_clp(self):
        try:
            n = int(self.precio_unitario)
        except Exception:
            return str(self.precio_unitario)
        return f"{n:,}".replace(",", ".")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.get_tipo_producto_display()} - {self.proveedor.nombre_comercial}"



class Servicio(models.Model):
    class TipoServicio(models.TextChoices):
        CORTE = "CORTE", _("Corte de leña")
        PICADO = "PICADO", _("Picado / trozado")
        TRANSPORTE = "TRANSPORTE", _("Transporte")
        LIMPIEZA_CANALES = "LIMPIEZA_CANALES", _("Limpieza de estufas / cañones")

    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="servicios"
    )
    tipo_servicio = models.CharField(max_length=30, choices=TipoServicio.choices)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=12, decimal_places=2)
    unidad_precio = models.CharField(
        max_length=20, help_text="Ej: viaje, hora, m3 transportado"
    )
    comunas_cobertura = models.ManyToManyField(
        Comuna, related_name="servicios_disponibles", blank=True
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre


class TarifaEnvio(models.Model):
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="tarifas_envio"
    )
    comuna = models.ForeignKey(
        Comuna,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarifas_envio",
    )
    tarifa_por_km = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_minima = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tarifa de envío"
        verbose_name_plural = "Tarifas de envío"

    def __str__(self):
        return f"Tarifa {self.proveedor} ({self.comuna or 'Todas las comunas'})"


class Resena(models.Model):
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="resenas"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resenas"
    )
    puntaje = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    moderado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resenas_moderadas",
    )
    fecha_moderacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"

    def __str__(self):
        return f"{self.proveedor} - {self.puntaje} estrellas"


class ContenidoEducativo(models.Model):
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    resumen = models.TextField(blank=True)
    texto = models.TextField()
    tema = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    autor_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contenidos_publicados",
    )

    class Meta:
        verbose_name = "Contenido educativo"
        verbose_name_plural = "Contenidos educativos"

    def __str__(self):
        return self.titulo


class QuizPregunta(models.Model):
    class TipoPregunta(models.TextChoices):
        OPCION_MULTIPLE = "OPCION_MULTIPLE", _("Opción múltiple")
        VERDADERO_FALSO = "VERDADERO_FALSO", _("Verdadero/Falso")

    contenido = models.ForeignKey(
        ContenidoEducativo,
        on_delete=models.CASCADE,
        related_name="preguntas",
    )
    enunciado = models.TextField()
    tipo_pregunta = models.CharField(
        max_length=20,
        choices=TipoPregunta.choices,
        default=TipoPregunta.OPCION_MULTIPLE,
    )
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Pregunta de quiz"
        verbose_name_plural = "Preguntas de quiz"
        ordering = ["orden"]

    def __str__(self):
        return f"Pregunta {self.orden} - {self.contenido.titulo}"


class QuizOpcion(models.Model):
    pregunta = models.ForeignKey(
        QuizPregunta, on_delete=models.CASCADE, related_name="opciones"
    )
    texto_opcion = models.CharField(max_length=255)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Opción de quiz"
        verbose_name_plural = "Opciones de quiz"

    def __str__(self):
        return f"Opción '{self.texto_opcion}'"


class QuizIntentoUsuario(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="intentos_quiz",
    )
    contenido = models.ForeignKey(
        ContenidoEducativo,
        on_delete=models.CASCADE,
        related_name="intentos",
    )
    puntaje_obtenido = models.PositiveIntegerField()
    total_preguntas = models.PositiveIntegerField()
    fecha_intento = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Intento de quiz"
        verbose_name_plural = "Intentos de quiz"

    def __str__(self):
        return f"{self.usuario} - {self.contenido} ({self.puntaje_obtenido}/{self.total_preguntas})"
