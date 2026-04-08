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

## 認証API（ISSUE-0004, ISSUE-0005, ISSUE-0006, ISSUE-0007）
- JWT設定は環境変数で管理します（例: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`, `AUTH_ENABLE_DEV_TOKEN_ENDPOINT`）。
- OTP設定は環境変数で管理します（例: `OTP_EXPIRES_SECONDS`, `OTP_MIN_RESEND_SECONDS`, `OTP_MAX_REQUESTS_PER_HOUR`, `OTP_MAX_VERIFY_ATTEMPTS`）。
- Google OAuth ログインを利用する場合は `GOOGLE_OAUTH_CLIENT_ID` を設定してください。
- 本実装済みエンドポイント
  - `POST /api/quizzes`: JWT必須。クイズ本体 + 問題 + 選択肢を一括作成（MVP: 4択等の選択式、各問題2〜6択、正答は1つ）
  - `GET /api/quizzes`: クイズ一覧を取得（`q` キーワード検索, `category` 完全一致, `page`/`per_page` ページング）
  - `GET /api/quizzes/{quiz_id}`: クイズ詳細を取得（問題・選択肢を返却、正答は返さない）
  - `POST /api/quizzes/{quiz_id}/play`: JWT必須。回答送信・採点・プレイ履歴保存（`quiz_plays`/`quiz_play_answers`）
  - `GET /api/quizzes/{quiz_id}/rankings`: クイズ単位ランキング（ユーザーごとのベストプレイ採用、同点時は score/correct_count/played_at/play_id で決定）
  - `GET /api/rankings`: 総合ランキング（ユーザー×クイズのベストスコアを合算、ページング対応）
  - `POST /api/auth/register`: メールアドレス・パスワードで新規登録しJWTを発行
  - `POST /api/auth/login`: メールアドレス・パスワードでJWTを発行
  - `POST /api/auth/google`: Google ID token を検証し、OAuthログインでJWTを発行
  - `POST /api/auth/otp/request`: OTPコードを発行・保存し、メール送信基盤で送信（MVPではemailのみ対応）
  - `POST /api/auth/otp/verify`: destination / purpose に紐づくOTPコードを検証し、成功時に使用済み化
  - `GET /api/auth/me`: JWTからログイン中ユーザーの基本情報を返却
- 開発補助エンドポイント
  - `POST /api/auth/dev-token`: 開発/検証専用の仮トークン発行（`AUTH_ENABLE_DEV_TOKEN_ENDPOINT=true` の場合のみ）
- 検証用保護ルート
  - `GET /api/auth/protected`: JWT必須の保護エンドポイント
- `AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` を本番で明示設定し、`dev-token` を無効化してください。
- `channel=phone` は将来拡張用のインターフェースのみで、MVPでは `auth/otp_channel_not_implemented` を返します。

## ドキュメント
- ロードマップ: `docs/roadmap.md`
- Issue: `docs/issues/ISSUE-0001.md`
- Issue: `docs/issues/ISSUE-0002.md`
- Issue: `docs/issues/ISSUE-0003.md`
- Issue: `docs/issues/ISSUE-0004.md`
- Issue: `docs/issues/ISSUE-0005.md`
- Issue: `docs/issues/ISSUE-0006.md`
- Issue: `docs/issues/ISSUE-0007.md`
- Issue: `docs/issues/ISSUE-0008.md`
- Issue: `docs/issues/ISSUE-0009.md`
- Issue: `docs/issues/ISSUE-0010.md`
- Issue: `docs/issues/ISSUE-0011.md`
- スキーマ定義: `docs/schema/mvp_core_tables.md`
- Qiita下書き: `docs/qiita/ISSUE-0001_mvp_infra_bootstrap.md`
- Qiita下書き: `docs/qiita/ISSUE-0002_flask_migrate_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0003_mvp_db_design.md`
- Qiita下書き: `docs/qiita/ISSUE-0004_jwt_auth_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0005_email_register_login.md`
- Qiita下書き: `docs/qiita/ISSUE-0006_google_oauth_login.md`
- Qiita下書き: `docs/qiita/ISSUE-0007_otp_verification_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0008_quiz_create_api.md`
- Qiita下書き: `docs/qiita/ISSUE-0009_quiz_list_search_detail_api.md`
- Qiita下書き: `docs/qiita/ISSUE-0010_quiz_play_scoring_api.md`
- Qiita下書き: `docs/qiita/ISSUE-0011_ranking_api.md`
