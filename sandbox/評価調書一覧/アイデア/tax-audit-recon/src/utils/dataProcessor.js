import Papa from 'papaparse';
import { getDistrictName } from './districtCodes';

// 資産種類の定義 (1〜7)
const ASSET_TYPES = [1, 2, 3, 4, 5, 6, 7];

// CSVヘッダーのマッピング定義（必要に応じて調整）
// 元データ.csvのカラム名を想定
const COLUMN_MAP = {
    TAX_DISTRICT_CODE: '課税区コード',
    TAX_DISTRICT_NAME: '課税区', // CSVにあれば使う、なければコードから変換
    TAXPAYER_ID: '宛名番号',
    TAXPAYER_NAME: '氏名・名称',
    ADDRESS: '住所・所在地',
};

// 数値パース用ユーティリティ
const parseNum = (val) => {
    if (typeof val === 'number') return val;
    if (!val) return 0;
    // カンマ除去して数値化
    const num = Number(String(val).replace(/,/g, ''));
    return isNaN(num) ? 0 : num;
};

/**
 * CSVファイルをパースする関数
 * @param {File} file
 * @returns {Promise<Array>}
 */
export const parseCSV = (file) => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                resolve(results.data);
            },
            error: (error) => {
                reject(error);
            }
        });
    });
};

/**
 * データの正規化・前処理を行う関数
 * @param {Array} rawData 元データの配列
 * @returns {Array} 加工済みのデータ配列
 */
export const processTaxData = (rawData) => {
    return rawData.map((row) => {
        const districtCode = row[COLUMN_MAP.TAX_DISTRICT_CODE];
        const taxpayerId = row[COLUMN_MAP.TAXPAYER_ID];

        // 基本情報オブジェクト
        const baseInfo = {
            id: taxpayerId, // 一意のキーとして使用
            taxpayerId: taxpayerId,
            name: row[COLUMN_MAP.TAXPAYER_NAME] || '',
            address: row[COLUMN_MAP.ADDRESS] || '',
            districtCode: districtCode,
            districtName: getDistrictName(districtCode),
            assets: [],
            totalAppraisedValue: 0, // 評価額合計
            totalTaxableValue: 0,   // 課税標準額合計
            totalAcquisitionCost: 0, // 取得価額合計
            verificationStatus: 'pending', // pending, verified, discrepancy
            isPerfectMatch: false,  // 自動消込フラグ
            hasDiscrepancy: false,  // 2000円差異など
        };

        // 資産種類ごとのデータを抽出して配列化（縦持ち変換）
        let totalAppraised = 0;
        let totalTaxable = 0;
        let totalAcquisition = 0;

        ASSET_TYPES.forEach((typeNum) => {
            // カラム名のパターン: "種類１取得価額", "種類１評価額" ...
            // ※ 全角半角の揺らぎに対応するため、正規表現などでマッチさせるのが理想だが、
            // ここでは提供されたCSVヘッダーに合わせて実装する。
            // CSV: 種類１取得価額, 種類１評価額, ...
            // 全角数字が含まれる可能性に注意

            const typeStr = toFullWidth(typeNum); // 1 -> １
            const prefix = `種類${typeStr}`;

            const appraisedValue = parseNum(row[`${prefix}評価額`]);
            const taxableValue = parseNum(row[`${prefix}課税標準額`]);
            const acquisitionCost = parseNum(row[`${prefix}取得価額`]);
            const determinationValue = parseNum(row[`${prefix}決定価格`]);
            const itemCount = parseNum(row[`${prefix}資産件数`]);

            // 資産データが存在する場合のみ追加、あるいは全種類追加して0表示するか？
            // 要件「縦持ち形式（1〜7の行＋合計行）に展開」に従い、全種類保持する。

            const assetData = {
                type: typeNum,
                acquisitionCost,
                appraisedValue,
                determinationValue,
                taxableValue,
                itemCount
            };

            baseInfo.assets.push(assetData);

            // 合計値には種類7（合計行）を含めない（二重計上防止）
            if (typeNum !== 7) {
                totalAppraised += appraisedValue;
                totalTaxable += taxableValue;
                totalAcquisition += acquisitionCost;
            }
        });

        baseInfo.totalAppraisedValue = totalAppraised;
        baseInfo.totalTaxableValue = totalTaxable;
        baseInfo.totalAcquisitionCost = totalAcquisition;

        // 2,000円差異チェック
        // 条件: 評価額合計 - 課税標準額合計 >= 2,000
        const diff = totalAppraised - totalTaxable;
        if (diff >= 2000) {
            baseInfo.hasDiscrepancy = true;
            baseInfo.verificationStatus = 'discrepancy';
        }

        return baseInfo;
    });
};

// 数字を全角文字に変換するヘルパー
const toFullWidth = (num) => {
    const map = {
        1: '１', 2: '２', 3: '３', 4: '４', 5: '５',
        6: '６', 7: '７', 8: '８', 9: '９', 0: '０'
    };
    return map[num] || num;
};

/**
 * 2つのデータセット（今年度・前年度など）を比較する関数
 * @param {Array} currentData 今年度データ（processTaxData済み）
 * @param {Array} pastData 比較対象データ（processTaxData済み）
 * @returns {Array} 比較結果を含んだデータ
 */
export const compareDatasets = (currentData, pastData) => {
    // 宛名番号をキーにしてMap化
    const pastMap = new Map(pastData.map(d => [d.taxpayerId, d]));

    return currentData.map(current => {
        const past = pastMap.get(current.taxpayerId);

        // 比較結果オブジェクト
        const comparisonResult = {
            ...current,
            pastData: past || null,
            isNew: !past, // 新規（前年にない）
            isMissing: false, // 前年にはあったが今はない（これはCurrentベースのループでは検出できないため別途リストアップが必要だが、今回はCurrent主眼）
            matchStatus: 'diff', // exact, diff, new
        };

        if (past) {
            // 完全一致判定ロジック
            // 各資産種類の全数値項目が一致するか
            let allAssetsMatch = true;

            if (current.assets.length !== past.assets.length) {
                allAssetsMatch = false;
            } else {
                for (let i = 0; i < current.assets.length; i++) {
                    const cAsset = current.assets[i];
                    const pAsset = past.assets[i]; // 同じ順序であることを前提（正規化済みならOK）

                    if (
                        cAsset.acquisitionCost !== pAsset.acquisitionCost ||
                        cAsset.appraisedValue !== pAsset.appraisedValue ||
                        cAsset.determinationValue !== pAsset.determinationValue ||
                        cAsset.taxableValue !== pAsset.taxableValue ||
                        cAsset.itemCount !== pAsset.itemCount
                    ) {
                        allAssetsMatch = false;
                        break;
                    }
                }
            }

            if (allAssetsMatch) {
                comparisonResult.matchStatus = 'exact';
                comparisonResult.isPerfectMatch = true;
                comparisonResult.verificationStatus = 'verified'; // 自動済
            }
        } else {
            comparisonResult.matchStatus = 'new';
        }

        return comparisonResult;
    });
};
