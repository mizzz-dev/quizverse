---
title: "Flaskでクイズ回答・採点・プレイ履歴保存APIを実装する（ISSUE-0010）"
description: QuizVerseでPOST /api/quizzes/{quiz_id}/playを追加し、採点とプレイ履歴保存をサーバー側に集約した実装メモ
tags: ["Flask", "SQLAlchemy", "API", "Backend", "Python"]
private: false
updated_at: 2026-04-08
issue_id: ISSUE-0010
pr_id: PR-0010
project: QuizVerse
repository: quizverse
category: quiz
---

# 概要
QuizVerse のMVPで「クイズを遊ぶ」ための最小APIとして、回答送信→採点→履歴保存までを一気通貫で実装しました。

# 背景
- ISSUE-0009 まででクイズ一覧/詳細は取得できる状態
- 次段のランキングAPIやプレイ履歴表示には、採点済みの永続データが必要
- 正誤判定ロジックをクライアントへ持たせると改ざん余地があるため、サーバー側に集約

# 実装内容
- `backend/app/api/quizzes.py`
  - `POST /api/quizzes/<quiz_id>/play` を追加（JWT必須）
  - `answers: [{question_id, selected_choice_id}]` を受け取り、`question_id` ベースで採点
  - `quiz_plays` と `quiz_play_answers` を同一トランザクションで保存
  - 不正入力（存在しない question/choice、他問題のchoice混在、重複question_id）をバリデーション
  - 結果レスポンスで `correct_count` / `incorrect_count` / `skipped_count` / `score` / `score_percentage` を返却
- `backend/tests/test_quizzes.py`
  - 採点成功とDB保存確認
  - JWT必須チェック
  - 存在しないquestion_id
  - 他クイズのchoice混在
  - 未回答（skipped）許容

# 注意点
- **仮置き**: MVPでは認証済みユーザーのみプレイ結果を保存
- **仮置き**: 未回答は `skipped` として採点対象外（0点）
- 結果レスポンスは各問題の正誤は返すが、正答選択肢テキストは返さない
- 同一クイズの複数回プレイは全件保存（集計ロジックは後続Issue）

# 次回
- ランキングAPI（集計エンドポイント）
- プレイ履歴一覧API
- score重み付け/タイムアタック等の拡張採点
