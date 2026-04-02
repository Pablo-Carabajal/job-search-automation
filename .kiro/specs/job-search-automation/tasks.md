# Plan de Implementación: job-search-automation (Iteración de Correcciones)

## Descripción General

Correcciones sobre el sistema existente, ordenadas de menor a mayor dependencia: primero los cambios atómicos (templates, config), luego los componentes centrales (email_sender, job_filter, scrapers) y finalmente dependencias de infraestructura (requirements.txt).

## Tareas

- [x] 1. Corregir template de asunto
  - [x] 1.1 Eliminar el prefijo `"Asunto: "` del archivo `templates/asunto_oferta.txt`
    - El archivo debe contener únicamente el texto del asunto sin ningún prefijo
    - Resultado esperado: `Postulación – {puesto} en {empresa}`
    - _Requisitos: 1.1_

  - [ ]* 1.2 Escribir test unitario para verificar que el asunto no contiene prefijos espurios
    - Verificar que el asunto resultante no comience con `"Asunto:"`, `"Subject:"`, `"Re:"` ni `"Fwd:"`
    - _Requisitos: 1.4_

- [x] 2. Corregir `config.py` — valor por defecto de `NOMBRE_REMITENTE`
  - [x] 2.1 Verificar que el valor por defecto de `NOMBRE_REMITENTE` sea `"Pablo Ezequiel Carabajal"` en `config.py`
    - El valor actual ya es correcto; confirmar que no hay otro hardcode en el archivo
    - _Requisitos: 10.3_

- [x] 3. Corregir `core/email_sender.py` — eliminar todos los valores hardcodeados
  - [x] 3.1 Reemplazar el nombre del archivo adjunto hardcodeado `"CV_Eyla_Bohr.pdf"` por uno dinámico
    - Usar `config.nombre_remitente` formateado como `"CV_{nombre_sin_espacios}.pdf"` (espacios → guiones bajos)
    - Si `config.nombre_remitente` está vacío, registrar error en log y retornar `False` sin lanzar excepción
    - Archivo: `core/email_sender.py`, método `_enviar`
    - _Requisitos: 2.1, 2.2, 2.3_

  - [x] 3.2 Reemplazar el asunto hardcodeado `"Presentación espontánea - Eyla Bohr"` por uno dinámico
    - Usar `f"Presentación espontánea - {self.config.nombre_remitente}"`
    - Archivo: `core/email_sender.py`, método `enviar_cv_directo`
    - _Requisitos: 3.3, 10.1_

  - [x] 3.3 Reemplazar el fallback hardcodeado `"Eyla Bohr"` en `_construir_cuerpo`
    - Usar `self.config.nombre_remitente` como valor de fallback para la variable `{nombre}`
    - Archivo: `core/email_sender.py`, método `_construir_cuerpo`
    - _Requisitos: 3.2, 10.2_

  - [x] 3.4 Agregar cabeceras anti-spam obligatorias en el método `_enviar`
    - Agregar `Reply-To` con el valor de `self.config.usuario`
    - Agregar `Date` con la fecha y hora actuales en formato RFC 2822 (`email.utils.formatdate(localtime=True)`)
    - Agregar `Message-ID` generado con `email.utils.make_msgid(domain=self.config.usuario.split("@")[-1])`
    - Asegurar que el campo `From` use el formato `"Nombre Apellido <usuario@dominio>"`
    - Archivo: `core/email_sender.py`, método `_enviar`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [x] 3.5 Cambiar el cuerpo del email a formato `multipart/alternative` con partes `text/plain` y `text/html`
    - Reemplazar el `MIMEMultipart()` actual por `MIMEMultipart("mixed")` con una parte interna `MIMEMultipart("alternative")`
    - La parte `text/plain` debe ser la primera alternativa
    - La parte `text/html` debe ser un HTML mínimo válido que envuelva el mismo texto en `<pre>` o párrafos `<p>`
    - El adjunto CV debe seguir adjuntándose al mensaje externo `mixed`
    - Archivo: `core/email_sender.py`, método `_enviar`
    - _Requisitos: 5.1, 5.3, 5.4_

  - [ ]* 3.6 Escribir tests unitarios para `EmailSender`
    - Usar mock de SMTP para verificar que el mensaje construido contiene las cabeceras `Reply-To`, `Date`, `Message-ID`
    - Verificar que el nombre del adjunto es dinámico y coincide con `config.nombre_remitente`
    - Verificar que el asunto espontáneo usa `config.nombre_remitente`
    - _Requisitos: 2.1, 3.3, 4.1, 4.2, 4.4_

- [x] 4. Checkpoint — Verificar correcciones de email
  - Asegurar que todos los tests pasen. Consultar al usuario si hay dudas sobre el formato HTML mínimo esperado.

