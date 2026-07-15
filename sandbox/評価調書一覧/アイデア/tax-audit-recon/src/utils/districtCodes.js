export const DISTRICT_CODES = {
    0: "鶴見",
    10: "神奈川",
    20: "西",
    30: "中",
    40: "南",
    41: "港南",
    50: "保土ヶ谷",
    51: "旭",
    60: "磯子",
    70: "金沢",
    80: "港北",
    81: "緑",
    82: "青葉",
    83: "都筑",
    88: "泉",
    89: "栄",
    90: "戸塚",
    91: "瀬谷"
};

export const getDistrictName = (code) => {
    // 文字列の場合もあるので数値変換を試みる、またはそのままキーとして使う
    // CSVなどからは文字列として来ることが多い
    let parsedCode = parseInt(code, 10);
    if (isNaN(parsedCode)) {
        return code; // 数値変換できなければそのまま返す
    }
    return DISTRICT_CODES[parsedCode] || String(code);
};
