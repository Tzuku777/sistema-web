import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

RUT_REGEX = re.compile(r"^(\d{1,3}(?:\.\d{3})*)\-([\dkK])$")


def validar_rut_chileno(rut: str):
    """
    Valida formato y dígito verificador de un RUT chileno.
    Formato esperado: 12.345.678-5 o 12345678-5
    """
    if rut is None:
        raise ValidationError(_("RUT no puede ser nulo"))

    rut = rut.strip()

    # Normalizar: quitar puntos
    rut_sin_puntos = rut.replace(".", "")
    partes = rut_sin_puntos.split("-")
    if len(partes) != 2:
        raise ValidationError(_("Formato de RUT inválido. Use 12.345.678-5"))

    cuerpo, dv_ingresado = partes[0], partes[1].upper()

    if not cuerpo.isdigit():
        raise ValidationError(_("El cuerpo del RUT debe ser numérico"))

    # Cálculo dígito verificador
    reversed_digits = map(int, reversed(cuerpo))
    factors = [2, 3, 4, 5, 6, 7]
    suma = 0
    factor_index = 0

    for d in reversed_digits:
        suma += d * factors[factor_index]
        factor_index = (factor_index + 1) % len(factors)

    resto = suma % 11
    dv_calculado_num = 11 - resto

    if dv_calculado_num == 11:
        dv_calculado = "0"
    elif dv_calculado_num == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado_num)

    if dv_ingresado != dv_calculado:
        raise ValidationError(_("RUT inválido: dígito verificador incorrecto"))
