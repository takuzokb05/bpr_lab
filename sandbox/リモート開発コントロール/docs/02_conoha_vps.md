## ConoHa Windows Server のスペック・料金・MT5/Claude Code同居可能性

調査日: 2026-03-03

---

### 主要な発見

1. **ConoHa for Windows Server の料金プラン一覧（2026年3月時点）**
   - 要点: 初期費用無料・最低利用期間なし。時間課金と「まとめトク」（長期割引、最大10%OFF）の2体系。Windows Server 2016/2019/2022/2025 Datacenter Edition 対応
   - データ/数字:

   | プラン | メモリ | CPU | SSD | 月額（税込・1ヶ月契約） |
   |--------|--------|-----|-----|------------------------|
   | WIN1GB | 1 GB | 2コア | 100 GB | 約1,392円 |
   | WIN2GB | 2 GB | 3コア | 100 GB | 約2,715円 |
   | WIN4GB | 4 GB | 4コア | 100 GB | 約5,288円 |
   | WIN8GB | 8 GB | 6コア | 100 GB | 約9,196円 |
   | WIN16GB | 16 GB | 8コア | 100 GB | 約19,832円 |
   | WIN32GB | 32 GB | 12コア | 100 GB | 約40,354円 |
   | WIN64GB | 64 GB | 24コア | 100 GB | 約82,099円 |

   ※ まとめトク（長期契約）で最大10%OFF。キャンペーン適用で月額1,077円〜の場合もあり
   ※ 料金は変動する可能性あり。最新は [公式料金ページ](https://vps.conoha.jp/windows/pricing/) を参照

   - ソース: [ConoHa for Windows Server 料金](https://vps.conoha.jp/windows/pricing/), [SERVERSUS ConoHa比較](https://www.serversus.work/services/conoha-for-windows-server/)

2. **MT5 の最小動作要件**
   - 要点:
     - **最小**: CPU 1 GHz、RAM 2 GB（Windows Server 2016以降）
     - **実用**: CPU 2コア、RAM 2 GB 以上推奨
     - **実測**: MT5 単体の消費メモリは約 100 MB。EA 付きで 1.5 GB あれば余裕
     - **複数インスタンス**: 3台のMT5 + EA でも 1.5 GB で問題なし
   - データ/数字: MT5 単体 ≈ 100 MB RAM、Windows Server 2025 の OS 自体で約 1-1.5 GB 使用
   - ソース: [カゴヤ MT5 VPS ガイド](https://www.kagoya.jp/howto/cloud/vps/mt5/), [VPS Specifications for MT5](https://www.vpsforextrader.com/blog/vps-specifications-for-metatrader-5/), [HostStage MT5 VPS Setup](https://www.host-stage.net/case-study/forex/mt4-mt5-vps-setup-guide/)

3. **Claude Code の動作要件**
   - 要点:
     - **最小**: RAM 4 GB、ストレージ 10 GB
     - **推奨**: RAM 8 GB 以上、マルチコアプロセッサ
     - **ランタイム**: Node.js 18+（ネイティブインストーラー使用時は不要）
     - **CLI 自体**: インストールサイズ 100 MB 未満と軽量
     - **注意**: Claude Code は API 呼び出し型であり、ローカルで LLM を動かすわけではない。リモート API への接続が主な負荷
   - データ/数字: CLI 本体 < 100 MB、実行時は API 通信のため CPU/RAM 負荷は軽微
   - ソース: [Claude Code Docs - Setup](https://code.claude.com/docs/en/setup), [Claude Code CLI Hardware Requirements](https://www.claudedirectory.co/blog/claude-code-cli-hardware-requirements)

4. **OpenClaw の動作要件**
   - 要点:
     - **最小**: 2 vCPU、4 GB RAM、40 GB SSD
     - **推奨**（ブラウザ自動化あり）: 4 vCPU、8 GB RAM、80 GB NVMe SSD
     - **OpenClaw 本体**: 300-500 MB RAM
     - **Chromium（ブラウザ自動化）**: 2-4 GB RAM（負荷時）
     - **Docker オーバーヘッド**: 500 MB - 1 GB
     - **Docker イメージ**: 2-4 GB（ブラウザ自動化込みで 6-8 GB）
     - **OS**: Ubuntu 22.04 / Debian 12 推奨。Windows は WSL2 経由
   - データ/数字: 本体 300-500 MB + Chromium 2-4 GB + Docker 0.5-1 GB = 最大約 5.5 GB
   - ソース: [OpenClaw Hardware Requirements - Boostedhost](https://boostedhost.com/blog/en/openclaw-hardware-requirements/), [OpenClaw Server Requirements - clawtrust.ai](https://clawtrust.ai/blog/openclaw-server-requirements)

5. **3つ（MT5 + Claude Code + OpenClaw）の同居に必要な最小スペック**
   - 要点:

   **メモリ積算（ブラウザ自動化なし）:**

   | コンポーネント | メモリ使用量 |
   |---------------|-------------|
   | Windows Server 2025 OS | 1.0 - 1.5 GB |
   | MT5 + EA（1インスタンス） | 0.1 - 0.3 GB |
   | Claude Code CLI | 0.1 - 0.3 GB |
   | WSL2 + OpenClaw（ブラウザなし） | 1.5 - 2.5 GB |
   | バッファ | 0.5 - 1.0 GB |
   | **合計** | **3.2 - 5.6 GB** |

   **メモリ積算（ブラウザ自動化あり）:**

   | コンポーネント | メモリ使用量 |
   |---------------|-------------|
   | Windows Server 2025 OS | 1.0 - 1.5 GB |
   | MT5 + EA（1インスタンス） | 0.1 - 0.3 GB |
   | Claude Code CLI | 0.1 - 0.3 GB |
   | WSL2 + OpenClaw + Chromium | 3.5 - 5.5 GB |
   | バッファ | 1.0 - 1.5 GB |
   | **合計** | **5.7 - 9.1 GB** |

   **推奨プラン:**
   - **最小構成（ブラウザ自動化なし）**: WIN4GB（4 GB / 4コア / 100 GB）= 月額約5,288円
     - ギリギリの運用。メモリスワップが頻発する可能性あり
   - **推奨構成**: **WIN8GB（8 GB / 6コア / 100 GB）= 月額約9,196円**
     - ブラウザ自動化なしなら余裕あり。ブラウザ自動化ありでもギリギリ運用可能
   - **安全構成（ブラウザ自動化あり）**: WIN16GB（16 GB / 8コア / 100 GB）= 月額約19,832円
     - 全機能を余裕を持って運用可能

   **ストレージ考慮:**
   - 全プラン共通 SSD 100 GB
   - Windows OS ≈ 20 GB + WSL2 ≈ 2-5 GB + OpenClaw Docker ≈ 6-8 GB + MT5 ≈ 1 GB + Claude Code ≈ 0.1 GB = 約30-35 GB
   - 残り約65 GB はデータ・ログに使用可能。十分

   **CPU 考慮:**
   - MT5 は軽負荷（1コア以下）
   - Claude Code は API 通信主体で軽負荷
   - OpenClaw は 2-4 コア推奨
   - WIN8GB の 6コアなら十分

   - ソース: 上記の各コンポーネント要件から積算

6. **代替 VPS サービスとの比較（参考）**
   - 要点:

   | サービス | 最安プラン（Windows） | メモリ | CPU | SSD | 月額（税込目安） | 特記 |
   |---------|---------------------|--------|-----|-----|----------------|------|
   | **ConoHa for Windows** | WIN8GB | 8 GB | 6コア | 100 GB | 約9,196円 | 同居推奨プラン |
   | **ABLENET VPS** | Win2（参考） | 3.5 GB | 3コア | 60-120 GB | 約2,800-3,200円 + ライセンス1,250円 | 大阪DC、220Gbps回線。メモリ増量キャンペーンあり |
   | **お名前.com デスクトップクラウド** | Premium 8GB | 8 GB | - | - | 約4,000-6,000円 | FX自動売買特化。MT4プリインストール。稼働率99.99% |
   | **さくら VPS** | Windows対応プラン | 2-8 GB | 2-6コア | 50-400 GB | 約2,000-8,000円 | Linux VPS が主力。Windows は限定的 |

   **補足:**
   - お名前.com デスクトップクラウドは FX 自動売買に特化しており、MT4/MT5 がプリインストール済みで即利用可能。ただし OpenClaw や Claude Code の同居には汎用 VPS の方が柔軟
   - ABLENET は全プランにライセンス費用 1,250円/月が別途必要
   - 各社キャンペーンで料金が大幅に変動するため、契約時に最新情報を確認すべき

   - ソース: [FXキーストン VPS ランキング](https://www.fxnav.net/mt4-mt5-fxvps/), [ABLENET VPS](https://www.ablenet.jp/vps/), [お名前.com デスクトップクラウド](https://www.onamae-desktop.com/spec/), [streamrental ConoHa解説](https://streamrental.com/conoha-for-windows-server/)

---

### 同居構成の結論

| 項目 | 判定 |
|------|------|
| MT5 単体（現在の用途） | WIN1GB-2GB で十分 |
| MT5 + Claude Code | WIN2GB で動作可能（Claude Code は API 通信主体で軽量） |
| MT5 + Claude Code + OpenClaw（ブラウザなし） | **WIN8GB を推奨**（WIN4GB は最小限） |
| MT5 + Claude Code + OpenClaw（ブラウザあり） | WIN8GB〜WIN16GB（安全を取るなら16GB） |

**コスト最適化の観点:**
- 段階的にスケールアップするのが賢明。ConoHa はプラン変更が可能
- まず WIN4GB（約5,288円/月）で OpenClaw をブラウザ自動化なしで試し、不足を感じたら WIN8GB に変更
- OpenClaw を Docker ではなくネイティブ WSL2 で動かせばメモリ節約になる可能性あり

---

### 情報の信頼性評価

- 一次ソース（公式サイト・公式ドキュメント）: 6件
  - ConoHa 公式料金ページ、ABLENET 公式、お名前.com 公式
  - Claude Code 公式ドキュメント、OpenClaw 公式ドキュメント
- 二次ソース（比較サイト・テックメディア）: 7件
  - FXキーストン、SERVERSUS、streamrental、カゴヤ等
- 注意が必要な情報:
  - 料金は頻繁にキャンペーンで変動する。特に ConoHa は「まとめトク」と時間課金で大きく異なる
  - メモリ積算は理論値。実際の消費量は使用パターンにより変動する
  - OpenClaw の Windows (WSL2) 上での安定性は公式でも「強く推奨」だが完全保証ではない
  - Claude Code のメモリ消費は API 呼び出し型のため軽量だが、大規模プロジェクトのインデックス作成時は一時的に増加する可能性

---

### ソース一覧

1. [ConoHa for Windows Server 料金](https://vps.conoha.jp/windows/pricing/) - 公式
2. [ConoHa for Windows Server トップ](https://vps.conoha.jp/windows/) - 公式
3. [SERVERSUS ConoHa for Windows Server 比較](https://www.serversus.work/services/conoha-for-windows-server/) - 比較サイト
4. [ConoHa for Windows Server プラン体験記](https://relax-tech.net/conoha-vps-for-windows-server/) - レビュー
5. [streamrental ConoHa 解説](https://streamrental.com/conoha-for-windows-server/) - 解説サイト
6. [カゴヤ MT5 VPS ガイド](https://www.kagoya.jp/howto/cloud/vps/mt5/) - VPS 活用ガイド
7. [VPS Specifications for MT5](https://www.vpsforextrader.com/blog/vps-specifications-for-metatrader-5/) - MT5要件
8. [HostStage MT5 VPS Setup Guide](https://www.host-stage.net/case-study/forex/mt4-mt5-vps-setup-guide/) - セットアップガイド
9. [Claude Code Docs - Setup](https://code.claude.com/docs/en/setup) - 公式ドキュメント
10. [Claude Code CLI Hardware Requirements](https://www.claudedirectory.co/blog/claude-code-cli-hardware-requirements) - 要件まとめ
11. [OpenClaw Hardware Requirements - Boostedhost](https://boostedhost.com/blog/en/openclaw-hardware-requirements/) - 要件まとめ
12. [OpenClaw Server Requirements - clawtrust.ai](https://clawtrust.ai/blog/openclaw-server-requirements) - サーバー要件
13. [FXキーストン MT4/MT5 VPS ランキング](https://www.fxnav.net/mt4-mt5-fxvps/) - 比較ランキング
14. [ABLENET VPS](https://www.ablenet.jp/vps/) - 公式
15. [お名前.com デスクトップクラウド スペック](https://www.onamae-desktop.com/spec/) - 公式
16. [FX自動売買VPS比較 - streamrental](https://streamrental.com/fxvps-vpdhikaku/) - 比較サイト
