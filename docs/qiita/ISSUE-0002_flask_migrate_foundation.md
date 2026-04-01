---
title: "Flask-MigrateでPostgreSQLスキーマ変更を安全に管理する（QuizVerse ISSUE-0002）"
description: QuizVerseのMVP開発でFlask-Migrateを導入し、DB変更を履歴管理可能にした実装メモ
tags: ["Flask", "SQLAlchemy", "Alembic", "PostgreSQL", "Docker"]
private: false
updated_at: 2026-04-01
issue_id: ISSUE-0002
pr_id: PR-0002
project: QuizVerse
repository: quizverse
category: db
---

# 概要
QuizVerse の MVP 開発に向けて、Flask-Migrate（Alembic）を導入し、DBスキーマ変更をバージョン管理できる状態を作りました。

# 背景
ISSUE-0001 で Docker + Flask + React + PostgreSQL の起動基盤は整備済みでしたが、DB定義変更の履歴管理が未整備でした。

# 前提
- Flask app factory 構成
- SQLAlchemy 拡張導入済み
- PostgreSQL は Docker Compose の `db` サービスで起動

# 実装内容
- `Flask-Migrate` を requirements に追加
- `extensions.py` に `migrate = Migrate()` を追加
- `create_app` で `migrate.init_app(app, db)` を実行
- `backend/migrations` に Alembic 管理ファイルを追加
- baseline migration (`20260401_0002_initial_baseline.py`) を追加
- README に `flask db migrate/upgrade` 手順を追記

# 設計上のポイント
- モデル追加前に migration 基盤だけを先に整備し、以降のIssueで増分管理できるように分離
- 設定値をコードに埋め込まず、既存の環境変数ベース構成を維持
- `flask --app app db ...` にコマンドを統一し、運用を単純化

# ハマりどころ
- 実行環境に依存ライブラリが不足していると `flask db` が失敗する
- モデル未追加の段階では初期 migration が空になりやすい（これは仕様通り）

# まとめ
マイグレーション基盤を先に固定したことで、今後のユーザー/クイズ関連テーブル追加を安全に追跡できるようになりました。

# 次回
ISSUE-0003（MVP向けデータモデル定義）で、`users` を起点にテーブル定義と migration の増分作成を実施予定です。
