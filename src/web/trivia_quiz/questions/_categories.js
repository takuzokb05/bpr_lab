/*
 * 問題データの土台
 * ----------------------------------------------------------------------
 * 読み込み順：このファイル → 各カテゴリファイル(it.js / life.js / culture.js)
 *            → index.html 内の本体スクリプト
 *
 * 新しいカテゴリを足すときは
 *   1) CATEGORIES にキーを追加
 *   2) questions/<キー>.js を作って addQuestions("<キー>", [...]) で登録
 *   3) index.html の <script src="questions/<キー>.js"> を1行足す
 */

const CATEGORIES = {
  it: { label: "IT・デジタル", emoji: "💻" },
  life: { label: "日常お役立ち", emoji: "💰" },
  culture: { label: "教養・一般常識", emoji: "📚" },
  health: { label: "健康・からだ", emoji: "🩺" },
  law: { label: "くらしと法律", emoji: "⚖️" },
  business: { label: "仕事・ビジネス", emoji: "💼" },
  nature: { label: "自然・防災", emoji: "🌏" },
};

// 全問題がここに集まる
const QUIZ_DATA = [];

/*
 * カテゴリ単位で問題を登録するヘルパー。
 * 各問に category を自動付与するので、問題側で category を書く必要はない。
 *
 * 1問の形:
 *   {
 *     qual: "ITパスポート",   // この知識が役立つ代表的な資格名（ラベル表示用）
 *     question: "問題文",
 *     choices: ["選1", "選2", "選3", "選4"],
 *     answer: 0,              // 正解の番号（0始まり）
 *     explanation: {
 *       conclusion: "結論", why: "なぜ", useful: "こう役立つ",
 *       trivia: "おまけ（任意）"
 *     }
 *     // id は本体スクリプトが問題文から自動生成するので不要
 *   }
 */
function addQuestions(category, items) {
  items.forEach((item) => {
    item.category = category;
    QUIZ_DATA.push(item);
  });
}
