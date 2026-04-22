# React + Flaskで管理ダッシュボード基盤を実装する（QuizVerse ISSUE-0014）

## 概要
QuizVerse の運営者向けに、管理ダッシュボードの最小構成（MVP）を実装した。

- 管理トップ（サマリーカード）
- ユーザー管理一覧
- クイズ管理一覧
- サービス状況カード
- メール設定導線（雛形）

## 背景
プレイヤー向け機能（認証・クイズ作成/プレイ・ランキング）は整ってきたが、運営者が全体状況を確認する導線が不足していた。
そこで `/admin/*` に管理UIを切り出し、将来のRBAC・監査ログ・設定管理につながる土台を先に整えた。

## 実装内容

### 1. 管理レイアウト
- sticky サイドバー + sticky ヘッダー
- SaaSライクなカードUI
- 余白重視のミニマル構成

### 2. ダッシュボードサマリー
- ユーザー数
- クイズ数
- プレイ数
- ランキング件数（submitted play件数を仮置き採用）

### 3. 一覧画面
- ユーザー管理一覧（email はマスク値のみ表示）
- クイズ管理一覧（作成者・ステータス・プレイ数）

### 4. サービス状況
- API
- Database
- Mail Delivery（MVPでは warning 表示）

### 5. backend read-only API
- `GET /api/admin/overview`
- `GET /api/admin/users`
- `GET /api/admin/quizzes`

## デザイン上の工夫
- Bento Grid 風のサマリーカード
- subtle gradient + soft shadow
- skeleton loading
- hover/focus の軽い micro interaction
- status badge を `ok / warning / error` で色分け

## 注意点
- admin 判定は `localStorage["quizverse_is_admin"]` の**仮置き**
- 本番運用前に RBAC / JWT claim 判定へ置換が必須
- 管理APIは read-only 前提で、更新系追加時は認可と監査ログ設計が必要

## 次回
- RBAC（adminロール + 権限粒度）
- ユーザー編集/BAN
- クイズ公開状態の運用管理
- メール設定保存 + 接続テスト
- 監査ログ画面
