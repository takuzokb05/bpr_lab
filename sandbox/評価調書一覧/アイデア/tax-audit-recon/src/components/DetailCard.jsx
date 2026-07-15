import React from 'react';
import { X, Check } from 'lucide-react';
import { cn } from '../utils/cn';


const toFullWidth = (num) => {
    const map = { 1: '１', 2: '２', 3: '３', 4: '４', 5: '５', 6: '６', 7: '７', 8: '８', 9: '９', 0: '０' };
    return map[num] || num;
};

const formatAssetType = (type) => {
    if (type === 7) return '合計';
    return `${toFullWidth(type)}種`;
};

const DetailCard = ({ data, onClose }) => {
    if (!data) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
            <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-xl bg-white dark:bg-[#1e2329] shadow-xl flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-[#e8f0f2] dark:border-gray-700 bg-gray-50 dark:bg-[#252a30]">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">資産詳細</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto flex-grow">
                    <div className="mb-6">
                        <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3">基本情報</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <p className="text-gray-600 dark:text-gray-400"><span className="font-medium text-gray-800 dark:text-gray-200">氏名:</span> {data.name}</p>
                            <p className="text-gray-600 dark:text-gray-400"><span className="font-medium text-gray-800 dark:text-gray-200">住所:</span> {data.address}</p>
                            <p className="text-gray-600 dark:text-gray-400"><span className="font-medium text-gray-800 dark:text-gray-200">生年月日:</span> {data.dob}</p>
                            <p className="text-gray-600 dark:text-gray-400"><span className="font-medium text-gray-800 dark:text-gray-200">電話番号:</span> {data.phone}</p>
                        </div>
                    </div>

                    <div>
                        <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3">資産一覧</h4>
                        <div className="overflow-x-auto rounded-lg border border-[#e8f0f2] dark:border-gray-700">
                            <table className="min-w-full divide-y divide-[#e8f0f2] dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-[#252a30]">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">資産種別</th>
                                        <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">個数</th>
                                        <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">取得価額</th>
                                        <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">評価額</th>
                                        <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">課税評価額</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#e8f0f2] dark:divide-gray-700">
                                    {data.assets.map((asset) => (
                                        <tr key={asset.type} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                                            <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{formatAssetType(asset.type)}</td>
                                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">{asset.itemCount}</td>
                                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">¥{asset.acquisitionCost.toLocaleString()}</td>
                                            <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">¥{asset.appraisedValue.toLocaleString()}</td>
                                            <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">¥{asset.taxableValue.toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table >
                        </div >
                    </div >
                </div >

                {/* Footer Actions */}
                <div className="p-6 border-t border-[#e8f0f2] dark:border-gray-700 bg-gray-50 dark:bg-[#252a30] flex justify-end gap-3" >
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        閉じる
                    </button>
                    <button className="px-4 py-2 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-lg shadow-sm transition-all flex items-center gap-2">
                        <Check size={16} /> 確認済にする
                    </button>
                </div >
            </div >
        </div >
    );
};

export default DetailCard;
