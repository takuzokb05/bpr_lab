# Oracle、フロンティアAIが原因でセキュリティパッチを四半期→毎月に変更（2026年5月〜）

- URL: https://x.com/IntCyberDigest/status/2051374140578312649
- ソース: x
- 言語: en
- テーマ: ai-news
- 取得日: 2026-05-04
- いいね: 67 / RT: 8 / リプライ: 0
- 投稿者: @IntCyberDigest / フォロワー 145016

## 投稿内容
🚨 Frontier AI models are forcing Oracle to move from quarterly to monthly critical security patches.

Starting May 2026, Oracle will release a monthly Critical Security Patch Update for high-priority vulnerabilities, breaking with the quarterly cadence the company has used for nearly two decades. Quarterly Critical Patch Updates will continue, but they will now bundle the prior monthly them into one cumulative drop.

The reason Oracle gave is AI, it is changing how fast vulnerabilities are found and how fast they need to be patched. Oracle confirmed it is using Anthropic's Claude Mythos Preview and OpenAI's most capable models, accessed through Trusted Access for Cyber, to identify vulnerabilities across Oracle-developed software, Oracle Health, and the open-source components built into their products.

This is the same trend that surfaced last week with Theori's Xint Code finding the Copy Fail kernel bug after about one hour of AI scan time. Defenders are now finding bugs faster than the old patch cycles can deliver them.

Summarized:
🔴 Oracle has historically been one of the slowest of the major vendors to ship security fixes. Critical bugs disclosed early in a quarter could sit unpatched for up to three months...
🔴 Adobe and Microsoft have been on monthly cycles for years. Oracle was the holdout
🔴 Oracle still acknowledges the same problem at every patch round: customers who got breached because they did not install available updates
🔴 The CSPU patches are smaller and more targeted, which Oracle says will make them easier to apply quickly

What this means for defenders:
🔴 If you run on-premises Oracle, get ready for monthly patch nights instead of quarterly ones
🔴 Plan testing pipelines that can validate small, targeted patches in days, not weeks
🔴 The old "we patch quarterly" risk model is officially obsolete across most of the industry

AI-assisted vulnerability research is now a permanent fixture in the stack, and the bugs it finds do not wait for the next quarterly window.

## 要約
@IntCyberDigest（フォロワー14.5万）が報告。閲覧6994、いいね67。Oracleが2026年5月から重大なセキュリティ脆弱性に対して毎月のCritical Security Patch Updateを発行する方針に変更。従来の四半期サイクルから月次へ切り替えた主な原因がフロンティアAIモデルによる高優先度脆弱性の発見頻度増加。AIモデルがセキュリティ研究・脆弱性発見を加速させ、企業のセキュリティ対応サイクルそのものを変える現実を示すデータポイント。
