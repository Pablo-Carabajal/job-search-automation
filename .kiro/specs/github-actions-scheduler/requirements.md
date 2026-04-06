# Documento de Requisitos: github-actions-scheduler

## Introducción

Esta funcionalidad automatiza la ejecución diaria del ciclo de búsqueda y envío de CVs mediante GitHub Actions, eliminando la dependencia de tener la PC encendida. Incluye persistencia del historial SQLite entre ejecuciones via artifacts, un reporte diario por email al candidato, gestión de credenciales via GitHub Secrets, soporte de Chrome/Selenium en ubuntu-latest y manejo robusto de errores.

---

## Glosario

- **Workflow**: Archivo YAML en `.github/workflows/job-search.yml` que define el pipeline de GitHub Actions.
- **Runner**: Máquina virtual efímera `ubuntu-latest` provista por GitHub Actions donde se ejecuta el job.
- **Artifact**: Archivo persistido entre ejecuciones de GitHub Actions mediante la API de artifacts.
- **HistoryManager**: Componente Python (`core/history_manager.py`) que gestiona la base de datos SQLite de envíos.
- **Reporter**: Componente Python (`core/reporter.py`) que genera y envía el email de reporte diario al candidato.
- **EmailSender**: Componente Python (`core/email_sender.py`) que gestiona el envío de emails via SMTP.
- **Config**: Clase Python (`config.py`) que lee la configuración desde variables de entorno.
- **Scraper**: Componente Python que extrae ofertas laborales de un portal web (Computrabajo, Bumeran, ZonaJobs).
- **Sistema**: El conjunto completo de componentes Python que conforman job-search-automation.
- **Cooldown**: Período de 20 días durante el cual no se reenvía a una empresa ya contactada.
- **Fallback**: Mecanismo de envío espontáneo a empresas locales cuando no hay ofertas de portales disponibles.
- **SendRecord**: Registro de un envío individual almacenado en la base de datos SQLite.
- **GitHub Secrets**: Variables cifradas configuradas en el repositorio de GitHub, accesibles como variables de entorno durante la ejecución del Workflow.

---

## Requisitos

### Requisito 1: Ejecución automática diaria via GitHub Actions

**Historia de usuario:** Como candidato, quiero que el ciclo de búsqueda y envío de CVs se ejecute automáticamente cada día a las 9:00 AM hora Argentina, para no depender de tener mi PC encendida.

#### Criterios de aceptación

1. WHEN el reloj UTC alcanza las 12:00 (equivalente a 09:00 AM UTC-3), THE Workflow SHALL disparar automáticamente el job `run-job-search` en un Runner `ubuntu-latest`.
2. WHEN un usuario invoca `workflow_dispatch` desde la interfaz de GitHub, THE Workflow SHALL iniciar el job `run-job-search` de forma inmediata.
3. WHILE el job `run-job-search` está en ejecución, THE Workflow SHALL inyectar los GitHub Secrets como variables de entorno al proceso Python.
4. IF el job `run-job-search` supera 60 minutos de ejecución, THEN THE Workflow SHALL cancelar la ejecución y marcar el job como fallido.
5. THE Workflow SHALL ejecutar `python main.py` como paso principal del ciclo diario.

---

### Requisito 2: Persistencia del historial SQLite entre ejecuciones

**Historia de usuario:** Como candidato, quiero que el historial de empresas contactadas se conserve entre ejecuciones diarias, para que el sistema respete el período de cooldown de 20 días y no reenvíe CVs a las mismas empresas.

#### Criterios de aceptación

1. WHEN el artifact `historial` existe de una ejecución previa, THE Workflow SHALL descargar `data/historial.db` antes de ejecutar `python main.py`.
2. WHEN el artifact `historial` no existe (primera ejecución o artifact expirado), THE Workflow SHALL continuar sin error y THE HistoryManager SHALL crear una base de datos SQLite vacía con el esquema correcto.
3. WHEN el ciclo diario completa (con o sin errores en los envíos), THE Workflow SHALL subir `data/historial.db` como artifact `historial` con retención de 30 días, sobreescribiendo el artifact anterior.
4. THE HistoryManager SHALL persistir cada SendRecord en la base de datos SQLite de forma que sea recuperable mediante `obtener_historial()` en ejecuciones posteriores.
5. WHEN se consulta `obtener_historial()` con un rango de fechas, THE HistoryManager SHALL retornar únicamente los registros cuya `fecha_envio` esté dentro del rango especificado.
6. IF el archivo `data/historial.db` está corrupto o no es un SQLite válido, THEN THE HistoryManager SHALL registrar el error y crear una base de datos nueva sin interrumpir la ejecución.

---

### Requisito 3: Email de reporte diario al candidato

