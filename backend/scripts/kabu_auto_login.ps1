param(
    [Parameter(Mandatory=$true)][string]$LoginId,
    [Parameter(Mandatory=$true)][string]$LoginPassword
)

$KabuExe = "$env:LOCALAPPDATA\kabuStation\KabuS.exe"

# 1. 既存プロセス停止
Stop-Process -Name KabuS -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 2. 起動
Start-Process $KabuExe
Write-Host "kabu STATION起動中..."

# 3. ログインウィンドウを待つ（最大60秒）
Add-Type -AssemblyName System.Windows.Forms
$found = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $proc = Get-Process KabuS -ErrorAction SilentlyContinue
    if ($proc -and $proc.MainWindowHandle -ne 0) {
        $found = $true
        Write-Host "ウィンドウ検出 (${i}回目)"
        break
    }
}
if (-not $found) {
    Write-Error "kabu STATIONのウィンドウが見つかりません"
    exit 1
}

Start-Sleep -Seconds 3

# 4. ウィンドウをアクティブにしてログイン情報入力
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$proc = Get-Process KabuS -ErrorAction SilentlyContinue
if ($proc.MainWindowHandle -eq 0) {
    Write-Error "ウィンドウハンドル取得失敗"
    exit 1
}

[Win32]::ShowWindow($proc.MainWindowHandle, 9) | Out-Null  # SW_RESTORE
Start-Sleep -Milliseconds 500
[Win32]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 500

# Tab でログインIDフィールドへ移動 → 入力 → Tab → パスワード入力 → Enter
# kabu STATIONのログイン画面: ID → Password → ログインボタン
[System.Windows.Forms.SendKeys]::SendWait($LoginId)
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait("{TAB}")
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait($LoginPassword)
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")

Write-Host "ログイン送信完了"

# 5. API有効化を待つ（最大60秒）
for ($i = 0; $i -lt 12; $i++) {
    Start-Sleep -Seconds 5
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:18080/kabusapi/token" -Method Post -ContentType "application/json" -Body '{"APIPassword":"'+ $env:API_PASSWORD + '"}' -ErrorAction Stop
        if ($resp.Token) {
            Write-Host "API接続成功: Token取得"
            exit 0
        }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        Write-Host "API待機中... ($i) status=$status"
    }
}

# APIポートが開いているかだけ確認
$conn = Test-NetConnection -ComputerName localhost -Port 18080 -WarningAction SilentlyContinue
if ($conn.TcpTestSucceeded) {
    Write-Host "APIポート開放確認。ログイン成功の可能性あり"
    exit 0
} else {
    Write-Error "APIポートが開放されていません。ログイン失敗の可能性"
    exit 1
}
