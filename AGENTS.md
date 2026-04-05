# AGENTS.md（QuizVerse リポジトリ運用ルール）

## 1. このリポジトリの目的
- 本リポジトリは **QuizVerse（クイズ作成・プレイ・ランキング基盤）** の継続開発を目的とする。
- 読者は **開発者 / Codex / AI エージェント** を想定し、同じ品質・同じ判断基準で実装できる状態を維持する。
- 実装だけでなく、テスト・ドキュメント・Issue/PR 運用を含めて一貫性を保つ。

## 2. 技術スタック
- Frontend: React.js + Tailwind CSS + Vite
- Backend: Flask（App Factory Pattern + Blueprint）
- DB: PostgreSQL（本番想定）
- ORM: SQLAlchemy
- Auth: Flask-JWT-Extended + Google OAuth + OTP
- 開発環境: Windows + Docker（Docker Compose で再現可能であること）

## 3. リポジトリ構成の考え方
- `frontend/`: React + Tailwind の UI 実装。
- `backend/`: Flask API 実装。
- `backend/app/`: App Factory / extensions / config / models / api を責務分離して配置。
- `backend/migrations/`: Alembic マイグレーション履歴。
- `backend/tests/`: backend の pytest テスト。
- `docs/issues/`: Issue ごとの仕様・背景・完了条件。
- `docs/schema/`: DB スキーマ仕様。
- `docs/qiita/`: 外部公開前提の技術解説下書き。
- `README.md`: セットアップ・利用方法・公開 API の入口。

## 4. 開発フロー
1. Issue を作成（目的・背景・完了条件を明記）
2. ブランチ作成（1 Issue = 1 ブランチ）
3. 実装（1 ブランチ = 1 目的を維持）
4. テスト（実行コマンドと結果を記録）
5. コミット（日本語メッセージ）
6. プッシュ
7. PR 作成（日本語タイトル・日本語本文）
8. レビュー後に main へマージ
9. 対応 Issue をクローズ

## 5. Issue / Branch / Commit / PR / Merge のルール

### Issue
- **Issue ベースで開発すること**。
- **Issue がない状態で実装を始めないこと**。
- 仕様が曖昧な場合は、Issue に「仮置き」と明記してから着手する。

### Branch
- 原則: **1 Issue = 1 ブランチ = 1 目的**。
- 無関係な変更を同一ブランチに混在させない。

### Commit
- **コミットメッセージは日本語で書くこと**。
- 意味のある粒度で分割し、レビュー可能性を優先する。
- 先頭プレフィックス例:
  - `feat:`
  - `fix:`
  - `refactor:`
  - `docs:`
  - `test:`
  - `chore:`
- 例:
  - `feat: クイズ一覧APIを追加`
  - `fix: JWTエラー時のレスポンス形式を修正`
  - `docs: READMEにローカル起動手順を追記`

### PR
- **PRタイトルは日本語を基本とする**。
- **PR本文は日本語で書くこと**。
- PR 本文の推奨構成:
  - 背景
  - 変更内容
  - 確認内容
  - 補足
- 実行できなかったテスト・環境制約（ネットワーク/プロキシ/依存解決失敗等）は隠さず記載する。
- 「コード上妥当」と「実行確認済み」は分けて書く。

### Merge
- レビュー指摘の解消と、チェックリスト充足を確認してからマージする。
- マージ時に対応 Issue を明示し、クローズ漏れを防ぐ。

## 6. 実装時の基本方針
- 設定値はハードコードしない（環境変数または設定層で管理）。
- セキュリティ・運用・保守の観点を省略しない。
- 不明点は勝手に確定しすぎず、**「仮置き仕様」** と明記する。
- 一般ユーザー向け API と 管理用/開発用 API を混同しない。
- 既存の命名・責務分離・レスポンス形式との整合性を優先する。

## 7. バックエンド実装ルール
- Flask は **App Factory Pattern** を前提とする。
- ルーティングは **Blueprint** 単位で分離する。
- `extensions` / `config` / `models` / `api` の責務を混在させない。
- SQLAlchemy モデル変更時は、マイグレーション・スキーマ文書・関連テストをセットで更新する。
- API エラー形式は既存仕様に合わせる（status code・error code・message の整合性）。
- 一般向け API では正答情報を不用意に返さない（例: クイズ詳細 API で正解を直接返却しない）。

