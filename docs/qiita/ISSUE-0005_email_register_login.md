---
title: "Flaskでメールアドレス認証（register/login）とJWT発行を実装する（ISSUE-0005）"
description: QuizVerseでメールアドレス登録・ログインAPIを実装し、JWT基盤へ接続した実装メモ
tags: ["Flask", "JWT", "SQLAlchemy", "Authentication", "Python"]
private: false
updated_at: 2026-04-04
issue_id: ISSUE-0005
pr_id: PR-0005
project: QuizVerse
repository: quizverse
category: auth
---

# 概要
ISSUE-0004 で整備した JWT 基盤に接続し、メールアドレス + パスワードによる register/login/me API を本実装しました。

# 背景
- dev-token だけでは実ユーザー導線の確認ができない
- フロントエンド統合前に最小の認証業務ロジックが必要
- 今後の OAuth / OTP 追加時にも共通化できる形へ寄せたい

# 実装内容
- `backend/app/models.py`
  - `users.password_hash` を追加
  - `User.set_password` / `User.check_password` を追加
- `backend/migrations/versions/20260404_0005_add_users_password_hash.py`
  - users テーブルへ `password_hash` カラム追加
- `backend/app/api/auth.py`
  - `POST /api/auth/register`
    - email/password バリデーション
    - 重複emailの409エラー
    - password hash 保存
    - JWT発行
  - `POST /api/auth/login`
    - 認証成功でJWT発行
    - 失敗時は `auth/invalid_credentials`
  - `GET /api/auth/me`
    - JWT identity から users を引いてプロフィール返却
  - `POST /api/auth/dev-token`
    - 開発専用であることを明確化
- `backend/tests/test_auth.py`
  - register/login/me の正常系・異常系を追加
  - 既存 protected/dev-token テストを維持

# 注意点
- SQLite テスト環境では `BigInteger` の自動採番が効かないため、暫定でアプリ側採番を実装。
- 本番では `AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` を必ず設定し、dev-token を無効化する。
- refresh token / revoke / password reset は次Issue以降。

# 次回
- パスワード再設定
- メール認証
- OAuth / OTP の本実装
- refresh token と失効戦略
