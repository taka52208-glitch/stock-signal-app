@echo off
echo WSL Auto Start タスク登録中...
schtasks /create /tn "WSL Auto Start" /tr "wsl.exe -d Ubuntu -u taka5 -- bash -c \"systemctl --user start stock-backend.service\"" /sc onlogon /rl highest /f
if %errorlevel% equ 0 (
    echo 登録完了！PC起動時にWSL+バックエンドが自動起動します。
) else (
    echo エラー: 管理者として実行してください。
)
pause
