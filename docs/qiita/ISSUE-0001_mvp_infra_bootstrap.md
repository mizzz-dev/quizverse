---
title: "Docker ComposeでFlask/React/PostgreSQLのMVP開発基盤を構築する"
description: QuizVerseのMVP開発を高速化するための再現性あるローカル基盤構築手順
tags: ["React", "Flask", "PostgreSQL", "Docker"]
private: false
updated_at: 2026-04-01
issue_id: ISSUE-0001
pr_id: PR-0001
project: QuizVerse
repository: quizverse
category: infra
---

# 概要
QuizVerseのMVP立ち上げとして、Windows + Docker前提でfrontend/backend/dbの3サービスを一括起動できる構成を作成しました。

# 背景
機能実装より先に、開発者全員が同じ環境を再現できる基盤を整える必要がありました。

# 前提
- Docker Desktop
- docker compose
- Node.js/Pythonはローカル未導入でもOK（コンテナ実行前提）

# 実装内容
- Flask app factory + `/api/health`
- React + Vite + Tailwindの最小画面
- PostgreSQLコンテナ連携
- `.env.example` で設定分離

# 設計上のポイント
- ハードコード禁止: すべて環境変数化
- app factory patternで将来のblueprint分割に備える
- MVPはまず疎通確認可能な最小単位で閉じる

# ハマりどころ
- Tailwindは設定ファイル不足でビルド失敗しやすい
- DB接続先ホスト名はDocker内では `db` になる点に注意

# まとめ
開発基盤を先に固めることで、以後の認証・クイズ機能をIssue単位で安全に積み上げられる状態を作れました。

# 次回
ISSUE-0002として、SQLAlchemyマイグレーション基盤（Alembic/Flask-Migrate）を導入予定です。
