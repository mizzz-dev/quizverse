---
id: ISSUE-0015
title: "[feat] メール設定画面とSMTP設定保存機能を実装する"
description: 管理者がGUIからSMTP設定を取得・更新できるようにする
type: feat
priority: high
area: admin
status: done
estimate_hours: 24
owner: codex
repository: quizverse
related_epics:
  - EPIC-ADMIN
related_issues:
  - ISSUE-0014
related_prs:
  - PR-0015
labels:
  - type:feature
  - area:frontend
  - area:backend
  - area:admin
  - area:security
  - priority:high
  - milestone:mvp
  - tech:react
  - tech:flask
milestone: MVP
qiita_article: true
qiita_theme: "管理画面からSMTP設定を安全に更新できるようにする"
breaking_change: false
created_at: 2026-04-22
updated_at: 2026-04-22
---

## 概要
管理ダッシュボード配下にメール設定画面を実装し、SMTP設定を `GET/PUT /api/admin/email-settings` で取得・保存できるようにする。

## 背景
- OTP送信基盤はあるが、運営者がGUIで送信設定を更新する導線が不足していた
- 送信元名・送信元メール・SMTP接続情報は運用時に頻繁に変更されるため、環境変数だけでは対応しづらい
- 機密情報（SMTPパスワード）を安全に扱う画面/APIの土台が必要

## 対応範囲
- 管理画面ルートを `/admin/settings/email` に整理
- メール設定フォーム（基本設定 / SMTP接続設定 / セキュリティ関連）
- skeleton / インラインエラー / 保存成功フィードバック
- 機密入力（SMTPパスワード）の show/hide 切替
- `GET /api/admin/email-settings`
- `PUT /api/admin/email-settings`
- 最低限バリデーション（email形式, port範囲, TLS/SSL排他, 必須項目）
- 権限制御の仮導線（`X-Admin-Mode: true`）
- DBテーブル `email_settings` 追加
- README / docs/issues / docs/schema / docs/qiita 更新

## 対応しないこと
- メールテンプレート管理の本実装
- メールテスト送信
- 外部メールサービス高度連携（SendGrid/SES）
- RBAC本設計
- 設定履歴復元・監査ログ画面

## 実装方針（仮置き）
- **仮置き**: 管理者判定は `X-Admin-Mode: true` を要求（本来はJWT claim + RBACへ移行）
- **仮置き**: メール設定は単一レコードのみ管理
- **仮置き**: SMTPパスワードはDBに暗号化保存し、取得APIでは平文を返さない
- **仮置き**: 保存先はDB `email_settings` を優先
- **仮置き**: テスト送信は次Issueへ切り出し

## タスク
- [x] メール設定画面の実装
- [x] SMTP設定取得/保存APIの追加
- [x] 入力バリデーション追加
- [x] 機密値のマスク・再表示抑止
- [x] 管理者仮導線の追加
- [x] migration + schema docs 更新
- [x] README / Issue / Qiita 更新

## 受け入れ条件
- [x] 管理画面からメール設定画面へ遷移できる
- [x] SMTP 設定取得 API が利用できる
- [x] SMTP 設定保存 API が利用できる
- [x] 入力バリデーションが機能する
- [x] パスワード等の機密情報が危険な形で再表示されない
- [x] 保存成功 / 失敗がUIで分かる
- [x] 管理者向け導線として成立している
- [x] README と `docs/issues/ISSUE-0015.md` が更新されている
- [x] Qiita下書きが追加されている

## リスク・懸念
- 管理者判定は仮置きのため本番運用不可
- 暗号鍵（`EMAIL_SETTINGS_ENCRYPTION_KEY`）運用ポリシー未確定時は復号不能リスクがある
- 実送信機能追加時にSMTP接続タイムアウト・再試行設計が必要
