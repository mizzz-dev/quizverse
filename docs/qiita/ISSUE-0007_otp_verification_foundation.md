---
title: "FlaskでOTP認証コードの発行・送信・検証基盤を実装する（ISSUE-0007）"
description: QuizVerseでOTP発行API/検証API、ハッシュ保存、有効期限、再送制御までをMVP実装したメモ
tags: ["Flask", "OTP", "JWT", "SQLAlchemy", "Security"]
private: false
updated_at: 2026-04-04
issue_id: ISSUE-0007
pr_id: PR-0007
project: QuizVerse
repository: quizverse
category: auth
---

# 概要
QuizVerse の認証導線拡張に向けて、OTPコードの発行・保存・送信・検証を行うMVP基盤を実装しました。

# 背景
- email/password と Google OAuth の基盤は実装済み
- 次段で必要になるメール認証強化、電話番号認証、2FA、再設定に流用できる共通パーツが必要
- 送信手段を先に抽象化して、後で SMS 連携を追加しやすくする

# 実装内容
- `backend/app/api/auth.py`
  - `POST /api/auth/otp/request` を追加
  - `POST /api/auth/otp/verify` を追加
  - OTPコード生成、ハッシュ保存、期限判定、使用済み化、試行回数管理
  - `OtpDeliveryService` による送信抽象化（MVPはemail送信相当をログ出力）
  - `channel=phone` は `auth/otp_channel_not_implemented` で明示
  - 最低限のレート制限（短時間再送抑止・1時間上限）
- `backend/app/models.py`
  - `otp_verifications.user_id` を nullable 化
  - `otp_verifications.destination` を追加
- `backend/migrations/versions/20260404_0006_otp_destination_and_nullable_user.py`
  - destination列追加、user_id nullable 化、検索用インデックス追加
- `backend/tests/test_auth.py`
  - OTP正常系/異常系/期限切れ/再利用不可/レート制限/phone未実装テストを追加

# 注意点
- 送信はMVPとしてログ出力。実運用ではメール/SMSプロバイダ実装に差し替えること。
- 現時点のOTPは検証成功・失敗判定までで、signup/login/resetの本体フロー接続は次Issue。
- `OTP_INCLUDE_CODE_IN_RESPONSE` はテスト用途向け。運用環境では `false` を必須推奨。

# 次回
- OTP検証成功後の用途別アクション（ユーザー作成、ログイン許可、再設定トークン払い出し）接続
- SMS送信プロバイダ実装
- レート制限のストレージ/分散対応（Redis 等）
