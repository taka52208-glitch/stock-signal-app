#!/bin/bash
cd "$(dirname "$0")"

RENDER_API="https://stock-signal-api-u9al.onrender.com"
CLOUDFLARED="$HOME/bin/cloudflared"
LOG_DIR="$HOME/.kabu-signal"
mkdir -p "$LOG_DIR"

# ネットワーク準備待ち（再起動直後対策）
for i in $(seq 1 30); do
  curl -s --max-time 2 https://www.google.com > /dev/null 2>&1 && break
  echo "ネットワーク待ち... ($i/30)"
  sleep 2
done

# バックエンド起動
cd backend
source venv/bin/activate
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8734 &
BACK_PID=$!
echo "バックエンド起動中... (PID: $BACK_PID)"

# バックエンド起動待ち
for i in $(seq 1 30); do
  curl -s http://localhost:8734/api/health > /dev/null 2>&1 && break
  sleep 1
done

# cloudflared トンネル起動
$CLOUDFLARED tunnel --url http://localhost:8734 > "$LOG_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!
echo "トンネル起動中... (PID: $TUNNEL_PID)"

# トンネルURL取得待ち
TUNNEL_URL=""
for i in $(seq 1 15); do
  TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_DIR/tunnel.log" | head -1)
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  sleep 1
done

if [ -n "$TUNNEL_URL" ]; then
  echo "トンネルURL: $TUNNEL_URL"
  # RenderのDBにトンネルURLを登録
  curl -s -X PUT "$RENDER_API/api/settings/tunnel-url" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$TUNNEL_URL\"}" > /dev/null 2>&1
  echo "トンネルURLをRenderに登録しました"
else
  echo "警告: トンネルURL取得失敗"
fi

echo ""
echo "=== 起動完了 ==="
echo "フロント: https://kabu-signal-navi.vercel.app"
echo "ローカル: http://localhost:8734"
echo "トンネル: $TUNNEL_URL"
echo "終了: Ctrl+C"
echo ""

cleanup() {
  echo "停止中..."
  # トンネルURLをクリア
  curl -s -X PUT "$RENDER_API/api/settings/tunnel-url" \
    -H "Content-Type: application/json" \
    -d '{"url": ""}' > /dev/null 2>&1
  kill $BACK_PID $TUNNEL_PID 2>/dev/null
  exit
}

trap cleanup INT TERM
wait
