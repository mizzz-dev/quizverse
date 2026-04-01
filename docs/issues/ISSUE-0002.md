---
id: ISSUE-0002
title: "[feat] PostgreSQL接続とSQLAlchemyマイグレーション基盤を整備する"
description: Flask-Migrateを導入し、DBスキーマ変更を履歴管理できる基盤を構築する
type: feat
priority: high
area: db
status: done
estimate_hours: 4
owner: codex
repository: quizverse
related_epics:
  - EPIC-INFRA
related_issues:
  - ISSUE-0001
related_prs:
  - PR-0002
labels:
  - type:feature
  - area:db
  - area:backend
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:sqlalchemy
  - tech:postgresql
milestone: MVP
qiita_article: true
qiita_theme: "Flask-MigrateでPostgreSQLスキーマ変更を安全に管理する"
breaking_change: false
created_at: 2026-04-01
updated_at: 2026-04-01
---

## 概要
Flaskバックエンドに Flask-Migrate（Alembic）を導入し、PostgreSQLのスキーマ変更をマイグレーションとして管理できるようにする。

## 背景
ISSUE-0001でMVPの起動基盤は整ったが、DB定義変更を安全に積み上げるためのスキーマ履歴管理が未整備だった。今後のユーザー認証・クイズ機能の実装前に、マイグレーション基盤を先に確立する必要がある。

## 対応範囲
- Flask-Migrate 依存追加
- app factory への migrate extension 組み込み
- Alembic 設定ファイルと migrations ディレクトリ追加
- 初期ベースライン migration 追加
- README と運用ドキュメント更新

## 対応しないこと
- MVP業務テーブル（users/quizzes/answers など）の本定義
- 認証API実装
- 本番デプロイ用マイグレーション運用（CI/CD統合）

## 実装方針
- 既存 app factory パターンを維持し、extensions.py に migrate を追加
- `flask --app app db ...` コマンド体系で今後の migration を統一
- 初回は空の baseline revision を作成し、次Issueでモデル追加時に migration を増分管理する

## タスク
- [x] 実装
- [x] テスト
- [x] ドキュメント更新
- [x] PR作成

## 受け入れ条件
- `Flask-Migrate` が requirements に追加されている
- `create_app` 内で `migrate.init_app(app, db)` が呼ばれている
- `backend/migrations` 以下に初期 migration 管理ファイルが存在する
- README に migration 実行手順が追記されている

## リスク・懸念
- 実行環境の依存不足により、`flask db` 実コマンドの検証がローカルで未完になる可能性
- モデル未定義のため初期 migration が空である点（次Issueで解消予定）
