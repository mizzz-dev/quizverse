---
id: ISSUE-0007
title: "[feat] OTP認証コード送信基盤を実装する"
description: QuizVerse の認証導線を拡張し、メール/電話番号向けOTP発行・送信・検証の共通基盤を整備する
type: feat
priority: high
area: auth
status: done
estimate_hours: 12
owner: codex
repository: quizverse
related_epics:
  - EPIC-AUTH
related_issues:
  - ISSUE-0005
  - ISSUE-0006
related_prs:
  - PR-0007
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
  - tech:otp
milestone: MVP
qiita_article: true
qiita_theme: "FlaskでOTP認証コードの発行・送信・検証基盤を実装する"
breaking_change: false
created_at: 2026-04-04
updated_at: 2026-04-04
---

## 概要
メール/電話番号を将来扱える前提で、OTPコードの発行・保存・送信・検証を担うMVP基盤を実装する。

## 背景
- ISSUE-0005/0006 で password / Google OAuth のログイン導線は整備済み
- 本人確認の共通基盤として OTP を追加し、今後の二要素認証・再設定フローに流用可能にしたい
- 送信手段を抽象化し、将来的な SMS プロバイダ接続を容易にする

## 対応範囲
- `POST /api/auth/otp/request` を追加
- `POST /api/auth/otp/verify` を追加
- `otp_verifications` へ destination / expires_at / consumed_at / attempt_count を活用した保存ロジックを実装
- OTPコードはハッシュ保存（平文非保存）
- 有効期限・失敗時応答・使用済み管理を実装
- 最低限の再送制御（短時間連投抑止）と1時間あたり上限を実装
- メール送信を抽象化し、phone は未実装として明示
- auth テスト追加
- README / Issue / Qiita 下書き更新

## 対応しないこと
- SMSプロバイダとの本番接続
- メールテンプレート管理UI
- OTPを利用した完成済み2FAフロー
- パスワード再設定フロー全体

## 実装方針
- 既存 `backend/app/api/auth.py` にOTP endpointと共通ヘルパーを追加
- `OtpDeliveryService` を用意し、MVPでは email 送信のみ実装（実体はログ出力）
- `otp_verifications` は `destination` を持つ設計へ拡張し、`user_id` は nullable 化
- `OTP_EXPIRES_SECONDS=300`（5分）をデフォルト設定
- レート制限は `OTP_MIN_RESEND_SECONDS=60`, `OTP_MAX_REQUESTS_PER_HOUR=5` をデフォルト設定

## タスク
- [x] OTP発行API実装
- [x] OTP検証API実装
- [x] `otp_verifications` テーブル利用ロジック実装
- [x] 有効期限・使用済み管理・失敗時応答整備
- [x] 送信抽象化（email実装/phone未実装明示）
- [x] レート制限最小実装
- [x] auth テスト追加
- [x] README / ISSUE / Qiita 下書き更新
- [x] PR作成

## 受け入れ条件
- [x] OTP発行 endpoint が追加されている
- [x] OTP検証 endpoint が追加されている
- [x] OTP が保存され、有効期限切れが検証失敗する
- [x] 正しいOTPは検証成功する
- [x] 誤ったOTPは検証失敗する
- [x] 使用済みOTPの再利用ができない
- [x] メール送信処理が抽象化されている
- [x] phone未実装の場合に明示されている
- [x] auth テストが追加されている
- [x] README と docs が更新されている

## リスク・懸念
- メール送信はMVPでログ出力実装のため、本番運用には実送信実装の差し替えが必要
- OTP検証の目的別ワークフロー（signup/login/reset本体）は次Issueで接続が必要
- 既知課題として `PYTHONPATH=. pytest` 前提は継続
