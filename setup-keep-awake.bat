@echo off
chcp 65001 > nul
echo Keep-Awake タスク登録中...

set TARGET=%USERPROFILE%\stock-keep-awake.ps1
set SRC_DIR=\\wsl.localhost\Ubuntu\home\taka5\株自動売買ツール\backend\scripts

REM WSLからWindows側にコピー（日本語パス回避）
copy /Y "%SRC_DIR%\keep-awake.ps1" "%TARGET%" > nul
if %errorlevel% neq 0 (
    echo エラー: keep-awake.ps1 のコピーに失敗しました
    echo 確認パス: %SRC_DIR%\keep-awake.ps1
    pause
    exit /b 1
)

REM タスク登録（管理者権限が必要）
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SRC_DIR%\register-keep-awake.ps1" -ScriptPath "%TARGET%"

if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo  登録完了！平日 09:00〜16:00 はPCがスリープしません。
    echo ====================================================
    echo.
    echo 確認:    schtasks /query /tn "StockAutoTrade-KeepAwake"
    echo 解除:    schtasks /delete /tn "StockAutoTrade-KeepAwake" /f
) else (
    echo エラー: 管理者として実行してください。
)
pause
