# Documento de Requisitos: job-search-automation (Nuevo Enfoque — Postulación via Selenium)

## Introducción

Este documento formaliza los requisitos del sistema `job-search-automation` tras el cambio de enfoque: en lugar de enviar emails directos a empresas (que rebotaban por direcciones incorrectas), el sistema ahora se postula directamente en ar.computrabajo.com usando Selenium con login real del usuario. El CV ya está cargado en el perfil de Computrabajo; el sistema solo ejecuta el clic en "Postularme".

---

## Glosario

- **ComputrabajoApplicant**: componente que gestiona el login y la postulación en ar.computrabajo.com via Selenium.
- **JobFilter**: componente que filtra ofertas según blacklist y cooldown de 20 días.
- **HistoryManager**: componente que gestiona el historial de postulaciones en SQLite.
- **Reporter**: componente que envía el reporte diario por email.
- **EmailSender**: componente usado exclusivamente para enviar el reporte diario (no para postulaciones).
- **Cooldown**: período de 20 días durante el cual no se vuelve a postular a la misma empresa.
- **Blacklist**: lista de empresas excluidas permanentemente del proceso de postulación.
- **Postulación directa**: acción de hacer clic en el botón "Postularme" en la página de una oferta en Computrabajo.
- **Artifact**: archivo persistido entre ejecuciones de GitHub Actions (usado para `historial.db`).

---

## Requisitos

### Requisito 1: Login en Computrabajo

**User Story:** Como candidato, quiero que el sistema inicie sesión automáticamente en ar.computrabajo.com con mis credenciales, para que pueda postularse en mi nombre sin intervención manual.

#### Criterios de aceptación

1. THE ComputrabajoApplicant SHALL leer las credenciales de login exclusivamente desde las variables de entorno `COMPUTRABAJO_EMAIL` y `COMPUTRABAJO_PASSWORD`, sin ningún valor hardcodeado en el código fuente.
2. WHEN el login es exitoso, THE ComputrabajoApplicant SHALL confirmar la sesión verificando que la URL actual no contenga `/login` después de la redirección.
3. IF el login falla por credenciales incorrectas, THEN THE Sistema SHALL registrar un error crítico en el log y detener el ciclo de postulaciones sin lanzar una excepción no controlada.
4. IF el login falla por CAPTCHA u otro bloqueo temporal, THEN THE ComputrabajoApplicant SHALL reintentar una vez con un delay de 30 segundos antes de abortar.
5. THE ComputrabajoApplicant SHALL cerrar el driver de Selenium en un bloque `finally` para garantizar que no queden procesos Chrome huérfanos.

---

### Requisito 2: Búsqueda de ofertas en San Francisco, Córdoba

**User Story:** Como candidato, quiero que el sistema busque ofertas laborales específicamente en San Francisco, Córdoba, para que las postulaciones sean relevantes a mi ubicación.

#### Criterios de aceptación

1. THE ComputrabajoApplicant SHALL buscar ofertas usando la URL de búsqueda de Computrabajo filtrada por "San Francisco, Córdoba".
2. THE ComputrabajoApplicant SHALL extraer de cada oferta al menos: título del puesto, nombre de la empresa, URL de la oferta.
3. WHEN el nombre de la empresa no puede ser identificado en el listado, THE ComputrabajoApplicant SHALL asignar el valor `"desconocida"` al campo `empresa` del objeto `JobOffer`.
4. THE ComputrabajoApplicant SHALL seguir la paginación de resultados hasta un máximo de 5 páginas por ejecución.
5. IF no se encuentran ofertas en la búsqueda, THEN THE ComputrabajoApplicant SHALL retornar una lista vacía y registrar un mensaje informativo en el log.

---

### Requisito 3: Filtrado por cooldown y blacklist

**User Story:** Como candidato, quiero que el sistema no se postule dos veces a la misma empresa en menos de 20 días, ni a empresas que he excluido explícitamente, para evitar postulaciones repetidas o no deseadas.

#### Criterios de aceptación

1. THE JobFilter SHALL excluir toda oferta cuya empresa esté listada en `data/blacklist.txt`, usando comparación case-insensitive y por substring.
2. THE JobFilter SHALL excluir toda oferta cuya empresa tenga una postulación con `estado = 'postulado'` en los últimos 20 días en `historial.db`.
3. WHEN el campo `empresa` de una oferta es `"desconocida"`, THE JobFilter SHALL usar el campo `id` o `url_oferta` de la oferta como clave de cooldown, de modo que el bloqueo de una oferta anónima no afecte a otras ofertas anónimas distintas.
4. THE JobFilter SHALL retornar únicamente las ofertas que pasen ambos filtros (blacklist y cooldown).

---

### Requisito 4: Postulación directa en Computrabajo

**User Story:** Como candidato, quiero que el sistema haga clic en "Postularme" en cada oferta elegible, para que mi CV (ya cargado en Computrabajo) sea enviado al empleador sin que yo tenga que hacerlo manualmente.

#### Criterios de aceptación

