# Claude Code Auto ModeがBedrock/Vertex AI/Foundryでデフォルト有効—ガバナンスギャップに注意

- URL: https://www.digitalapplied.com/blog/claude-code-auto-mode-bedrock-vertex-foundry-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-14

## 要約
DigitalAppliedによるv2.1.207 auto mode展開の詳細分析。重要発見：Bedrockでの「sonnet」エイリアスはまだSonnet 4.5を指しており（非対応）、「opus」エイリアスはFoundryで4.6を指す（非対応）。ガバナンスギャップ：Anthropic管理コンソールのdisableAutoMode設定はBedrock/Vertex/Foundryに届かず、組織はself-hosted Claude appsゲートウェイまたはMDM/Windowsレジストリでのローカル設定が必要。autoMode.environmentに信頼ドメインを設定しない場合「$defaults」の省略でAnthropicのデフォルト保護が消える危険性。セキュリティクラシファイア：2段階評価（高速フィルタ+CoT推論）、連続3ブロックまたはセッション20ブロックで自動停止（変更不可）。規制クラウド利用者には影響大きいコンプライアンス課題。