## 8. フロントエンド実装ルール
- React コンポーネントは **画面単位 + 機能単位** で分割する。
- UI 実装は Tailwind CSS を前提とし、独自 CSS の乱立を避ける。
- API 連携時は、読み込み中・空状態・エラー状態を明示的に扱う。
- 認証付き画面では JWT の有無/期限切れ時の遷移を考慮する。

## 9. DB / マイグレーション運用ルール
- 本番 DB は PostgreSQL 前提で設計する。
- ローカル/CI で SQLite を使う場合、型・制約・トランザクション差異を意識して検証する。
- migration を伴う変更時は以下を必須とする:
  - `backend/migrations` の更新
  - `docs/schema` の更新
  - 影響 API の仕様更新（必要時）

## 10. 認証 / セキュリティ方針
- JWT / OAuth / OTP は既存方針に沿って拡張する。
- 開発用暫定実装（dev-token 等）と本番前提実装を明確に区別する。
- `AUTH_ENABLE_DEV_TOKEN_ENDPOINT` は本番で `false` 推奨（明示設定）。
- 秘密情報（JWT secret, OAuth client secret, DB 接続情報等）は必ず環境変数管理する。
- ログ/レスポンスに機微情報（トークン、認証コード、正答、個人情報）を過剰に出さない。

## 11. テスト方針
- backend テストの基本コマンド:
  - `cd backend && PYTHONPATH=. pytest`
- 既知課題:
  - `cd backend && pytest` は環境により `ModuleNotFoundError: No module named 'app'` になる場合がある。
- 外部依存（Python/pip/Docker/ネットワーク/プロキシ）で実行不能な場合は、失敗理由を記録する。
- テスト結果は以下を分けて記述:
  - 実行確認済み（実コマンドと結果）
  - コード上妥当（未実行だが妥当と判断した理由）
- 実行できないコマンドを「成功した」と扱わない。

## 12. ドキュメント更新方針
- 新 API 追加・変更時は `README.md` と `docs/issues` を更新する。
- migration を含む変更時は `docs/schema` を更新する。
- 実装背景・設計判断・注意点は `docs/issues` または `docs/qiita` に残す。
- Qiita 記事化を前提に、再利用可能な説明（背景・比較・採用理由）を記録する。
- README / docs / API仕様 / Issue / Qiita 下書きの整合性を常に保つ。

## 13. 禁止事項 / 注意事項
- Issue なしで実装を開始しない。
- ハードコードした秘密情報をコミットしない。
- 管理用 API / 開発用 API を一般公開 API と同列に扱わない。
- テスト未実施を隠蔽しない。
- 暫定実装を本番仕様として確定扱いしない。
- 既知制約（PYTHONPATH 依存、ネットワーク制約等）を無視して手順化しない。

## 14. Codex / AI エージェント向けの行動指針
- 着手前に確認すること:
  - 対応 Issue
  - 関連 `docs/issues`
  - 影響範囲（backend/frontend/schema/auth）
- 変更時に必ず確認・更新すること:
  - コード
  - テスト
  - README
  - `docs/issues`
  - `docs/schema`（DB変更時）
  - `docs/qiita`（背景整理が必要な変更時）
- 出力時の原則:
  - 仮置き判断は「仮置き」と明記
  - 未実行項目は理由付きで明記
  - セキュリティ影響を省略しない

## 15. 変更前チェックリスト
- [ ] 対応 Issue が存在する
- [ ] 目的と完了条件を Issue で確認した
- [ ] 影響範囲（API / DB / Auth / UI）を整理した
- [ ] 既存 docs（README / docs/issues / docs/schema）を確認した
- [ ] 本番影響（セキュリティ・運用）を確認した

## 16. PR前チェックリスト
- [ ] 変更内容が Issue の目的と一致している
- [ ] テストを実行し、結果を記録した（未実行は理由を記載）
- [ ] 新規/変更 API の README 反映が完了している
- [ ] `docs/issues` を更新済み
- [ ] DB変更がある場合 `docs/schema` を更新済み
- [ ] 仮置き仕様を PR 本文と docs に明記した
- [ ] PR タイトル・本文が日本語になっている
- [ ] PR 本文に「背景 / 変更内容 / 確認内容 / 補足」を含めた

## 17. マージ前チェックリスト
- [ ] レビュー指摘を解消した
- [ ] CI/ローカル確認結果を共有した
- [ ] 開発用機能（例: dev-token）の本番設定を確認した
- [ ] ドキュメント整合性（README / docs/issues / docs/schema / docs/qiita）を確認した
- [ ] 対応 Issue のクローズ準備ができている
