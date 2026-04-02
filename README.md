# Job Search Automation

Sistema automatizado de búsqueda y envío de CVs para San Francisco, Córdoba, Argentina.

## Descripción

Este proyecto busca ofertas de empleo diariamente en portales laborales gratuitos, filtra por la ciudad de San Francisco, Córdoba, y envía el CV automáticamente a las empresas. Incluye:

- ✅ Scraping de portales laborales (Computrabajo, Bumeran, ZonaJobs)
- ✅ Cooldown de 20 días por empresa (anti-spam)
- ✅ Fallback a empresas locales cuando no hay ofertas
- ✅ Registro SQLite del historial de envíos
- ✅ Programación automática con Windows Task Scheduler
- ✅ Envío de emails con Gmail SMTP

## Estructura del Proyecto

```
Buscador de trabajo/
├── main.py                 # Orquestador principal
├── config.py               # Configuración centralizada
├── .env                    # Credenciales SMTP (no incluir en git)
├── requirements.txt        # Dependencias Python
├── run.bat                 # Script para Task Scheduler
├── install.bat             # Script de instalación
├── scrapers/               # Módulos de scraping
│   ├── base.py
│   ├── computrabajo.py
│   ├── bumeran.py
│   └── zonajobs.py
├── core/                   # Componentes principales
│   ├── models.py           # Modelos de datos
│   ├── history_manager.py  # Gestor SQLite
│   ├── job_filter.py       # Filtros y blacklist
│   ├── email_sender.py     # Envío de emails
│   └── fallback.py         # Empresas locales
├── data/                   # Archivos de datos
│   ├── historial.db        # SQLite (generado automáticamente)
│   ├── local_companies.json # Empresas para fallback
│   └── blacklist.txt        # Empresas bloqueadas
├── templates/               # Plantillas de email
├── assets/                 # CV y recursos
│   └── cv.pdf
└── tests/                  # Tests unitarios
    └── test_core.py
```

## Requisitos

- Python 3.11+
- Windows
- Cuenta Gmail con contraseña de aplicación

## Instalación

1. Clonar el repositorio:
```bash
git clone <repositorio>
cd job-search-automation
```

2. Crear entorno virtual e instalar dependencias:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Configurar variables de entorno:
   - Copiar `.env` y completar con tus credenciales
   - Generar contraseña de aplicación en Google Account

4. Copiar tu CV a `assets/cv.pdf`

## Configuración

Editar `.env` con tus datos:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tuemail@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
NOMBRE_REMITENTE=Tu Nombre

# Rutas
RUTA_CV=assets/cv.pdf

# Configuración
COOLDOWN_DIAS=20
MAX_FALLBACK_POR_DIA=10
```

## Uso

### Ejecución manual:
```bash
python main.py
```

### Programar ejecución automática:
```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\ruta\al\proyecto\run.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 11:00AM
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -WakeToRun
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
Register-ScheduledTask -TaskName "JobSearchAutomation" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
```

## Testing

```bash
pytest tests/ -v
```

## Cómo obtener contraseña de aplicación Gmail

1. Ve a [Mi Cuenta Google](https://myaccount.google.com/)
2. Seguridad → Verificación en 2 pasos (activala si no está)
3. Buscá "Contraseñas de aplicación"
4. Generá una nueva para "Correo"
5. Usá ese código de 16 caracteres en `SMTP_PASSWORD`

## Notas

- Las ofertas de portales como Computrabajo no exponen emails de contacto directamente
- El sistema marca como "omitido" las ofertas sin email disponible
- El fallback de empresas locales permite envíos cuando no hay ofertas de portales

## Licencia

MIT