1. THE ComputrabajoApplicant SHALL navegar a la URL de cada oferta elegible y localizar el botón "Postularme" en la página.
2. WHEN el botón "Postularme" está presente y habilitado, THE ComputrabajoApplicant SHALL hacer clic en él y confirmar que la postulación fue registrada.
3. IF el botón "Postularme" no está presente (oferta cerrada, ya postulado previamente en el sitio), THEN THE ComputrabajoApplicant SHALL registrar la oferta como `"omitido"` en el historial y continuar con la siguiente.
4. THE Sistema SHALL registrar cada postulación exitosa en `historial.db` con `tipo = "postulacion_computrabajo"` y `estado = "postulado"`.
5. THE Sistema SHALL registrar cada postulación fallida en `historial.db` con `estado = "error"` y una nota descriptiva del motivo.

---

### Requisito 5: Límite diario de postulaciones

**User Story:** Como candidato, quiero que el sistema se limite a 7 postulaciones por día, para no saturar el portal ni generar una actividad que parezca automatizada de forma agresiva.

#### Criterios de aceptación

1. THE Sistema SHALL detenerse al alcanzar 7 postulaciones exitosas (`estado = "postulado"`) en el ciclo diario.
2. IF hay menos de 7 ofertas elegibles disponibles, THEN THE Sistema SHALL postularse a todas las disponibles sin generar error ni advertencia por no alcanzar el límite.
3. THE Sistema SHALL aplicar un delay aleatorio de entre 3 y 8 segundos entre cada postulación para simular comportamiento humano.
4. THE Límite de 7 postulaciones SHALL ser configurable mediante la variable de entorno `MAX_POSTULACIONES_DIA`.

---

### Requisito 6: Registro en historial

**User Story:** Como candidato, quiero que cada postulación quede registrada en la base de datos local, para poder consultar el historial y que el sistema aplique correctamente el cooldown de 20 días.

#### Criterios de aceptación

1. THE HistoryManager SHALL registrar cada postulación en `historial.db` con los campos: `empresa`, `email_destino` (valor `"postulacion_directa"`), `fecha_envio`, `tipo`, `estado`, `url_oferta`, `notas`.
2. THE HistoryManager SHALL persistir `historial.db` como artifact de GitHub Actions para que el historial se conserve entre ejecuciones diarias.
3. THE HistoryManager SHALL crear la tabla `envios` automáticamente si no existe al inicializar.
4. THE HistoryManager SHALL usar el nombre de empresa en minúsculas como clave de cooldown para garantizar consistencia en las comparaciones.

---

### Requisito 7: Reporte diario por email

**User Story:** Como candidato, quiero recibir un email diario con el resumen de postulaciones realizadas, para saber qué empresas fueron contactadas ese día.

#### Criterios de aceptación

1. THE Reporter SHALL enviar un email de reporte al finalizar cada ciclo diario, independientemente de si hubo postulaciones o no.
2. THE Reporte SHALL incluir: fecha del ciclo, cantidad de postulaciones exitosas, cantidad de errores, y el detalle de cada postulación (empresa, puesto, URL de oferta, estado).
3. IF no hubo postulaciones en el día, THE Reporte SHALL indicar el motivo (sin ofertas disponibles, todas en cooldown, etc.).
4. THE EmailSender SHALL ser usado exclusivamente para el envío del reporte diario, no para postulaciones directas a empresas.
5. THE Reporter SHALL leer las credenciales SMTP desde variables de entorno (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).

---

### Requisito 8: Ejecución en GitHub Actions

**User Story:** Como candidato, quiero que el sistema corra automáticamente en GitHub Actions todos los días, para no depender de que mi computadora esté encendida.

#### Criterios de aceptación

1. THE Workflow de GitHub Actions SHALL ejecutarse diariamente a las 11:00 AM hora Argentina (UTC-3), equivalente a `cron: '0 14 * * *'`.
2. THE Workflow SHALL instalar Chromium en el runner de Ubuntu para que Selenium pueda ejecutarse en modo headless.
3. THE Workflow SHALL descargar el artifact `historial` al inicio de cada ejecución para restaurar el historial de postulaciones previas.
4. THE Workflow SHALL subir el artifact `historial` al finalizar cada ejecución (incluso si hubo errores) para persistir las nuevas postulaciones.
5. THE Workflow SHALL leer todas las credenciales desde GitHub Secrets: `COMPUTRABAJO_EMAIL`, `COMPUTRABAJO_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOMBRE_REMITENTE`, `CANDIDATO_EMAIL`.
6. THE Workflow SHALL permitir ejecución manual mediante `workflow_dispatch`.

---

### Requisito 9: Eliminación de componentes obsoletos

**User Story:** Como desarrollador, quiero que el código no contenga componentes del sistema anterior (fallback de emails, scrapers de Bumeran/ZonaJobs), para mantener el código limpio y evitar confusión.

#### Criterios de aceptación

1. THE Codebase SHALL no contener `core/fallback.py` ni ninguna referencia a `LocalCompanyFallback` en el código activo.
2. THE Codebase SHALL no contener `data/local_companies.json` ni referencias a este archivo en el código activo.
3. THE Codebase SHALL no importar ni instanciar `ScraperBumeran` ni `ScraperZonaJobs` desde `main.py` ni desde ningún otro módulo activo.
4. THE `main.py` SHALL no contener lógica de fallback a empresas locales ni envío de emails de postulación directa.
5. THE `core/email_sender.py` SHALL conservarse únicamente para el envío del reporte diario; los métodos `enviar_cv` y `enviar_cv_directo` pueden eliminarse o quedar sin uso.
