# React + Flaskで管理画面のメール設定（SMTP）を安全に実装する（QuizVerse ISSUE-0015）

## 概要
QuizVerse の管理画面に、SMTP設定をGUIで編集できるメール設定画面を追加した。

- `/admin/settings/email` 画面
- `GET /api/admin/email-settings`
- `PUT /api/admin/email-settings`
- パスワード平文の再表示防止

## 背景
OTP認証や通知メールの基盤は既に存在するが、送信設定を変更するたびに環境変数やサーバ設定を直接触る運用は非効率だった。
MVP段階でも、管理者が「送信元」「SMTP接続情報」を更新できるGUIが必要だった。

## 実装内容

### 1. 画面設計
フォームを3カードに分割した。

1. 基本設定（送信元名 / 送信元メール）
2. SMTP接続設定（ホスト / ポート / ユーザー名）
3. セキュリティ関連（パスワード / TLS / SSL）

UXとして以下を実装。

- skeleton loading
- インラインエラー
- 保存成功メッセージ
- パスワード show/hide
- 右下 sticky 保存ボタン

### 2. API設計
- `GET /api/admin/email-settings`
  - 保存済み設定を返却
  - 機密値は `smtp_password_masked` のみ返却
- `PUT /api/admin/email-settings`
  - 入力を検証し、設定を保存
  - `smtp_password` は更新時のみ受け付け

### 3. セキュリティ上の工夫
- SMTPパスワードは `email_settings.smtp_password_encrypted` に暗号化保存
- 取得APIは平文の `smtp_password` を返さない
- 管理APIは仮置きとして `X-Admin-Mode: true` を要求

## 注意点
- 管理者判定は仮置きであり、本番では JWT claim + RBAC へ置換必須
- `EMAIL_SETTINGS_ENCRYPTION_KEY` のローテーション方針が未確定だと復号不能リスクがある
- TLS/SSLは排他（同時ON不可）として検証している

## 次回
- SMTP接続テスト送信
- メールテンプレート管理
- 監査ログへの設定変更履歴記録
- RBACの本設計