- [x] 5. Corregir `core/job_filter.py` — clave de cooldown para empresas desconocidas
  - [x] 5.1 Reemplazar la comparación `oferta.empresa != "No especificada"` por `oferta.empresa != "desconocida"`
    - La clave de cooldown para ofertas anónimas debe ser `oferta.id` (no el nombre de empresa)
    - Archivo: `core/job_filter.py`, método `filtrar`
    - _Requisitos: 8.2, 8.4_

  - [ ]* 5.2 Escribir test de propiedad para la lógica de cooldown de ofertas anónimas
    - **Propiedad 1: Independencia de cooldown entre ofertas anónimas**
    - Para cualquier par de ofertas con `empresa == "desconocida"` e `id` distintos, el bloqueo de una no debe afectar a la otra
    - **Valida: Requisito 8.3**

- [x] 6. Corregir `scrapers/computrabajo.py` — valor estándar para empresa desconocida
  - [x] 6.1 Reemplazar todas las ocurrencias de `"No especificada"` por `"desconocida"` en `scrapers/computrabajo.py`
    - Afecta la asignación inicial `empresa = "No especificada"` y la comparación `if empresa == "No especificada"`
    - Archivo: `scrapers/computrabajo.py`, método `_parse_listado`
    - _Requisitos: 8.4_

  - [ ]* 6.2 Escribir test unitario para verificar que el campo `empresa` nunca toma el valor `"No especificada"`
    - Parsear HTML de muestra y verificar que el campo `empresa` es `"desconocida"` cuando no se identifica la empresa
    - _Requisitos: 8.4_

- [x] 7. Limpiar e implementar `scrapers/bumeran.py`
  - [x] 7.1 Eliminar los métodos muertos `_parse_listado`, `_parse_fecha` y `_generar_id` de `scrapers/bumeran.py`
    - Estos métodos retornan siempre valores vacíos y no son invocados desde ningún otro componente
    - _Requisitos: 9.1_

  - [x] 7.2 Implementar el método `scrape()` real en `scrapers/bumeran.py` usando Selenium headless
    - Inicializar `webdriver.Chrome` con opciones headless (`--headless`, `--no-sandbox`, `--disable-dev-shm-usage`)
    - URL de búsqueda: `https://www.bumeran.com.ar/empleos-san-francisco-cordoba.html`
    - Esperar a que carguen los resultados (usar `WebDriverWait` o `time.sleep` con valor razonable)
    - Parsear el HTML resultante con `BeautifulSoup` para extraer título, empresa, URL de oferta
    - Construir objetos `JobOffer` con `portal_origen="bumeran"` y `empresa="desconocida"` cuando no se identifique
    - Manejar excepciones: registrar error en log y retornar lista vacía sin interrumpir el proceso
    - Cerrar el driver en bloque `finally`
    - _Requisitos: 6.1, 6.3, 6.4, 6.5_

  - [ ]* 7.3 Escribir test unitario para `ScraperBumeran.scrape()` con mock de Selenium
    - Verificar que ante un error de WebDriver se retorna lista vacía y se registra el error
    - _Requisitos: 6.4, 6.5_

- [x] 8. Limpiar e implementar `scrapers/zonajobs.py`
  - [x] 8.1 Eliminar los métodos muertos `_parse_listado`, `_parse_fecha` y `_generar_id` de `scrapers/zonajobs.py`
    - Misma razón que en bumeran: retornan valores vacíos y no son invocados
    - _Requisitos: 9.2_

  - [x] 8.2 Implementar el método `scrape()` real en `scrapers/zonajobs.py` usando Selenium headless
    - Inicializar `webdriver.Chrome` con las mismas opciones headless que en bumeran
    - URL de búsqueda: `https://www.zonajobs.com.ar/empleos-en-san-francisco-cordoba.html`
    - Esperar carga de resultados, parsear con `BeautifulSoup`, construir objetos `JobOffer` con `portal_origen="zonajobs"`
    - Usar `"desconocida"` cuando no se identifique la empresa
    - Manejar excepciones: registrar error en log y retornar lista vacía
    - Cerrar el driver en bloque `finally`
    - _Requisitos: 6.2, 6.3, 6.4, 6.5_

  - [ ]* 8.3 Escribir test unitario para `ScraperZonaJobs.scrape()` con mock de Selenium
    - Verificar que ante un error de WebDriver se retorna lista vacía y se registra el error
    - _Requisitos: 6.4, 6.5_

- [x] 9. Actualizar `requirements.txt` — agregar `selenium`
  - [x] 9.1 Agregar `selenium>=4.15.0` a `requirements.txt` si no está presente
    - Verificar que no haya duplicados
    - Archivo: `requirements.txt`
    - _Requisitos: 6.3_

- [x] 10. Checkpoint final — Verificar integridad del sistema
  - Asegurar que todos los tests pasen y que no quede ninguna ocurrencia de `"Eyla Bohr"` ni `"No especificada"` en archivos `.py`
  - Consultar al usuario si hay dudas antes de cerrar.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- El orden de las tareas respeta dependencias: los cambios de valor estándar (`"desconocida"`) deben hacerse en `job_filter.py` y `computrabajo.py` antes de implementar los scrapers nuevos, para que todos usen el mismo valor
- Los scrapers de Bumeran y ZonaJobs requieren que `selenium` esté en `requirements.txt` (tarea 9) antes de ejecutarse en producción
- ChromeDriver es gestionado automáticamente por `selenium-manager` (incluido en Selenium 4.6+), no requiere instalación manual
