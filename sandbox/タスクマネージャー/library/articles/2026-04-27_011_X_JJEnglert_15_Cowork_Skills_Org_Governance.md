# Claude Coworkスキル15本を24時間で組織展開 — .skillファイル構造と承認ガバナンス設計

- URL: https://twitter.com/JJEnglert/status/2047764744845615608
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-27
- いいね: 17 / RT: 1 / リプライ: 0
- 投稿者: @JJEnglert / フォロワー 34,886

## 投稿内容
I created 15 @claudeai Cowork skills for my organization in the last 24 hours.

One thing I was quickly reminded of: Claude Code skills and Claude Cowork skills are packaged a little differently.

For Claude Cowork, the skill is packaged as a .skill file, which is essentially a zip file. Inside that package, I standardized each skill around a structure like this:

<Skill Name>/
├── SKILL.md
├── README.md
├── reference/
 │   ├── gotchas.md
 │   ├── <connector>-fields.md
 │   └── examples/
 │        └── *.md
└── scripts/

（省略）

The future of work is not just people using AI tools.

It is organizations building approved, reusable, versioned workflows that let AI operate safely inside the systems where work already happens.

## 要約
@JJEnglert（3.5万フォロワー）が24時間で組織向けCoworkスキル15本を構築した体験談（17いいね）。重要な技術的知見：①Claude Coworkのスキルは.skillファイル（zipベース）でパッケージング、Claude Codeスキルとは異なる。②標準構造：SKILL.md + README.md + reference/（gotchas.md・コネクタフィールド定義・事例）+ scripts/。③スキル管理用スキル3本（Create/Validate/Update）で組織内の作成・検証・更新を体系化。④QuickBooks・DocuSign・Square・PayPalなど10+のコネクタを接続。コネクタの深度や制限が実務の成否を左右するという洞察が重要。「スキルだけでなくコネクタと承認ガバナンスの整備が企業AIの鍵」という結論は、エンタープライズClaude活用の方向性を示す。
