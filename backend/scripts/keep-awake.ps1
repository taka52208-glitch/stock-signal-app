# Prevents Windows sleep during trading hours (09:00 - 16:00 JST weekdays)
# Started by Task Scheduler at 09:00 Mon-Fri, exits automatically at 16:00.

$ErrorActionPreference = 'Continue'
$logDir = Join-Path $env:LOCALAPPDATA 'StockAutoTrade'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir 'keep-awake.log'

function Write-Log($msg) {
    $line = "{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Power {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS        = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED   = 0x00000001;
}
'@

$flags = [Power]::ES_CONTINUOUS -bor [Power]::ES_SYSTEM_REQUIRED
[Power]::SetThreadExecutionState($flags) | Out-Null
Write-Log 'Keep-awake engaged. Will release at 16:00 JST.'

try {
    $endTime = (Get-Date).Date.AddHours(16)
    while ((Get-Date) -lt $endTime) {
        Start-Sleep -Seconds 60
    }
} finally {
    [Power]::SetThreadExecutionState([Power]::ES_CONTINUOUS) | Out-Null
    Write-Log 'Keep-awake released.'
}
