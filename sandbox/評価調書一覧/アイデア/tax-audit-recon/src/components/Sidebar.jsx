import React from 'react';
import { cn } from '../utils/cn';
import { LayoutDashboard, FileText, AlertTriangle, Settings, LogOut } from 'lucide-react';
import ExcelExportButton from './ExcelExportButton';

const Sidebar = ({ filters, setFilters, stats, processedData, cellStatus }) => {
    return (
        <aside className="w-64 bg-white dark:bg-[#1a1d21] border-r border-[#e8f0f2] dark:border-gray-700 flex flex-col overflow-y-auto custom-scrollbar h-full">
            <div className="p-6">
                <div className="flex items-center gap-2 mb-8">
                    <div className="bg-primary p-1.5 rounded-lg text-white">
                        <LayoutDashboard size={20} />
                    </div>
                    <h1 className="text-lg font-bold tracking-tight text-gray-900 dark:text-white">
                        評価調書一覧確認システム
                    </h1>
                </div>

                <div className="mb-8">
                    <h3 className="text-xs font-bold text-[#538393] uppercase tracking-wider mb-4">メニュー</h3>
                    <div className="flex flex-col gap-1">
                        <button
                            className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-[#538393] font-medium transition-colors w-full text-left"
                        >
                            <LayoutDashboard size={18} />
                            <span className="text-sm">ダッシュボード</span>
                        </button>
                        <button
                            onClick={() => setFilters(prev => ({ ...prev, showDiscrepancyOnly: false, showPendingOnly: false }))}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors w-full text-left",
                                !filters.showDiscrepancyOnly && !filters.showPendingOnly
                                    ? "bg-primary/10 text-primary font-semibold"
                                    : "hover:bg-gray-50 dark:hover:bg-gray-800 text-[#538393]"
                            )}
                        >
                            <FileText size={18} />
                            <span className="text-sm">データ一覧</span>
                        </button>
                        <button
                            onClick={() => setFilters(prev => ({ ...prev, showDiscrepancyOnly: true }))}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors w-full text-left",
                                filters.showDiscrepancyOnly
                                    ? "bg-primary/10 text-primary font-semibold"
                                    : "hover:bg-gray-50 dark:hover:bg-gray-800 text-[#538393]"
                            )}
                        >
                            <AlertTriangle size={18} />
                            <span className="text-sm">要確認データ</span>
                            {stats?.discrepancyCount > 0 && (
                                <span className="ml-auto bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full font-bold">
                                    {stats.discrepancyCount}
                                </span>
                            )}
                        </button>
                        <ExcelExportButton data={processedData} cellStatus={cellStatus} />
                    </div>
                </div>

                <div className="space-y-6">
                    <h3 className="text-xs font-bold text-[#538393] uppercase tracking-wider">絞り込み</h3>

                    <div>
                        <label className="text-xs font-semibold mb-2 block text-gray-700 dark:text-gray-300">氏名・宛名番号検索</label>
                        <input
                            type="text"
                            placeholder="名前または番号を入力..."
                            className="w-full text-sm rounded-lg border-[#e8f0f2] dark:border-gray-700 dark:bg-gray-800 px-3 py-2 focus:ring-2 focus:ring-primary focus:outline-none"
                            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-semibold mb-2 block text-gray-700 dark:text-gray-300">地区</label>
                        <select
                            className="w-full text-sm rounded-lg border-[#e8f0f2] dark:border-gray-700 dark:bg-gray-800 px-3 py-2 focus:ring-2 focus:ring-primary focus:outline-none"
                            onChange={(e) => setFilters(prev => ({ ...prev, district: e.target.value }))}
                        >
                            <option value="">全地区</option>
                            {/* Options will be populated dynamically if needed, or static commonly used ones */}
                            <option value="0">鶴見区</option>
                            <option value="10">神奈川区</option>
                            <option value="20">西区</option>
                            <option value="30">中区</option>
                            <option value="40">南区</option>
                        </select>
                    </div>

                    <div>
                        <label className="text-xs font-semibold mb-2 block text-gray-700 dark:text-gray-300">表示切替</label>
                        <div className="flex flex-col gap-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={filters.showDiscrepancyOnly}
                                    onChange={(e) => setFilters(prev => ({ ...prev, showDiscrepancyOnly: e.target.checked }))}
                                    className="rounded text-primary focus:ring-primary"
                                />
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">疑義ありのみ表示</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={filters.showPendingOnly}
                                    onChange={(e) => setFilters(prev => ({ ...prev, showPendingOnly: e.target.checked }))}
                                    className="rounded text-primary focus:ring-primary"
                                />
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">未確認のみ表示</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-auto p-6 border-t border-[#e8f0f2] dark:border-gray-700">
                <button className="flex items-center gap-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors w-full">
                    <Settings size={18} />
                    <span className="text-sm font-medium">設定</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
