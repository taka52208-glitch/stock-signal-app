#!/bin/bash
set -e

echo "=== 本番デプロイ開始 ==="

# バックエンド（GitHubプッシュで自動デプロイ）
echo ">>> バックエンド: GitHubにプッシュ..."
git push origin master

# フロントエンド
echo ">>> フロントエンドデプロイ中..."
"$(dirname "$0")/deploy-frontend.sh"

echo "=== 本番デプロイ完了 ==="
echo ""
echo "Frontend: https://kabu-signal.vercel.app"
echo "Backend:  https://stock-signal-app-9cqb.onrender.com"
