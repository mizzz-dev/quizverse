---
id: ISSUE-0011
title: "[feat] ランキングAPIを実装する"
description: quiz_plays を集計し、総合ランキング・クイズ単位ランキングAPIを提供する
type: feat
priority: high
area: ranking
status: done
estimate_hours: 16
owner: codex
repository: quizverse
related_epics:
  - EPIC-QUIZ
related_issues:
  - ISSUE-0010
related_prs:
  - PR-0011
labels:
  - type:feature
  - area:ranking
  - area:backend
  - area:api
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:sqlalchemy
milestone: MVP
qiita_article: true
qiita_theme: "Flask + SQLAlchemyでランキングAPIを設計・実装する"
breaking_change: false
created_at: 2026-04-08
updated_at: 2026-04-08
---

## 概要
QuizVerse の継続利用を促進する MVP 機能として、プレイ履歴からランキングを取得できる API を追加する。

## 背景
- ISSUE-0010 で回答送信・採点・プレイ履歴保存が可能になった
- ダッシュボード表示やプロフィール実装の前段としてランキング参照APIが必要
- 同点時や複数プレイ時の扱いを仕様化し、フロントと整合したレスポンスを提供する必要がある

## 対応範囲
- `GET /api/rankings`（総合ランキング）
- `GET /api/quizzes/{quiz_id}/rankings`（クイズ単位ランキング）
- ページング（`page`, `per_page`）
- 同点時の順位ルール実装
- 同一ユーザー複数プレイ時のベスト採用ロジック実装
- テスト追加（正常系/異常系）
- README / docs/issues / docs/qiita 更新

## 対応しないこと
- リアルタイム更新（WebSocket/SSE）
- snapshot テーブルの本運用
- シーズン制・イベント制
- フロントエンド画面本体

## 実装方針（仮置き）
- **仮置き**: クイズ単位ランキングは「ユーザーごとのベストプレイ1件」を採用
- **仮置き**: 総合ランキングは「ユーザー×クイズのベストスコアをクイズ横断で合算」
- **仮置き**: 同点時は `score desc` → `correct_count desc` → `played_at asc` → `play_id asc`
- **仮置き**: 総合ランキング同点時は `total_score desc` → `total_correct_count desc` → `first_played_at asc` → `user_id asc`
- **仮置き**: 表示名は `display_name` を優先し、空の場合は `user-{id}` マスクを返す
- **仮置き**: MVPは都度集計（`leaderboard_snapshots` 活用は将来Issueで検討）

## タスク
- [x] ランキングAPI追加（総合/クイズ単位）
- [x] 集計ロジック追加（ベストプレイ採用 + 総合合算）
- [x] 同点ルールを実装・明文化
- [x] ページング実装
- [x] テスト追加（正常系/異常系）
- [x] README / docs/issues / docs/qiita 更新
- [x] PR作成

## 受け入れ条件
- [x] `GET /api/rankings` で総合ランキング取得
- [x] `GET /api/quizzes/{quiz_id}/rankings` でクイズ単位ランキング取得
- [x] 並び順ルールが仕様化・実装済み
- [x] ページング動作
- [x] 同一ユーザー複数プレイ時の扱い明文化
- [x] レスポンスに email を含めない
- [x] 正常系/異常系テストが存在
- [x] README / `docs/issues/ISSUE-0011.md` 更新
- [x] Qiita下書き追加

## リスク・懸念
- 集計クエリの複雑化に伴うパフォーマンス劣化（データ増加時）
- SQLite と PostgreSQL のWindow関数挙動差異
- `PYTHONPATH=. pytest` 依存の既知課題は継続
