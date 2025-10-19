# インクリメンタル売上パイプライン
再実行安全（idempotent）な日次パイプライン。pandas + DuckDB による **データ品質チェック（5層）** を実装。
- **重複/欠損/外れ値/スキーマ/タイムゾーン** を検証
- CI（push + nightly）で常に緑、Markdown レポートを生成
- もう一つの OSS（JP Retail Medallion）→ https://github.com/TraderKAI619/project-a-jp-retail-pipeline
英語版: `README.md`
