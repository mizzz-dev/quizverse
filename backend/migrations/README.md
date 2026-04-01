# Migrations

このディレクトリは Flask-Migrate (Alembic) のマイグレーション管理用です。

## 主要コマンド

```bash
cd backend
flask --app app db upgrade
flask --app app db migrate -m "describe change"
flask --app app db upgrade
```

## 補足
- 初期化 (`flask --app app db init`) はこのリポジトリでは実施済みです。
- 変更時は `versions/` 配下に新しい migration script が追加されます。
