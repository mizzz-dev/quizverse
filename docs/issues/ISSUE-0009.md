---
id: ISSUE-0009
title: "[feat] クイズ一覧・検索・詳細取得APIを実装する"
description: QuizVerse に登録済みクイズを一覧・検索・詳細表示できる読み取り系APIを整備する
type: feat
priority: high
area: quiz
status: done
estimate_hours: 12
owner: codex
repository: quizverse
related_epics:
  - EPIC-QUIZ
related_issues:
  - ISSUE-0008
related_prs:
  - PR-0009
labels:
  - type:feature
  - area:quiz
  - area:backend
  - area:api
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:sqlalchemy
milestone: MVP
qiita_article: true
qiita_theme: "Flaskでクイズ一覧・検索・詳細取得APIを実装する"
breaking_change: false
created_at: 2026-04-05
updated_at: 2026-04-05
---

## 概要
クイズを「作る」だけでなく「探す・選ぶ」体験を実現するため、一覧・検索・詳細取得APIを追加する。

## 背景
- ISSUE-0008 でクイズ作成APIは実装済み
- 回答APIやランキングAPI、フロント統合前に読み取り系APIが必要
- 詳細APIで正答を返してしまうとプレイ体験が破綻するため、明確なレスポンス境界が必要

## 対応範囲
- `GET /api/quizzes` の追加
- キーワード検索（title + description）
- カテゴリ絞り込み（完全一致）
- ページング（`page` / `per_page`, 最大50）
- `GET /api/quizzes/{quiz_id}` の追加
- 詳細で問題と選択肢を返却（正答は返却しない）
- 作成者情報（id/display_name）を最小限返却
- クエリバリデーション追加
- 正常系/異常系テスト追加
- README / docs / Qiita下書き更新

## 対応しないこと
- クイズ編集API / 削除API
- 公開制御の高度化
- レコメンド / 人気順並び替え
- 回答API / ランキングAPI
- フロントエンド画面実装

## 実装方針（仮置き）
- 公開状態フィルタは未導入（MVPでは全件対象）
- 一覧APIの返却項目は最小限（title / description_summary / category / question_count / author / created_at）
- 詳細APIは問題文・選択肢を返却し、`is_correct` は返さない
- デフォルト並び順は `created_at desc`
- カテゴリは `quizzes.category` の完全一致
- `per_page` 最大値は 50

## タスク
- [x] 一覧APIの追加
- [x] 検索・カテゴリ絞り込み実装
- [x] ページング実装
- [x] 詳細APIの追加
- [x] 正答情報の非公開化
- [x] テスト追加（正常系/異常系）
- [x] README / docs / Qiita更新
- [x] PR作成

## 受け入れ条件
- [x] `GET /api/quizzes` で一覧取得できる
- [x] `q` でキーワード検索できる
- [x] `category` で絞り込みできる
- [x] `page` / `per_page` が動作する
- [x] `GET /api/quizzes/{quiz_id}` で詳細取得できる
- [x] 詳細で問題・選択肢を取得できる
- [x] 一般向け詳細APIで正答情報が漏れない
- [x] 正常系 / 異常系テストがある
- [x] README と `docs/issues/ISSUE-0009.md` が更新されている
- [x] Qiita下書きが追加されている

## リスク・懸念
- 公開/非公開仕様導入時に一覧・詳細クエリへ追加条件が必要
- SQLite と PostgreSQL の文字列検索挙動差異に注意
- 既知課題として `PYTHONPATH=. pytest` 前提は継続
