# QuizVerse Roadmap (2026-04-01)

## Epic / Feature / Task 再分解

### EPIC-INFRA
- Feature: Docker開発基盤
  - Task: compose定義、env整理、ヘルスチェック
- Feature: DBマイグレーション基盤
  - Task: Flask-Migrate導入、初期migration

### EPIC-AUTH
- Feature: JWT認証
  - Task: signup/login API、トークン発行
- Feature: Google OAuth
  - Task: OAuth callback/API連携
- Feature: OTP認証
  - Task: メール/電話OTP送信・検証

### EPIC-QUIZ
- Feature: クイズCRUD
- Feature: クイズ回答とスコア計算
- Feature: ランキング

### EPIC-FRONTEND
- Feature: 認証UI
- Feature: クイズ一覧/作成/プレイUI
- Feature: 共通レイアウトと状態管理

### EPIC-ADMIN
- Feature: 管理ダッシュボード
- Feature: メール設定
- Feature: サービス状況

### EPIC-ATTENDANCE
- Feature: 勤怠集計API
- Feature: ダッシュボードグラフ

### EPIC-DOCS
- Feature: API仕様/README/Qiita運用

---

## MVP優先Issue一覧（優先順）

1. ISSUE-0001 [feat] MVP開発基盤（Docker + Flask + React + PostgreSQL）
2. ISSUE-0002 [feat] Flask-Migrate導入と初期スキーマ作成
3. ISSUE-0003 [feat] ユーザーサインアップ/ログインJWT API
4. ISSUE-0004 [feat] 認証フロント画面（signup/login）
5. ISSUE-0005 [feat] Google OAuthログイン基盤
6. ISSUE-0006 [feat] メールOTP認証API
7. ISSUE-0007 [feat] クイズ作成API/モデル
8. ISSUE-0008 [feat] クイズ一覧・検索API
9. ISSUE-0009 [feat] クイズ回答APIとスコア計算
10. ISSUE-0010 [feat] ランキングAPI
11. ISSUE-0011 [feat] クイズUI（作成/一覧/回答）
12. ISSUE-0012 [feat] ランキングUI
13. ISSUE-0013 [feat] 管理ダッシュボード初期画面
14. ISSUE-0014 [feat] 利用規約/ライセンス画面
15. ISSUE-0015 [docs] MVP API仕様と運用手順整備
