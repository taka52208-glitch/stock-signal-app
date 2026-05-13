# Combined setup: Keep-Awake + WSL Auto Start
# Must run elevated.

$ErrorActionPreference = 'Stop'
$repoScripts = '\\wsl.localhost\Ubuntu\home\taka5\株自動売買ツール\backend\scripts'
$target = Join-Path $env:USERPROFILE 'stock-keep-awake.ps1'

Write-Host '=== 1/3 Copy keep-awake.ps1 ===' -ForegroundColor Cyan
Copy-Item (Join-Path $repoScripts 'keep-awake.ps1') $target -Force
Write-Host "Copied to: $target"

Write-Host ''
Write-Host '=== 2/3 Register StockAutoTrade-KeepAwake ===' -ForegroundColor Cyan
& (Join-Path $repoScripts 'register-keep-awake.ps1') -ScriptPath $target

Write-Host ''
Write-Host '=== 3/3 Register WSL Auto Start ===' -ForegroundColor Cyan
$wslCmd = 'wsl.exe -d Ubuntu -u taka5 -- bash -c \"systemctl --user start stock-backend.service\"'
schtasks /create /tn 'WSL Auto Start' /tr $wslCmd /sc onlogon /rl highest /f

Write-Host ''
Write-Host '=== Verify ===' -ForegroundColor Cyan
schtasks /query /tn 'StockAutoTrade-KeepAwake'
schtasks /query /tn 'WSL Auto Start'

Write-Host ''
Write-Host 'Done. Press any key to close...' -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
