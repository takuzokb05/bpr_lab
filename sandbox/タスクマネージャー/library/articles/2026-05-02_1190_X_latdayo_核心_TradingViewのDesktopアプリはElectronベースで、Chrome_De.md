# ■ 核心 TradingViewのDesktopアプリはElectronベースで、Chrome DevTools Protocol経由でClaude Codeが

- URL: https://x.com/latdayo/status/2050679893042569241
- ソース: x
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-02
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @latdayo / フォロワー 577

## 投稿内容
■ 核心
TradingViewのDesktopアプリはElectronベースで、Chrome DevTools Protocol経由でClaude Codeがチャートの生データにアクセスする。画像認識じゃなくコードレベルで全ローソク足・ティック・インジケーターを読み取る仕組み

■ 主要機能
・リアルタイムOHLC/価格/出来高の取得
・Pine Scriptの自動生成・デバッグ・反復改善
・RSI+移動平均線等のテクニカル戦略を自然言語で構築
・取引所APIと接続して自動売買にも対応

■ 利用方法
1. TradingView Desktopを --remote-debugging-port=9222 で起動
2. tradingview-mcpをgit clone
3. Claude Codeにmcp addで接続
4. あとは自然言語でチャート分析を指示するだけ

■ 背景
AIトレーディングには専門的なAPI連携が必要だった。MCP経由でTradingViewに直接繋がることで、コード書けない個人投資家でもAIトレーディングの入口に立てるようになった。GitHub: https://t.co/9j74ihSCpK

## 要約
■ 核心
TradingViewのDesktopアプリはElectronベースで、Chrome DevTools Protocol経由でClaude Codeがチャートの生データにアクセスする。画像認識じゃなくコードレベルで全ローソク足・ティック・インジケーターを読み取る仕組み

■ 主要機能
・リアルタイムOHLC/価格/出来高の取得
・Pine Scriptの自動生成・デバッグ・反復改善
・RSI+移動平均線等のテクニカル戦略を自然言語で構築
・取引所APIと接続して自動売買にも対応

■ 利用方法
1. TradingView Desktopを --remote-debugging-po

関連URL: https://github.com/tradesdontlie/tradingview-mcp
