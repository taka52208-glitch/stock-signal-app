#!/bin/bash
set -e

cd "$(dirname "$0")/../frontend"

echo ">>> フロントエンドデプロイ中..."
vercel --prod

echo ">>> エイリアス更新..."
DEPLOYMENT_URL=$(vercel ls --json 2>/dev/null | jq -r '.[0].url' 2>/dev/null || echo "")
if [ -n "$DEPLOYMENT_URL" ]; then
    vercel alias set "$DEPLOYMENT_URL" kabu-signal.vercel.app
fi

echo "✅ フロントエンドデプロイ完了"
echo "URL: https://kabu-signal.vercel.app"
