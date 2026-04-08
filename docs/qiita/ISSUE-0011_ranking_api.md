# Flask + SQLAlchemyでランキングAPI（総合 / クイズ単位）を実装する

## 概要
QuizVerse のMVPとして、`quiz_plays` を都度集計してランキングを返すAPIを実装した。

- `GET /api/rankings`: 総合ランキング
- `GET /api/quizzes/{quiz_id}/rankings`: クイズ単位ランキング

本記事では、同点ルール・ベストスコア採用方針・ページング設計を中心に整理する。

## 背景
ISSUE-0010 で回答送信と採点、プレイ履歴保存ができるようになったため、次の価値提供として「結果の可視化」が必要になった。
ランキングは継続利用に直結するため、MVP段階で最小構成を先に実装する。

## 実装内容

### 1. ランキングのデータソース
`quiz_plays` を利用し、`status=submitted` のレコードのみ集計対象とした。

### 2. クイズ単位ランキングの定義
- 単位: 1 quiz
- 採用レコード: **ユーザーごとのベストプレイ1件**
- ソート: `score desc` → `correct_count desc` → `played_at asc` → `play_id asc`

同一ユーザーの複数プレイがある場合でも、ランキング表示にはベストのみ採用する。

### 3. 総合ランキングの定義（仮置き）
- 単位: 全クイズ横断
- 集計方法: **ユーザー×クイズのベストスコアを合算**
- ソート: `total_score desc` → `total_correct_count desc` → `first_played_at asc` → `user_id asc`

この定義により、同じクイズを繰り返しプレイした回数ではなく、到達した成果を評価しやすくなる。

### 4. 表示名と個人情報
ランキングレスポンスには email を含めない。
表示名は `display_name` を優先し、未設定時は `user-{id}` のマスク値を返す。

### 5. ページング
`page`, `per_page` を受け付け、`pagination` に `total` / `total_pages` を返す。

## 注意点
- MVPでは都度集計のため、データ増加時にSQL最適化やsnapshot導入が必要
- SQLiteとPostgreSQLでWindow関数の挙動差異を確認する
- 同点ルールはフロント表示仕様と必ず同期する

## 次回
- `leaderboard_snapshots` を使った事前集計
- 期間別（週次 / 月次）ランキング
- プロフィール画面へのランキング埋め込み
