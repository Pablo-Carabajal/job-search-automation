import subprocess
import sys

# Intentar eliminar la tarea
result = subprocess.run(
    ['schtasks', '/delete', '/tn', 'JobSearchAutomation', '/f'],
    capture_output=True,
    text=True
)

print("Resultado eliminar tarea:", result.returncode)
if result.stderr:
    print("Error:", result.stderr[:200])
else:
    print("OK - tarea eliminada o no existía")

# Crear nueva tarea
result2 = subprocess.run(
    ['schtasks', '/create', '/tn', 'JobSearchAutomation', 
     '/tr', 'cmd /c D:\\Users\\Usuario\\Documents\\Proyectos\\Buscador de trabajo\\run.bat',
     '/sc', 'daily', '/st', '11:00', '/rl', 'highest'],
    capture_output=True,
    text=True
)

print("Resultado crear tarea:", result2.returncode)
if result2.stderr:
    print("Error:", result2.stderr[:200])
else:
    print("OK - tarea creada")

# Verificar
result3 = subprocess.run(
    ['schtasks', '/query', '/tn', 'JobSearchAutomation', '/fo', 'list'],
    capture_output=True,
    text=True
)
print("\n--- Tarea actual ---")
print(result3.stdout)