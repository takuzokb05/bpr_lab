import React, { useState } from 'react';
import { cn } from '../utils/cn';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Circle, ArrowRight } from 'lucide-react';

const StatusBadge = ({ status }) => {
    switch (status) {
        case 'discrepancy':
            return (
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-red-100 text-red-700">
                    <AlertTriangle size={12} /> 疑義あり
                </span>
            );
        case 'verified':
            return (
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-green-100 text-green-700">
                    <CheckCircle size={12} /> 確認済
                </span>
            );
        case 'pending':
        default:
            return (
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-gray-100 text-gray-600">
                    <Clock size={12} /> 未確認
                </span>
            );
    }
};

const toFullWidth = (num) => {
    const map = { 1: '１', 2: '２', 3: '３', 4: '４', 5: '５', 6: '６', 7: '７', 8: '８', 9: '９', 0: '０' };
    return map[num] || num;
};

const formatAssetType = (type) => {
    if (type === 7) return '合計';
    return `${toFullWidth(type)}種`;
};

const ComparisonTable = ({ data, onRowClick, cellStatus, setCellStatus }) => {
    // ...

    // デフォルトで全て展開しておく（詳細を見たいという要望のため）
    const [expandedIds, setExpandedIds] = useState(new Set(data?.map(d => d.id) || []));

    // セルごとの判定状態管理（App.jsxにリフトアップ済み）

    const toggleExpand = (id, e) => {
        e.stopPropagation();
        const newSet = new Set(expandedIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setExpandedIds(newSet);
    };

    const toggleCellStatus = (id, type, field, e) => {
        // e.preventDefault(); // ボタンクリックなどの標準動作を阻害しないように削除
        e.stopPropagation();

        const key = `${id}-${type}-${field}`;
        const current = cellStatus[key];

        let next;
        if (!current) next = 'verified';
        else if (current === 'verified') next = 'alert';
        else next = null;

        console.log("Toggle Status:", key, next);

        setCellStatus(prev => ({ ...prev, [key]: next }));
    };

    const renderCellAction = (id, type, field) => {
        const key = `${id}-${type}-${field}`;
        const status = cellStatus[key];

        return (
            <button
                type="button"
                onClick={(e) => toggleCellStatus(id, type, field, e)}
                className={cn(
                    "relative z-20 ml-2 p-1 rounded-full transition-all opacity-100 cursor-pointer hover:bg-gray-200",
                    status === 'verified' && "text-green-600 bg-green-100 ring-2 ring-green-100",
                    status === 'alert' && "text-red-600 bg-red-100 ring-2 ring-red-100",
                    !status && "text-gray-400 bg-gray-100"
                )}
                title={status === 'verified' ? "確認済解除" : "確認済/疑義あり"}
            >
                {status === 'verified' ? <CheckCircle size={16} /> :
                    status === 'alert' ? <AlertTriangle size={16} /> :
                        <Circle size={16} />}
            </button>
        );
    };

    // 全ての項目を一括で「確認済」にする（ID・名前・住所は除く、数値のみ）
    const toggleAllVerified = (id, row, e) => {
        e.stopPropagation();

        // 各資産の項目のキー
        const assetKeys = row.assets.flatMap(asset => [
            `${id}-${asset.type}-acquisition`,
            `${id}-${asset.type}-appraised`,
            `${id}-${asset.type}-taxable`
        ]);

        const allKeys = [...assetKeys,
        `${id}-total-acquisition`,
        `${id}-total-appraised`,
        `${id}-total-taxable`,
        `${id}-header-id`,
        `${id}-header-name`,
        `${id}-header-address`
        ];

        // 現在の状態を確認（一つでも未確認があれば、全て確認済にする。全て確認済なら解除）
        const isAllVerified = allKeys.every(key => cellStatus[key] === 'verified');

        const newStatus = {};
        allKeys.forEach(key => {
            newStatus[key] = isAllVerified ? null : 'verified';
        });

        setCellStatus(prev => ({ ...prev, ...newStatus }));
    };

    if (!data || data.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400 bg-white dark:bg-[#1a1d21] rounded-xl border border-[#e8f0f2] dark:border-gray-700">
                <p>データがありません</p>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-[#1a1d21] rounded-xl border border-[#e8f0f2] dark:border-gray-700 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 dark:bg-[#252a30] border-b border-[#e8f0f2] dark:border-gray-700">
                        <tr>
                            <th className="px-4 py-3 w-[40px]"></th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-left min-w-[200px]">宛名 / 資産種類</th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-left">氏名・名称 / 所在地</th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-right min-w-[140px]">取得価額(円)</th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-right min-w-[140px]">評価額(円)</th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-right min-w-[140px]">課税標準額(円)</th>
                            <th className="px-4 py-3 text-[12px] font-bold text-gray-600 text-center">判定</th>
                        </tr>
                    </thead>
                    {data.map((row, rowIndex) => {
                        // IDがデータに含まれていない場合のフォールバック
                        const safeId = row.id || `row-${rowIndex}`;
                        const isExpanded = expandedIds.has(safeId);
                        const isDiscrepancy = row.verificationStatus === 'discrepancy';
                        const taxYear = "R6";

                        // 行全体の確認状態を計算
                        const assetKeys = row.assets.flatMap(asset => [
                            `${safeId}-${asset.type}-acquisition`,
                            `${safeId}-${asset.type}-appraised`,
                            `${safeId}-${asset.type}-taxable`
                        ]);
                        const allCheckKeys = [...assetKeys,
                        `${safeId}-total-acquisition`,
                        `${safeId}-total-appraised`,
                        `${safeId}-total-taxable`,
                        `${safeId}-header-id`,
                        `${safeId}-header-name`,
                        `${safeId}-header-address`
                        ];
                        const isRowVerified = allCheckKeys.length > 0 && allCheckKeys.every(key => cellStatus[key] === 'verified');

                        return (
                            <tbody key={`${safeId}-${rowIndex}`} className="border-b border-[#e8f0f2] dark:border-gray-700 last:border-0 hover:bg-gray-50/50">
                                {/* 親行（納税者ヘッダー） */}
                                <tr className="bg-blue-50/30 dark:bg-blue-900/10">
                                    <td
                                        className="px-4 py-4 text-center text-gray-400 cursor-pointer hover:text-primary transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                                        onClick={(e) => toggleExpand(safeId, e)}
                                    >
                                        {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-xs text-[#538393] font-bold uppercase tracking-wider">宛名番号</span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-lg font-bold text-gray-900 dark:text-white">{row.taxpayerId}</span>
                                                {renderCellAction(safeId, 'header', 'id')}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex flex-col">
                                            <div className="flex items-center gap-2">
                                                <span className="text-base font-bold text-gray-900 dark:text-white">{row.name}</span>
                                                {renderCellAction(safeId, 'header', 'name')}
                                            </div>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-sm text-gray-500">{row.address}</span>
                                                {renderCellAction(safeId, 'header', 'address')}
                                            </div>
                                            <div className="mt-1 flex gap-2">
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                                    {row.districtName}
                                                </span>
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                                    {taxYear}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    {/* 合計行 */}
                                    <td className="px-4 py-4 text-right">
                                        <div className="text-xs text-gray-500 mb-1">合計</div>
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="font-bold text-gray-900 dark:text-white text-base">
                                                ¥{(row.totalAcquisitionCost || 0).toLocaleString()}
                                            </div>
                                            {renderCellAction(safeId, 'total', 'acquisition')}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-right">
                                        <div className="text-xs text-gray-500 mb-1">合計</div>
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="font-bold text-gray-900 dark:text-white text-base">
                                                ¥{row.totalAppraisedValue.toLocaleString()}
                                            </div>
                                            {renderCellAction(safeId, 'total', 'appraised')}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-right">
                                        <div className="text-xs text-gray-500 mb-1">合計</div>
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="font-bold text-gray-900 dark:text-white text-base">
                                                ¥{row.totalTaxableValue.toLocaleString()}
                                            </div>
                                            {renderCellAction(safeId, 'total', 'taxable')}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-center">
                                        <button
                                            type="button"
                                            onClick={(e) => toggleAllVerified(safeId, row, e)}
                                            className={cn(
                                                "relative z-20 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-bold rounded-lg shadow-md transition-all cursor-pointer min-w-[120px]",
                                                isRowVerified
                                                    ? "bg-green-600 text-white hover:bg-green-700 ring-4 ring-green-100"
                                                    : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg"
                                            )}
                                        >
                                            <CheckCircle size={18} />
                                            <span>{isRowVerified ? "確認完了" : "一括確認"}</span>
                                        </button>
                                        {isDiscrepancy && (
                                            <div className="mt-2 text-xs font-bold text-red-600 bg-red-50 py-0.5 rounded border border-red-100">
                                                ⚠ 差額あり
                                            </div>
                                        )}
                                    </td>
                                </tr>

                                {/* 子行（資産明細展開） */}
                                {isExpanded && row.assets.map((asset, idx) => (
                                    <tr key={`${safeId}-asset-${idx}`} className="hover:bg-amber-50/40 transition-colors">
                                        <td></td>
                                        <td className="px-4 py-3 pl-8 flex items-center h-full relative">
                                            {/* ツリーラインのような装飾 */}
                                            <div className="absolute left-4 top-0 bottom-1/2 w-4 border-l-2 border-b-2 border-gray-200 rounded-bl-lg"></div>
                                            <div className="relative pl-2">
                                                <span className="px-2 py-1 rounded-md bg-white border border-gray-200 text-sm font-bold shadow-sm whitespace-nowrap">
                                                    {formatAssetType(asset.type)}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-500">
                                            {asset.itemCount > 0 ? `${asset.itemCount} 件の資産` : '-'}
                                        </td>
                                        <td className="px-4 py-3 text-right font-medium text-gray-700 font-mono text-[15px]">
                                            <div className="flex items-center justify-end group">
                                                {asset.acquisitionCost.toLocaleString()}
                                                {renderCellAction(safeId, asset.type, 'acquisition')}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right font-medium text-gray-700 font-mono text-[15px]">
                                            <div className="flex items-center justify-end group">
                                                {asset.appraisedValue.toLocaleString()}
                                                {renderCellAction(safeId, asset.type, 'appraised')}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right font-medium text-gray-700 font-mono text-[15px]">
                                            <div className="flex items-center justify-end group">
                                                {asset.taxableValue.toLocaleString()}
                                                {renderCellAction(safeId, asset.type, 'taxable')}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            {/* 行ごとの簡易判定結果（仮） */}
                                        </td>
                                    </tr>
                                ))}
                                {isExpanded && row.assets.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="px-8 py-4 text-gray-400 italic text-sm">
                                            資産データがありません
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        );
                    })}
                </table>
            </div>
        </div>
    );
};

export default ComparisonTable;
