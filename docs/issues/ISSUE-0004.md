---
id: ISSUE-0004
title: "[feat] JWT認証基盤を実装する"
description: QuizVerse API認証のためにFlask-JWT-Extendedの基盤と最小疎通エンドポイントを整備する
type: feat
priority: high
area: auth
status: done
estimate_hours: 6
owner: codex
repository: quizverse
related_epics:
  - EPIC-AUTH
related_issues:
  - ISSUE-0003
related_prs:
  - PR-0004
labels:
  - type:feature
  - area:auth
  - area:backend
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:jwt
milestone: MVP
qiita_article: true
qiita_theme: "Flask-JWT-ExtendedでQuizVerseのJWT認証基盤を整備する"
breaking_change: false
created_at: 2026-04-04
updated_at: 2026-04-04
---

## 概要
QuizVerse の register/login/me/protected API を安全に追加するため、JWT 認証基盤を backend に実装する。

## 背景
ISSUE-0003 でコアデータモデルを整備したため、次段階として API 認証の共通基盤を先に固める。

## 対応範囲
- Flask-JWT-Extended を app factory / extensions に統合
- JWT 設定値の config/env 管理
- JWT 必須の protected endpoint 追加
- 開発用 token 発行 endpoint（仮置き）追加
- JWT エラーレスポンス整備
- README / docs / Qiita 下書き更新
- pytest で auth 基本疎通テスト追加

## 対応しないこと
- メールアドレス登録/ログイン本実装
- パスワードハッシュ認証
- Google OAuth 本実装
- OTP送信本実装
- 高度な refresh token 運用
- 本格的な RBAC

## 実装方針
- 既存 app factory pattern を維持
- `backend/app/api/auth.py` に auth blueprint を分離
- `AUTH_ENABLE_DEV_TOKEN_ENDPOINT` で仮token発行エンドポイントを制御
- エラー形式を `error.code` / `error.message` / `error.detail` に統一

## タスク
- [x] JWT設定・初期化の整備
- [x] auth blueprint の追加
- [x] protected/me endpoint の追加
- [x] dev-token endpoint の追加（仮置き）
- [x] JWTエラーハンドリングの追加
- [x] authテストの追加
- [x] README / docs / Qiita更新
- [x] PR作成

## 受け入れ条件
- [x] Flask-JWT-Extended が組み込まれている
- [x] 環境変数経由で JWT 設定を変更できる
- [x] token ありで protected endpoint が成功する
- [x] token なし / 不正token で適切に失敗する
- [x] ドキュメントが更新されている
- [x] テスト実行可否を明確化している

## リスク・懸念
- dev-token endpoint は仮置きであり、本番前に login/register へ置換が必要
- identity/claims 拡張は users テーブルと整合を取って段階的に見直す
- 環境依存で pytest が未実行の場合は依存セットアップが必要
