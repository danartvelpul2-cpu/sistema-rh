"""Vistas del sistema de gestión de RRHH."""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models as db_models
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import (
    AreaForm, CargoForm, EmpleadoForm, ContratoForm, PeriodoForm, NovedadForm,
    PermisoForm, PermisoAprobacionForm, DotacionForm, VacanteForm,
    CandidatoForm, CandidatoEtapaForm,
)
from .models import (
    Area, Cargo, Empleado, Contrato, NominaPeriodo, NovedadNomina,
    Permiso, Dotacion, Vacante, Candidato,
)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "gestion/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = date.today()
        limite = hoy + timedelta(days=30)

        ctx["total_empleados"] = Empleado.objects.filter(estado="ACTIVO").count()
        ctx["total_areas"] = Area.objects.count()
        ctx["contratos_vigentes"] = Contrato.objects.filter(estado="VIGENTE").count()
        ctx["contratos_por_vencer"] = Contrato.objects.filter(
            estado="VIGENTE", fecha_fin__isnull=False, fecha_fin__lte=limite, fecha_fin__gte=hoy
        ).order_by("fecha_fin")
        ctx["permisos_pendientes"] = Permiso.objects.filter(estado="PENDIENTE").count()
        ctx["vacantes_abiertas"] = Vacante.objects.filter(estado="ABIERTA").count()
        ctx["candidatos_activos"] = Candidato.objects.exclude(
            etapa__in=[Candidato.Etapa.CONTRATADO, Candidato.Etapa.RECHAZADO]
        ).count()
        ctx["dotaciones_pendientes"] = Dotacion.objects.filter(estado="PENDIENTE").count()
        ctx["ultimos_permisos"] = Permiso.objects.select_related("empleado")[:6]
        ctx["ultimas_novedades"] = NovedadNomina.objects.select_related("empleado", "periodo")[:6]

        # Distribución de empleados por área para el gráfico del dashboard
        ctx["areas_chart"] = Area.objects.annotate(
            total=Count("empleados", filter=db_models.Q(empleados__estado="ACTIVO"))
        ).values("nombre", "total").order_by("-total")
        return ctx


# ---------------------------------------------------------------------------
# Mixin común para vistas CRUD
# ---------------------------------------------------------------------------

class MensajeMixin:
    """Muestra un mensaje de éxito después de guardar."""

    mensaje_exito = "Registro guardado correctamente."

    def form_valid(self, form):
        messages.success(self.request, self.mensaje_exito)
        return super().form_valid(form)


class EliminarMixin(MensajeMixin):
    """Muestra mensaje tras eliminar."""

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Registro eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Estructura: áreas y cargos
# ---------------------------------------------------------------------------

class AreaListView(LoginRequiredMixin, ListView):
    model = Area
    template_name = "gestion/area_lista.html"
    context_object_name = "areas"


class AreaCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Area
    form_class = AreaForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("area-lista")
    extra_context = {"titulo": "Nueva área"}


class AreaUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Area
    form_class = AreaForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("area-lista")
    extra_context = {"titulo": "Editar área"}


class AreaDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Area
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("area-lista")


class CargoListView(LoginRequiredMixin, ListView):
    model = Cargo
    template_name = "gestion/cargo_lista.html"
    context_object_name = "cargos"


class CargoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Cargo
    form_class = CargoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("cargo-lista")
    extra_context = {"titulo": "Nuevo cargo"}


class CargoUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Cargo
    form_class = CargoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("cargo-lista")
    extra_context = {"titulo": "Editar cargo"}


class CargoDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Cargo
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("cargo-lista")


# ---------------------------------------------------------------------------
# Empleados
# ---------------------------------------------------------------------------

class EmpleadoListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = "gestion/empleado_lista.html"
    context_object_name = "empleados"

    def get_queryset(self):
        qs = Empleado.objects.select_related("area", "cargo", "jefe")
        busqueda = self.request.GET.get("q")
        if busqueda:
            qs = qs.filter(
                db_models.Q(nombres__icontains=busqueda)
                | db_models.Q(apellidos__icontains=busqueda)
                | db_models.Q(numero_documento__icontains=busqueda)
                | db_models.Q(cargo__nombre__icontains=busqueda)
            )
        return qs


class EmpleadoDetailView(LoginRequiredMixin, DetailView):
    model = Empleado
    template_name = "gestion/empleado_detalle.html"
    context_object_name = "empleado"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contratos"] = self.object.contratos.all()
        ctx["permisos"] = self.object.permisos.all()[:5]
        ctx["dotaciones"] = self.object.dotaciones.all()[:5]
        ctx["subordinados"] = self.object.subordinados.filter(estado="ACTIVO")
        return ctx


class EmpleadoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("empleado-lista")
    extra_context = {"titulo": "Nuevo empleado"}


class EmpleadoUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("empleado-lista")
    extra_context = {"titulo": "Editar empleado"}


class EmpleadoDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Empleado
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("empleado-lista")


# ---------------------------------------------------------------------------
# Contratos
# ---------------------------------------------------------------------------

class ContratoListView(LoginRequiredMixin, ListView):
    model = Contrato
    template_name = "gestion/contrato_lista.html"
    context_object_name = "contratos"

    def get_queryset(self):
        return Contrato.objects.select_related("empleado").filter(
            estado=self.request.GET.get("estado", "VIGENTE")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro_estado"] = self.request.GET.get("estado", "VIGENTE")
        return ctx


class ContratoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Contrato
    form_class = ContratoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("contrato-lista")
    extra_context = {"titulo": "Nuevo contrato"}


class ContratoUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Contrato
    form_class = ContratoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("contrato-lista")
    extra_context = {"titulo": "Editar contrato"}


class ContratoDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Contrato
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("contrato-lista")


# ---------------------------------------------------------------------------
# Nómina: periodos, liquidación y novedades
# ---------------------------------------------------------------------------

def liquidar_periodo(periodo):
    """
    Calcula la liquidación de un periodo: por cada empleado activo con
    contrato vigente, toma el salario del contrato, suma los devengados
    y resta las deducciones registradas como novedades.
    Devuelve una lista de diccionarios con el desglose por empleado.
    """
    liquidacion = []
    empleados = Empleado.objects.filter(
        estado="ACTIVO", contratos__estado="VIGENTE"
    ).distinct()

    for emp in empleados:
        contrato = emp.contratos.filter(estado="VIGENTE").order_by("-fecha_inicio").first()
        basico = contrato.salario if contrato else emp.salario_base
        novedades = NovedadNomina.objects.filter(periodo=periodo, empleado=emp)
        devengados = novedades.filter(movimiento=NovedadNomina.Movimiento.DEVENGADO).aggregate(
            t=Sum(db_models.F("cantidad") * db_models.F("valor_unitario"))
        )["t"] or 0
        deducciones = novedades.filter(movimiento=NovedadNomina.Movimiento.DEDUCIDO).aggregate(
            t=Sum(db_models.F("cantidad") * db_models.F("valor_unitario"))
        )["t"] or 0
        liquidacion.append({
            "empleado": emp,
            "contrato": contrato,
            "basico": basico,
            "devengados": devengados,
            "deducciones": deducciones,
            "neto": basico + devengados - deducciones,
            "novedades": novedades,
        })
    return liquidacion


class PeriodoListView(LoginRequiredMixin, ListView):
    model = NominaPeriodo
    template_name = "gestion/periodo_lista.html"
    context_object_name = "periodos"


class PeriodoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = NominaPeriodo
    form_class = PeriodoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("periodo-lista")
    extra_context = {"titulo": "Nuevo periodo de nómina"}


class PeriodoDetailView(LoginRequiredMixin, DetailView):
    model = NominaPeriodo
    template_name = "gestion/periodo_detalle.html"
    context_object_name = "periodo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["liquidacion"] = liquidar_periodo(self.object)
        ctx["total_neto"] = sum(f["neto"] for f in ctx["liquidacion"])
        return ctx


class NovedadListView(LoginRequiredMixin, ListView):
    model = NovedadNomina
    template_name = "gestion/novedad_lista.html"
    context_object_name = "novedades"

    def get_queryset(self):
        return NovedadNomina.objects.select_related("empleado", "periodo")


class NovedadCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = NovedadNomina
    form_class = NovedadForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("novedad-lista")
    extra_context = {"titulo": "Nueva novedad de nómina"}


class NovedadUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = NovedadNomina
    form_class = NovedadForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("novedad-lista")
    extra_context = {"titulo": "Editar novedad de nómina"}


class NovedadDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = NovedadNomina
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("novedad-lista")


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------

class PermisoListView(LoginRequiredMixin, ListView):
    model = Permiso
    template_name = "gestion/permiso_lista.html"
    context_object_name = "permisos"

    def get_queryset(self):
        return Permiso.objects.select_related("empleado")


class PermisoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Permiso
    form_class = PermisoForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("permiso-lista")
    extra_context = {"titulo": "Nuevo permiso"}


@login_required
def permiso_aprobar(request, pk):
    permiso = get_object_or_404(Permiso, pk=pk)
    if request.method == "POST":
        form = PermisoAprobacionForm(request.POST, instance=permiso)
        if form.is_valid():
            permiso = form.save(commit=False)
            permiso.aprobado_por = request.user
            permiso.save()
            messages.success(request, f"Permiso marcado como {permiso.get_estado_display()}.")
            return redirect("permiso-lista")
    else:
        form = PermisoAprobacionForm(instance=permiso)
    return render(request, "gestion/permiso_aprobar.html", {"form": form, "permiso": permiso})


class PermisoDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Permiso
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("permiso-lista")


# ---------------------------------------------------------------------------
# Dotaciones
# ---------------------------------------------------------------------------

class DotacionListView(LoginRequiredMixin, ListView):
    model = Dotacion
    template_name = "gestion/dotacion_lista.html"
    context_object_name = "dotaciones"

    def get_queryset(self):
        return Dotacion.objects.select_related("empleado")


class DotacionCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Dotacion
    form_class = DotacionForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("dotacion-lista")
    extra_context = {"titulo": "Nueva dotación"}


class DotacionUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Dotacion
    form_class = DotacionForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("dotacion-lista")
    extra_context = {"titulo": "Editar dotación"}


class DotacionDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Dotacion
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("dotacion-lista")


# ---------------------------------------------------------------------------
# Selección: vacantes y candidatos
# ---------------------------------------------------------------------------

class VacanteListView(LoginRequiredMixin, ListView):
    model = Vacante
    template_name = "gestion/vacante_lista.html"
    context_object_name = "vacantes"

    def get_queryset(self):
        return Vacante.objects.select_related("cargo", "cargo__area").annotate(
            num_candidatos=Count("candidatos")
        )


class VacanteCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Vacante
    form_class = VacanteForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("vacante-lista")
    extra_context = {"titulo": "Nueva vacante"}


class VacanteUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Vacante
    form_class = VacanteForm
    template_name = "gestion/formulario.html"
    success_url = reverse_lazy("vacante-lista")
    extra_context = {"titulo": "Editar vacante"}


class VacanteDetailView(LoginRequiredMixin, DetailView):
    model = Vacante
    template_name = "gestion/vacante_detalle.html"
    context_object_name = "vacante"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["candidatos"] = self.object.candidatos.all()
        return ctx


class VacanteDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Vacante
    template_name = "gestion/confirmar_eliminar.html"
    success_url = reverse_lazy("vacante-lista")


class CandidatoCreateView(LoginRequiredMixin, MensajeMixin, CreateView):
    model = Candidato
    form_class = CandidatoForm
    template_name = "gestion/formulario.html"

    def get_success_url(self):
        return reverse("vacante-detalle", kwargs={"pk": self.object.vacante_id})


class CandidatoUpdateView(LoginRequiredMixin, MensajeMixin, UpdateView):
    model = Candidato
    form_class = CandidatoForm
    template_name = "gestion/formulario.html"

    def get_success_url(self):
        return reverse("vacante-detalle", kwargs={"pk": self.object.vacante_id})


@login_required
def candidato_etapa(request, pk):
    candidato = get_object_or_404(Candidato, pk=pk)
    if request.method == "POST":
        form = CandidatoEtapaForm(request.POST, instance=candidato)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{candidato.nombre_completo} ahora está en etapa "
                f"{candidato.get_etapa_display()}.",
            )
            return redirect("vacante-detalle", pk=candidato.vacante_id)
    else:
        form = CandidatoEtapaForm(instance=candidato)
    return render(request, "gestion/candidato_etapa.html", {"form": form, "candidato": candidato})


class CandidatoDeleteView(LoginRequiredMixin, EliminarMixin, DeleteView):
    model = Candidato
    template_name = "gestion/confirmar_eliminar.html"

    def get_success_url(self):
        return reverse("vacante-detalle", kwargs={"pk": self.object.vacante_id})


# ---------------------------------------------------------------------------
# Organigrama
# ---------------------------------------------------------------------------

class OrganigramaView(LoginRequiredMixin, TemplateView):
    template_name = "gestion/organigrama.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        activos = Empleado.objects.filter(estado="ACTIVO").select_related("cargo", "area")
        empleados_ids = set(activos.values_list("pk", flat=True))
        # Raíces: activos sin jefe, o cuyo jefe no está activo
        raices = [
            e for e in activos
            if e.jefe_id is None or e.jefe_id not in empleados_ids
        ]

        def nodo(emp):
            return {
                "empleado": emp,
                "hijos": [nodo(h) for h in emp.subordinados.filter(estado="ACTIVO")],
            }

        ctx["raices"] = [nodo(r) for r in raices]
        return ctx
