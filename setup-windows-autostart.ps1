# WSL起動のみ（サービスはsystemdが自動起動）
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -- sleep 3"
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "KabuSignalAutoStart" -Action $action -Trigger $trigger -Settings $settings -Description "KabuSignal AutoStart (WSL boot)" -RunLevel Highest -Force
Write-Host "Done: KabuSignalAutoStart"
