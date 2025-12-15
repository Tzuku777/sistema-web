from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

class BloqueoPorNoVerificarEmailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            if not user.email_verificado:
                if timezone.now() > user.date_joined + timedelta(days=7):
                    user.bloqueado = True
                    user.save(update_fields=["bloqueado"])

            if getattr(user, "bloqueado", False):
                # Permite logout y verificar-email, bloquea el resto
                ruta = request.path
                allow = [
                    reverse("plataforma:logout"),
                ]
                if ruta.startswith("/verificar-email/") or ruta in allow:
                    return self.get_response(request)
                return redirect("plataforma:logout")

        return self.get_response(request)
