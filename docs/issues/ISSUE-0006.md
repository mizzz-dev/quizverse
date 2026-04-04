---
id: ISSUE-0006
title: "[feat] Google OAuth ログインを実装する"
description: QuizVerse の認証導線に Google OAuth ログインを追加し、既存 JWT 基盤へ接続する
type: feat
priority: high
area: auth
status: done
estimate_hours: 10
owner: codex
repository: quizverse
related_epics:
  - EPIC-AUTH
related_issues:
  - ISSUE-0005
related_prs:
  - PR-0006
labels:
  - type:feature
  - area:auth
  - area:backend
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:oauth
  - tech:jwt
  - tech:sqlalchemy
milestone: MVP
qiita_article: true
qiita_theme: "FlaskでGoogle OAuthログインを受け、既存JWTへ接続する"
breaking_change: false
created_at: 2026-04-04
updated_at: 2026-04-04
---

## 概要
Google アカウントでのログイン導線を追加し、成功時に QuizVerse の JWT access token を返す。

## 背景
- ISSUE-0005 で email/password 認証は実装済み
- OAuth ログインを追加し、認証手段を増やしたい
- `user_oauth_accounts` を実際に活用して今後の OTP / 統合設計につなげる

## 対応範囲
- `POST /api/auth/google` を追加
- Google ID token の検証（署名検証・issuer・client_id）
- `user_oauth_accounts` による Google アカウント紐付け
- 初回 OAuth ログインで users を必要に応じて作成
- 既存 email と Google email 一致時の既存ユーザーへの紐付け
- ログイン成功時に JWT 発行
- 異常系（不正 token / issuer 不正 / email 不備等）をハンドリング
- auth テスト追加
- README / docs / Qiita 下書き更新

## 対応しないこと
- フロントエンド Google ログインUI
- Google 以外の OAuth provider
- refresh token の本格運用
- OTP 複合フロー
- 高度な権限管理

## 実装方針
- `auth.py` に Google ログイン endpoint を追加
- Google token 検証には `google-auth` を利用
- 設定値 `GOOGLE_OAUTH_CLIENT_ID` を環境変数で注入
- email 一致時の仮ルール: 既存ユーザーを再利用して OAuth アカウントを追加
- 既存エラー形式（`error.code`, `error.message`, `error.detail`）に統一

## タスク
- [x] Google OAuth endpoint を実装
- [x] token 検証ロジックを実装
- [x] OAuth アカウント紐付けロジックを実装
- [x] 既存 email へのリンク方針を実装
- [x] JWT 発行処理を接続
- [x] 正常系/異常系テストを追加
- [x] README / ISSUE / Qiita 下書きを更新
- [x] PR作成

## 受け入れ条件
- [x] Google OAuth endpoint が追加されている
- [x] token 検証ができる
- [x] 初回ログインで users / user_oauth_accounts が作成される
- [x] 2回目以降は同一ユーザーでログインできる
- [x] 成功時に JWT access token が返る
- [x] 無効 token で適切に失敗する
- [x] auth テストが追加される
- [x] README / ISSUE / Qiita 下書きが更新される

## リスク・懸念
- email 一致時の自動リンクは将来のアカウント統合ポリシーで見直し余地あり
- 本番で `GOOGLE_OAUTH_CLIENT_ID` 未設定だと OAuth ログインが無効になる
- テストは Google 外部通信をモックし、E2E 検証は別Issueで実施する
