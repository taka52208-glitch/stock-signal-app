#!/bin/bash
# バックグラウンドで起動するデーモン版
LOG="$HOME/.kabu-signal/daemon.log"
mkdir -p "$HOME/.kabu-signal"

exec >> "$LOG" 2>&1
echo "=== $(date) 起動開始 ==="

cd /home/taka/優良株情報取得ツール
/home/taka/優良株情報取得ツール/start.sh &
echo $! > "$HOME/.kabu-signal/daemon.pid"
