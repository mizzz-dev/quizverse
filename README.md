# QuizVerse
クイズ作成・プレイ・ランキングを軸としたWebプラットフォーム。

## 技術スタック
- Frontend: React + Tailwind + Vite
- Backend: Flask + Flask-JWT-Extended + Flask-Migrate + SQLAlchemy
- DB: PostgreSQL
- Infra: Docker Compose

## クイックスタート
1. `.env.example` をコピーして `.env` を作成
2. 起動
   ```bash
   docker compose up --build
   ```
3. backendヘルスチェック
   - `http://localhost:5000/api/health`
4. frontend
   - `http://localhost:5173`

## DBマイグレーション
```bash
cd backend
flask --app app db upgrade
```

モデル変更時:
```bash
cd backend
flask --app app db migrate -m "describe change"
flask --app app db upgrade
```

## テスト
```bash
cd backend && pytest
```

## JWT認証基盤（ISSUE-0004）
- JWT設定は環境変数で管理します（例: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`, `AUTH_ENABLE_DEV_TOKEN_ENDPOINT`）。
- JWT疎通確認用の仮エンドポイントを用意しています。
  - `POST /api/auth/dev-token`: 開発用アクセストークン発行（本番用login/register実装までの仮置き）
  - `GET /api/auth/protected`: JWT必須の保護エンドポイント
  - `GET /api/auth/me`: JWTから取得した `user_id` を返却
- `AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` で `dev-token` を無効化できます。

## ドキュメント
- ロードマップ: `docs/roadmap.md`
- Issue: `docs/issues/ISSUE-0001.md`
- Issue: `docs/issues/ISSUE-0002.md`
- Issue: `docs/issues/ISSUE-0003.md`
- Issue: `docs/issues/ISSUE-0004.md`
- スキーマ定義: `docs/schema/mvp_core_tables.md`
- Qiita下書き: `docs/qiita/ISSUE-0001_mvp_infra_bootstrap.md`
- Qiita下書き: `docs/qiita/ISSUE-0002_flask_migrate_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0003_mvp_db_design.md`
- Qiita下書き: `docs/qiita/ISSUE-0004_jwt_auth_foundation.md`
