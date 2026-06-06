# Anthropic Claude サブスクリプション分割：Agent SDK クレジット分離 6月15日施行

- URL: https://devtoolpicks.com/blog/anthropic-splits-claude-subscriptions-agent-sdk-credit-june-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-06

## 要約

2026年6月15日から施行されるAnthropicの課金変更を開発者視点で解説。従来はAgent SDK・`claude -p`使用がサブスクリプションの使用量プールから引かれていたが、6月15日以降は専用クレジットバランスから引き落とされる2バケット制へ移行。インタラクティブ使用（チャット・IDE）と自動化・エージェント使用が完全分離。各プランのクレジット割当量と超過時のAPI料金レートを表で整理。「自動化パイプラインが突然コストスパイクを起こす」移行期リスクへの対応として、ANTHROPIC_API_KEY確認・クレジット上限設定・使用量モニタリング設定のチェックリストを提供。Agent SDK組み込み済みの開発者・企業は2026年6月15日までに対応必須。
