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

## ドキュメント
- ロードマップ: `docs/roadmap.md`
- Issue: `docs/issues/ISSUE-0001.md`
- Issue: `docs/issues/ISSUE-0002.md`
- Issue: `docs/issues/ISSUE-0003.md`
- スキーマ定義: `docs/schema/mvp_core_tables.md`
- Qiita下書き: `docs/qiita/ISSUE-0001_mvp_infra_bootstrap.md`
- Qiita下書き: `docs/qiita/ISSUE-0002_flask_migrate_foundation.md`
- Qiita下書き: `docs/qiita/ISSUE-0003_mvp_db_design.md`
