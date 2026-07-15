import React from 'react';
import { Upload, FileUp, X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../utils/cn';

const FileUpload = ({ label, subLabel, accept, onFileSelect, fileInfo, status }) => {
    const [isDragOver, setIsDragOver] = React.useState(false);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => {
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            onFileSelect(e.target.files[0]);
        }
    };

    return (
        <div className="bg-white dark:bg-[#1a1d21] p-6 rounded-xl border border-[#e8f0f2] dark:border-gray-700 shadow-sm flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "p-2 rounded-lg",
                        status === 'ready' ? "bg-green-100 text-green-700" : "bg-primary/10 text-primary"
                    )}>
                        {status === 'ready' ? <CheckCircle size={20} /> : <Upload size={20} />}
                    </div>
                    <div>
                        <h4 className="text-sm font-bold text-gray-900 dark:text-white">{label}</h4>
                        <p className="text-xs text-[#538393]">{subLabel}</p>
                    </div>
                </div>
                {status === 'ready' && (
                    <span className="text-[10px] font-bold px-2 py-1 rounded bg-green-100 text-green-700 uppercase">
                        準備完了
                    </span>
                )}
            </div>

            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                    "flex-1 border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center transition-all cursor-pointer relative",
                    isDragOver
                        ? "border-primary bg-primary/5"
                        : "border-[#d1e0e5] dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:border-primary/50"
                )}
            >
                <input
                    type="file"
                    accept={accept}
                    onChange={handleChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />

                {fileInfo ? (
                    <div className="z-10">
                        <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                            <FileUp className="text-green-600 dark:text-green-400" size={24} />
                        </div>
                        <p className="text-sm font-bold text-gray-900 dark:text-white truncate max-w-[200px]">
                            {fileInfo.name}
                        </p>
                        <p className="text-xs text-[#538393] mt-1">
                            {(fileInfo.size / 1024).toFixed(1)} KB
                        </p>
                    </div>
                ) : (
                    <div className="z-10 pointer-events-none">
                        <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
                            <Upload className="text-gray-400" size={24} />
                        </div>
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            ファイルをここにドロップ
                        </p>
                        <p className="text-xs text-[#538393] mt-1">
                            またはクリックして選択
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileUpload;
