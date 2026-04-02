---
title: "QuizVerse MVP のDB設計: users / quizzes / questions / plays をどう切るか（ISSUE-0003）"
description: QuizVerse MVPの認証・クイズ・回答・ランキングAPIの土台となるデータモデル設計メモ
tags: ["Flask", "SQLAlchemy", "PostgreSQL", "Alembic", "DatabaseDesign"]
private: false
updated_at: 2026-04-01
issue_id: ISSUE-0003
pr_id: PR-0003
project: QuizVerse
repository: quizverse
category: db
---

# 概要
QuizVerse MVPに必要なコア業務テーブル（users, quizzes, questions, plays など）を定義し、Alembic migrationに反映しました。

# 背景
認証API・クイズ作成API・回答APIを実装するには、先にモデルの責務分離と履歴構造を確定しておく必要があります。ISSUE-0002で導入したFlask-Migrate基盤の上に、今回の本体スキーマを積み上げました。

# 前提
- Flask + Flask-SQLAlchemy
- Flask-Migrate/Alembic 導入済み
- PostgreSQL運用を前提（ローカルはDocker Compose想定）

# 実装内容
- SQLAlchemyモデルを `backend/app/models.py` に追加
- 以下テーブルを migration (`20260401_0003_mvp_core_schema.py`) へ反映
  - users
  - user_oauth_accounts
  - otp_verifications
  - quizzes
  - questions
  - choices
  - quiz_plays
  - quiz_play_answers
  - leaderboard_snapshots
  - audit_logs
- テーブル定義書を `docs/schema/mvp_core_tables.md` として追加

# 設計上のポイント
- users本体とOAuth/OTP情報を分離し、認証方式追加時の拡張余地を確保
- 回答履歴は `quiz_play_answers` に明示的に保持し、採点再計算や分析に利用可能
- ランキングは固定`rankings`ではなく、`leaderboard_snapshots`を採用
  - MVP時点ではAPI応答を安定化
  - 将来は集計SQLやmaterialized viewへ移行しやすい構造

# ハマりどころ
- SQLAlchemyモデル側の列名 `metadata` は予約語衝突を避ける必要があるため、属性名とDB列名を分離
- 実行環境の依存不足があると migration/pytest の完全実行確認ができない

# まとめ
MVP機能を進めるための最小スキーマを先に確定し、後続Issue（Google OAuth、OTP、クイズAPI実装）を進めやすい土台を作れました。

# 次回
- 認証API（Google OAuth/OTP）実装
- クイズ作成・公開・回答API実装
- leaderboard作成タイミングと集計戦略の詳細確定
