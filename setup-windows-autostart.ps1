$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -- /home/taka/優良株情報取得ツール/start-daemon.sh"
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "KabuSignalAutoStart" -Action $action -Trigger $trigger -Settings $settings -Description "株シグナルアプリ自動起動" -RunLevel Highest
Write-Host "タスク登録完了: KabuSignalAutoStart"
