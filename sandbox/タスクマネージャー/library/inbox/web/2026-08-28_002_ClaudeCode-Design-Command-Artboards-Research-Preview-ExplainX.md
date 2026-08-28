# Claude Code /design コマンド詳解：UIアートボード生成の仕組みと制限

- URL: https://www.explainx.ai/blog/claude-code-design-command-artboards-research-preview-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-28

## 要約

Claude Code の `/design` コマンド（research preview）の詳細解説記事。

**動作フロー（5ステップ）**:
1. `/design <feature>` で意図を記述
2. 複数のartboardをArtifactsランタイム上にレンダリング
3. ユーザーが好みの案を選択（再生成不要）
4. WYSIWYG形式でインライン編集
5. 同じセッション内でコードベースへの実装を依頼

**主な特徴**:
- デザイン探索をコーディングセッション内に統合（タブ切り替え不要）
- claude.ai/designとターミナルの往復を排除
- ArtifactsインフラによるLive Rendering
- Pro/Max/Team/Enterprise対応

**実用的なユースケース**: 実装フェーズに入ったセッションで素早くUIプロトタイプが必要な場面に最適。ステークホルダー向けの設計書作成や、全画面設計レビューには向かない。

**重要な制限**:
- **トークン消費が大きい**: 複数artboardの生成はコンテキストを消費する
- **既存デザインシステムとの整合性**: 既存コンポーネントライブラリの自動継承は未確認
- **Research Preview**: 今後の仕様変更・rough edgeが予想される

**位置づけ**: 従来パワーユーザーが手動で組み合わせていたワークフロー（designで案出し→codeで実装）を1コマンドに統合したもの。CLI・Claude Code Desktopの両方で利用可能。
