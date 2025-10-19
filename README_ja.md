# インクリメンタル売上パイプライン

**冪等（idempotent）な日次インクリメンタル・パイプライン。**  
pandas + DuckDB による **データ品質チェック（5層）** を実装。

- **検証範囲（5層）**：重複／欠損／外れ値／スキーマ／タイムゾーン
- **CI**（push + nightly）で常にグリーン、Markdown レポートを自動生成
- 関連 OSS（JP Retail Medallion）→ <https://github.com/TraderKAI619/project-a-jp-retail-pipeline>  
- **英語版 README** → [README.md](./README.md)

**最新のメトリクス／レポート（Artifacts）**：  
<https://github.com/TraderKAI619/incremental-sales-pipeline/actions/workflows/ci.yml?query=branch%3Amain>

---

## 品質メトリクス（最終実行: 2025-10-20）
- **Pass**：95.2%（772/811）  
- **Quarantine**：4.8%（39, 理由は [こちら](./data/silver/quarantine/README.md)）  
- **Gold 出力**：fact_sales 261 行 + fact_returns 11 行  
- **アラート閾値**：Quarantine 25% 超で通知

> 図表・詳細は英語版 README の「Architecture / Performance Snapshot」を参照してください。
