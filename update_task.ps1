$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c D:\Users\Usuario\Documents\Proyectos\Buscador de trabajo\run.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 11:00AM
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -WakeToRun -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
Register-ScheduledTask -TaskName "JobSearchAutomation" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
Write-Host "Tarea actualizada correctamente a las 11:00 AM"