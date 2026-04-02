---
id: ISSUE-0003
title: "[feat] MVP向けデータモデルを定義する"
description: QuizVerse MVP に必要なユーザー、認証、クイズ、回答、プレイ履歴、ランキング関連のデータモデルを定義し migration に反映する
type: feat
priority: high
area: db
status: done
estimate_hours: 8
owner: codex
repository: quizverse
related_epics:
  - EPIC-AUTH
  - EPIC-QUIZ
related_issues:
  - ISSUE-0002
related_prs:
  - PR-0003
labels:
  - type:feature
  - area:db
  - area:backend
  - priority:high
  - status:done
  - milestone:mvp
  - tech:sqlalchemy
  - tech:postgresql
milestone: MVP
qiita_article: true
qiita_theme: "QuizVerse MVP のDB設計: users / quizzes / questions / plays をどう切るか"
breaking_change: true
created_at: 2026-04-01
updated_at: 2026-04-01
---

## 概要
QuizVerse MVP に必要な主要データモデルを定義し、migration に反映する。

## 背景
認証API、クイズ作成API、回答API、ランキングAPIの実装に先立って、MVP範囲のデータスキーマを確定する必要がある。

## 対応範囲
- users
- user_oauth_accounts
- otp_verifications
- quizzes
- questions
- choices
- quiz_plays
- quiz_play_answers
- leaderboard_snapshots
- audit_logs（最小限）
- migration 反映
- テーブル定義書更新

## 対応しないこと
- 勤怠系テーブル
- メール設定詳細テーブル
- ゲーム拡張系テーブル
- 高度な分析用テーブル

## 実装方針
- SQLAlchemy モデルとして定義する
- migration に反映する
- MVP に必要な最小限のカラムに絞る
- 将来拡張のために users と OAuth/OTP の関連を分離する
- 採点/ランキングロジックに必要な履歴構造を保持する

## タスク
- [x] ER観点でモデル構造を整理する
- [x] SQLAlchemy モデルを実装する
- [x] migration を作成 / 更新する
- [x] テーブル定義書を更新する
- [x] テストまたは静的検証を行う
- [x] PRを作成する

## 受け入れ条件
- [x] MVPで必要な主要テーブルが定義されている
- [x] migration に反映されている
- [x] モデル間の関連が不自然でない
- [x] 後続Issue（認証 / クイズ作成 / 回答）に進める状態になっている

## リスク・懸念
- 将来機能を見越しすぎて過剰設計になる可能性
- rankings の詳細ロジックは後続Issueで最終確定
- 実行環境制約により migration 実行確認が限定される可能性
