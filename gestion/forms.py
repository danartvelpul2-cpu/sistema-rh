"""Formularios del sistema de gestión de RRHH."""
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Area, Cargo, Empleado, Contrato, NominaPeriodo, NovedadNomina,
    Permiso, Dotacion, Vacante, Candidato,
)


class FormEstilo:
    """Aplica clases de Bootstrap 5 a los widgets automáticamente."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            clase = "form-select" if isinstance(
                campo.widget, forms.Select
            ) else "form-control"
            if isinstance(campo.widget, forms.CheckboxInput):
                clase = "form-check-input"
            elif isinstance(campo.widget, forms.DateInput):
                campo.widget.input_type = "date"
            elif isinstance(campo.widget, forms.NumberInput):
                clase = "form-control"
            campo.widget.attrs["class"] = clase


class AreaForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Area
        fields = ["nombre", "descripcion"]


class CargoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ["nombre", "area", "descripcion"]


class EmpleadoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            "nombres", "apellidos", "tipo_documento", "numero_documento",
            "email", "telefono", "fecha_nacimiento", "fecha_ingreso",
            "area", "cargo", "jefe", "salario_base", "estado",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["jefe"].queryset = Empleado.objects.filter(estado="ACTIVO").exclude(
            pk=self.instance.pk
        )

    def clean_fecha_ingreso(self):
        # Si viene vacío se aplica el valor por defecto (fecha de hoy)
        return self.cleaned_data.get("fecha_ingreso") or date.today()


class ContratoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            "empleado", "tipo", "fecha_inicio", "fecha_fin",
            "salario", "modalidad", "estado", "observaciones",
        ]

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        fecha_fin = cleaned.get("fecha_fin")
        requieren_fin = {
            Contrato.Tipo.FIJO, Contrato.Tipo.OBRA_LABOR, Contrato.Tipo.APRENDIZAJE
        }
        if tipo in requieren_fin and not fecha_fin:
            self.add_error("fecha_fin", "Este tipo de contrato exige fecha de finalización.")
        return cleaned


class PeriodoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = NominaPeriodo
        fields = ["anio", "mes", "estado"]


class NovedadForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = NovedadNomina
        fields = [
            "periodo", "empleado", "concepto", "movimiento",
            "cantidad", "valor_unitario", "descripcion",
        ]


class PermisoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ["empleado", "tipo", "fecha_inicio", "fecha_fin", "motivo"]


class PermisoAprobacionForm(FormEstilo, forms.ModelForm):
    """Formulario corto para aprobar o rechazar un permiso."""

    class Meta:
        model = Permiso
        fields = ["estado"]


class DotacionForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Dotacion
        fields = [
            "empleado", "item", "descripcion", "fecha_entrega", "estado",
        ]

    def clean_fecha_entrega(self):
        return self.cleaned_data.get("fecha_entrega") or date.today()


class VacanteForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Vacante
        fields = [
            "cargo", "descripcion", "salario_ofrecido",
            "fecha_apertura", "fecha_cierre", "estado", "responsable",
        ]


class CandidatoForm(FormEstilo, forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            "vacante", "nombres", "apellidos", "email", "telefono",
            "fuente", "etapa", "notas",
        ]


class CandidatoEtapaForm(FormEstilo, forms.ModelForm):
    """Formulario corto para mover un candidato de etapa."""

    class Meta:
        model = Candidato
        fields = ["etapa"]
