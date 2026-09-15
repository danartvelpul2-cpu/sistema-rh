from django.contrib import admin

from .models import (
    Area, Cargo, Empleado, Contrato, NominaPeriodo, NovedadNomina,
    Permiso, Dotacion, Vacante, Candidato,
)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "area")
    list_filter = ("area",)
    search_fields = ("nombre",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "numero_documento", "cargo", "area", "jefe", "estado")
    list_filter = ("estado", "area", "cargo")
    search_fields = ("nombres", "apellidos", "numero_documento", "email")


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "tipo", "fecha_inicio", "fecha_fin", "salario", "estado")
    list_filter = ("tipo", "estado", "modalidad")
    search_fields = ("empleado__nombres", "empleado__apellidos")


@admin.register(NominaPeriodo)
class NominaPeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "estado")


@admin.register(NovedadNomina)
class NovedadNominaAdmin(admin.ModelAdmin):
    list_display = ("empleado", "periodo", "concepto", "movimiento", "total")
    list_filter = ("periodo", "movimiento", "concepto")


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "tipo", "fecha_inicio", "fecha_fin", "estado")
    list_filter = ("tipo", "estado")


@admin.register(Dotacion)
class DotacionAdmin(admin.ModelAdmin):
    list_display = ("empleado", "tipo", "descripcion", "fecha_entrega", "estado")
    list_filter = ("tipo", "estado")


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ("cargo", "estado", "fecha_apertura", "fecha_cierre")
    list_filter = ("estado",)


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "vacante", "etapa", "fuente")
    list_filter = ("etapa", "vacante")
