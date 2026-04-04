---
id: ISSUE-0005
title: "[feat] メールアドレスによるサインアップ / ログインAPIを実装する"
description: QuizVerse の JWT 認証基盤に接続する register/login/me API を実装し、メールアドレス認証の最小本番導線を整備する
type: feat
priority: high
area: auth
status: done
estimate_hours: 8
owner: codex
repository: quizverse
related_epics:
  - EPIC-AUTH
related_issues:
  - ISSUE-0004
related_prs:
  - PR-0005
labels:
  - type:feature
  - area:auth
  - area:backend
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:jwt
  - tech:sqlalchemy
milestone: MVP
qiita_article: true
qiita_theme: "Flaskでメールアドレス認証（register/login）とJWT発行を実装する"
breaking_change: false
created_at: 2026-04-04
updated_at: 2026-04-04
---

## 概要
JWT 認証基盤（ISSUE-0004）を活用し、メールアドレス + パスワードによる register/login/me API を本実装する。

## 背景
- 前回PRでは dev-token で JWT 疎通のみ確認できる状態だった
- フロントエンド統合に向けて実ユーザーでの認証導線が必要
- Google OAuth / OTP 追加前に基本認証フローを確立する

## 対応範囲
- `POST /api/auth/register` 実装
- `POST /api/auth/login` 実装
- パスワードのハッシュ保存（平文禁止）
- email 重複登録防止
- register/login の入力バリデーション
- login/register 成功時の JWT 発行
- `GET /api/auth/me` の実ユーザー返却
- auth テスト追加/更新
- README / docs / Qiita 下書き更新
- `dev-token` endpoint を開発限定用途として明文化

## 対応しないこと
- パスワード再設定
- メール認証フロー
- 電話番号ログイン
- OTP 本実装
- Google OAuth 本実装詳細
- refresh token の本格運用
- RBAC 本格実装

## 実装方針
- `backend/app/api/auth.py` を中心に拡張
- `users` に `password_hash` カラム追加（マイグレーション追加）
- Werkzeug の `generate_password_hash` / `check_password_hash` を採用
- エラーレスポンス形式は既存 `error.code` / `error.message` と整合
- `dev-token` は残しつつ、開発専用であることをレスポンス/READMEで明示

## タスク
- [x] register API を実装
- [x] login API を実装
- [x] users への password_hash 追加
- [x] me endpoint を実ユーザー返却へ更新
- [x] 入力バリデーション/重複エラー実装
- [x] auth テストを register/login/me 含めて拡張
- [x] README / docs / Qiita 更新
- [x] PR作成

## 受け入れ条件
- [x] register で新規ユーザー登録できる
- [x] 重複 email で登録できない
- [x] パスワードがハッシュ化される
- [x] login 成功で JWT が返る
- [x] 不正資格情報で login が失敗する
- [x] me でログインユーザー情報を返す
- [x] auth テストが追加/更新される
- [x] README / ISSUE / Qiita 下書きが更新される

## リスク・懸念
- SQLite テスト環境では `BigInteger` 主キー自動採番が効かないため、暫定でアプリ側採番を導入
- 本番環境では `AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false` を明示し、dev-token の誤有効化を防止する必要がある
