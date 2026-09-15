"""URLs de la aplicación de gestión."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Autenticación
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="gestion/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Áreas
    path("areas/", views.AreaListView.as_view(), name="area-lista"),
    path("areas/nueva/", views.AreaCreateView.as_view(), name="area-crear"),
    path("areas/<int:pk>/editar/", views.AreaUpdateView.as_view(), name="area-editar"),
    path("areas/<int:pk>/eliminar/", views.AreaDeleteView.as_view(), name="area-eliminar"),

    # Cargos
    path("cargos/", views.CargoListView.as_view(), name="cargo-lista"),
    path("cargos/nuevo/", views.CargoCreateView.as_view(), name="cargo-crear"),
    path("cargos/<int:pk>/editar/", views.CargoUpdateView.as_view(), name="cargo-editar"),
    path("cargos/<int:pk>/eliminar/", views.CargoDeleteView.as_view(), name="cargo-eliminar"),

    # Empleados
    path("empleados/", views.EmpleadoListView.as_view(), name="empleado-lista"),
    path("empleados/nuevo/", views.EmpleadoCreateView.as_view(), name="empleado-crear"),
    path("empleados/<int:pk>/", views.EmpleadoDetailView.as_view(), name="empleado-detalle"),
    path("empleados/<int:pk>/editar/", views.EmpleadoUpdateView.as_view(), name="empleado-editar"),
    path("empleados/<int:pk>/eliminar/", views.EmpleadoDeleteView.as_view(), name="empleado-eliminar"),

    # Contratos
    path("contratos/", views.ContratoListView.as_view(), name="contrato-lista"),
    path("contratos/nuevo/", views.ContratoCreateView.as_view(), name="contrato-crear"),
    path("contratos/<int:pk>/editar/", views.ContratoUpdateView.as_view(), name="contrato-editar"),
    path("contratos/<int:pk>/eliminar/", views.ContratoDeleteView.as_view(), name="contrato-eliminar"),

    # Nómina
    path("nomina/", views.PeriodoListView.as_view(), name="periodo-lista"),
    path("nomina/nuevo/", views.PeriodoCreateView.as_view(), name="periodo-crear"),
    path("nomina/<int:pk>/", views.PeriodoDetailView.as_view(), name="nomina-detalle"),
    path("novedades/", views.NovedadListView.as_view(), name="novedad-lista"),
    path("novedades/nueva/", views.NovedadCreateView.as_view(), name="novedad-crear"),
    path("novedades/<int:pk>/editar/", views.NovedadUpdateView.as_view(), name="novedad-editar"),
    path("novedades/<int:pk>/eliminar/", views.NovedadDeleteView.as_view(), name="novedad-eliminar"),

    # Permisos
    path("permisos/", views.PermisoListView.as_view(), name="permiso-lista"),
    path("permisos/nuevo/", views.PermisoCreateView.as_view(), name="permiso-crear"),
    path("permisos/<int:pk>/aprobar/", views.permiso_aprobar, name="permiso-aprobar"),
    path("permisos/<int:pk>/eliminar/", views.PermisoDeleteView.as_view(), name="permiso-eliminar"),

    # Dotaciones
    path("dotaciones/", views.DotacionListView.as_view(), name="dotacion-lista"),
    path("dotaciones/nueva/", views.DotacionCreateView.as_view(), name="dotacion-crear"),
    path("dotaciones/<int:pk>/editar/", views.DotacionUpdateView.as_view(), name="dotacion-editar"),
    path("dotaciones/<int:pk>/eliminar/", views.DotacionDeleteView.as_view(), name="dotacion-eliminar"),

    # Selección
    path("seleccion/", views.VacanteListView.as_view(), name="vacante-lista"),
    path("seleccion/nueva/", views.VacanteCreateView.as_view(), name="vacante-crear"),
    path("seleccion/<int:pk>/", views.VacanteDetailView.as_view(), name="vacante-detalle"),
    path("seleccion/<int:pk>/editar/", views.VacanteUpdateView.as_view(), name="vacante-editar"),
    path("seleccion/<int:pk>/eliminar/", views.VacanteDeleteView.as_view(), name="vacante-eliminar"),
    path("candidatos/nuevo/", views.CandidatoCreateView.as_view(), name="candidato-crear"),
    path("candidatos/<int:pk>/editar/", views.CandidatoUpdateView.as_view(), name="candidato-editar"),
    path("candidatos/<int:pk>/etapa/", views.candidato_etapa, name="candidato-etapa"),
    path("candidatos/<int:pk>/eliminar/", views.CandidatoDeleteView.as_view(), name="candidato-eliminar"),

    # Organigrama
    path("organigrama/", views.OrganigramaView.as_view(), name="organigrama"),
]
