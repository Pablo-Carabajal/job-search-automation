# Documento de Requisitos: job-search-automation (Iteración de Correcciones)

## Introducción

Este documento formaliza los requisitos derivados de una auditoría sobre el sistema `job-search-automation` ya implementado. El sistema busca ofertas laborales diariamente en portales web (Computrabajo, Bumeran, ZonaJobs), envía el CV del candidato por email, aplica un cooldown de 20 días por empresa y recurre a un fallback de empresas locales de San Francisco, Córdoba, Argentina cuando no hay ofertas disponibles.

Los problemas identificados en la auditoría se agrupan en seis áreas: calidad anti-spam del email, scrapers desactivados, nombres hardcodeados incorrectos, lista de empresas locales, lógica de cooldown para empresas desconocidas, y código muerto.

---

## Glosario

- **EmailSender**: componente responsable de construir y enviar emails con el CV adjunto.
- **Scraper**: componente que extrae ofertas laborales de un portal web específico.
- **ScraperBumeran**: scraper del portal bumeran.com.ar.
- **ScraperZonaJobs**: scraper del portal zonajobs.com.ar.
- **ScraperComputrabajo**: scraper del portal computrabajo.com.ar.
- **HistoryManager**: componente que gestiona el historial de envíos y la lógica de cooldown en SQLite.
- **JobFilter**: componente que filtra ofertas según blacklist y cooldown.
- **LocalCompanyFallback**: componente que gestiona el envío a empresas locales cuando no hay ofertas en portales.
- **Template**: archivo de texto con variables de sustitución para construir asuntos y cuerpos de email.
- **Cooldown**: período de 20 días durante el cual no se reenvía CV a la misma empresa.
- **Oferta anónima**: oferta laboral cuyo campo empresa no fue identificado por el scraper.
- **Clave de cooldown**: identificador usado para verificar si una empresa u oferta está en período de cooldown.
- **Código muerto**: código que existe en el repositorio pero nunca se ejecuta ni es invocado.
- **Reply-To**: cabecera de email que indica la dirección a la que debe responder el destinatario.
- **MIME**: estándar de formato para mensajes de email que permite adjuntos y múltiples partes.

---

## Requisitos

### Requisito 1: Asunto del email sin prefijos espurios

**User Story:** Como candidato, quiero que el asunto del email no contenga el prefijo "Asunto:" ni "Subject:", para que los filtros de spam no lo marquen como no deseado.

#### Criterios de aceptación

1. THE Template de asunto SHALL contener únicamente el texto del asunto, sin prefijos como "Asunto:", "Subject:" u otros literales que no formen parte del asunto real.
2. WHEN el EmailSender construye el asunto a partir del template, THE EmailSender SHALL usar el contenido del template directamente como valor del campo `Subject` del mensaje MIME, sin agregar ni quitar texto.
3. IF el template de asunto contiene un prefijo del tipo `"Asunto: "` o `"Subject: "`, THEN THE EmailSender SHALL eliminar dicho prefijo antes de asignar el valor al campo `Subject`.
4. THE EmailSender SHALL verificar que el asunto resultante no comience con ninguno de los siguientes literales: `"Asunto:"`, `"Subject:"`, `"Re:"`, `"Fwd:"`.

---

### Requisito 2: Nombre del archivo adjunto correcto

**User Story:** Como candidato, quiero que el CV adjunto tenga el nombre correcto con mi nombre real, para que el destinatario identifique correctamente el archivo y no se generen señales de spam por inconsistencia de identidad.

#### Criterios de aceptación

1. THE EmailSender SHALL nombrar el archivo adjunto del CV usando el valor de `config.nombre_remitente` formateado como `"CV_{nombre_sin_espacios}.pdf"`, donde los espacios del nombre se reemplazan por guiones bajos.
2. THE EmailSender SHALL obtener el nombre del remitente exclusivamente desde la configuración (`EmailConfig.nombre_remitente`), sin ningún valor hardcodeado en el código fuente.
3. IF `config.nombre_remitente` está vacío o no configurado, THEN THE EmailSender SHALL registrar un error en el log y detener el envío sin lanzar una excepción no controlada.

---

### Requisito 3: Eliminación de nombres hardcodeados incorrectos

**User Story:** Como candidato, quiero que ningún nombre de persona esté hardcodeado en el código fuente, para que el sistema sea correcto y reutilizable sin necesidad de modificar código.

