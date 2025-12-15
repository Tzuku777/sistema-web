from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import (
    Usuario,
    Producto,
    Servicio,
    SolicitudRolComercial,
    Comuna,
    Region,
    ContenidoEducativo,
)


class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario para crear el usuario base.
    OJO: aquí NO se pide tipo_solicitud. Eso va en SolicitudRolComercialForm.
    """

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "rut",
            "region",
            "comuna",
        ]
        labels = {
            "username": "Usuario",
            "email": "Correo electrónico",
            "rut": "RUT",
            "region": "Región donde opera",
            "comuna": "Comuna principal",
        }


class SolicitudRolComercialForm(forms.ModelForm):
    """
    Formulario para la solicitud de rol comercial (proveedor / prestador / ambos).
    Se usa en registro.html junto con RegistroUsuarioForm.
    """

    class Meta:
        model = SolicitudRolComercial
        fields = [
            "tipo_solicitud",
            "nombre_comercio",
            "giro_comercial",
            "direccion_punto_venta",
            "acepta_ley_biocombustibles",
            "ciudad",
            "datos_contacto",
            "tipo_servicios",
            "acepta_terminos",
        ]
        labels = {
            "tipo_solicitud": "¿Quieres registrarte como?",
            "nombre_comercio": "Nombre del comercio",
            "giro_comercial": "Giro comercial",
            "direccion_punto_venta": "Dirección / punto de venta",
            "acepta_ley_biocombustibles": "Declaro cumplir la Ley de Biocombustibles y haber leído los términos",
            "ciudad": "Ciudad",
            "datos_contacto": "Datos de contacto (teléfono / correo)",
            "tipo_servicios": "Tipo de servicios",
            "acepta_terminos": "Acepto los términos y condiciones del sitio",
        }
        widgets = {
            "tipo_solicitud": forms.Select(attrs={"class": "form-select"}),
            "nombre_comercio": forms.TextInput(attrs={"class": "form-control"}),
            "giro_comercial": forms.TextInput(attrs={"class": "form-control"}),
            "direccion_punto_venta": forms.TextInput(attrs={"class": "form-control"}),
            "acepta_ley_biocombustibles": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ciudad": forms.TextInput(attrs={"class": "form-control"}),
            "datos_contacto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_servicios": forms.TextInput(attrs={"class": "form-control"}),
            "acepta_terminos": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
        ]
        labels = {
            "username": "Usuario",
            "email": "Correo electrónico",
            "first_name": "Nombre",
            "last_name": "Apellido",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

class SolicitudRolAdminForm(forms.ModelForm):
    """
    Formulario que usará el administrador para revisar la solicitud.
    Solo expone estado y comentario_admin.
    """

    class Meta:
        model = SolicitudRolComercial
        fields = ["estado", "comentario_admin"]
        labels = {
            "estado": "Estado de la solicitud",
            "comentario_admin": "Comentario del administrador",
        }
        widgets = {
            "estado": forms.Select(attrs={"class": "form-select"}),
            "comentario_admin": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ----------------- FORMULARIOS CRUD -----------------



class ProductoForm(ModelForm):

    UNIDAD_CHOICES = [
        ("m3", "m³"),
        ("saco", "Saco"),
        ("kg", "Kilogramo"),
        ("bolsa", "Bolsa"),
        ("pallet", "Pallet"),
    ]

    FORMATO_CHOICES = [
        ("METRO_RUMA", "Metro ruma"),
        ("M3_GRANEL", "m³ a granel"),
        ("SACO_15", "Saco 15 kg"),
        ("SACO_20", "Saco 20 kg"),
        ("SACO_25", "Saco 25 kg"),
        ("BOLSA", "Bolsa"),
        ("OTRO", "Otro"),
    ]

    class Meta:
        model = Producto
        fields = [
            "tipo_producto",
            "especie",
            "contenido_humedad",
            "formato",
            "unidad_medida",
            "precio_unitario",
            "descripcion",
            "comuna",
            "stock_disponible",
            "certificado_sncl",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Forzar desplegables
        self.fields["unidad_medida"].widget = forms.Select(choices=self.UNIDAD_CHOICES)
        self.fields["formato"].widget = forms.Select(choices=self.FORMATO_CHOICES)

        # Comuna: por ahora, fija a la del usuario
        if user and getattr(user, "comuna_id", None):
            self.fields["comuna"].queryset = Comuna.objects.filter(id=user.comuna_id)
            self.fields["comuna"].initial = user.comuna_id
            self.fields["comuna"].disabled = True

class ServicioForm(ModelForm):
    class Meta:
        model = Servicio
        fields = [
            "tipo_servicio",
            "nombre",
            "descripcion",
            "precio_base",
            "unidad_precio",
            "comunas_cobertura",
            "activo",
        ]


class ContenidoEducativoForm(ModelForm):
    class Meta:
        model = ContenidoEducativo
        fields = [
            "titulo",
            "slug",
            "resumen",
            "texto",
            "tema",
            "activo",
        ]
