# がんばるリスト (Home Hero)

妻の日常タスク消化を「義務」から「癒やしと達成感」に変える、心理学に基づいたToDoアプリ。

## 🧠 コンセプト & 心理学機能

UX心理学のナレッジベースに基づき、以下の動機づけ設計を行っています。

*   **変動報酬 (Variable Reward)**: タスク完了時、確率で演出が変化（60%小/30%中/10%ジャックポット）。「次はどうなる？」という期待感でドーパミンを刺激します。
*   **付与された進捗 (Endowed Progress)**: 毎日「今日の私、起きてえらい！」というタスクが自動生成され、最初から完了状態でスタート。「0からのスタート」を防ぎます。
*   **損失回避 (Loss Aversion)**: LocalStorageへのデータ永続化（※）により、積み上げた努力を可視化します。
*   **Fitts's Law (フィッツの法則)**: モバイルでの操作性を考慮し、ボタンや入力欄を大きく配置し、誤操作を防ぐレイアウト（入力とボタンの分離）を採用しています。

*(※) データはブラウザのLocalStorageに保存されます。PCとスマホでデータは同期されません。*

## 🛠 技術スタック

*   **Frontend**: React 19, TypeScript
*   **Build Tool**: Vite
*   **Styling**: Tailwind CSS (v4), PostCSS
*   **Animation**: Framer Motion, canvas-confetti
*   **Icons**: Lucide React
*   **Font**: Zen Maru Gothic (Google Fonts)

## 🚀 起動方法

### 開発サーバーの起動

```bash
# 依存関係のインストール
npm install

# サーバー起動 (PCのみ)
npm run dev

# サーバー起動 (スマホからアクセスする場合)
npm run dev -- --host
```

スマホからアクセスする場合:
1. PCとスマホを同じWi-Fiに接続する。
2. コマンド実行後に表示される `Network: http://192.168.x.x:5173/` のURLをスマホのブラウザに入力する。

## 📁 ディレクトリ構成

*   `src/App.tsx`: アプリケーションのメインロジック（心理学演出、データ永続化など）
*   `src/types.ts`: TypeScript型定義
*   `src/index.css`: Tailwind CSS設定とフォント定義
