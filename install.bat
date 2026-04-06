@echo off
REM ===============================================
REM Job Search Automation - Script de instalación
REM ===============================================

cd /d %~dp0

echo.
echo ============================================
echo   Job Search Automation - Instalación
echo ============================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Por favor instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Falló la instalación de dependencias
    echo Verifica tu conexión a internet
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Instalación completada!
echo ============================================
echo.
echo El sistema está listo para ejecutar.
echo.
echo Para probar manualmente: python main.py
echo.
echo Para configurar ejecución automática:
echo   1. Abre "Programador de tareas" (Taskschd.msc)
echo   2. Crea una tarea básica
echo   3. Programa diariamente a las 09:00
echo   4. Ejecuta: run.bat
echo.
pause