#### Criterios de aceptación

1. THE EmailSender SHALL obtener el nombre del remitente en todos los contextos (asunto espontáneo, cuerpo de fallback, cuerpo de oferta) exclusivamente desde `config.nombre_remitente`.
2. IF el método `_construir_cuerpo` no puede resolver las variables del template, THEN THE EmailSender SHALL usar `config.nombre_remitente` como valor de fallback para la variable `{nombre}`, sin usar ningún nombre literal en el código.
3. IF el método `enviar_cv_directo` construye el asunto de presentación espontánea, THEN THE EmailSender SHALL construir dicho asunto usando `config.nombre_remitente`, sin ningún nombre literal hardcodeado.
4. THE Sistema SHALL no contener en ningún archivo `.py` la cadena literal `"Eyla Bohr"`.

---

### Requisito 4: Cabeceras de email anti-spam obligatorias

**User Story:** Como candidato, quiero que los emails enviados incluyan las cabeceras estándar necesarias, para reducir la probabilidad de que sean clasificados como spam.

#### Criterios de aceptación

1. THE EmailSender SHALL incluir la cabecera `Reply-To` en todos los mensajes enviados, con el valor de la dirección de email del candidato obtenida desde la configuración.
2. THE EmailSender SHALL incluir la cabecera `Date` en todos los mensajes enviados, con la fecha y hora actuales en formato RFC 2822.
3. THE EmailSender SHALL configurar el campo `From` con el formato `"Nombre Apellido <usuario@dominio>"`, usando `config.nombre_remitente` y `config.usuario`.
4. THE EmailSender SHALL incluir la cabecera `Message-ID` generada con el dominio del remitente para facilitar el rastreo y reducir señales de spam.

---

### Requisito 5: Formato del cuerpo del email compatible con filtros anti-spam

**User Story:** Como candidato, quiero que el cuerpo del email tenga un formato que no active filtros de spam, para maximizar la tasa de entrega en la bandeja de entrada.

#### Criterios de aceptación

1. THE EmailSender SHALL enviar el cuerpo del email como mensaje MIME multipart/alternative con al menos una parte `text/plain` y una parte `text/html`.
2. THE Template de cuerpo SHALL no contener palabras que activen filtros de spam comunes, tales como: "urgente", "gratis", "oferta especial", "haga clic aquí", ni secuencias de mayúsculas de más de 3 caracteres consecutivos en el asunto.
3. WHEN el EmailSender construye la parte HTML del cuerpo, THE EmailSender SHALL generar un HTML mínimo válido que contenga el mismo texto que la parte plain/text, sin imágenes externas ni scripts.
4. THE EmailSender SHALL mantener la parte `text/plain` como primera alternativa en el mensaje multipart/alternative para compatibilidad con clientes de email que no renderizan HTML.

---

### Requisito 6: Scrapers Bumeran y ZonaJobs funcionales

**User Story:** Como usuario del sistema, quiero que los tres scrapers (Computrabajo, Bumeran y ZonaJobs) retornen ofertas reales, para maximizar la cobertura de búsqueda laboral.

#### Criterios de aceptación

1. THE ScraperBumeran SHALL implementar el método `scrape()` retornando una lista de objetos `JobOffer` con datos reales extraídos del portal bumeran.com.ar, sin retornar siempre una lista vacía.
2. THE ScraperZonaJobs SHALL implementar el método `scrape()` retornando una lista de objetos `JobOffer` con datos reales extraídos del portal zonajobs.com.ar, sin retornar siempre una lista vacía.
3. WHEN ScraperBumeran o ScraperZonaJobs requieren renderizado JavaScript para obtener resultados, THE Scraper SHALL usar Selenium en modo headless para obtener el contenido de la página antes de parsearlo.
4. WHEN un scraper no encuentra ofertas para la ciudad configurada, THE Scraper SHALL retornar una lista vacía y registrar un mensaje informativo en el log, sin lanzar una excepción.
5. IF el portal no está disponible o retorna un error HTTP, THEN THE Scraper SHALL registrar el error en el log y retornar una lista vacía, sin interrumpir la ejecución de los demás scrapers.
6. THE Sistema SHALL alcanzar una cobertura mínima de 2 de 3 scrapers activos en cada ejecución bajo condiciones normales de red.

---

### Requisito 7: Lista de empresas locales con datos verificables

