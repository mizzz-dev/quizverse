---
id: ISSUE-0001
title: "[feat] MVP開発基盤（Docker + Flask + React + PostgreSQL）を構築する"
description: Windows + Docker前提で再現可能なMVP開発基盤を構築し、ヘルスチェックまで疎通確認可能にする
type: feat
priority: high
area: infra
status: done
estimate_hours: 6
owner: codex
repository: quizverse
related_epics:
  - EPIC-INFRA
related_issues: []
related_prs:
  - PR-0001
labels:
  - feature
  - infra
milestone: MVP
qiita_article: true
qiita_theme: "Docker ComposeでFlask/React/PostgreSQLのMVP基盤を最短で立ち上げる"
breaking_change: false
created_at: 2026-04-01
updated_at: 2026-04-01
---

## 概要
QuizVerseのMVP開発を進めるため、Docker Composeでbackend/frontend/dbを同時起動できる開発基盤を作成する。

## 背景
Issue駆動開発の初手として、実装を積み上げる共通土台が必要。環境差分を減らし、Windows + Dockerで誰でも同じ手順で再現できる状態を作る。

## 対応範囲
- backend Flask app factoryの最小構成
- `/api/health` ヘルスチェックAPI
- frontend React + Vite + Tailwind最小画面
- PostgreSQLコンテナと接続用環境変数
- `docker-compose.yml` と `.env.example`
- backend単体テスト（health endpoint）
- README更新

## 対応しないこと
- 認証（JWT/OAuth/OTP）の本実装
- クイズ作成・回答・ランキングの業務ロジック
- 本番用CI/CD

## 実装方針
- 設定値は環境変数から読み込む
- backendはapp factory patternを採用
- 初期検証容易性を優先し、健康状態確認APIを実装
- フロントはモダンUIの起点としてTailwind導入のみ

## タスク
- [x] 設計確認
- [x] 実装
- [x] テスト
- [x] ドキュメント更新
- [x] Qiita下書き作成

## 受け入れ条件
- `docker compose config` が成功する
- backendのテストで `/api/health` が200を返す
- READMEに起動手順・構成・次Issueへの接続が明記されている

## リスク・懸念
- Windows環境でのボリュームマウント速度劣化
- DB migration導入前のためスキーマ管理が暫定（仮置き）
