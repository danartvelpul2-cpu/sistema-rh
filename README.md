# Sistema de Gestión de Recursos Humanos

Aplicación web desarrollada en **Python + Django** para centralizar la gestión de
Recursos Humanos: empleados, contratos, nómina, novedades, permisos, dotaciones,
procesos de selección y organigrama.

## Módulos

| Módulo | Descripción |
|---|---|
| Dashboard | Indicadores: contratos por vencer, permisos pendientes, empleados por área |
| Empleados | Fichas con área, cargo, jefe inmediato, salario y estado |
| Contratos | Indefinidos, **término fijo con duración diferente por persona**, obra/labor, prestación de servicios y aprendizaje, con alertas de vencimiento |
| Nómina | Periodos mensuales con liquidación automática: básico + devengados − deducciones |
| Novedades | Horas extra, recargos, bonificaciones, comisiones, incapacidades, ausencias, descuentos |
| Permisos | Vacaciones, licencias e incapacidades con aprobación/rechazo |
| Dotaciones | Según ley colombiana: trabajadores < 2 SMMLV, entregas a más tardar el 30/abr, 31/ago y 20/dic (camisa, camiseta, jean, botas). SMMLV editable por año |
| Selección | Vacantes y candidatos con embudo de etapas |
| Organigrama | Generado automáticamente desde la jerarquía de jefes |

## Ejecutar en local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # datos de ejemplo (usuario: admin / admin123)
python manage.py runserver        # http://127.0.0.1:8000
```

## Ejecutar con Docker (recomendado)

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

```bash
docker compose up --build
```

Eso levanta **dos contenedores**: la app y una base de datos PostgreSQL local
(con volumen persistente, tus datos sobreviven reinicios). Abre
http://localhost:8000 e ingresa con `admin` / `admin123` (usuario y datos de
ejemplo creados automáticamente la primera vez gracias a `SEED_DEMO: "true"`
en `docker-compose.yml`).

Comandos útiles:

```bash
docker compose logs -f     # ver los logs en vivo
docker compose down        # detener todo
docker compose down -v     # detener y BORRAR la base de datos local
```

## Panel de administración

En `/admin/` con el mismo usuario. Todos los modelos son administrables.

## Despliegue a internet (Render.com — plan gratis)

1. Crea una cuenta en [Render](https://render.com) y sube este proyecto a un
   repositorio de GitHub/GitLab.
2. En Render: **New → Web Service** → conecta el repositorio.
3. Configura:
   - **Build command:** `./build.sh` (o `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`)
   - **Start command:** `gunicorn rh.wsgi --log-file -`
4. Variables de entorno:
   - `SECRET_KEY` → genera una clave larga y aleatoria
   - `DEBUG` → `False`
   - `ALLOWED_HOSTS` → `tudominio.onrender.com`
   - `DATABASE_URL` → crea una base de datos PostgreSQL en Render
     (New → PostgreSQL) y copia su URL interna
5. Despliega. Crea el superusuario con el shell de Render:
   `python manage.py createsuperuser`

### Alternativa: Railway

Mismo repositorio. Railway detecta el `Procfile` automáticamente.
Agrega las mismas variables de entorno (`SECRET_KEY`, `DEBUG=False`,
`ALLOWED_HOSTS`, `DATABASE_URL` de PostgreSQL).

## Estructura

```
rh_sistema/
├── manage.py
├── requirements.txt
├── Procfile / build.sh / runtime.txt
├── rh/                  # configuración del proyecto
└── gestion/             # aplicación principal
    ├── models.py        # 10 modelos de RRHH
    ├── views.py         # vistas y lógica de liquidación
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── management/commands/seed_demo.py
    └── templates/gestion/
```

## Seguridad

- Login obligatorio en todas las vistas (redirige a `/login/`).
- `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` se configuran por variables de
  entorno en producción.
- HTTPS forzado, cookies seguras y CSRF activado cuando `DEBUG=False`.