**User Story:** Como candidato, quiero que la lista de empresas locales contenga empresas reales de San Francisco, Córdoba, para que los envíos de fallback lleguen a destinatarios válidos.

#### Criterios de aceptación

1. THE LocalCompanyFallback SHALL cargar empresas desde `data/local_companies.json` donde cada entrada contiene al menos los campos: `nombre`, `email`, `rubro` y `direccion`.
2. THE Lista de empresas locales SHALL contener únicamente empresas con presencia verificable en San Francisco, Córdoba, Argentina o en la región del centro de la provincia de Córdoba.
3. THE Lista de empresas locales SHALL contener un mínimo de 10 empresas con dirección de email válida (formato `usuario@dominio`).
4. IF una entrada en `local_companies.json` tiene el campo `email` vacío o con formato inválido, THEN THE LocalCompanyFallback SHALL omitir esa entrada y registrar una advertencia en el log.
5. THE Lista de empresas locales NO SHALL contener emails con dominios genéricos inventados que no correspondan a la empresa indicada.

---

### Requisito 8: Cooldown por oferta individual para empresas desconocidas

**User Story:** Como usuario del sistema, quiero que el cooldown se aplique por oferta individual cuando la empresa no es identificada, para evitar que todas las ofertas anónimas queden bloqueadas bajo una misma clave.

#### Criterios de aceptación

1. WHEN el scraper no puede identificar el nombre de la empresa de una oferta, THE HistoryManager SHALL usar el identificador único de la oferta (URL o hash de la oferta) como clave de cooldown en lugar del valor `"No especificada"` u otro valor genérico.
2. THE JobFilter SHALL verificar el cooldown de una oferta anónima usando su `id` o `url_oferta` como clave, no el campo `empresa`.
3. WHEN dos ofertas distintas tienen empresa desconocida, THE HistoryManager SHALL tratarlas como entidades independientes a efectos del cooldown, de modo que el bloqueo de una no afecte a la otra.
4. THE JobOffer SHALL tener el campo `empresa` con el valor `"desconocida"` (en minúsculas) cuando el scraper no puede identificar la empresa, en lugar de `"No especificada"` u otras variantes.
5. IF el campo `empresa` de una oferta es `"desconocida"`, THEN THE HistoryManager SHALL almacenar en la columna `empresa` de la tabla `envios` el valor del campo `url_oferta` o `id` de la oferta para garantizar unicidad del cooldown.

---

### Requisito 9: Eliminación de código muerto en scrapers

**User Story:** Como desarrollador, quiero que el código de los scrapers no contenga métodos que nunca se ejecutan, para mantener el código limpio y evitar confusión sobre qué está activo.

#### Criterios de aceptación

1. THE ScraperBumeran SHALL no contener los métodos `_parse_listado`, `_parse_fecha` y `_generar_id` si dichos métodos retornan siempre valores vacíos o no son invocados desde ningún otro método del sistema.
2. THE ScraperZonaJobs SHALL no contener los métodos `_parse_listado`, `_parse_fecha` y `_generar_id` si dichos métodos retornan siempre valores vacíos o no son invocados desde ningún otro método del sistema.
3. WHERE un método de scraper es necesario para la implementación funcional del `scrape()`, THE Scraper SHALL conservar dicho método con una implementación real y no vacía.
4. THE Codebase SHALL no contener archivos de debug (`debug_*.py`) en el directorio raíz del proyecto en el entorno de producción.

---

### Requisito 10: Consistencia de identidad del remitente en todos los envíos

**User Story:** Como candidato, quiero que todos los emails enviados por el sistema muestren mi nombre correcto de forma consistente, para proyectar una imagen profesional coherente.

#### Criterios de aceptación

1. THE EmailSender SHALL usar `config.nombre_remitente` como fuente única del nombre del candidato en: el campo `From`, la cabecera `Reply-To`, el nombre del archivo adjunto, el asunto de presentación espontánea y el cuerpo de fallback.
2. WHEN el EmailSender construye cualquier mensaje, THE EmailSender SHALL obtener el nombre del remitente desde `EmailConfig.nombre_remitente` sin excepción.
3. THE Config SHALL leer `NOMBRE_REMITENTE` desde la variable de entorno correspondiente, con el valor por defecto `"Pablo Ezequiel Carabajal"`.
4. FOR ALL emails enviados por el sistema, el nombre visible en el campo `From` SHALL coincidir con el nombre en el archivo adjunto y con el nombre firmante en el cuerpo del mensaje.
