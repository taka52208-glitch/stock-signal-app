# スコープ進捗管理

## フェーズ進捗

- [x] Phase 1: 要件定義
- [ ] Phase 2: Git管理（推奨）
- [x] Phase 3: フロントエンド基盤
- [x] Phase 4: バックエンド基盤
- [ ] Phase 5: 機能実装
- [ ] Phase 6: テスト・デプロイ

---

## ページ管理表

| ID | ページ名 | ルート | 権限 | 着手 | 完了 |
|----|----------|--------|------|------|------|
| P-001 | 銘柄一覧（メイン） | `/` | 全員 | [x] | [x] |
| P-002 | 銘柄詳細 | `/stock/:code` | 全員 | [x] | [x] |
| P-003 | 設定 | `/settings` | 全員 | [x] | [x] |

---

## API エンドポイント管理表

| メソッド | エンドポイント | 説明 | 着手 | 完了 |
|----------|---------------|------|------|------|
| GET | `/api/health` | ヘルスチェック | [x] | [x] |
| GET | `/api/stocks` | 監視銘柄一覧取得 | [x] | [x] |
| POST | `/api/stocks` | 銘柄追加 | [x] | [x] |
| DELETE | `/api/stocks/:code` | 銘柄削除 | [x] | [x] |
| GET | `/api/stocks/:code` | 銘柄詳細取得 | [x] | [x] |
| GET | `/api/stocks/:code/chart` | チャートデータ取得 | [x] | [x] |
| GET | `/api/settings` | 設定取得 | [x] | [x] |
| PUT | `/api/settings` | 設定更新 | [x] | [x] |
| POST | `/api/update` | 手動データ更新トリガー | [x] | [x] |

---

## 成果物チェックリスト

### ドキュメント
- [x] `docs/requirements.md` - 要件定義書
- [x] `docs/SCOPE_PROGRESS.md` - 進捗管理表
- [x] `CLAUDE.md` - プロジェクト設定

### フロントエンド
- [x] `frontend/` - Reactアプリケーション
- [x] 銘柄一覧ページ
- [x] 銘柄詳細ページ
- [x] 設定ページ

### バックエンド
- [x] `backend/` - FastAPIアプリケーション
- [x] データベースマイグレーション
- [x] 株価取得ジョブ
- [x] シグナル判定ロジック
