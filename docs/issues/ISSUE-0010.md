---
id: ISSUE-0010
title: "[feat] クイズ回答・採点・プレイ履歴保存APIを実装する"
description: クイズ回答を受け付けて採点し、quiz_plays / quiz_play_answers へ保存するAPIを実装する
type: feat
priority: high
area: quiz
status: done
estimate_hours: 14
owner: codex
repository: quizverse
related_epics:
  - EPIC-QUIZ
related_issues:
  - ISSUE-0008
  - ISSUE-0009
related_prs:
  - PR-0010
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
qiita_theme: "Flaskでクイズ回答・採点・プレイ履歴保存APIを実装する"
breaking_change: false
created_at: 2026-04-08
updated_at: 2026-04-08
---

## 概要
QuizVerse の「遊ぶ」中核機能として、回答送信・採点・プレイ履歴保存を担うAPIを追加する。

## 背景
- ISSUE-0009 まででクイズ一覧・詳細の読み取りは可能になった
- ランキングAPIやプレイ履歴表示を実装する前に、採点済みデータの永続化が必要
- クライアント側採点を避け、正誤判定ロジックをサーバーへ集約する必要がある

## 対応範囲
- `POST /api/quizzes/{quiz_id}/play` の追加（JWT必須）
- `question_id` ごとの `selected_choice_id` を受け取ってサーバー側採点
- `quiz_plays` へプレイ結果（score/correct/total/status）を保存
- `quiz_play_answers` へ問題単位の回答履歴を保存
- `correct_count` / `total_questions` / `score` / `score_percentage` を返却
- 不正な `question_id` / `selected_choice_id` / 問題と選択肢の不整合をバリデーション
- 正常系/異常系テスト追加
- README / docs / Qiita下書き更新

## 対応しないこと
- ランキングAPI
- プレイ履歴一覧API
- タイムアタック
- 複数回挑戦時のベストスコア集計
- フロントエンド画面本体

## 実装方針（仮置き）
- **仮置き**: MVPでは認証済みユーザーのみ保存対象（JWT必須）
- **仮置き**: 未回答はエラーにせず `skipped` として保存
- **仮置き**: スコアは `score(整数)` と `score_percentage(%)` を併記
- **仮置き**: 結果レスポンスでは各問題の `result` を返すが、正答選択肢の全文は返さない
- **仮置き**: 同一クイズの複数回プレイはすべて履歴保存
- **仮置き**: 回答順ではなく `question_id` ベースで採点

## タスク
- [x] 回答API追加
- [x] 採点ロジック実装
- [x] プレイ履歴保存（quiz_plays）
- [x] 回答履歴保存（quiz_play_answers）
- [x] 異常系バリデーション
- [x] テスト追加（正常系/異常系）
- [x] README / docs/issues / docs/qiita 更新
- [x] PR作成

## 受け入れ条件
- [x] `POST /api/quizzes/{quiz_id}/play` で回答を受け付ける
- [x] サーバー側で正誤判定できる
- [x] `quiz_plays` にプレイ結果が保存される
- [x] `quiz_play_answers` に設問ごとの回答履歴が保存される
- [x] 正解数 / 総問題数 / スコアを返す
- [x] 存在しない `question_id` / `choice_id` を弾ける
- [x] 他クイズに属する choice 混在を弾ける
- [x] 正常系 / 異常系テストがある
- [x] README / `docs/issues/ISSUE-0010.md` を更新
- [x] Qiita下書きを追加

## リスク・懸念
- 問題数が多い場合の採点性能（現状はMVP向けにシンプル実装）
- SQLite と PostgreSQL のトランザクション挙動差異
- `PYTHONPATH=. pytest` 前提の既知テスト実行制約は継続
