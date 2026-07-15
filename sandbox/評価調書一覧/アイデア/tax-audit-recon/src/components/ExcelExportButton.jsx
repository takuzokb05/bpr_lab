import React from 'react';
import { Download } from 'lucide-react';
import * as XLSX from 'xlsx';

const ExcelExportButton = ({ data, cellStatus }) => {

    const handleExport = () => {
        // 1. データの整形
        const exportData = data.map((item, index) => {
            const safeId = item.id || `row-${index}`;
            const cellEntries = Object.entries(cellStatus);

            // この行に関連する疑義（Alert）を取得
            const alerts = cellEntries
                .filter(([key, status]) => key.startsWith(`${safeId}-`) && status === 'alert')
                .map(([key]) => {
                    const parts = key.split('-');
                    // key format: id-type-field e.g. 70000034-header-name, 70000034-2-acquisition
                    // We want readable names.
                    const type = parts[1]; // 'header', 'total', '1'...'6'
                    const field = parts[2]; // 'name', 'acquisition', etc.

                    let readableType = type;
                    if (type === 'header') readableType = 'ヘッダー';
                    else if (type === 'total') readableType = '合計';
                    else readableType = `${type}種`;

                    let readableField = field;
                    const fieldMap = {
                        'name': '氏名',
                        'address': '住所',
                        'id': '宛名番号',
                        'acquisition': '取得価額',
                        'appraised': '評価額',
                        'taxable': '課税標準額'
                    };
                    readableField = fieldMap[field] || field;

                    return `${readableType}:${readableField}`;
                });

            const alertText = alerts.length > 0 ? alerts.join(', ') : '';

            // 判定ロジック
            const requiredChecks = [
                `${safeId}-header-id`,
                `${safeId}-header-name`,
                `${safeId}-header-address`,
                `${safeId}-total-acquisition`,
                `${safeId}-total-appraised`,
                `${safeId}-total-taxable`
            ];
            const isVerified = requiredChecks.every(key => cellStatus[key] === 'verified');

            let statusText = '未確認';
            if (alerts.length > 0 || item.hasDiscrepancy) {
                statusText = '要確認';
            } else if (isVerified) {
                statusText = '確認済';
            }

            return {
                '宛名番号': item.taxpayerId,
                '氏名': item.name,
                '所在地': item.address,
                '地区コード': item.districtCode,
                '地区名': item.districtName,
                '取得価額合計': item.totalAcquisitionCost,
                '評価額合計': item.totalAppraisedValue,
                '課税標準額合計': item.totalTaxableValue,
                '判定': statusText,
                '疑義詳細': alertText
            };
        });

        // 2. ワークブック作成
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(exportData);

        // カラム幅の調整（簡易）
        const wscols = [
            { wch: 15 }, // ID
            { wch: 30 }, // Name
            { wch: 40 }, // Address
            { wch: 10 }, // District Code
            { wch: 10 }, // District Name
            { wch: 15 }, // Cost
            { wch: 15 }, // Appraised
            { wch: 15 }, // Taxable
            { wch: 10 }, // Status
            { wch: 50 }, // Alerts
        ];
        ws['!cols'] = wscols;

        XLSX.utils.book_append_sheet(wb, ws, "評価調書データ");

        // 3. ダウンロード実行
        XLSX.writeFile(wb, "tax_recon_export.xlsx");
    };

    return (
        <button
            onClick={handleExport}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-[#538393] font-medium transition-colors w-full text-left"
        >
            <Download size={18} />
            <span className="text-sm">表示データをExcel出力</span>
        </button>
    );
};

export default ExcelExportButton;
