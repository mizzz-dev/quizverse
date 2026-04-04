---
title: "FlaskでGoogle OAuthログインを受けて既存JWT認証に接続する（ISSUE-0006）"
description: QuizVerseでGoogle IDトークン検証、OAuthアカウント紐付け、JWT発行までを実装したメモ
tags: ["Flask", "OAuth", "Google", "JWT", "SQLAlchemy"]
private: false
updated_at: 2026-04-04
issue_id: ISSUE-0006
pr_id: PR-0006
project: QuizVerse
repository: quizverse
category: auth
---

# 概要
メールアドレス認証に加えて Google OAuth ログインを追加し、成功時に既存 JWT 基盤で access token を発行するようにしました。

# 背景
- ISSUE-0005 までで email/password 認証を実装済み
- OAuth ログインの導線を追加し、認証手段を拡張したい
- `user_oauth_accounts` を利用した紐付けロジックの実運用を始めたい

# 実装内容
- `backend/app/api/auth.py`
  - `POST /api/auth/google` を追加
  - `google-auth` による ID token 検証
  - issuer / subject / email / email_verified をチェック
  - `user_oauth_accounts` を使ったログイン・初回作成・既存 email 連携
  - 成功時に `auth_method=google` で JWT 発行
- `backend/app/config.py`
  - `GOOGLE_OAUTH_CLIENT_ID` を追加（環境変数で管理）
- `backend/tests/test_auth.py`
  - 初回作成、既存 email リンク、再ログイン、異常系（トークン不正・issuer不正・email欠落）を追加
  - Google 外部依存は `_verify_google_id_token` のモックで切り離し
- `backend/requirements.txt`
  - `google-auth` を追加

# 注意点
- 本番では `GOOGLE_OAUTH_CLIENT_ID` の設定が必須。
- email 一致時の自動リンクは仮ルール。運用要件に応じて再認証や確認フローを追加検討。
- E2E レベル（実 Google 認可画面を含む）検証は別Issueで行う想定。

# 次回
- アカウント統合UIの追加
- OTP との複合フロー
- refresh token / revoke 戦略
- provider 追加（Google 以外）
