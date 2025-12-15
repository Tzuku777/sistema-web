from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "plataforma"

urlpatterns = [

    # PÚBLICO
    path("", views.home, name="home"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("proveedor/<int:proveedor_id>/", views.detalle_proveedor, name="detalle_proveedor"),

    # API AUXILIARES
    path("api/comunas/<int:region_id>/", views.api_comunas_por_region, name="api_comunas_por_region"),

    # API para MODAL de solicitudes de proveedor
    path("api/solicitudes/<int:pk>/",views.api_solicitud_detalle,name="api_solicitud_detalle"),

    # AUTENTICACIÓN
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro_view, name="registro"),
    path("cuenta/configuracion/", views.configuracion_cuenta, name="configuracion_cuenta"),
    path("cuenta/password/",auth_views.PasswordChangeView.as_view(template_name="plataforma/cuenta_password.html",success_url="/cuenta/configuracion/?pwd=ok"),name="password_change",),


    # PANELES
    path("panel/", views.panel_usuario, name="panel_usuario"),
    path("panel-admin/", views.panel_admin, name="panel_admin"),
    path("panel-proveedor/", views.panel_proveedor, name="panel_proveedor"),

    # CRUD PRODUCTOS
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # CRUD SERVICIOS
    path("servicios/nuevo/", views.servicio_crear, name="servicio_crear"),
    path("servicios/<int:pk>/editar/", views.servicio_editar, name="servicio_editar"),
    path("servicios/<int:pk>/eliminar/", views.servicio_eliminar, name="servicio_eliminar"),

    # SOLICITUDES DE PROVEEDOR (ADMIN)
    path("panel-admin/solicitudes-proveedores/",views.solicitudes_proveedores_view,name="solicitudes_proveedores"),
    path("solicitudes/<int:pk>/cambiar-estado/",views.solicitud_proveedor_cambiar_estado,name="solicitud_proveedor_cambiar_estado"),
    path("solicitudes/",views.solicitudes_proveedores_view,name="solicitudes_proveedor_lista"),

    # CONTENIDO EDUCATIVO (ADMIN)
    path("educativo/admin/",views.educativo_admin_lista,name="educativo_admin_lista"),
    path("educativo/admin/nuevo/",views.educativo_admin_crear,name="educativo_admin_crear"),
    path("educativo/admin/<int:pk>/editar/",views.educativo_admin_editar,name="educativo_admin_editar"),
    path("educativo/admin/<int:pk>/eliminar/",views.educativo_admin_eliminar,name="educativo_admin_eliminar"),

    # CONTENIDO EDUCATIVO
    path("educativo/", views.educativo_lista, name="educativo_lista"),
    path("educativo/<slug:slug>/", views.educativo_detalle, name="educativo_detalle"),
    path("educativo/<slug:slug>/quiz/", views.quiz, name="quiz"),

]
