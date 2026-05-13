# Registers the Keep-Awake task in Windows Task Scheduler.
# Must run as Administrator. Called by setup-keep-awake.bat.

param(
    [string]$ScriptPath = "$env:USERPROFILE\stock-keep-awake.ps1"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ScriptPath)) {
    Write-Error "keep-awake.ps1 が見つかりません: $ScriptPath"
    exit 1
}

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 9:00am

# StartWhenAvailable: 09:00を逃したら起動後即実行
# AllowStartIfOnBatteries / DontStopIfGoingOnBatteries: ノートPC対応
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 8)

Register-ScheduledTask `
    -TaskName 'StockAutoTrade-KeepAwake' `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Prevents Windows sleep during stock trading hours (09:00-16:00 JST, Mon-Fri).' `
    -Force | Out-Null

Write-Host "登録完了: StockAutoTrade-KeepAwake"
Write-Host "  - 起動: 平日 09:00"
Write-Host "  - 起動時刻を過ぎていた場合は起動後即実行 (StartWhenAvailable)"
Write-Host "  - 16:00に自動終了"
Write-Host "  - ログ: $env:LOCALAPPDATA\StockAutoTrade\keep-awake.log"
