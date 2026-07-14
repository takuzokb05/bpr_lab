# Claude Code Auto ModeがBedrock/Vertex AI/Foundryでデフォルト化：ガバナンスギャップと設定詳細

- URL: https://www.digitalapplied.com/blog/claude-code-auto-mode-bedrock-vertex-foundry-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-14

## 要約
DigitalAppliedによるv2.1.207 auto mode展開の実務的詳細分析（2026年7月13日）。実装詳細：`CLAUDE_CODE_ENABLE_AUTO_MODE`環境変数が不要に変更、対応モデルはSonnet 5・Opus 4.7・4.8の3種（エイリアス「sonnet」はBedrock/VertexでSonnet 4.5を指すため非対応が落とし穴）。重大ガバナンスギャップ：Anthropic管理コンソールの`disableAutoMode`設定がBedrock/Vertex/Foundryには届かない（管理コントロールの盲点）。無効化にはself-hostedゲートウェイかMDM/Windowsレジストリが必要。設定の落とし穴：`autoMode.environment`で`"$defaults"`を省略するとAnthropicデフォルト保護が全消去される。セキュリティクラシファイア：2段階評価（高速フィルタ→CoT推論）、連続3ブロックまたはセッション20ブロムで自動停止（閾値変更不可）。コンプライアンス基盤を理由に規制クラウドを選んだ組織にとって中央ポリシー制御が届かない逆説的状況が発生。
