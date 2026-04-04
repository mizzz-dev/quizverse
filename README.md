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
cd backend && PYTHONPATH=. pytest
```

## 認証API（ISSUE-0004, ISSUE-0005）
- JWT設定は環境変数で管理します（例: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`, `AUTH_ENABLE_DEV_TOKEN_ENDPOINT`）。
- 本実装済みエンドポイント
  - `POST /api/auth/register`: メールアドレス・パスワードで新規登録しJWTを発行
  - `POST /api/auth/login`: メールアドレス・パスワードでJWTを発行
  - `GET /api/auth/me`: JWTからログイン中ユーザーの基本情報を返却
- 開発補助エンドポイント
  - `POST /api/auth/dev-token`: 開発/検証専用の仮トークン発行（`AUTH_ENABLE_DEV_TOKEN_ENDPOINT=true` の場合のみ）
- 検証用保護ルート
  - `GET /api/auth/protected`: JWT必須の保護エンドポイント
- `AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` を本番で明示設定し、`dev-token` を無効化してください。

## ドキュメント
- ロードマップ: `docs/roadmap.md`
- Issue: `docs/issues/ISSUE-0001.md`
- Issue: `docs/issues/ISSUE-0002.md`
- Issue: `docs/issues/ISSUE-0003.md`
- Issue: `docs/issues/ISSUE-0004.md`
- Issue: `docs/issues/ISSUE-0005.md`
- スキーマ定義: `docs/schema/mvp_core_tables.md`
- Qiita下書き: `docs/qiita/ISSUE-0001_mvp_infra_bootstrap.md`
- Qiita下書き: `docs/qiita/ISSUE-0002_flask_migrate_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0003_mvp_db_design.md`
- Qiita下書き: `docs/qiita/ISSUE-0004_jwt_auth_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0005_email_register_login.md`