**Historia de usuario:** Como candidato, quiero recibir un email de resumen al finalizar cada ciclo diario, para saber cuántos CVs se enviaron, a qué empresas y si hubo errores.

#### Criterios de aceptación

1. WHEN el ciclo diario completa, THE Reporter SHALL generar un email de reporte que incluya la fecha, el conteo de envíos exitosos, el conteo de errores y el detalle de cada SendRecord del día.
2. WHEN `envios_exitosos == 0` AND `envios_error == 0`, THE Reporter SHALL incluir en el reporte el motivo por el cual no se realizaron envíos.
3. THE Reporter SHALL enviar el email de reporte al destinatario `carabajalpabloezequiel@gmail.com` usando el EmailSender con el asunto en formato `[Job Search] Reporte diario - {fecha} | {N} envíos exitosos`.
4. THE Reporter SHALL enviar el email de reporte sin adjuntar el archivo CV.
5. IF el envío del reporte falla por error SMTP, THEN THE Reporter SHALL registrar el error en el log y retornar `False` sin lanzar excepción, permitiendo que el Workflow continúe con el upload del artifact.
6. THE Reporter SHALL enviar el reporte incluso cuando el ciclo de envíos de CVs haya tenido errores parciales.

---

### Requisito 4: Credenciales via GitHub Secrets

**Historia de usuario:** Como candidato, quiero que las credenciales SMTP y mi nombre no estén hardcodeadas en el repositorio, para mantener la seguridad de mi cuenta de email.

#### Criterios de aceptación

1. THE Config SHALL leer `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `NOMBRE_REMITENTE` desde variables de entorno en tiempo de ejecución.
2. THE Workflow SHALL inyectar cada GitHub Secret (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOMBRE_REMITENTE`) como variable de entorno al paso `Run job search`.
3. THE Workflow SHALL inyectar `RUTA_CV` con el valor `assets/cv.pdf` como variable de entorno normal (no como secret) al paso `Run job search`.
4. IF `SMTP_USER` o `SMTP_PASSWORD` están vacíos o son `None`, THEN THE EmailSender SHALL registrar el error en el log y retornar `False` sin lanzar excepción.
5. THE Workflow SHALL utilizar únicamente GitHub Secrets para almacenar credenciales; ninguna credencial SHALL estar presente en texto plano en el repositorio.

---

### Requisito 5: Chrome/Selenium funcional en ubuntu-latest

**Historia de usuario:** Como candidato, quiero que los scrapers que usan Selenium funcionen correctamente en el Runner de GitHub Actions, para que las búsquedas en portales que requieren JavaScript se ejecuten sin errores.

#### Criterios de aceptación

1. THE Workflow SHALL instalar `chromium-browser` via `apt-get` antes de ejecutar `python main.py`.
2. WHEN un Scraper Selenium inicializa ChromeDriver en el Runner, THE Scraper SHALL configurar las opciones `--headless`, `--no-sandbox` y `--disable-dev-shm-usage` en el objeto `ChromeOptions`.
3. WHEN Selenium Manager detecta el binario de Chromium instalado, THE Scraper SHALL descargar automáticamente el ChromeDriver compatible sin configuración adicional.
4. IF Chrome no está disponible en el Runner al momento de inicializar el Scraper, THEN THE Scraper SHALL registrar el error en el log y THE Sistema SHALL continuar la ejecución con los scrapers restantes.

---

### Requisito 6: Manejo de errores y casos borde

**Historia de usuario:** Como candidato, quiero que el sistema sea resiliente ante fallos parciales, para que un error en un componente no impida que los demás continúen funcionando y que el historial siempre se persista.

#### Criterios de aceptación

1. IF un Scraper individual lanza una excepción durante el scraping, THEN THE Sistema SHALL registrar el error en el log y continuar la ejecución con los scrapers restantes.
2. IF todos los Scrapers retornan listas vacías o fallan, THEN THE Sistema SHALL activar el mecanismo de Fallback con empresas locales.
3. IF el Fallback no tiene empresas habilitadas (todas en Cooldown), THEN THE Reporter SHALL incluir en el reporte el motivo "Todas las empresas encontradas están en período de cooldown (20 días)".
4. WHEN el ciclo diario completa con cualquier resultado, THE Workflow SHALL ejecutar el paso de upload del artifact `historial` independientemente del exit code de `python main.py`.
5. IF `python main.py` termina con exit code distinto de 0, THEN THE Workflow SHALL marcar el job como fallido después de completar el upload del artifact.
6. WHEN una oferta de portal no tiene email de contacto, THE Sistema SHALL registrar el SendRecord con estado `omitido` y continuar con la siguiente oferta sin interrumpir el ciclo.
