import React, { useState, useEffect } from 'react';
import SkeletonSlide from './SkeletonSlide';
import StudioModal from './StudioModal';
import { scanPdf } from '../utils/pdf';
import { generatePptx } from '../utils/pptx';
import { performRemaster, analyzeSlide } from '../utils/gemini';
import { base64ToBlobUrl, sleep, safeJsonParse } from '../utils/common';

const App = () => {
    const [apiKey, setApiKey] = useState(localStorage.getItem('gemini_api_key') || '');
    const [importFiles, setImportFiles] = useState(null);

    // App Status: 'idle' -> 'scanning' -> 'selecting' -> 'processing' -> 'done'
    const [appStatus, setAppStatus] = useState('idle');

    const [progress, setProgress] = useState({ current: 0, total: 0, msg: '' });
    const [slides, setSlides] = useState([]);
    const [logs, setLogs] = useState([]);

    // Selection Helper
    const [selectAll, setSelectAll] = useState(false);

    const [modelConfig, setModelConfig] = useState({
        vision: 'gemini-3-pro-preview',
        image: 'gemini-3-pro-image-preview'
    });
    const [presentationRatio, setPresentationRatio] = useState("16:9");

    // UI Targets
    const [previewTarget, setPreviewTarget] = useState(null);
    const [studioTarget, setStudioTarget] = useState(null);

    const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);

    const handleApiKeyChange = (e) => {
        const key = e.target.value;
        setApiKey(key);
        localStorage.setItem('gemini_api_key', key);
    };

    // --- Image Import (Direct) ---
    async function scanImages(fileList) {
        setAppStatus('scanning');
        setSlides([]);
        setLogs([]);

        const newSlides = [];
        for (let i = 0; i < fileList.length; i++) {
            const file = fileList[i];
            setProgress({ current: i + 1, total: fileList.length, msg: `Importing Image ${i + 1}...` });

            try {
                const base64 = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.readAsDataURL(file);
                });
                const blobUrl = URL.createObjectURL(file); // Direct blob from file

                // Detect ratio from first image
                if (i === 0) {
                    const img = new Image();
                    img.src = blobUrl;
                    await new Promise(r => img.onload = r);
                    const ratioVal = img.width / img.height;
                    const detectedRatio = ratioVal < 1.5 ? "4:3" : "16:9";
                    setPresentationRatio(detectedRatio);
                    addLog(`📐 Ratio Detected from Image 1: ${detectedRatio}`);
                }

                newSlides.push({
                    id: i + 1,
                    status: 'ORIGINAL',
                    isSelected: false,
                    originalImage: base64,
                    displayImage: blobUrl,
                    bgImage: null,
                    textData: [],
                    bgType: 'ORIGINAL'
                });
            } catch (e) {
                addLog(`Error reading image ${file.name}: ${e.message}`);
            }
        }
        setSlides(newSlides);
        setAppStatus('selecting');
        setProgress({ current: 0, total: 0, msg: 'Select images to remaster.' });
        addLog(`Import Complete. ${newSlides.length} images ready.`);
    }

    const handleStartImport = async () => {
        if (!importFiles || !apiKey) return alert("Please set API Key & File(s)");

        // Check if first file is PDF
        if (importFiles[0].type === 'application/pdf') {
            setAppStatus('scanning');
            setSlides([]);
            setLogs([]);
            try {
                const { slides: scannedSlides, ratio } = await scanPdf(importFiles[0], {
                    onProgress: (current, total, msg) => setProgress({ current, total, msg }),
                    onLog: addLog
                });
                setPresentationRatio(ratio);
                setSlides(scannedSlides);
                setAppStatus('selecting');
                setProgress({ current: 0, total: 0, msg: 'Select slides to remaster.' });
                addLog(`Scan Complete. ${scannedSlides.length} slides ready.`);
            } catch (e) {
                addLog(`Critical Scan Error: ${e.message}`);
                setAppStatus('idle');
            }
        } else {
            scanImages(importFiles);
        }
    };

    // --- UX: Sample Data Loader ---
    const handleLoadSample = async () => {
        if (!apiKey) return alert("Please enter your API Key first to try the sample.");

        setAppStatus('scanning');
        setProgress({ current: 0, total: 1, msg: 'Generating Sample Slide...' });

        // Create a dynamic sample slide using canvas
        const cvs = document.createElement('canvas');
        cvs.width = 1280;
        cvs.height = 720;
        const ctx = cvs.getContext('2d');

        // Draw a "bad" slide to remaster
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, 1280, 720);

        // Bad title
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 60px Arial';
        ctx.fillText("QUARTERLY REPORT 2024", 100, 150);

        // Bad chart (hand drawn looking)
        ctx.beginPath();
        ctx.moveTo(100, 500);
        ctx.lineTo(100, 250);
        ctx.lineTo(1100, 250); // Axes
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 5;
        ctx.stroke();

        // Squiggly line
        ctx.beginPath();
        ctx.moveTo(100, 500);
        ctx.bezierCurveTo(400, 400, 600, 550, 1100, 100);
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 8;
        ctx.stroke();

        ctx.fillStyle = 'red';
        ctx.font = '40px Arial';
        ctx.fillText("Growth!!", 800, 150);

        const sampleBase64 = cvs.toDataURL('image/jpeg', 0.8);
        const sampleBlob = base64ToBlobUrl(sampleBase64.split(',')[1], 'image/jpeg');

        await sleep(500);

        setSlides([{
            id: 1,
            status: 'ORIGINAL',
            isSelected: false,
            originalImage: sampleBase64,
            displayImage: sampleBlob,
            bgImage: null,
            textData: [],
            bgType: 'ORIGINAL'
        }]);

        setPresentationRatio("16:9");
        setAppStatus('selecting');
        setProgress({ current: 0, total: 0, msg: 'Sample Loaded. Try the "Remaster This" button!' });
    };

    // --- Phase 2: Selection Logic ---
    const toggleSelection = (id) => {
        setSlides(prev => prev.map(s => s.id === id ? { ...s, isSelected: !s.isSelected } : s));
    };

    const toggleAll = () => {
        const newState = !selectAll;
        setSelectAll(newState);
        setSlides(prev => prev.map(s => ({ ...s, isSelected: newState })));
    };

    // --- AI Batch Remaster ---
    const runBatchRemaster = async () => {
        const targets = slides.filter(s => s.isSelected);
        if (targets.length === 0) return alert("No slides selected for remastering.");

        setAppStatus('processing');

        for (let i = 0; i < targets.length; i++) {
            const slide = targets[i];
            setProgress({ current: i + 1, total: targets.length, msg: `Remastering Phase: Slide ${slide.id}...` });

            // Mark as processing
            setSlides(prev => prev.map(s => s.id === slide.id ? { ...s, status: 'PROCESSING' } : s));

            try {
                const result = await performRemaster(apiKey, modelConfig, slide, presentationRatio, (msg) => {
                    // Simplified progress for batch: just update message
                    setProgress(p => ({ ...p, msg }));
                });

                setSlides(prev => prev.map(s => s.id === slide.id ? {
                    ...s,
                    ...result,
                    status: 'REMASTERED'
                } : s));
                addLog(`✅ Slide ${slide.id} Remastered.`);
            } catch (e) {
                addLog(`❌ Slide ${slide.id} Failed: ${e.message}`);
                setSlides(prev => prev.map(s => s.id === slide.id ? { ...s, status: 'ERROR' } : s));
            }
            // Rate limit buffer
            await sleep(1000);
        }

        setAppStatus('done');
        addLog('Batch Processing Complete.');
    };

    // --- Helpers ---
    const comesFromOriginal = (s) => s.status === 'ORIGINAL' || !s.bgImage;

    // --- IndexedDB Logic ---
    const dbName = 'NotebookLM_Remaster_DB';
    const storeName = 'sessions';

    const openDB = () => {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(dbName, 1);
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(storeName)) {
                    db.createObjectStore(storeName, { keyPath: 'id' });
                }
            };
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = (event) => reject(event.target.error);
        });
    };

    const saveSessionToIDB = async (data) => {
        try {
            const db = await openDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(storeName, 'readwrite');
                const store = tx.objectStore(storeName);
                store.put({ id: 'current_session', slides: data, timestamp: Date.now() });
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            });
        } catch (e) {
            console.error("IDB Save Error:", e);
        }
    };

    const loadSessionFromIDB = async () => {
        try {
            const db = await openDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(storeName, 'readonly');
                const store = tx.objectStore(storeName);
                const request = store.get('current_session');
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        } catch (e) {
            console.error("IDB Load Error:", e);
            return null;
        }
    };

    const clearSessionIDB = async () => {
        const db = await openDB();
        const tx = db.transaction(storeName, 'readwrite');
        tx.objectStore(storeName).delete('current_session');
    };

    useEffect(() => {
        const initRestore = async () => {
            const saved = await loadSessionFromIDB();
            if (saved && saved.slides && saved.slides.length > 0) {
                // Simple restoration check
                const restore = window.confirm(`前回の作業セッションが見つかりました (${new Date(saved.timestamp).toLocaleString()})。\n復元しますか？ (キャンセルで新規作成)`);
                if (restore) {
                    // Rehydrate Blob URLs from Base64
                    const rehydratedSlides = saved.slides.map(s => {
                        let displayUrl = null;
                        // 1. Try to restore valid display blob from Base64 sources
                        if (s.bgImage && s.bgImage.startsWith('data:')) {
                            const parts = s.bgImage.split(',');
                            const mime = parts[0].match(/:(.*?);/)[1];
                            const b64 = parts[1];
                            displayUrl = base64ToBlobUrl(b64.trim(), mime);
                        } else if (s.originalImage && s.originalImage.startsWith('data:')) {
                            const parts = s.originalImage.split(',');
                            const mime = parts[0].match(/:(.*?);/)[1];
                            const b64 = parts[1];
                            displayUrl = base64ToBlobUrl(b64, mime);
                        }

                        return {
                            ...s,
                            displayImage: displayUrl || s.displayImage
                        };
                    });

                    setSlides(rehydratedSlides);
                    setAppStatus('selecting');
                    addLog("🔄 Session Restored from Auto-Save.");
                } else {
                    clearSessionIDB();
                }
            }
        };
        initRestore();
    }, []);

    useEffect(() => {
        if (slides.length > 0) {
            saveSessionToIDB(slides);
        }
    }, [slides]);


    return (
        <div className="min-h-screen text-zinc-900 p-6 md:p-12 flex flex-col items-center max-w-7xl mx-auto font-sans bg-zinc-50">
            {/* Header: Clean & Minimal */}
            <header className="w-full flex justify-between items-center mb-10 pb-6 border-b border-zinc-200">
                <div className="flex flex-col">
                    <div className="flex items-center gap-3 mb-1">
                        <span className="text-zinc-900 text-xl font-bold">●</span>
                        <h1 className="text-4xl font-bold tracking-tight text-zinc-900">NotebookLM <span className="font-light text-zinc-400">Remaster</span></h1>
                    </div>
                    <p className="text-sm text-zinc-500 pl-7 leading-relaxed">AI FORCE MULTIPLIER • GEMINI 3 PRO</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${apiKey ? 'bg-zinc-100 border-zinc-200 text-zinc-700' : 'bg-red-50 border-red-200 text-red-600'}`}>
                        <div className={`w-2 h-2 rounded-full ${apiKey ? 'bg-zinc-900' : 'bg-red-500'}`}></div>
                        <span className="text-[10px] font-bold tracking-wider">{apiKey ? 'SYSTEM ONLINE' : 'API KEY REQUIRED'}</span>
                    </div>
                </div>
            </header>

            {/* Main Control Grid */}
            <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-8 mb-12 animate-fade-in-up">

                {/* Left Panel: Inputs & Configuration */}
                <div className="md:col-span-5 space-y-6">
                    <div className="glass p-8 rounded-2xl relative overflow-hidden group">
                        {/* API Key Section */}
                        <div className="mb-6">
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">System Access</label>
                                <div className="flex items-center gap-2">
                                    {apiKey && <span className="text-[10px] text-zinc-600">● READY</span>}
                                </div>
                            </div>
                            <div className="relative group/input">
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={handleApiKeyChange}
                                    className="w-full bg-zinc-50 border border-zinc-200 rounded p-2 pl-8 text-xs text-zinc-800 outline-none focus:border-zinc-400 focus:bg-white transition-all placeholder-zinc-400"
                                    placeholder="Gemini API Key (Auto-saved)"
                                />
                                <span className="absolute left-2.5 top-2 text-[10px] text-zinc-400">🔑</span>
                            </div>
                        </div>

                        {/* Import Section */}
                        <div>
                            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 block">02. Source Material</label>
                            {appStatus === 'idle' ? (
                                <div
                                    className="border-2 border-dashed border-zinc-200 rounded-xl p-8 text-center cursor-pointer hover:border-zinc-400 hover:bg-zinc-50 transition-all group/drop relative"
                                    onClick={() => document.getElementById('fileInput').click()}
                                >
                                    <input type="file" id="fileInput" accept="application/pdf, image/*" multiple className="hidden" onChange={(e) => setImportFiles(e.target.files)} />
                                    <div className="text-4xl mb-4 text-zinc-300 group-hover/drop:text-zinc-600 transition-colors transform group-hover/drop:scale-110 duration-200">📂</div>
                                    <p className="text-zinc-900 font-bold mb-1">Import PDF or Images</p>
                                    <p className="text-xs text-zinc-500">{importFiles ? `${importFiles.length} file(s) ready` : "Drag & Drop or Click to Browse"}</p>
                                </div>
                            ) : (
                                <div className="p-6 bg-zinc-50 rounded-xl border border-zinc-200 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="text-2xl">📑</div>
                                        <div>
                                            <p className="font-bold text-zinc-900 text-sm">Source Loaded</p>
                                            <p className="text-xs text-zinc-500">{slides.length} Slides Processed</p>
                                        </div>
                                    </div>
                                    <button onClick={() => setAppStatus('idle')} className="text-xs text-zinc-400 hover:text-zinc-700 underline">Reset</button>
                                </div>
                            )}

                            {/* Primary CTA */}
                            {appStatus === 'idle' && importFiles && apiKey && (
                                <button
                                    onClick={handleStartImport}
                                    className="mt-6 w-full py-4 bg-zinc-900 text-white font-bold tracking-wide rounded-lg hover:bg-zinc-800 hover:shadow-lg active:scale-[0.99] transition-all btn-base"
                                >
                                    INITIALIZE SCAN SEQUENCE
                                </button>
                            )}

                            {/* UX: Onboarding / Empty State Actions */}
                            {appStatus === 'idle' && !importFiles && (
                                <div className="mt-8 pt-6 border-t border-zinc-200">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">or try now</h3>
                                    </div>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={handleLoadSample}
                                            className="flex-1 bg-white hover:bg-zinc-50 border border-zinc-200 hover:border-indigo-300 p-3 rounded-lg flex items-center justify-center gap-3 transition-all group shadow-sm hover:shadow-md"
                                        >
                                            <span className="text-xl grayscale group-hover:grayscale-0 transition-all">✨</span>
                                            <div className="text-left">
                                                <div className="text-xs font-bold text-zinc-700 group-hover:text-indigo-600 transition-colors">Load Sample Slide</div>
                                                <div className="text-[10px] text-zinc-400">Test the "Hand-Drawn to Pro" flow</div>
                                            </div>
                                        </button>
                                    </div>

                                    {/* Visual Flow Hint */}
                                    <div className="mt-8 flex justify-center items-center gap-4 opacity-30 select-none pointer-events-none">
                                        <div className="text-center">
                                            <div className="w-8 h-10 border border-current rounded flex items-center justify-center">📄</div>
                                            <div className="text-[9px] mt-1 font-mono">INPUT</div>
                                        </div>
                                        <div className="text-xs">→</div>
                                        <div className="text-center">
                                            <div className="w-10 h-10 border border-current rounded-full flex items-center justify-center">🔮</div>
                                            <div className="text-[9px] mt-1 font-mono">AI REMASTER</div>
                                        </div>
                                        <div className="text-xs">→</div>
                                        <div className="text-center">
                                            <div className="w-12 h-8 border-2 border-current rounded flex items-center justify-center">🖥️</div>
                                            <div className="text-[9px] mt-1 font-mono">4K PPTX</div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Panel: Mission Control (Status) */}
                <div className="md:col-span-7 space-y-4 flex flex-col">
                    <div className="glass p-1 rounded-2xl flex-1 flex flex-col min-h-[300px]">
                        <div className="p-4 border-b border-zinc-200 bg-zinc-50 rounded-t-xl flex justify-between items-center">
                            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                                <span className={`w-1.5 h-1.5 rounded-full ${appStatus === 'idle' ? 'bg-zinc-400' : 'bg-indigo-600 animate-pulse'}`}></span>
                                System Status
                            </span>
                            <span className="font-mono text-[10px] text-zinc-400">ID: {Date.now().toString().slice(-6)}</span>
                        </div>

                        <div className="flex-1 p-8 flex flex-col justify-center items-center text-center relative overflow-hidden">
                            {/* Background Graphic */}
                            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.02)_0%,transparent_70%)] pointer-events-none"></div>

                            {appStatus === 'idle' ? (
                                <div className="text-zinc-600 space-y-2 max-w-sm">
                                    <div className="text-4xl mb-2 opacity-30 text-zinc-300">📡</div>
                                    <p className="font-medium text-zinc-700">System Standby</p>
                                    <p className="text-sm text-zinc-500">Awaiting user configuration. Please provide authentication and source material to begin.</p>
                                </div>
                            ) : (
                                <div className="w-full max-w-md space-y-6 relative z-10">
                                    <div className="flex justify-between items-end">
                                        <span className="text-2xl font-bold text-zinc-900 uppercase tracking-tight">{appStatus}</span>
                                        <span className="font-mono text-zinc-900 text-xl">{Math.round((progress.current / Math.max(progress.total, 1)) * 100)}%</span>
                                    </div>

                                    {/* Progress Bar (Minimal) */}
                                    <div className="h-1.5 bg-zinc-100 rounded-full overflow-hidden w-full">
                                        <div
                                            className="h-full bg-indigo-600 transition-all duration-300 ease-out shadow-sm"
                                            style={{ width: `${(progress.current / Math.max(progress.total, 1)) * 100}%` }}
                                        ></div>
                                    </div>

                                    <div className="bg-white rounded-lg p-3 shadow-md ring-1 ring-black/5 text-left">
                                        <span className="text-xs text-zinc-400 font-mono block mb-1">$ processing...</span>
                                        <p className="text-sm text-zinc-800 font-mono animate-pulse">{progress.msg}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Collapsible Logs */}
                        <div className="bg-zinc-50 p-2 max-h-32 overflow-y-auto font-mono text-[10px] text-zinc-500 border-t border-zinc-200 mx-2 mb-2 rounded">
                            {logs.length > 0 ? logs.map((l, i) => <div key={i} className="py-0.5 border-b border-zinc-200 last:border-0">{l}</div>) : <div className="text-center italic opacity-30">No active logs</div>}
                        </div>
                    </div>
                </div>
            </div>

            {/* Action Bar (Visible in Selecting/Done) */}
            {(appStatus === 'selecting' || appStatus === 'done' || appStatus === 'processing') && (
                <div className="sticky top-6 z-40 w-full bg-white/90 backdrop-blur-xl border border-zinc-200 p-4 rounded-2xl shadow-xl flex flex-col md:flex-row justify-between items-center mb-12 animate-fade-in-up">

                    {/* Selection Status */}
                    <div className="flex items-center gap-6 mb-4 md:mb-0">
                        <button onClick={toggleAll} className="text-xs font-bold text-zinc-500 hover:text-zinc-900 transition-colors uppercase tracking-wider">
                            {selectAll ? '[-] Deselect All' : '[+] Select All'}
                        </button>
                        <div className="text-sm font-bold bg-zinc-100 px-3 py-1 rounded-full border border-zinc-200">
                            <span className="text-zinc-900">{slides.filter(s => s.isSelected).length}</span> <span className="text-zinc-500">Selected</span>
                        </div>
                    </div>

                    {/* Primary Actions */}
                    <div className="flex gap-4">
                        {(() => {
                            // Count any SELECTED slides
                            const selectedCount = slides.filter(s => s.isSelected).length;

                            if (slides.length === 0) return null;

                            if (selectedCount === 0) {
                                return (
                                    <button
                                        disabled
                                        className="bg-zinc-100 text-zinc-400 font-bold text-xs uppercase tracking-wide px-6 py-3 rounded-lg border border-zinc-200 cursor-not-allowed shadow-none"
                                    >
                                        Select Slides to Remaster
                                    </button>
                                );
                            }

                            return (
                                <button
                                    onClick={() => setTimeout(runBatchRemaster, 0)}
                                    className="bg-zinc-900 hover:bg-violet-600 text-white font-bold text-xs uppercase tracking-wide px-6 py-3 rounded-lg shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center gap-2 group animate-in fade-in zoom-in duration-300"
                                >
                                    <span className="text-lg group-hover:rotate-12 transition-transform">✨</span>
                                    Run Magic Remaster ({selectedCount})
                                </button>
                            );
                        })()}
                        <button
                            onClick={() => generatePptx(slides, presentationRatio)}
                            className="px-8 py-3 bg-white text-zinc-900 text-sm font-bold rounded-lg shadow-sm border border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300 transition-all flex items-center gap-2"
                        >
                            <span>💾</span> EXPORT PPTX
                        </button>
                    </div>
                </div>
            )}

            {/* Slide Grid */}
            {slides.length > 0 && (
                <div className="w-full grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pb-20">
                    {slides.map((slide) => {
                        if (slide.status === 'PROCESSING') {
                            return <SkeletonSlide key={slide.id} />;
                        }
                        return (
                            <div
                                key={slide.id}
                                onClick={() => toggleSelection(slide.id)}
                                className={`relative group rounded-xl overflow-hidden cursor-pointer transition-all duration-300 border bg-white ${slide.isSelected
                                    ? 'border-zinc-900 ring-1 ring-zinc-900/10 shadow-lg'
                                    : 'border-zinc-200 hover:border-zinc-300 hover:-translate-y-1 hover:shadow-md'
                                    }`}
                            >
                                {/* Status Badge */}
                                <div className="absolute top-3 right-3 z-20 flex flex-col items-end gap-1">
                                    <span className={`px-2 py-1 text-[10px] font-bold rounded-md shadow-sm border ${slide.status === 'REMASTERED' ? 'bg-zinc-900 text-white border-zinc-900' :
                                        slide.status === 'PROCESSING' ? 'bg-blue-500 text-white border-blue-600 animate-pulse' :
                                            slide.status === 'ERROR' ? 'bg-red-500 text-white border-red-600' :
                                                'bg-white text-zinc-500 border-zinc-200'
                                        }`}>
                                        {slide.status}
                                    </span>
                                </div>

                                {/* Selection Checkbox */}
                                <div className={`absolute top-3 left-3 z-20 w-6 h-6 rounded-md border flex items-center justify-center transition-all duration-200 shadow-sm ${slide.isSelected
                                    ? 'bg-zinc-900 border-zinc-900 scale-100'
                                    : 'bg-white/80 border-zinc-300 text-transparent hover:border-zinc-400'
                                    }`}>
                                    {slide.isSelected && <span className="text-white text-sm font-bold">✓</span>}
                                </div>

                                {/* Comparing Image Container */}
                                <div
                                    className="aspect-video w-full bg-zinc-100 relative group/image overflow-hidden"
                                    onMouseMove={(e) => {
                                        if (slide.status !== 'REMASTERED') return;
                                        const rect = e.currentTarget.getBoundingClientRect();
                                        const x = e.clientX - rect.left;
                                        const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
                                        e.currentTarget.style.setProperty('--compare-pos', `${pct}%`);
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.setProperty('--compare-pos', '50%');
                                    }}
                                    style={{ '--compare-pos': '100%' }} // Default show full remastered
                                >
                                    {/* 1. Underlying: Original (Only if Remastered) */}
                                    {slide.status === 'REMASTERED' && (
                                        <img
                                            src={slide.originalImage}
                                            className="absolute inset-0 w-full h-full object-cover"
                                        />
                                    )}

                                    {/* 2. Overlying: New Image (Clipped) */}
                                    <div
                                        className={`absolute inset-0 w-full h-full ${slide.status === 'REMASTERED' ? 'compare-clip' : ''}`}
                                        style={slide.status === 'REMASTERED' ? { clipPath: 'polygon(0 0, var(--compare-pos) 0, var(--compare-pos) 100%, 0 100%)' } : {}}
                                    >
                                        <img
                                            src={slide.displayImage}
                                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                            loading="lazy"
                                        />
                                        {/* Text Overlay Hints */}
                                        {!comesFromOriginal(slide) && slide.textData.map((t, idx) => (
                                            <div key={idx} className="absolute border border-blue-500/30 bg-blue-500/5" style={{ left: `${t.x_pct}%`, top: `${t.y_pct}%`, width: `${t.width_pct}%`, height: '10%' }} />
                                        ))}
                                    </div>

                                    {/* Slider Handle */}
                                    {slide.status === 'REMASTERED' && (
                                        <div
                                            className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] z-10 pointer-events-none"
                                            style={{ left: 'var(--compare-pos)' }}
                                        >
                                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center">
                                                <svg className="w-3 h-3 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l4-4 4 4m0 6l-4 4-4-4" transform="rotate(90 12 12)" /></svg>
                                            </div>
                                        </div>
                                    )}

                                    {/* Hover Actions */}
                                    <div className="absolute inset-0 bg-white/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-3 backdrop-blur-[2px]" onClick={e => e.stopPropagation()}>
                                        <button
                                            onClick={() => setPreviewTarget(slide)}
                                            className="w-10 h-10 flex items-center justify-center rounded-full bg-white text-zinc-700 hover:text-black transition-all border border-zinc-200 hover:scale-110 shadow-sm"
                                            title="View Fullscreen"
                                        >
                                            🔍
                                        </button>
                                        <button
                                            onClick={() => { if (!slide.isSelected) toggleSelection(slide.id); setStudioTarget({ ...slide }); }}
                                            className="px-4 py-2 rounded-full bg-zinc-900 text-white font-bold text-xs shadow-lg hover:bg-zinc-800 hover:scale-105 transition-all flex items-center gap-1"
                                            title="Open Studio"
                                        >
                                            <span>🎨</span> EDIT / AI
                                        </button>
                                    </div>
                                </div>

                                {/* Footer Info */}
                                <div className="p-3 bg-white border-t border-zinc-100 flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                                    <span>SLIDE {String(slide.id).padStart(2, '0')}</span>
                                    <span>{slide.originalImage ? 'IMG' : 'RAW'}</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {studioTarget && (
                <StudioModal
                    isOpen={!!studioTarget}
                    slide={studioTarget}
                    apiKey={apiKey}
                    modelConfig={modelConfig}
                    ratio={presentationRatio}
                    onPreview={setPreviewTarget}
                    onClose={() => setStudioTarget(null)}
                    onSave={(newImageBase64, newTextData) => {
                        setSlides(prev => prev.map(s => s.id === studioTarget.id ? {
                            ...s,
                            bgImage: newImageBase64, // Combined Image
                            displayImage: newImageBase64,
                            textData: newTextData,
                            status: 'REMASTERED',
                            bgType: 'STUDIO_EDITED'
                        } : s));
                        setStudioTarget(null);
                        addLog(`✅ Slide ${studioTarget.id} Studio Edit Saved.`);
                    }}
                />
            )}

            {/* Image Preview Overlay */}
            {previewTarget && (
                <div
                    className="fixed inset-0 z-[200] bg-black/95 flex items-center justify-center p-8 animate-in fade-in duration-200 cursor-zoom-out"
                    onClick={() => setPreviewTarget(null)}
                >
                    <button
                        className="absolute top-6 right-6 text-white/70 hover:text-white transition-colors z-[210] p-2 hover:bg-white/10 rounded-full"
                        onClick={() => setPreviewTarget(null)}
                    >
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                    <img
                        src={typeof previewTarget === 'string' ? previewTarget : (previewTarget.displayImage || previewTarget.originalImage)}
                        className="max-w-full max-h-full object-contain rounded shadow-2xl cursor-default"
                        onClick={e => e.stopPropagation()}
                    />
                    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-white/50 text-xs font-mono bg-black/50 px-4 py-2 rounded-full backdrop-blur-md">
                        {typeof previewTarget === 'string' ? 'PREVIEW' : `PREVIEW: SLIDE ${String(previewTarget.id).padStart(2, '0')}`}
                    </div>
                </div>
            )}
        </div>
    );
};

export default App;
