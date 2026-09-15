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
        DEVENGADO = "DEVENGADO", "Remunerado (suma en nómina)"
        DEDUCIDO = "DEDUCIDO", "Deducido (resta en nómina)"
        COMPENSABLE = "COMPENSABLE", "Compensable en tiempo (sin pago)"

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
    movimiento = models.CharField(max_length=12, choices=Movimiento.choices)
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
    remunerado = models.BooleanField(
        default=True,
        help_text="Si NO es remunerado, al aprobarse se descuenta automáticamente de la nómina.",
    )
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


class SalarioMinimo(models.Model):
    """Salario mínimo legal mensual (SMMLV) por año vigente en Colombia.

    Se usa para validar el derecho a dotación (trabajadores que devengan
    menos de 2 SMMLV) y otros auxilios. Actualizar cada año según decreto.
    """

    anio = models.PositiveIntegerField(unique=True, verbose_name="Año")
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["-anio"]
        verbose_name = "Salario mínimo (SMMLV)"
        verbose_name_plural = "Salarios mínimos (SMMLV)"

    def __str__(self):
        return f"SMMLV {self.anio}: ${self.valor:,.0f}"

    @classmethod
    def vigente_para(cls, anio):
        """SMMLV aplicable a un año: el más reciente definido hasta ese año."""
        return cls.objects.filter(anio__lte=anio).order_by("-anio").first()


class Dotacion(models.Model):
    """
    Entregas de dotación según la ley colombiana:
    - Derecho solo para trabajadores que devenguen MENOS de 2 SMMLV.
    - Entregas a más tardar el 30 de abril, 31 de agosto y 20 de diciembre.
    - Items: camisa, camiseta, jean y botas.
    """

    class Item(models.TextChoices):
        CAMISA = "CAMISA", "Camisa"
        CAMISETA = "CAMISETA", "Camiseta"
        JEAN = "JEAN", "Jean / Pantalón"
        BOTAS = "BOTAS", "Botas"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        ENTREGADA = "ENTREGADA", "Entregada"
        PENDIENTE = "PENDIENTE", "Pendiente"
        DEVUELTA = "DEVUELTA", "Devuelta"

    # (mes, día) de las fechas límite legales de entrega por periodo
    FECHAS_LIMITE = ((4, 30), (8, 31), (12, 20))
    NOMBRES_PERIODO = {4: "Primera entrega (abril)", 8: "Segunda entrega (agosto)",
                       12: "Tercera entrega (diciembre)"}

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="dotaciones")
    item = models.CharField(max_length=15, choices=Item.choices, default=Item.CAMISA)
    descripcion = models.CharField(
        max_length=200, blank=True,
        help_text="Talla, color u otras especificaciones.",
    )
    fecha_entrega = models.DateField(default=date.today, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ENTREGADA)

    class Meta:
        ordering = ["-fecha_entrega"]
        verbose_name_plural = "Dotaciones"

    def __str__(self):
        return f"{self.get_item_display()} — {self.empleado}"

    @property
    def fecha_limite_periodo(self):
        """Fecha límite legal del periodo al que pertenece la entrega."""
        anio = self.fecha_entrega.year
        for mes, dia in self.FECHAS_LIMITE:
            if self.fecha_entrega.month <= mes:
                return date(anio, mes, dia)
        return date(anio, 12, 20)

    @property
    def periodo(self):
        return self.NOMBRES_PERIODO.get(self.fecha_limite_periodo.month, "")

    @property
    def limite_elegibilidad(self):
        """Tope salarial para derecho a dotación: 2 SMMLV del año de entrega."""
        smmlv = SalarioMinimo.vigente_para(self.fecha_entrega.year)
        return (smmlv.valor * 2) if smmlv else None

    @property
    def empleado_es_elegible(self):
        """True si el trabajador devenga menos de 2 SMMLV (ley colombiana)."""
        limite = self.limite_elegibilidad
        if limite is None:
            return True  # sin SMMLV configurado no se puede validar
        contrato = (
            self.empleado.contratos.filter(estado=Contrato.Estado.VIGENTE)
            .order_by("-fecha_inicio").first()
        )
        salario = contrato.salario if contrato else self.empleado.salario_base
        return salario < limite

    def clean(self):
        limite_periodo = self.fecha_limite_periodo
        if self.fecha_entrega and self.fecha_entrega > limite_periodo:
            raise ValidationError({
                "fecha_entrega": (
                    f"La {self.periodo.lower()} debe entregarse a más tardar el "
                    f"{limite_periodo.strftime('%d/%m/%Y')} según la ley colombiana."
                )
            })
        if self.empleado_id and not self.empleado_es_elegible:
            raise ValidationError({
                "empleado": (
                    f"{self.empleado.nombre_completo} devenga igual o más de 2 SMMLV "
                    f"(tope: ${self.limite_elegibilidad:,.0f}) y por ley no tiene "
                    "derecho a dotación."
                )
            })


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


class CompensacionTiempo(models.Model):
    """
    Tiempo compensatorio por trabajos extra de cuadrillas: la empresa no paga
    horas extra sino que las compensa con tiempo libre, el cual debe tomarse
    a más tardar 1 mes después del día trabajado.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de tomar"
        TOMADA = "TOMADA", "Ya tomada"

    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="compensaciones"
    )
    fecha_trabajo = models.DateField(
        help_text="Día en que se realizó el trabajo extra (cuadrilla)."
    )
    horas = models.DecimalField(max_digits=6, decimal_places=2, help_text="Horas a compensar.")
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_limite = models.DateField(
        help_text="Fecha máxima para tomar el tiempo (regla interna: 1 mes)."
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_tomada = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["fecha_limite"]
        verbose_name = "Compensación de tiempo"
        verbose_name_plural = "Compensaciones de tiempo"

    def __str__(self):
        return f"{self.horas}h por compensar — {self.empleado}"

    @property
    def dias_restantes(self):
        return (self.fecha_limite - date.today()).days

    @property
    def vencida(self):
        return self.estado == self.Estado.PENDIENTE and self.fecha_limite < date.today()

    def clean(self):
        if self.fecha_limite and self.fecha_trabajo and self.fecha_limite < self.fecha_trabajo:
            raise ValidationError({"fecha_limite": "No puede ser anterior al día trabajado."})
        if self.estado == self.Estado.TOMADA:
            if not self.fecha_tomada:
                raise ValidationError({"fecha_tomada": "Indica cuándo se tomó el tiempo."})
            elif self.fecha_limite and self.fecha_tomada > self.fecha_limite:
                raise ValidationError(
                    {"fecha_tomada": "Se tomó después de la fecha límite (máximo 1 mes)."}
                )
