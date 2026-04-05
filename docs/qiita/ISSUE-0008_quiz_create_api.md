---
title: "Flaskでクイズ作成API（問題・選択肢ネスト登録）を実装する（ISSUE-0008）"
description: QuizVerseでJWT必須のクイズ作成APIを実装し、クイズ本体/問題/選択肢/正答を一括登録したメモ
tags: ["Flask", "JWT", "SQLAlchemy", "API", "Backend"]
private: false
updated_at: 2026-04-04
issue_id: ISSUE-0008
pr_id: PR-0008
project: QuizVerse
repository: quizverse
category: quiz
---

# 概要
QuizVerse の中核となる「クイズ作成」を実現するため、JWT認証必須でクイズ本体・問題・選択肢・正答を一括登録できる API を実装しました。

# 背景
- 認証基盤（register/login/google/otp）は実装済み
- 回答APIやランキングAPIを作る前に、正しいデータを作成できる作成APIが必要
- 正答なし/複数正答のような不整合を登録時点で弾く必要がある

# 実装内容
- `backend/app/api/quizzes.py`
  - `POST /api/quizzes` を追加（JWT必須）
  - ネストJSONのバリデーションを実装
    - questions は 1〜50
    - choices は各問題2〜6
    - 各問題で `is_correct=true` はちょうど1件
  - title / description / question body / choice body の入力チェック
  - 保存時は quiz -> questions -> choices を一括作成
  - 途中失敗時はロールバック
  - クイズ作成時 `status=draft` 固定（公開制御は次Issueへ）
- `backend/app/__init__.py`
  - quizzes blueprint を登録
- `backend/tests/test_quizzes.py`
  - 正常系（保存成功・作成者紐付け）
  - 異常系（JWTなし、正答なし、複数正答、選択肢不足）

# 注意点
- MVPでは選択式のみ対応。記述式や複数正答は未対応。
- `category` / `difficulty` は現行モデル未対応のため次Issueで追加予定。
- `cd backend && pytest` は import path 制約で失敗するため、`PYTHONPATH=. pytest` を利用。

# 次回
- クイズ一覧API / 詳細API
- 回答API（`quiz_plays`, `quiz_play_answers` 利用）
- 公開状態の制御（draft/published遷移）
- category/difficulty 追加と検索最適化
