"""
Carga datos de demostración para explorar el sistema.

Uso:  python manage.py seed_demo
Crea el usuario admin / admin123 y un juego completo de datos de ejemplo.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from gestion.models import (
    Area, Cargo, Empleado, Contrato, NominaPeriodo, NovedadNomina,
    Permiso, Dotacion, Vacante, Candidato,
)


class Command(BaseCommand):
    help = "Carga datos de demostración (usuario: admin / admin123)"

    def handle(self, *args, **options):
        # Usuario administrador
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@empresa.com", "admin123")
            self.stdout.write("Usuario creado: admin / admin123")

        # Áreas
        areas_data = [
            ("Dirección General", "Alta dirección y estrategia"),
            ("Recursos Humanos", "Gestión del talento humano"),
            ("Contabilidad y Finanzas", "Pagos, tesorería y reporting"),
            ("Comercial y Ventas", "Fuerza de ventas y postventa"),
            ("Operaciones", "Producción y logística"),
            ("Tecnología", "Sistemas e infraestructura"),
        ]
        areas = {}
        for nombre, desc in areas_data:
            areas[nombre], _ = Area.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})

        # Cargos
        cargos_data = [
            ("Gerente General", "Dirección General"),
            ("Jefe de RRHH", "Recursos Humanos"),
            ("Analista de Nómina", "Recursos Humanos"),
            ("Reclutador", "Recursos Humanos"),
            ("Jefe de Contabilidad", "Contabilidad y Finanzas"),
            ("Contador", "Contabilidad y Finanzas"),
            ("Jefe Comercial", "Comercial y Ventas"),
            ("Asesor Comercial", "Comercial y Ventas"),
            ("Jefe de Operaciones", "Operaciones"),
            ("Auxiliar de Bodega", "Operaciones"),
            ("Desarrollador", "Tecnología"),
            ("Líder Técnico", "Tecnología"),
        ]
        cargos = {}
        for nombre, area in cargos_data:
            cargos[nombre], _ = Cargo.objects.get_or_create(
                nombre=nombre, area=areas[area], defaults={"descripcion": ""}
            )

        hoy = date.today()

        def crear_empleado(nombres, apellidos, doc, cargo, jefe, salario, dias_ingreso):
            emp, _ = Empleado.objects.get_or_create(
                numero_documento=doc,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "email": f"{nombres.split()[0].lower()}.{apellidos.split()[0].lower()}@empresa.com",
                    "telefono": "3000000000",
                    "fecha_ingreso": hoy - timedelta(days=dias_ingreso),
                    "area": cargos[cargo].area,
                    "cargo": cargos[cargo],
                    "jefe": jefe,
                    "salario_base": Decimal(str(salario)),
                },
            )
            return emp

        # Jerarquía
        gerente = crear_empleado("Carolina", "Restrepo", "1001", "Gerente General", None, 9000000, 1200)
        jefe_rrhh = crear_empleado("Andrés", "García", "1002", "Jefe de RRHH", gerente, 6000000, 800)
        jefe_contab = crear_empleado("María", "Fernández", "1003", "Jefe de Contabilidad", gerente, 6000000, 750)
        jefe_comercial = crear_empleado("Julián", "Torres", "1004", "Jefe Comercial", gerente, 6500000, 900)
        jefe_oper = crear_empleado("Paola", "Zapata", "1005", "Jefe de Operaciones", gerente, 6200000, 820)
        lider_tec = crear_empleado("Sergio", "Ramírez", "1006", "Líder Técnico", gerente, 7000000, 700)

        empleados = [
            crear_empleado("Laura", "Gómez", "1007", "Analista de Nómina", jefe_rrhh, 3200000, 400),
            crear_empleado("Diego", "Martínez", "1008", "Reclutador", jefe_rrhh, 2800000, 350),
            crear_empleado("Ana", "López", "1009", "Contador", jefe_contab, 3500000, 500),
            crear_empleado("Camilo", "Ruiz", "1010", "Asesor Comercial", jefe_comercial, 2500000, 200),
            crear_empleado("Valentina", "Díaz", "1011", "Asesor Comercial", jefe_comercial, 2500000, 180),
            crear_empleado("Óscar", "Peña", "1012", "Auxiliar de Bodega", jefe_oper, 1800000, 600),
            crear_empleado("Natalia", "Castro", "1013", "Desarrollador", lider_tec, 4200000, 300),
            crear_empleado("Felipe", "Moreno", "1014", "Desarrollador", lider_tec, 4500000, 90),
        ]

        # Contratos con duraciones variables (fijos con diferente fecha fin por persona)
        contratos_data = [
            # (empleado, tipo, inicio_días_atras, fin, modalidad)
            (gerente, "INDEFINIDO", 1200, None, "PRESENCIAL"),
            (jefe_rrhh, "INDEFINIDO", 800, None, "HIBRIDO"),
            (jefe_contab, "FIJO", 750, hoy + timedelta(days=25), "PRESENCIAL"),        # por vencer
            (jefe_comercial, "FIJO", 900, hoy + timedelta(days=210), "PRESENCIAL"),
            (jefe_oper, "FIJO", 820, hoy + timedelta(days=545), "HIBRIDO"),
            (lider_tec, "INDEFINIDO", 700, None, "REMOTO"),
            (empleados[0], "FIJO", 400, hoy + timedelta(days=330), "PRESENCIAL"),
            (empleados[1], "FIJO", 350, hoy + timedelta(days=380), "PRESENCIAL"),
            (empleados[2], "FIJO", 500, hoy + timedelta(days=230), "HIBRIDO"),
            (empleados[3], "FIJO", 200, hoy + timedelta(days=165), "PRESENCIAL"),       # por vencer
            (empleados[4], "FIJO", 180, hoy + timedelta(days=185), "PRESENCIAL"),
            (empleados[5], "INDEFINIDO", 600, None, "PRESENCIAL"),
            (empleados[6], "FIJO", 300, hoy + timedelta(days=430), "REMOTO"),
            (empleados[7], "APRENDIZAJE", 90, hoy + timedelta(days=270), "REMOTO"),     # aprendizaje
        ]
        salarios = {
            gerente: 9000000, jefe_rrhh: 6000000, jefe_contab: 6000000,
            jefe_comercial: 6500000, jefe_oper: 6200000, lider_tec: 7000000,
        }
        for emp, sal in zip(empleados, [3200000, 2800000, 3500000, 2500000, 2500000, 1800000, 4200000, 4500000]):
            salarios[emp] = sal

        for emp, tipo, dias_inicio, fin, modalidad in contratos_data:
            Contrato.objects.get_or_create(
                empleado=emp,
                fecha_inicio=hoy - timedelta(days=dias_inicio),
                defaults={
                    "tipo": tipo,
                    "fecha_fin": fin,
                    "salario": Decimal(str(salarios[emp])),
                    "modalidad": modalidad,
                    "estado": "VIGENTE",
                },
            )

        # Periodo de nómina y novedades
        mes_anterior = (hoy.month - 1) if hoy.month > 1 else 12
        anio = hoy.year if hoy.month > 1 else hoy.year - 1
        periodo, _ = NominaPeriodo.objects.get_or_create(anio=anio, mes=mes_anterior)

        novedades_data = [
            (empleados[3], "HORAS_EXTRA", "DEVENGADO", 12, 15000, "Horas extra campaña"),
            (empleados[4], "COMISION", "DEVENGADO", 1, 800000, "Comisión ventas junio"),
            (empleados[0], "BONIFICACION", "DEVENGADO", 1, 500000, "Bonificación por cierre de nómina"),
            (empleados[5], "RECARGO_NOCTURNO", "DEVENGADO", 20, 12000, "Inventario nocturno"),
            (empleados[7], "AUSENCIA", "DEDUCIDO", 2, 17000, "Ausencia no justificada"),
            (jefe_contab, "DOMINICAL_FESTIVO", "DEVENGADO", 3, 30000, "Cierre contable festivo"),
        ]
        for emp, concepto, mov, cant, valor, desc in novedades_data:
            NovedadNomina.objects.get_or_create(
                periodo=periodo, empleado=emp, concepto=concepto,
                defaults={"movimiento": mov, "cantidad": Decimal(str(cant)),
                          "valor_unitario": Decimal(str(valor)), "descripcion": desc},
            )

        # Permisos
        permisos_data = [
            (empleados[2], "VACACIONES", hoy + timedelta(days=10), hoy + timedelta(days=24), "Vacaciones anuales", "PENDIENTE"),
            (empleados[6], "LICENCIA_REMUNERADA", hoy - timedelta(days=5), hoy + timedelta(days=2), "Trámite personal", "APROBADO"),
            (empleados[7], "INCAPACIDAD", hoy - timedelta(days=3), hoy + timedelta(days=4), "Incapacidad médica", "PENDIENTE"),
            (empleados[0], "PERMISO_NO_REMUNERADO", hoy + timedelta(days=20), hoy + timedelta(days=20), "Evento familiar", "RECHAZADO"),
        ]
        for emp, tipo, ini, fin_, motivo, estado in permisos_data:
            Permiso.objects.get_or_create(
                empleado=emp, tipo=tipo, fecha_inicio=ini,
                defaults={"fecha_fin": fin_, "motivo": motivo, "estado": estado},
            )

        # Dotaciones
        dotaciones_data = [
            (empleados[5], "UNIFORME", "Overol + botas de seguridad", hoy - timedelta(days=300), None, "ENTREGADA"),
            (empleados[5], "EPP", "Guantes, gafas y casco", hoy - timedelta(days=60), hoy + timedelta(days=305), "ENTREGADA"),
            (empleados[3], "UNIFORME", "Camisa corporativa x3", hoy - timedelta(days=30), None, "ENTREGADA"),
            (empleados[4], "UNIFORME", "Camisa corporativa x3", hoy, hoy + timedelta(days=365), "PENDIENTE"),
            (lider_tec, "HERRAMIENTA", "Laptop Lenovo ThinkPad", hoy - timedelta(days=700), None, "ENTREGADA"),
        ]
        for emp, tipo, desc, entrega, cambio, estado in dotaciones_data:
            Dotacion.objects.get_or_create(
                empleado=emp, tipo=tipo, descripcion=desc, fecha_entrega=entrega,
                defaults={"fecha_cambio": cambio, "estado": estado},
            )

        # Vacantes y candidatos
        vac1, _ = Vacante.objects.get_or_create(
            cargo=cargos["Asesor Comercial"],
            defaults={
                "descripcion": "Asesor comercial para la zona norte, con experiencia en ventas B2B.",
                "salario_ofrecido": Decimal("2600000"),
                "fecha_apertura": hoy - timedelta(days=15),
                "responsable": jefe_comercial,
            },
        )
        vac2, _ = Vacante.objects.get_or_create(
            cargo=cargos["Desarrollador"],
            defaults={
                "descripcion": "Desarrollador fullstack con conocimientos en Python y Django.",
                "salario_ofrecido": Decimal("4600000"),
                "fecha_apertura": hoy - timedelta(days=40),
                "responsable": lider_tec,
            },
        )

        candidatos_data = [
            (vac1, "Jorge", "Salazar", "ENTREVISTA", "LinkedIn"),
            (vac1, "Tatiana", "Vargas", "POSTULADO", "Computrabajo"),
            (vac1, "Iván", "Quintero", "RECHAZADO", "Referido"),
            (vac2, "Mónica", "Herrera", "PRUEBA", "LinkedIn"),
            (vac2, "Ricardo", "Gil", "ENTREVISTA", "Referido"),
            (vac2, "Elena", "Rojas", "OFERTA", "LinkedIn"),
        ]
        for vac, nom, ape, etapa, fuente in candidatos_data:
            Candidato.objects.get_or_create(
                vacante=vac, nombres=nom, apellidos=ape,
                defaults={"etapa": etapa, "fuente": fuente},
            )

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
        self.stdout.write("Ingresa con: admin / admin123")
