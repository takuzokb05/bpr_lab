import React, { useState, useEffect, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import ComparisonTable from './components/ComparisonTable';
import DetailCard from './components/DetailCard';
import { parseCSV, processTaxData } from './utils/dataProcessor';

function App() {
  const [currentFile, setCurrentFile] = useState(() => {
    try {
      const saved = localStorage.getItem('taxRecon_currentFile');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [pastFile, setPastFile] = useState(() => {
    try {
      const saved = localStorage.getItem('taxRecon_pastFile');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [processedData, setProcessedData] = useState(() => {
    try {
      const saved = localStorage.getItem('taxRecon_processedData');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });
  const [selectedRecord, setSelectedRecord] = useState(null);
  // セル単位のステータス管理（ComparisonTableからリフトアップ） + 永続化
  const [cellStatus, setCellStatus] = useState(() => {
    try {
      const saved = localStorage.getItem('taxRecon_cellStatus');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      console.error("Failed to load cell status", e);
      return {};
    }
  });

  // ステータス変更時にローカルストレージに保存
  useEffect(() => {
    localStorage.setItem('taxRecon_cellStatus', JSON.stringify(cellStatus));
  }, [cellStatus]);

  // データ変更時にローカルストレージに保存
  useEffect(() => {
    localStorage.setItem('taxRecon_processedData', JSON.stringify(processedData));
  }, [processedData]);

  useEffect(() => {
    localStorage.setItem('taxRecon_currentFile', JSON.stringify(currentFile));
  }, [currentFile]);

  useEffect(() => {
    localStorage.setItem('taxRecon_pastFile', JSON.stringify(pastFile));
  }, [pastFile]);

  // フィルタリング状態
  const [filters, setFilters] = useState({
    search: '',
    district: '',
    showDiscrepancyOnly: false,
    showPendingOnly: false
  });

  // ファイルアップロードハンドラー
  const handleCurrentFileUpload = async (file) => {
    try {
      const rawData = await parseCSV(file);
      const processed = processTaxData(rawData);
      setProcessedData(processed);
      setCurrentFile(file);
      setCellStatus({}); // 新しいデータがアップロードされたらセルステータスをリセット
    } catch (error) {
      console.error("Error parsing current file:", error);
      alert("Failed to parse CSV file. Please check the format.");
    }
  };

  const handlePastFileUpload = async (file) => {
    try {
      const rawData = await parseCSV(file);
      const pastProcessed = processTaxData(rawData);
      setPastFile(file);

      // 比較対象データと完全一致するレコードを除外
      if (processedData.length > 0) {
        const filtered = processedData.filter(currentItem => {
          const matchingPastItem = pastProcessed.find(
            pastItem => pastItem.taxpayerId === currentItem.taxpayerId
          );

          if (!matchingPastItem) return true; // 過去データにない = 新規 = 残す

          // 完全一致チェック（全ての資産データが一致するか）
          const isExactMatch =
            currentItem.name === matchingPastItem.name &&
            currentItem.address === matchingPastItem.address &&
            currentItem.totalAcquisitionCost === matchingPastItem.totalAcquisitionCost &&
            currentItem.totalAppraisedValue === matchingPastItem.totalAppraisedValue &&
            currentItem.totalTaxableValue === matchingPastItem.totalTaxableValue &&
            currentItem.assets.length === matchingPastItem.assets.length &&
            currentItem.assets.every((asset, idx) => {
              const pastAsset = matchingPastItem.assets[idx];
              return pastAsset &&
                asset.type === pastAsset.type &&
                asset.acquisitionCost === pastAsset.acquisitionCost &&
                asset.appraisedValue === pastAsset.appraisedValue &&
                asset.taxableValue === pastAsset.taxableValue;
            });

          return !isExactMatch; // 完全一致なら除外（falseを返す）
        });

        setProcessedData(filtered);
        console.log(`比較完了: ${processedData.length - filtered.length}件の一致データを除外しました`);
      }
    } catch (error) {
      console.error("Error parsing comparison file:", error);
      alert("比較対象ファイルの読み込みに失敗しました。");
    }
  };

  // フィルタリングロジック
  const filteredData = useMemo(() => {
    const cellEntries = Object.entries(cellStatus);

    return processedData.filter((item, index) => {
      // IDの安全性確保 (ComparisonTableと整合)
      const safeId = item.id || `row-${index}`;

      // テキスト検索
      const searchLower = filters.search.toLowerCase();
      const matchesSearch =
        item.name.toLowerCase().includes(searchLower) ||
        String(item.taxpayerId).includes(searchLower);

      // 地区フィルタ
      const matchesDistrict = filters.district === '' || String(item.districtCode) === filters.district;

      // 1. 疑義ありフィルタ（動的ステータス + 静的データ）
      // 行に関連するキーに 'alert' があるか
      const hasDynamicAlert = cellEntries.some(([key, status]) =>
        key.startsWith(`${safeId}-`) && status === 'alert'
      );
      const matchesDiscrepancy = !filters.showDiscrepancyOnly || (hasDynamicAlert || item.hasDiscrepancy);

      // 2. 未確認フィルタ（トップレベル項目がすべてチェックされているか）
      const requiredChecks = [
        `${safeId}-header-id`,
        `${safeId}-header-name`,
        `${safeId}-header-address`,
        `${safeId}-total-acquisition`,
        `${safeId}-total-appraised`,
        `${safeId}-total-taxable`
      ];
      const isVerified = requiredChecks.every(key => cellStatus[key] === 'verified');
      // 未確認のみ表示 = 確認完了（isVerified）なら表示しない
      const matchesPending = !filters.showPendingOnly || !isVerified;

      return matchesSearch && matchesDistrict && matchesDiscrepancy && matchesPending;
    });
  }, [processedData, filters, cellStatus]);

  // 統計情報
  const stats = useMemo(() => {
    const cellEntries = Object.entries(cellStatus);
    let discrepancyCount = 0;
    let verifiedCount = 0;

    processedData.forEach((item, index) => {
      const safeId = item.id || `row-${index}`;

      const hasDynamicAlert = cellEntries.some(([key, status]) =>
        key.startsWith(`${safeId}-`) && status === 'alert'
      );
      if (hasDynamicAlert || item.hasDiscrepancy) {
        discrepancyCount++;
      }

      const requiredChecks = [
        `${safeId}-header-id`,
        `${safeId}-header-name`,
        `${safeId}-header-address`,
        `${safeId}-total-acquisition`,
        `${safeId}-total-appraised`,
        `${safeId}-total-taxable`
      ];
      if (requiredChecks.every(key => cellStatus[key] === 'verified')) {
        verifiedCount++;
      }
    });

    return {
      total: processedData.length,
      discrepancyCount,
      verifiedCount
    };
  }, [processedData, cellStatus]);

  return (
    <div className="flex h-screen bg-background-light dark:bg-background-dark font-display text-[#0f171a] dark:text-white overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        filters={filters}
        setFilters={setFilters}
        stats={stats}
        processedData={filteredData}
        cellStatus={cellStatus}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header */}
        <Header />

        {/* Scrollable Main Content */}
        <main className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto space-y-8">

            {/* File Upload Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FileUpload
                label="Current Year Data (本年度)"
                subLabel="Upload master csv (元データ)"
                accept=".csv"
                onFileSelect={handleCurrentFileUpload}
                fileInfo={currentFile}
                status={currentFile ? 'ready' : 'idle'}
              />
              <FileUpload
                label="Comparison Source (比較対象)"
                subLabel="Last year or audit data"
                accept=".csv"
                onFileSelect={handlePastFileUpload}
                fileInfo={pastFile}
                status={pastFile ? 'ready' : 'idle'}
              />
            </div>

            {/* Main Table */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold tracking-tight">
                  Processed Records
                  <span className="text-sm font-normal text-gray-500 ml-3">
                    {filteredData.length} / {processedData.length} shown
                  </span>
                </h2>
              </div>

              <ComparisonTable
                data={filteredData}
                onRowClick={setSelectedRecord}
                cellStatus={cellStatus}
                setCellStatus={setCellStatus}
              />
            </div>

          </div>
        </main>
      </div>

      {/* Detail Modal */}
      {selectedRecord && (
        <DetailCard
          data={selectedRecord}
          onClose={() => setSelectedRecord(null)}
        />
      )}
    </div>
  );
}

export default App;
