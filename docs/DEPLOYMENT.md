# デプロイ設定

## 本番環境URL
- **Frontend**: https://kabu-signal.vercel.app
- **Backend**: https://stock-signal-app-9cqb.onrender.com
- **Database**: Neon PostgreSQL (ap-southeast-1)

## デプロイ方法

### フロントエンド (Vercel)
```bash
cd frontend
vercel --prod
vercel alias set <deployment-url> kabu-signal.vercel.app
```

### バックエンド (Render)
GitHubにプッシュすると自動デプロイされます。
```bash
git push origin master
```

手動デプロイ: Renderダッシュボード → Manual Deploy

## 環境変数

### Frontend (Vercel)
| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://stock-signal-app-9cqb.onrender.com` |

### Backend (Render)
| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://...@ep-dry-paper-a1obl95y.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `CORS_ORIGINS` | `https://kabu-signal.vercel.app` |
| `MOCK_MODE` | `false` |
| `PYTHON_VERSION` | `3.12.0` |

## 技術スタック
- Python 3.12 + FastAPI
- psycopg3 (PostgreSQL driver)
- pandas-ta (テクニカル指標)
