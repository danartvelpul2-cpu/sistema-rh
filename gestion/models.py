"""
Modelos del sistema de gestión de Recursos Humanos.
"""
from datetime import date
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Area(models.Model):
    """Áreas / departamentos de la empresa."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Áreas"

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    """Cargos disponibles en la empresa."""

    nombre = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="cargos")
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Cargos"
        unique_together = ("nombre", "area")

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


class Empleado(models.Model):
    """Colaborador de la empresa. El campo `jefe` construye el organigrama."""

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_documento = models.CharField(
        max_length=20,
        choices=[
            ("CC", "Cédula de ciudadanía"),
            ("CE", "Cédula de extranjería"),
            ("PA", "Pasaporte"),
            ("NIT", "NIT"),
        ],
        default="CC",
    )
    numero_documento = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_ingreso = models.DateField(default=date.today, blank=True)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="empleados")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="empleados")
    jefe = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinados",
        help_text="Jefe inmediato. Define la jerarquía del organigrama.",
    )
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def get_absolute_url(self):
        return reverse("empleado-detalle", kwargs={"pk": self.pk})

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def clean(self):
        if self.jefe_id and self.jefe_id == self.pk:
            raise ValidationError("Un empleado no puede ser su propio jefe.")


class Contrato(models.Model):
    """
    Contratos laborales. Se soportan contratos fijos con duraciones
    diferentes por persona (término fijo con fecha de finalización propia),
    indefinidos, obra/labor, prestación de servicios y aprendizaje.
    """

    class Tipo(models.TextChoices):
        INDEFINIDO = "INDEFINIDO", "Término indefinido"
        FIJO = "FIJO", "Término fijo"
        OBRA_LABOR = "OBRA_LABOR", "Obra o labor"
        PRESTACION_SERVICIOS = "PRESTACION_SERVICIOS", "Prestación de servicios"
        APRENDIZAJE = "APRENDIZAJE", "Contrato de aprendizaje"

    class Modalidad(models.TextChoices):
        PRESENCIAL = "PRESENCIAL", "Presencial"
        REMOTO = "REMOTO", "Remoto"
        HIBRIDO = "HIBRIDO", "Híbrido"

    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        FINALIZADO = "FINALIZADO", "Finalizado"

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="contratos")
    tipo = models.CharField(max_length=25, choices=Tipo.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(
        null=True, blank=True,
        help_text="Obligatoria para término fijo, obra/labor y aprendizaje.",
    )
    salario = models.DecimalField(max_digits=12, decimal_places=2)
    modalidad = models.CharField(max_length=15, choices=Modalidad.choices, default=Modalidad.PRESENCIAL)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.VIGENTE)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name_plural = "Contratos"

    def __str__(self):
        return f"Contrato {self.get_tipo_display()} — {self.empleado}"

    def clean(self):
        if self.tipo in (self.Tipo.FIJO, self.Tipo.OBRA_LABOR, self.Tipo.APRENDIZAJE) and not self.fecha_fin:
            raise ValidationError(
                {"fecha_fin": "Este tipo de contrato exige fecha de finalización."}
            )
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": "No puede ser anterior a la fecha de inicio."})

    @property
    def dias_para_vencer(self):
        """Días restantes hasta la fecha de finalización (None si no aplica)."""
        if not self.fecha_fin or self.estado != self.Estado.VIGENTE:
            return None
        return (self.fecha_fin - date.today()).days

    @property
    def esta_por_vencer(self):
        dias = self.dias_para_vencer
        return dias is not None and 0 <= dias <= 30


class NominaPeriodo(models.Model):
    """Periodo de nómina mensual."""

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        CERRADA = "CERRADA", "Cerrada"

    anio = models.PositiveIntegerField()
    mes = models.PositiveIntegerField(choices=[(m, m) for m in range(1, 13)])
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA)

    class Meta:
        ordering = ["-anio", "-mes"]
        unique_together = ("anio", "mes")
        verbose_name_plural = "Periodos de nómina"

    def __str__(self):
        return f"{self.anio}-{self.mes:02d}"

    def get_absolute_url(self):
        return reverse("nomina-detalle", kwargs={"pk": self.pk})


class NovedadNomina(models.Model):
    """
    Novedades de nómina: conceptos que suman (devengados) o restan
    (deducciones) al pago de un empleado en un periodo.
    """

    class Movimiento(models.TextChoices):
        DEVENGADO = "DEVENGADO", "Devengado (suma)"
        DEDUCIDO = "DEDUCIDO", "Deducido (resta)"

    class Concepto(models.TextChoices):
        HORAS_EXTRA = "HORAS_EXTRA", "Horas extra"
        RECARGO_NOCTURNO = "RECARGO_NOCTURNO", "Recargo nocturno"
        DOMINICAL_FESTIVO = "DOMINICAL_FESTIVO", "Trabajo dominical/festivo"
        BONIFICACION = "BONIFICACION", "Bonificación"
        COMISION = "COMISION", "Comisión"
        INCAPACIDAD = "INCAPACIDAD", "Incapacidad"
        AUSENCIA = "AUSENCIA", "Ausencia no justificada"
        DESCUENTO = "DESCUENTO", "Descuento autorizado"
        EMBARGO = "EMBARGO", "Embargo"
        OTRO_DEVENGADO = "OTRO_DEVENGADO", "Otro devengado"
        OTRO_DEDUCIDO = "OTRO_DEDUCIDO", "Otra deducción"

    # Conceptos que por defecto son deducciones
    DEDUCIDOS_POR_DEFECTO = {
        Concepto.AUSENCIA, Concepto.DESCUENTO, Concepto.EMBARGO, Concepto.OTRO_DEDUCIDO
    }

    periodo = models.ForeignKey(NominaPeriodo, on_delete=models.CASCADE, related_name="novedades")
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="novedades")
    concepto = models.CharField(max_length=25, choices=Concepto.choices)
    movimiento = models.CharField(max_length=10, choices=Movimiento.choices)
    cantidad = models.DecimalField(
        max_digits=8, decimal_places=2, default=1,
        help_text="Cantidad: horas, días o unidades.",
    )
    valor_unitario = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Valor por unidad. El total = cantidad × valor unitario.",
    )
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["empleado", "concepto"]
        verbose_name_plural = "Novedades de nómina"

    def __str__(self):
        return f"{self.get_concepto_display()} — {self.empleado} ({self.periodo})"

    @property
    def total(self):
        return self.cantidad * self.valor_unitario


class Permiso(models.Model):
    """Permisos, licencias, vacaciones e incapacidades."""

    class Tipo(models.TextChoices):
        VACACIONES = "VACACIONES", "Vacaciones"
        LICENCIA_REMUNERADA = "LICENCIA_REMUNERADA", "Licencia remunerada"
        LICENCIA_NO_REMUNERADA = "LICENCIA_NO_REMUNERADA", "Licencia no remunerada"
        PERMISO_REMUNERADO = "PERMISO_REMUNERADO", "Permiso remunerado"
        PERMISO_NO_REMUNERADO = "PERMISO_NO_REMUNERADO", "Permiso no remunerado"
        INCAPACIDAD = "INCAPACIDAD", "Incapacidad"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="permisos")
    tipo = models.CharField(max_length=25, choices=Tipo.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.TextField(blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name_plural = "Permisos"

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.empleado}"

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": "No puede ser anterior a la fecha de inicio."})

    @property
    def dias(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1


class Dotacion(models.Model):
    """Entregas de dotación: uniformes, EPP, herramientas."""

    class Tipo(models.TextChoices):
        UNIFORME = "UNIFORME", "Uniforme"
        EPP = "EPP", "Elemento de protección (EPP)"
        HERRAMIENTA = "HERRAMIENTA", "Herramienta"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        ENTREGADA = "ENTREGADA", "Entregada"
        PENDIENTE = "PENDIENTE", "Pendiente"
        DEVUELTA = "DEVUELTA", "Devuelta"

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="dotaciones")
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    descripcion = models.CharField(max_length=200)
    fecha_entrega = models.DateField(default=date.today, blank=True)
    fecha_cambio = models.DateField(
        null=True, blank=True, help_text="Fecha programada para reposición/cambio."
    )
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ENTREGADA)

    class Meta:
        ordering = ["-fecha_entrega"]
        verbose_name_plural = "Dotaciones"

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.descripcion} — {self.empleado}"

    @property
    def proximo_cambio(self):
        """Próxima fecha de reposición sugerida (anual por defecto)."""
        return self.fecha_cambio or (self.fecha_entrega + relativedelta(years=1))


class Vacante(models.Model):
    """Proceso de selección: vacante publicada."""

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        CERRADA = "CERRADA", "Cerrada"

    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="vacantes")
    descripcion = models.TextField()
    salario_ofrecido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_apertura = models.DateField(default=date.today)
    fecha_cierre = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA)
    responsable = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name="vacantes_responsables"
    )

    class Meta:
        ordering = ["-fecha_apertura"]
        verbose_name_plural = "Vacantes"

    def __str__(self):
        return f"Vacante: {self.cargo.nombre}"


class Candidato(models.Model):
    """Candidatos de un proceso de selección, con embudo de etapas."""

    class Etapa(models.TextChoices):
        POSTULADO = "POSTULADO", "Postulado"
        SCREENING = "SCREENING", "Filtrado (screening)"
        ENTREVISTA = "ENTREVISTA", "Entrevista"
        PRUEBA = "PRUEBA", "Prueba técnica"
        OFERTA = "OFERTA", "Oferta"
        CONTRATADO = "CONTRATADO", "Contratado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name="candidatos")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fuente = models.CharField(max_length=50, blank=True, help_text="LinkedIn, computrabajo, referido…")
    etapa = models.CharField(max_length=15, choices=Etapa.choices, default=Etapa.POSTULADO)
    notas = models.TextField(blank=True)
    fecha_postulacion = models.DateField(default=date.today, blank=True)

    class Meta:
        ordering = ["vacante", "-fecha_postulacion"]
        verbose_name_plural = "Candidatos"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
