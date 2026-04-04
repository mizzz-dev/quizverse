---
title: "Flask-JWT-ExtendedでQuizVerseのJWT認証基盤を整備する（ISSUE-0004）"
description: QuizVerseの認証API実装に向けてJWT基盤を先行実装したメモ
tags: ["Flask", "JWT", "Flask-JWT-Extended", "Python", "Backend"]
private: false
updated_at: 2026-04-04
issue_id: ISSUE-0004
pr_id: PR-0004
project: QuizVerse
repository: quizverse
category: auth
---

# 概要
QuizVerse の次Issueで予定している register/login 実装に先立ち、JWT 認証の土台を先行実装しました。今回は「認証基盤」が対象で、認証業務ロジック本体は次Issueへ切り出しています。

# 背景
- ISSUE-0003 で users / quizzes などのコアスキーマが整備済み
- API実装を進める前に、JWTの初期化・保護ルート・エラー形式を共通化しておきたい
- 後続で OAuth/OTP を追加しても破綻しにくい形にしたい

# 実装内容
- `backend/app/config.py`
  - `JWT_SECRET_KEY`
  - `JWT_ALGORITHM`
  - `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`（`timedelta`化）
  - `AUTH_ENABLE_DEV_TOKEN_ENDPOINT`
- `backend/app/api/auth.py`
  - `POST /api/auth/dev-token`（開発用の仮トークン発行）
  - `GET /api/auth/protected`（JWT必須）
  - `GET /api/auth/me`
  - JWTエラーハンドラ（missing / invalid / expired）
- `backend/tests/test_auth.py`
  - 正常系（token発行→protected成功）
  - 異常系（tokenなし / 不正token）
  - dev-token無効化時の403

# 注意点
- `dev-token` は暫定実装です。`AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` で無効化できます。
- 本番運用では login/register を実装し、`dev-token` は削除または完全に開発限定にする前提です。
- claims 設計は最小限（`scope`, `auth_method`）に留めています。

# テスト
- `cd backend && pytest` で auth + health の疎通を確認
- 以前の `ModuleNotFoundError: flask_migrate` は、依存をインストールした環境なら再現しない想定（`requirements.txt` に `Flask-Migrate` 定義済み）

# 次回
- register/login API の本実装
- password hash の導入
- users テーブルとの実連携
- refresh token / revocation 戦略の具体化
