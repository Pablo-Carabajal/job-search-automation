# Plan de Implementación: job-search-automation (Nuevo Enfoque — Postulación via Selenium)

## Descripción General

Migración completa del sistema de envío de emails a postulación directa en Computrabajo via Selenium. Las tareas están ordenadas de menor a mayor dependencia: primero eliminar lo obsoleto, luego crear el nuevo módulo, luego actualizar el orquestador y la infraestructura.

## Tareas

- [ ] 1. Eliminar componentes obsoletos
  - [ ] 1.1 Eliminar `core/fallback.py`
    - Borrar el archivo del repositorio
    - _Requisitos: 9.1_

  - [ ] 1.2 Eliminar `data/local_companies.json`
    - Borrar el archivo del repositorio
    - _Requisitos: 9.2_

  - [ ] 1.3 Eliminar `scrapers/bumeran.py` y `scrapers/zonajobs.py`
    - Borrar ambos archivos del repositorio
    - _Requisitos: 9.3_

  - [ ] 1.4 Eliminar templates de email de postulación no utilizados
    - Borrar `templates/asunto_oferta.txt`, `templates/cuerpo_oferta.txt`, `templates/cuerpo_espontaneo.txt`
    - Conservar `templates/reporte_diario.txt`
    - _Requisitos: 9.4_

- [ ] 2. Actualizar `config.py` — agregar credenciales de Computrabajo
  - [ ] 2.1 Agregar `COMPUTRABAJO_EMAIL` y `COMPUTRABAJO_PASSWORD` leídos desde variables de entorno
    - Agregar `MAX_POSTULACIONES_DIA = int(os.getenv("MAX_POSTULACIONES_DIA") or "7")`
    - Eliminar variables obsoletas: `RUTA_EMPRESAS_LOCALES`, `MAX_FALLBACK_POR_DIA`, `MINIMO_ENVIOS_DIARIOS`, `DELAY_ENTRE_FALLBACK`
    - _Requisitos: 1.1, 5.4_

- [ ] 3. Crear `core/computrabajo_applicant.py`
  - [ ] 3.1 Implementar `__init__` con inicialización del driver Chrome headless
    - Opciones: `--headless`, `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`
    - Recibir `email` y `password` como parámetros (leídos desde Config en main.py)
    - _Requisitos: 1.1, 1.5_

  - [ ] 3.2 Implementar método `login() -> bool`
    - Navegar a la página de login de ar.computrabajo.com
    - Completar campos email y password, hacer clic en submit
    - Verificar redirección exitosa (URL no contiene `/login`)
    - Reintentar una vez con delay de 30s si falla por bloqueo temporal
    - Retornar False y loguear error crítico si falla definitivamente
    - _Requisitos: 1.2, 1.3, 1.4_

  - [ ] 3.3 Implementar método `buscar_ofertas() -> list[JobOffer]`
    - Navegar a la URL de búsqueda filtrada por San Francisco, Córdoba
    - Extraer título, empresa, URL de cada oferta del listado
    - Usar `"desconocida"` cuando no se identifique la empresa
    - Seguir paginación hasta max 5 páginas
    - Retornar lista vacía con log informativo si no hay resultados
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.4 Implementar método `postularse(oferta: JobOffer) -> bool`
    - Navegar a `oferta.url_oferta`
    - Localizar y hacer clic en el botón "Postularme"
    - Confirmar que la postulación fue registrada (cambio en el botón o mensaje de confirmación)
    - Retornar False con log si el botón no existe o la oferta está cerrada
    - _Requisitos: 4.1, 4.2, 4.3_

  - [ ] 3.5 Implementar método `cerrar() -> None`
    - Llamar a `driver.quit()` para cerrar el browser
    - _Requisitos: 1.5_

- [ ] 4. Actualizar `main.py` — nuevo flujo de postulación
  - [ ] 4.1 Reemplazar la lógica de scraping multi-portal por el flujo de ComputrabajoApplicant
    - Importar y usar `ComputrabajoApplicant` en lugar de `ScraperComputrabajo`, `ScraperBumeran`, `ScraperZonaJobs`
    - Eliminar imports de `LocalCompanyFallback` y scrapers obsoletos
    - _Requisitos: 9.3, 9.4_

  - [ ] 4.2 Implementar el ciclo de postulación con límite de 7 por día
    - Login → buscar ofertas → filtrar → postularse hasta MAX_POSTULACIONES_DIA
    - Registrar cada postulación en historial con `tipo="postulacion_computrabajo"`
    - Aplicar delay aleatorio de 3-8s entre postulaciones
    - Cerrar el driver en bloque `finally`
    - _Requisitos: 4.4, 4.5, 5.1, 5.2, 5.3_

  - [ ] 4.3 Mantener el envío del reporte diario al finalizar el ciclo
    - Pasar la lista de postulaciones realizadas al `Reporter`
    - Incluir motivo si no hubo postulaciones
    - _Requisitos: 7.1, 7.2, 7.3_

- [ ] 5. Actualizar `.github/workflows/daily.yml`
  - [ ] 5.1 Agregar `COMPUTRABAJO_EMAIL` y `COMPUTRABAJO_PASSWORD` como variables de entorno en el step "Run job search"
    - Leer desde `${{ secrets.COMPUTRABAJO_EMAIL }}` y `${{ secrets.COMPUTRABAJO_PASSWORD }}`
    - Agregar `MAX_POSTULACIONES_DIA: "7"`
    - Eliminar variables obsoletas: `RUTA_EMPRESAS_LOCALES`, `MAX_FALLBACK_POR_DIA`, `MINIMO_ENVIOS_DIARIOS`, `DELAY_ENTRE_FALLBACK`
    - _Requisitos: 8.5_

  - [ ] 5.2 Eliminar el step "Verify CV exists" si el CV ya no es necesario en el runner
    - El CV está cargado en Computrabajo; el runner no necesita el archivo local para postularse
    - Conservar `assets/cv.pdf` en el repo solo como respaldo
    - _Requisitos: 8.2_

- [ ] 6. Actualizar `requirements.txt`
  - [ ] 6.1 Verificar que `selenium>=4.15.0` esté presente
    - Eliminar dependencias no utilizadas si las hay
    - _Requisitos: 8.2_

- [ ] 7. Checkpoint final — Verificar integridad del sistema
  - Confirmar que `main.py` no importa ningún componente eliminado
  - Confirmar que `config.py` tiene las nuevas variables y no las obsoletas
  - Confirmar que el workflow tiene los secrets correctos documentados
  - Ejecutar `pytest` para verificar que los tests existentes siguen pasando

## Notas

- El orden de las tareas es importante: eliminar primero (tarea 1) evita referencias rotas al actualizar main.py (tarea 4)
- El driver de Chrome es gestionado por `selenium-manager` (Selenium 4.6+); no requiere instalación manual de ChromeDriver
- GitHub Actions ya instala Chromium en el runner de Ubuntu (step existente en daily.yml)
- El historial.db se persiste como artifact entre ejecuciones; el cooldown de 20 días funciona correctamente siempre que el artifact se descargue al inicio de cada run
