# Plan de Implementación: github-actions-scheduler

## Descripción general

Automatizar la ejecución diaria del ciclo de búsqueda via GitHub Actions, con persistencia del historial SQLite entre ejecuciones, reporte diario por email al candidato y soporte de Chrome/Selenium en ubuntu-latest.

## Tareas

- [x] 1. Agregar `CANDIDATO_EMAIL` a `config.py`
  - Agregar atributo de clase `CANDIDATO_EMAIL = os.getenv("CANDIDATO_EMAIL", "carabajalpabloezequiel@gmail.com")` en la clase `Config`
  - _Requisitos: 3.3, 4.1_

- [x] 2. Agregar método `enviar_texto()` a `core/email_sender.py`
  - [x] 2.1 Implementar `enviar_texto(destinatario, asunto, cuerpo)` en `EmailSender`
    - Construir mensaje MIME sin adjunto CV (solo `MIMEMultipart("alternative")` con plain + html)
    - Validar que `SMTP_USER` y `SMTP_PASSWORD` no sean `None` ni vacíos; retornar `False` si lo son
    - Reutilizar `_texto_a_html()` y la lógica SMTP de `_enviar()`
    - _Requisitos: 3.4, 4.4_

  - [ ]* 2.2 Escribir test de propiedad para `enviar_texto()` sin adjunto
    - **Propiedad 6: El reporte se envía sin adjunto CV**
    - **Valida: Requisito 3.4**

  - [ ]* 2.3 Escribir test de propiedad para credenciales vacías
    - **Propiedad 9: EmailSender retorna False con credenciales vacías**
    - **Valida: Requisito 4.4**

- [x] 3. Crear `templates/reporte_diario.txt`
  - Crear el archivo con el template de texto del email de reporte según el diseño
  - Incluir placeholders: `{fecha}`, `{envios_exitosos}`, `{envios_error}`, `{total}`, `{seccion_envios}`, `{seccion_sin_envios}`
  - _Requisitos: 3.1, 3.2_

- [x] 4. Crear `core/reporter.py`
  - [x] 4.1 Implementar clase `Reporter` con `__init__(history, email_config)`
    - Recibir instancias de `HistoryManager` y `EmailConfig`
    - _Requisitos: 3.1_

  - [x] 4.2 Implementar `_construir_lineas_envios(registros)` en `Reporter`
    - Formatear cada `SendRecord` como: empresa, email_destino, tipo legible, estado con emoji (✓/✗/—)
    - Mapear `tipo`: `"oferta_portal"` → `"Oferta de portal"`, `"empresa_local"` → `"Envío espontáneo (fallback)"`
    - _Requisitos: 3.1_

  - [x] 4.3 Implementar `generar_reporte(fecha, envios_exitosos, envios_error, registros, motivo_sin_envios)` en `Reporter`
    - Leer `templates/reporte_diario.txt` y rellenar los placeholders
    - Si `envios_exitosos == 0` y `envios_error == 0`, incluir `motivo_sin_envios` en `{seccion_sin_envios}`
    - Si hay registros, incluir el detalle formateado en `{seccion_envios}`
    - Retornar el string del cuerpo completo
    - _Requisitos: 3.1, 3.2_

  - [ ]* 4.4 Escribir test de propiedad para `generar_reporte()`
    - **Propiedad 4: El reporte siempre contiene fecha y contadores**
    - **Valida: Requisito 3.1**

  - [ ]* 4.5 Escribir test de propiedad para reporte sin envíos
    - **Propiedad 5: El reporte incluye motivo cuando no hay envíos**
    - **Valida: Requisito 3.2**

  - [x] 4.6 Implementar `enviar_reporte(destinatario, fecha, envios_exitosos, envios_error, registros, motivo_sin_envios)` en `Reporter`
    - Llamar a `generar_reporte()` para construir el cuerpo
    - Construir asunto: `[Job Search] Reporte diario - {fecha} | {N} envíos exitosos`
    - Llamar a `email_sender.enviar_texto(destinatario, asunto, cuerpo)`
    - Capturar cualquier excepción, registrar en log y retornar `False` sin propagar
    - Retornar `True` si el envío fue exitoso
    - _Requisitos: 3.3, 3.5, 3.6_

  - [ ]* 4.7 Escribir test de propiedad para manejo de fallos SMTP
    - **Propiedad 7: Reporter maneja fallos SMTP sin propagar excepción**
    - **Valida: Requisito 3.5**

- [x] 5. Checkpoint — Verificar que todos los tests pasen
  - Asegurarse de que todos los tests pasen. Consultar al usuario si surgen dudas.

- [-] 6. Integrar `Reporter` en `main.py`
  - [x] 6.1 Importar `Reporter` y usar `Config.CANDIDATO_EMAIL` en `main.py`
    - Agregar `from core.reporter import Reporter` en los imports
    - _Requisitos: 3.3_

  - [ ] 6.2 Llamar a `reporter.enviar_reporte()` al final de `ejecutar_ciclo_diario()`
    - Después del log de cierre, consultar `history.obtener_historial(desde=date.today())`
    - Determinar `motivo_sin_envios` si `envios_exitosos == 0` y `envios_error == 0`
    - Instanciar `Reporter(history, email_config)` y llamar a `enviar_reporte()`
    - _Requisitos: 3.1, 3.3, 3.6, 6.3_

- [ ] 7. Crear `.github/workflows/job-search.yml`
  - Crear el directorio `.github/workflows/` si no existe
  - Implementar el workflow YAML completo según el diseño:
    - Trigger `schedule` con cron `0 12 * * *` y `workflow_dispatch`
    - Job `run-job-search` en `ubuntu-latest` con `timeout-minutes: 60`
    - Pasos: checkout, setup-python 3.11, install dependencies, install chromium-browser
    - Paso de descarga del artifact `historial` con `continue-on-error: true`
    - Paso `Run job search` con todos los GitHub Secrets inyectados como env vars y `RUTA_CV: assets/cv.pdf`
    - Paso de subida del artifact `historial` con `if: always()`, retención 30 días y `overwrite: true`
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 4.2, 4.3, 4.5, 5.1, 6.4, 6.5_

- [ ] 8. Actualizar scrapers Selenium con opciones de Linux
  - En cada scraper que inicialice `ChromeOptions`, asegurarse de que incluya `--headless`, `--no-sandbox` y `--disable-dev-shm-usage`
  - Envolver la inicialización del driver en try/except: registrar error en log y retornar lista vacía si Chrome no está disponible
  - _Requisitos: 5.2, 5.3, 5.4_

  - [ ]* 8.1 Escribir test de propiedad para opciones de ChromeOptions
    - **Propiedad 10: Scrapers Selenium incluyen opciones requeridas de Linux**
    - **Valida: Requisito 5.2**

- [ ] 9. Checkpoint final — Verificar que todos los tests pasen
  - Asegurarse de que todos los tests pasen. Consultar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints garantizan validación incremental
- Los tests de propiedad validan invariantes universales del sistema
