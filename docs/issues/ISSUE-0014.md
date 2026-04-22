---
id: ISSUE-0014
title: "[feat] 管理ダッシュボードの基本画面を実装する"
description: 運営者がユーザー・クイズ・サービス状況を把握できる管理UIの土台を作る
type: feat
priority: high
area: admin
status: done
estimate_hours: 20
owner: codex
repository: quizverse
related_epics:
  - EPIC-ADMIN
related_issues:
  - ISSUE-0011
related_prs:
  - PR-0014
labels:
  - type:feature
  - area:frontend
  - area:backend
  - area:admin
  - priority:high
  - milestone:mvp
  - tech:react
  - tech:flask
milestone: MVP
qiita_article: true
qiita_theme: "React + Flask で管理ダッシュボード基盤をMVP実装する"
breaking_change: false
created_at: 2026-04-22
updated_at: 2026-04-22
---

## 概要
QuizVerse の運営作業を開始するため、`/admin/*` 配下に管理ダッシュボード基盤を実装する。

## 背景
- 既存MVPはプレイヤー体験中心で、運営者向け導線が不足していた
- ユーザー/クイズ/プレイ状況を1画面で確認する最小構成が必要
- 将来のRBAC・監査ログ・メール設定本実装へつながる土台が必要

## 対応範囲
- フロントエンド管理レイアウト（ヘッダー / サイドナビ / コンテンツ）
- 管理トップのサマリーカード
- ユーザー管理一覧（MVP）
- クイズ管理一覧（MVP）
- サービス状況カード（API/DB/メール送信基盤）
- メール設定画面への導線 + 雛形
- ローディング / 空状態 / エラー状態の基本UI
- backend read-only 管理APIの最小追加
- README / docs/issues / docs/qiita 更新

## 対応しないこと
- RBAC本実装
- ユーザー/クイズ編集や削除
- メール設定保存
- 外部監視連携
- 高度な検索/フィルター

## 実装方針（仮置き）
- **仮置き**: admin判定は `localStorage["quizverse_is_admin"]` を利用（RBAC未実装のため）
- **仮置き**: 管理URLは `/admin`, `/admin/users`, `/admin/quizzes`, `/admin/settings`
- **仮置き**: backend は `GET /api/admin/*` の read-only API を新設
- **仮置き**: メール設定は導線 + 雛形のみ
- **仮置き**: ユーザー一覧の email はマスク表示のみ

## タスク
- [x] 管理画面共通レイアウト実装
- [x] サマリーカード実装
- [x] ユーザー/クイズ一覧画面実装
- [x] サービス状況表示実装
- [x] メール設定導線実装
- [x] backend read-only API追加
- [x] ローディング/空状態/エラー表示実装
- [x] README / docs/issues / docs/qiita 更新

## 受け入れ条件
- [x] 管理ダッシュボードトップが表示可能
- [x] 主要指標サマリーを表示可能
- [x] ユーザー管理一覧の基本表示
- [x] クイズ管理一覧の基本表示
- [x] サービス状況表示を確認可能
- [x] メール設定画面への導線あり
- [x] 管理画面レイアウトに一貫性あり
- [x] ローディング/空状態/エラー状態の少なくとも一部を実装
- [x] README / `docs/issues/ISSUE-0014.md` 更新
- [x] Qiita下書き追加

## リスク・懸念
- RBAC未実装のため本番開放は不可
- admin API は read-only 前提。更新系を追加する際は認可設計が必須
- 一覧画面は MVP のため検索/フィルタ不足
