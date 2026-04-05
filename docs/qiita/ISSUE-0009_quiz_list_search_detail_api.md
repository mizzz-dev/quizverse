---
title: "Flaskでクイズ一覧・検索・詳細取得APIを実装する（ISSUE-0009）"
description: QuizVerseでクイズ一覧/検索/詳細取得APIを追加し、プレイ前表示向けに正答非公開レスポンスを整備したメモ
tags: ["Flask", "SQLAlchemy", "API", "Backend", "Python"]
private: false
updated_at: 2026-04-05
issue_id: ISSUE-0009
pr_id: PR-0009
project: QuizVerse
repository: quizverse
category: quiz
---

# 概要
QuizVerse に登録済みのクイズを検索・選択できるように、一覧APIと詳細APIを実装しました。

# 背景
- すでに作成API（ISSUE-0008）はあるが、閲覧導線が未整備だった
- 回答API前提として、正答を返さない安全な詳細レスポンスが必要だった

# 実装内容
- `backend/app/api/quizzes.py`
  - `GET /api/quizzes`
    - `q`（title/description 部分一致）
    - `category`（完全一致）
    - `page`/`per_page`（最大50）
    - `created_at desc` で返却
  - `GET /api/quizzes/<quiz_id>`
    - 問題文と選択肢を返却
    - `is_correct` は返さない
  - 一覧/検索クエリのバリデーション追加
  - 作成APIに `category` 入力対応を追加
- `backend/app/models.py`
  - `quizzes.category` カラムを追加
- `backend/migrations/versions/20260405_0007_add_quizzes_category.py`
  - category 追加マイグレーション
- `backend/tests/test_quizzes.py`
  - 一覧検索・カテゴリ・ページングの正常系
  - ページング異常値の異常系
  - 詳細取得と正答非公開の確認

# 注意点
- MVPでは公開/非公開フィルタは未導入（次Issueで拡張想定）
- SQLiteでのテストを主に実施。PostgreSQL本番ではILIKEの実挙動確認を推奨
- テストは `PYTHONPATH=. pytest` 前提

# 次回
- 回答API（`quiz_plays`, `quiz_play_answers`）
- 公開状態制御（draft/publishedのアクセス境界）
- 一覧並び替え拡張（人気順・新着順）
