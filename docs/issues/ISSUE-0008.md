---
id: ISSUE-0008
title: "[feat] クイズ作成APIと問題・選択肢登録APIを実装する"
description: 認証済みユーザーがクイズ本体・問題・選択肢・正答情報を一括登録できる基盤APIを整備する
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
  - ISSUE-0003
  - ISSUE-0004
related_prs:
  - PR-0008
labels:
  - type:feature
  - area:quiz
  - area:backend
  - area:api
  - priority:high
  - status:done
  - milestone:mvp
  - tech:flask
  - tech:jwt
  - tech:sqlalchemy
milestone: MVP
qiita_article: true
qiita_theme: "Flaskでクイズ作成API（問題・選択肢ネスト登録）を実装する"
breaking_change: false
created_at: 2026-04-04
updated_at: 2026-04-04
---

## 概要
QuizVerse の中核機能として、認証済みユーザーがクイズ本体と設問・選択肢・正答を1リクエストで登録できる API を実装する。

## 背景
- ISSUE-0007 までで認証基盤（password / Google OAuth / OTP）は整備済み
- 次段の一覧・回答・ランキング実装前に、クイズデータを正しく作成できる登録基盤が必要
- 不整合データ（正答なし、複数正答、選択肢不足）を登録時点で防ぐ必要がある

## 対応範囲
- `POST /api/quizzes` を追加（JWT必須）
- クイズ本体（title/description）を保存
- 問題（questions）を保存
- 各問題の選択肢（choices）を保存
- 正答情報（`is_correct`）を保存
- 作成者を JWT のログインユーザーへ紐付け
- バリデーション実装
- トランザクションで一括保存し、失敗時ロールバック
- 正常系 / 異常系テスト追加
- README / docs / Qiita下書き更新

## 対応しないこと
- クイズ編集API / 削除API
- 公開制御（公開予約や権限拡張）
- クイズ一覧・検索API
- クイズ回答API
- ランキングAPI
- 画像付き問題や記述式など複雑形式

## 実装方針（MVP仮置き）
- 問題形式は選択式のみ
- 1問あたり選択肢数は `2〜6`
- 正答は単一選択のみ（各問題で `is_correct=true` はちょうど1件）
- 並び順は入力順を `sort_order` として保存
- クイズ `status` は `draft` 固定で作成（公開状態制御は次Issue）
- `category` / `difficulty` はモデル未定義のため次Issueで扱う

## タスク
- [x] quizzes API blueprint 追加
- [x] `POST /api/quizzes` 実装
- [x] ネストJSONバリデーション実装
- [x] クイズ・問題・選択肢の一括保存実装
- [x] JWTユーザー紐付け実装
- [x] テスト追加（正常系/異常系）
- [x] README / docs / Qiita更新
- [x] PR作成

## 受け入れ条件
- [x] 認証済みユーザーがクイズ作成できる
- [x] クイズ本体・問題・選択肢が保存される
- [x] 作成者がログインユーザーに紐付く
- [x] 不正入力は適切にエラーとなる
- [x] 正答ルール違反（正答なし/複数正答）を拒否できる
- [x] 正常系 / 異常系テストが追加されている
- [x] README と `docs/issues/ISSUE-0008.md` が更新されている
- [x] Qiita 下書きが追加されている

## リスク・懸念
- category/difficulty/publication などのメタ情報は次Issueでスキーマ拡張が必要
- SQLite テストと PostgreSQL 本番で制約評価順が異なる可能性あり
- 既知課題として `PYTHONPATH=. pytest` 前提は継続
