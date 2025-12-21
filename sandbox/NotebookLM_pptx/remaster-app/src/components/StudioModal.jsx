import React, { useState, useRef, useEffect } from 'react';
import { callGemini } from '../utils/gemini';

const StudioModal = ({ isOpen, slide, onClose, onSave, apiKey, modelConfig, ratio, onPreview }) => {
    if (!isOpen || !slide) return null;

    // -- State --
    const [mode, setMode] = useState('cursor'); // cursor, brush, eraser, text, ai (dropper removed)
    const [brushColor, setBrushColor] = useState('#000000');
    const [brushSize, setBrushSize] = useState(10);
    const [texts, setTexts] = useState(slide.textData ? JSON.parse(JSON.stringify(slide.textData)) : []);
    const [selectedTextId, setSelectedTextId] = useState(null);

    // Current working background (initialized from slide, but mutable in session)
    const [workingBgImage, setWorkingBgImage] = useState(slide.bgImage || slide.originalImage);

    // UX: Comparision & Onion Skin
    const [onionOpacity, setOnionOpacity] = useState(0); // 0.0 to 1.0

    // AI State
    const [aiPrompt, setAiPrompt] = useState("");
    const [aiCreativity, setAiCreativity] = useState(0.5); // 0.0 to 1.0
    const [isAiGenerating, setIsAiGenerating] = useState(false);
    const [aiError, setAiError] = useState("");
    const [aiCandidateCount, setAiCandidateCount] = useState(1);
    const [aiCandidates, setAiCandidates] = useState(null); // Array of base64 images

    // Canvas Refs
    const containerRef = useRef(null);
    const canvasRef = useRef(null); // Paint Layer
    const bgRef = useRef(null); // Base Image

    // Undo/Redo
    const [history, setHistory] = useState([]);
    const [historyStep, setHistoryStep] = useState(-1);

    // Helpers
    const [scale, setScale] = useState(1); // Auto-fit scale
    const [zoom, setZoom] = useState(1); // User zoom multiplier
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const panStart = useRef({ x: 0, y: 0 });

    const [isDrawing, setIsDrawing] = useState(false);
    const lastPos = useRef({ x: 0, y: 0 });

    useEffect(() => {
        // Initialize Canvas Size to match Image
        const img = new Image();
        img.src = slide.bgImage || slide.originalImage;
        img.onload = () => {
            if (canvasRef.current && containerRef.current) {
                canvasRef.current.width = img.width;
                canvasRef.current.height = img.height;

                // Fit to container
                const contW = containerRef.current.clientWidth;
                const contH = containerRef.current.clientHeight;
                const scaleW = contW / img.width;
                const scaleH = contH / img.height;
                setScale(Math.min(scaleW, scaleH) * 0.9); // 90% fit


                // Save initial blank state
                saveHistory();
            }
        };
    }, [slide]);

    // Fast-forward history on mount
    const updateHistory = (newHistory, newStep) => {
        setHistory(newHistory);
        setHistoryStep(newStep);
    }

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Ignore shortcuts if user is typing in an input or textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // Tools
            switch (e.key.toLowerCase()) {
                case 'v': setMode('cursor'); break;
                case 'b': setMode('brush'); break;
                case 'e': setMode('eraser'); break;
                case 't': setMode('text'); break;
                case 'h': setMode('hand'); break;
                case 'a': setMode('ai'); break;
            }

            // Undo / Redo
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
                e.preventDefault();
                if (e.shiftKey) {
                    redo();
                } else {
                    undo();
                }
            }
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
                e.preventDefault();
                redo();
            }

            // Save
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
                e.preventDefault();
                handleDownload('save');
            }

            // Delete (Text)
            if (e.key === 'Delete' || e.key === 'Backspace') {
                if (mode === 'text' || mode === 'cursor') deleteText();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [mode, historyStep, history, selectedTextId]);

    // AI Logic
    const runAiRemaster = async () => {
        if (!aiPrompt) return alert("Please enter instructions for the AI.");
        setIsAiGenerating(true);
        setAiError("");
        setAiCandidates(null);

        try {
            // 1. Capture Current Canvas State (Composite of BG + Paint) to send to AI
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = canvasRef.current.width;
            tempCanvas.height = canvasRef.current.height;
            const ctx = tempCanvas.getContext('2d');
            ctx.drawImage(bgRef.current, 0, 0, tempCanvas.width, tempCanvas.height);
            ctx.drawImage(canvasRef.current, 0, 0);

            const currentVisual = tempCanvas.toDataURL('image/jpeg', 0.8);
            const imagePart = {
                inline_data: { mime_type: "image/jpeg", data: currentVisual.split(',')[1] }
            };

            // 2. Construct Prompt based on Creativity
            const strengthDesc = aiCreativity < 0.4
                ? "Strictly maintain original layout and structure. Enhance only resolution and lighting. High fidelity."
                : (aiCreativity > 0.7
                    ? "Reimagine the visual style completely. Use modern, trending aesthetic. High impact, 8k resolution."
                    : "Refine and polish. Remove artifacts, improve color grading and sharpness. Professional presentation quality.");

            const prompt = `
            You are an expert Presentation Designer.
            [TASK] Remaster this slide image to be visually stunning and professional.
            [INSTRUCTIONS] ${aiPrompt}
            [MODE] ${strengthDesc} (Creativity: ${aiCreativity})
            [REQUIREMENTS] 
            - Output Resolution: 4K, Ultra HD.
            - Style: Modern, clean, professional.
            - Maintain Aspect Ratio: ${ratio || '16:9'}. 
            - NO TEXT IN OUTPUT unless part of the artistic background.
            - Return ONLY the generated image.
            `;

            // 3. API Call Helper (for parallel execution)
            const fetchImage = async () => {
                const res = await callGemini(apiKey, modelConfig.image, {
                    contents: [{ parts: [{ text: prompt }, imagePart] }],
                    generationConfig: {
                        responseModalities: ["TEXT", "IMAGE"]
                    }
                });
                return res;
            };

            // 4. Execute (Parallel if count > 1)
            const promises = [];
            for (let i = 0; i < aiCandidateCount; i++) {
                promises.push(fetchImage());
            }

            const results = await Promise.allSettled(promises);
            const newCandidates = [];
            let lastError = null;

            results.forEach(res => {
                if (res.status === 'fulfilled') {
                    const data = res.value;
                    if (data.candidates) {
                        data.candidates.forEach(c => {
                            // Check Safety
                            if (c.finishReason === 'SAFETY') {
                                lastError = { message: "Generation blocked by Safety Filters." };
                                return;
                            }

                            const p = c.content?.parts?.find(p => p.inline_data || p.inlineData);
                            if (p) {
                                const raw = p.inline_data || p.inlineData;
                                newCandidates.push(`data:${raw.mime_type};base64,${raw.data}`);
                            } else {
                                // Check for Text fallback (common if model config is wrong)
                                const textP = c.content?.parts?.find(p => p.text);
                                if (textP) {
                                    console.warn("Model returned text:", textP.text);
                                    lastError = { message: "Model returned text instead of image. Check Model ID." };
                                }
                            }
                        });
                    }
                } else {
                    console.error("Partial Failure:", res.reason);
                    lastError = res.reason;
                }
            });

            if (newCandidates.length > 0) {
                setAiCandidates(newCandidates);
                // Always show selection UI, never auto-apply
                // This fixes the issue where user cannot see the result before it vanishes / commits
            } else {
                throw new Error(lastError ? lastError.message : "Image generation failed (No candidates returned).");
            }

        } catch (e) {
            console.error(e);
            setAiError(e.message);
        } finally {
            setIsAiGenerating(false);
        }
    };

    const applyAiResult = async (base64) => {
        // 1. Update State
        setWorkingBgImage(base64);

        // 2. Clear Paint layer (baked in)
        const pCtx = canvasRef.current.getContext('2d');
        pCtx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);

        // 3. Save History (Pass new BG explicitely because State update is async)
        saveHistory(null, base64);

        setAiCandidates(null); // Clear selection UI
        setMode('cursor'); // Exit AI mode
    };

    // -- History Logic --
    const saveHistory = (overrideTexts = null, overrideBg = null) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const dataUrl = canvas.toDataURL(); // Paint layer
        // Use provided texts or current state (deep copy)
        const textData = JSON.parse(JSON.stringify(overrideTexts || texts));

        // Use provided BG or current state
        const bgSrc = overrideBg || workingBgImage;

        const newHistory = history.slice(0, historyStep + 1);
        newHistory.push({ image: dataUrl, texts: textData, bgImage: bgSrc }); // Store BG too

        // Limit history
        if (newHistory.length > 20) newHistory.shift();
        setHistory(newHistory);
        setHistoryStep(newHistory.length - 1);
    };

    const undo = () => {
        if (historyStep > 0) {
            const prevStep = historyStep - 1;
            loadHistory(history[prevStep]);
            setHistoryStep(prevStep);
        }
    };

    const redo = () => {
        if (historyStep < history.length - 1) {
            const nextStep = historyStep + 1;
            loadHistory(history[nextStep]);
            setHistoryStep(nextStep);
        }
    };

    const loadHistory = (stepData) => {
        if (!stepData) return;

        // Robust handling
        const paintSrc = typeof stepData === 'string' ? stepData : stepData.image;
        const textData = typeof stepData === 'string' ? [] : stepData.texts || [];
        const bgSrc = stepData.bgImage || slide.originalImage;

        // 1. Restore Background
        if (bgSrc) {
            setWorkingBgImage(bgSrc);
        }

        // 2. Restore Texts
        setTexts(textData);

        // 3. Restore Paint Layer
        const img = new Image();
        img.src = paintSrc;
        img.onload = () => {
            const ctx = canvasRef.current.getContext('2d');
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            ctx.drawImage(img, 0, 0);
        };

        // Restore Texts
        if (textData) {
            setTexts(JSON.parse(JSON.stringify(textData)));
        }
    };

    // -- Drawing Logic --
    const getPos = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const scaleX = canvasRef.current.width / rect.width;
        const scaleY = canvasRef.current.height / rect.height;
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    };

    const startDraw = (e) => {
        if (mode === 'hand') {
            setIsPanning(true);
            panStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
            return;
        }

        if (mode === 'cursor' || mode === 'text') {
            // Handle Text Deselect
            if (e.target === canvasRef.current) setSelectedTextId(null);
            return;
        }

        setIsDrawing(true);
        const pos = getPos(e);
        lastPos.current = pos;

        const ctx = canvasRef.current.getContext('2d');
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.lineWidth = brushSize;
        ctx.strokeStyle = brushColor;
        ctx.globalCompositeOperation = mode === 'eraser' ? 'destination-out' : 'source-over';

        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(pos.x, pos.y); // Dot
        ctx.stroke();
    };


    const draw = (e) => {
        if (isPanning) {
            setPan({
                x: e.clientX - panStart.current.x,
                y: e.clientY - panStart.current.y
            });
            return;
        }

        if (!isDrawing) return;
        const pos = getPos(e);
        const ctx = canvasRef.current.getContext('2d');
        ctx.beginPath();
        ctx.moveTo(lastPos.current.x, lastPos.current.y);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        lastPos.current = pos;
    };

    const stopDraw = () => {
        if (isPanning) {
            setIsPanning(false);
            return;
        }
        if (isDrawing) {
            setIsDrawing(false);
            saveHistory();
        }
    };

    // -- Text Logic --
    const handleTextDrag = (idx, e) => {
        // Simple drag implementation could be complex in React without lib. 
        // For now, we will assume user uses the inputs to fine-tune or we implement basic delta drag
    };

    // We'll use a simple "Click to select, Drag unavailable without lib, use Nudge or Inputs" 

    const draggingText = useRef(null);
    const resizingText = useRef(null);
    const rotatingText = useRef(null);

    const startTextDrag = (e, index) => {
        if (mode !== 'cursor') return;
        e.preventDefault();
        e.stopPropagation();
        setSelectedTextId(index);
        draggingText.current = {
            index,
            startX: e.clientX,
            startY: e.clientY,
            startPctX: texts[index].x_pct,
            startPctY: texts[index].y_pct
        };
    };

    const startTextRotate = (e, index) => {
        e.preventDefault();
        e.stopPropagation();
        // Calculate center of the text box for rotation origin
        const el = document.getElementById(`text-box-${index}`);
        const rect = el.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        rotatingText.current = {
            index,
            centerX,
            centerY,
            startRotation: texts[index].rotation || 0,
            startAngle: Math.atan2(e.clientY - centerY, e.clientX - centerX)
        };
    };

    const startTextResize = (e, index) => {
        e.preventDefault();
        e.stopPropagation();
        resizingText.current = {
            index,
            startX: e.clientX,
            startWidth: texts[index].width_pct || 20 // default fallbacks
        };
    };

    const onMouseMoveGlobal = (e) => {
        if (draggingText.current) {
            const { index, startX, startY, startPctX, startPctY } = draggingText.current;
            const rect = containerRef.current.getBoundingClientRect();
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;

            const deltaPctX = (deltaX / rect.width) * 100;
            const deltaPctY = (deltaY / rect.height) * 100;

            const newTexts = [...texts];
            newTexts[index].x_pct = startPctX + deltaPctX;
            newTexts[index].y_pct = startPctY + deltaPctY;
            setTexts(newTexts);
        } else if (resizingText.current) {
            const { index, startX, startWidth } = resizingText.current;
            const rect = containerRef.current.getBoundingClientRect();
            const deltaX = e.clientX - startX;
            const deltaPctW = (deltaX / rect.width) * 100;

            const newTexts = [...texts];
            newTexts[index].width_pct = Math.max(5, startWidth + deltaPctW); // Min width 5%
            setTexts(newTexts);
        } else if (rotatingText.current) {
            const { index, centerX, centerY, startRotation, startAngle } = rotatingText.current;
            const currentAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
            const deltaAngle = (currentAngle - startAngle) * (180 / Math.PI);

            const newTexts = [...texts];
            newTexts[index].rotation = (startRotation + deltaAngle);
            setTexts(newTexts);
        }
    };

    const onMouseUpGlobal = () => {
        if (draggingText.current || resizingText.current || rotatingText.current) {
            saveHistory(); // Auto-save after manipulation
        }
        draggingText.current = null;
        resizingText.current = null;
        rotatingText.current = null;
    };

    useEffect(() => {
        window.addEventListener('mousemove', onMouseMoveGlobal);
        window.addEventListener('mouseup', onMouseUpGlobal);
        return () => {
            window.removeEventListener('mousemove', onMouseMoveGlobal);
            window.removeEventListener('mouseup', onMouseUpGlobal);
        };
    }, [texts]); // Re-bind for simplicity or use refs for texts

    const addText = () => {
        const newTexts = [...texts, {
            content: "New Text", role: "Body",
            x_pct: 40, y_pct: 40, width_pct: 20,
            color_hex: "#ffffff", fontSize: 24, fontWeight: "normal",
            rotation: 0
        }];
        setTexts(newTexts);
        saveHistory(newTexts);
    };

    const deleteText = () => {
        if (selectedTextId !== null) {
            const newTexts = texts.filter((_, i) => i !== selectedTextId);
            setTexts(newTexts);
            setSelectedTextId(null);
            saveHistory(newTexts);
        }
    };

    // -- Export Logic --
    const handleDownload = async (formatOrSave) => {
        // 1. Create Composition Canvas
        const finalCanvas = document.createElement('canvas');
        finalCanvas.width = canvasRef.current.width;
        finalCanvas.height = canvasRef.current.height;
        const fCtx = finalCanvas.getContext('2d');

        // 2. Draw Base
        fCtx.drawImage(bgRef.current, 0, 0, finalCanvas.width, finalCanvas.height);

        // 3. Draw Paint Layer
        fCtx.drawImage(canvasRef.current, 0, 0);

        if (formatOrSave === 'save') {
            // Save back to App
            const combinedDataUrl = finalCanvas.toDataURL('image/png', 1.0);
            onSave(combinedDataUrl, texts);
            return;
        }

        // 4. Draw Texts (Rasterize) for Export Only
        // ... (existing text rasterization for export) ...
        const format = formatOrSave;


        // 4. Draw Texts (Rasterize)
        texts.forEach(t => {
            const x = (t.x_pct / 100) * finalCanvas.width;
            const y = (t.y_pct / 100) * finalCanvas.height;
            const w = (t.width_pct / 100) * finalCanvas.width;

            // Approximate Styling
            const fontSize = (t.fontSize || (t.role === 'Title' ? 40 : 20)) * (finalCanvas.width / 1280);
            const isBold = t.fontWeight === 'bold' || t.role === 'Title';

            // Match CSS Font Stack exactly to ensure similar metrics
            const fontFamily = t.fontFamily || '"Inter", "Noto Sans JP", sans-serif';

            fCtx.font = `${isBold ? 'bold' : 'normal'} ${fontSize}px ${fontFamily}`;
            fCtx.fillStyle = t.color_hex || '#ffffff';
            fCtx.textAlign = 'left';
            fCtx.textBaseline = 'top';

            // Padding Adjustment for p-1 (approx 4px at 1280px scale)
            const padding = 4 * (finalCanvas.width / 1280);
            const adjX = x + padding;
            const adjY = y + padding;
            const adjW = w - (padding * 2);

            // Strict Wrap (Character-based for CJK support)
            const paragraphs = t.content.split('\n');
            let testY = adjY;
            const lineHeight = fontSize * 1.5; // Slightly deeper leading for readability in export

            paragraphs.forEach(paragraph => {
                let line = '';
                for (let i = 0; i < paragraph.length; i++) {
                    const char = paragraph[i];
                    const testLine = line + char;
                    const metrics = fCtx.measureText(testLine);

                    // Check if adding this character exceeds width
                    if (metrics.width > adjW && line.length > 0) {
                        fCtx.fillText(line, adjX, testY);
                        line = char;
                        testY += lineHeight;
                    } else {
                        line = testLine;
                    }
                }
                fCtx.fillText(line, adjX, testY); // Draw remaining characters
                testY += lineHeight; // Newline for next paragraph
            });
        });

        // 5. Download
        const link = document.createElement('a');
        link.download = `Studio_Export_${Date.now()}.${format}`;
        link.href = finalCanvas.toDataURL(`image/${format}`, 0.9);
        link.click();
    };

    // -- Pan/Zoom Helpers --
    const handleZoom = (delta) => {
        setZoom(prev => Math.max(0.1, Math.min(5, prev + delta)));
    };

    const resetView = () => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    };

    const renderScale = scale * zoom;

    return (
        <div className="fixed inset-0 z-[100] flex flex-col bg-white text-zinc-900">
            {/* Header */}
            <div className="h-14 bg-white shadow-sm flex items-center justify-between px-4 z-20 relative">
                <div className="flex items-center gap-4">
                    <h2 className="font-semibold tracking-tight text-zinc-900 flex items-center gap-2"><span className="text-zinc-400">■</span> Studio Mode</h2>
                    <div className="flex bg-zinc-100 rounded p-1 gap-1">
                        <button onClick={undo} disabled={historyStep <= 0} className="p-2 hover:bg-zinc-200 rounded disabled:opacity-30 text-zinc-600" title="Undo">↩</button>
                        <button onClick={redo} disabled={historyStep >= history.length - 1} className="p-2 hover:bg-zinc-200 rounded disabled:opacity-30 text-zinc-600" title="Redo">↪</button>
                    </div>
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <button onClick={() => setMode('cursor')} className={`p-2 rounded ${mode === 'cursor' ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-100 text-zinc-600'}`} title="Select/Move (v)">↖</button>
                    <button onClick={() => setMode('hand')} className={`p-2 rounded ${mode === 'hand' ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-100 text-zinc-600'}`} title="Pan (H)">✋</button>
                    <button onClick={() => setMode('brush')} className={`p-2 rounded ${mode === 'brush' ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-100 text-zinc-600'}`} title="Brush (b)">🖌️</button>
                    <button onClick={() => setMode('eraser')} className={`p-2 rounded ${mode === 'eraser' ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-100 text-zinc-600'}`} title="Eraser (e)">🧹</button>
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <button onClick={() => setMode('ai')} className={`p-2 rounded flex items-center gap-2 ${mode === 'ai' ? 'bg-indigo-600 text-white shadow-sm' : 'hover:bg-zinc-100 text-zinc-600'}`} title="AI Remaster">
                        <span>✨</span> <span className="text-xs font-bold hidden md:inline">AI MAGIC</span>
                    </button>

                    {/* Zoom Controls */}
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <div className="flex bg-zinc-100 rounded p-1 items-center">
                        <button onClick={() => handleZoom(-0.1)} className="px-2 hover:bg-zinc-200 rounded text-zinc-600">-</button>
                        <span className="text-xs w-12 text-center text-zinc-600">{Math.round(zoom * 100)}%</span>
                        <button onClick={() => handleZoom(0.1)} className="px-2 hover:bg-zinc-200 rounded text-zinc-600">+</button>
                        <button onClick={resetView} className="ml-2 text-[10px] text-zinc-400 hover:text-zinc-600">RESET</button>
                    </div>

                    {/* UX: Compare - Onion Skin Slider */}
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <div className="flex items-center gap-2 bg-zinc-100 rounded px-3 py-1">
                        <span className="text-xs text-zinc-500">Onion Skin</span>
                        <input
                            type="range" min="0" max="1" step="0.1"
                            value={onionOpacity}
                            onChange={e => setOnionOpacity(parseFloat(e.target.value))}
                            className="w-20 accent-zinc-900 h-1 bg-zinc-300 rounded-lg appearance-none cursor-pointer"
                        />
                        <span className="text-[10px] w-8 text-zinc-600">{Math.round(onionOpacity * 100)}%</span>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button onClick={() => addText()} className="px-3 py-1.5 text-xs bg-zinc-100 hover:bg-zinc-200 text-zinc-900 border border-zinc-200 rounded font-medium">＋ Text</button>
                    <button onClick={() => handleDownload('save')} className="px-4 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold rounded shadow-sm border border-zinc-900">SAVE & CLOSE</button>
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <button onClick={() => handleDownload('png')} className="px-3 py-1.5 bg-white hover:bg-zinc-50 text-zinc-700 text-xs font-bold rounded border border-zinc-300">PNG</button>
                    <button onClick={() => handleDownload('jpg')} className="px-3 py-1.5 bg-white hover:bg-zinc-50 text-zinc-700 text-xs font-bold rounded border border-zinc-300">JPG</button>
                    <div className="h-6 w-px bg-zinc-200 mx-2"></div>
                    <button onClick={onClose} className="text-zinc-400 hover:text-zinc-700 text-sm">Cancel</button>
                </div>
            </div>

            {/* Main Workspace */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar (Tool Properties) */}
                <div className="w-64 bg-zinc-50 p-4 space-y-6 overflow-y-auto z-10 text-zinc-700 shadow-[1px_0_0_0_rgba(0,0,0,0.03)]">

                    {/* AI Panel */}
                    {mode === 'ai' && (
                        <div className="space-y-4 animate-in slide-in-from-left duration-200">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-xl animate-pulse-fast">✨</span>
                                <h3 className="text-zinc-800 font-bold text-sm">AIで背景を再生成</h3>
                            </div>

                            {aiError && (
                                <div className="p-2 bg-red-500/20 border border-red-500/50 rounded text-[10px] text-red-200">
                                    {aiError}
                                </div>
                            )}

                            {/* Magic Input Area */}
                            <div className="relative group">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-200 to-indigo-200 rounded-xl opacity-30 group-hover:opacity-100 transition duration-500 blur"></div>
                                <div className="relative bg-white rounded-xl shadow-sm border border-zinc-200">
                                    <textarea
                                        value={aiPrompt}
                                        onChange={e => setAiPrompt(e.target.value)}
                                        placeholder="どのような背景にしますか？&#13;&#10;(例: シンプルな白背景、テック企業のオフィス風...)"
                                        className="w-full bg-transparent p-3 text-xs text-zinc-700 placeholder-zinc-400 outline-none resize-none h-24 rounded-xl"
                                    />

                                    {/* Floating Action Button */}
                                    <div className="p-2 flex justify-end">
                                        <button
                                            onClick={runAiRemaster}
                                            disabled={isAiGenerating}
                                            className="bg-zinc-900 hover:bg-violet-600 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed group-hover:shadow-md"
                                        >
                                            {isAiGenerating ? (
                                                <>
                                                    <span className="animate-spin text-xs">⟳</span> 生成中...
                                                </>
                                            ) : (
                                                <>
                                                    <span>🪄</span> 生成する
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Advanced Options */}
                            <div className="space-y-4 pt-2">
                                {/* Creativity */}
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Creativity Level</label>
                                        <span className="text-[10px] font-mono text-violet-600 bg-violet-50 px-1.5 py-0.5 rounded">{Math.round(aiCreativity * 100)}%</span>
                                    </div>
                                    <div className="relative h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                                        <div
                                            className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-400 to-indigo-500"
                                            style={{ width: `${aiCreativity * 100}%` }}
                                        ></div>
                                        <input
                                            type="range" min="0" max="1" step="0.1"
                                            value={aiCreativity}
                                            onChange={e => setAiCreativity(parseFloat(e.target.value))}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        />
                                    </div>
                                    <div className="flex justify-between text-[9px] text-zinc-400">
                                        <span>補正 (Repair)</span>
                                        <span>創造 (Redesign)</span>
                                    </div>
                                </div>

                                {/* Count */}
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Output Count</label>
                                        <span className="text-[10px] font-mono text-zinc-600 bg-zinc-100 px-1.5 py-0.5 rounded">{aiCandidateCount}枚</span>
                                    </div>
                                    <div className="relative h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                                        <div
                                            className="absolute top-0 left-0 h-full bg-zinc-800"
                                            style={{ width: `${(aiCandidateCount / 4) * 100}%` }}
                                        ></div>
                                        <input
                                            type="range" min="1" max="4" step="1"
                                            value={aiCandidateCount}
                                            onChange={e => setAiCandidateCount(parseInt(e.target.value))}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        />
                                    </div>
                                    <div className="flex justify-between text-[9px] text-zinc-400">
                                        <span>1 (Faster)</span>
                                        <span>4 (Variations)</span>
                                    </div>
                                </div>
                            </div>

                            <div className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100/50">
                                <p className="text-[10px] text-indigo-400 leading-relaxed flex gap-2">
                                    <span>💡</span>
                                    <span>
                                        <strong>Hint:</strong> 不要な文字やオブジェクトは、先に<span className="font-bold underline cursor-pointer" onClick={() => setMode('brush')}>ブラシ(B)</span>で塗りつぶしておくと、より綺麗に消えます。
                                    </span>
                                </p>
                            </div>
                        </div>
                    )}

                    {(mode === 'brush' || mode === 'eraser') && (
                        <div>
                            <h3 className="text-xs font-bold text-zinc-400 mb-3">BRUSH SETTINGS</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs text-zinc-500">Size: {brushSize}px</label>
                                    <input type="range" min="1" max="100" value={brushSize} onChange={e => setBrushSize(Number(e.target.value))} className="w-full accent-zinc-900 bg-zinc-200 h-1 rounded-lg appearance-none" />
                                </div>
                                {mode === 'brush' && (
                                    <div>
                                        <label className="text-xs text-zinc-500">Color</label>
                                        <div className="flex gap-2 mt-1">
                                            <input type="color" value={brushColor} onChange={e => setBrushColor(e.target.value)} className="w-8 h-8 rounded border border-zinc-200 cursor-pointer" />
                                            <div className="text-xs font-mono self-center text-zinc-600 uppercase">{brushColor}</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {selectedTextId !== null && (
                        <div>
                            <h3 className="text-xs font-bold text-zinc-400 mb-3 block flex justify-between">
                                TEXT PROPERTIES
                                <button onClick={deleteText} className="text-red-500 hover:text-red-600 font-medium">Delete</button>
                            </h3>
                            {/* Text Inputs */}
                            <div className="space-y-3">
                                <textarea
                                    value={texts[selectedTextId].content}
                                    onChange={e => {
                                        const newTexts = [...texts];
                                        newTexts[selectedTextId].content = e.target.value;
                                        setTexts(newTexts);
                                    }}
                                    className="w-full h-24 bg-zinc-50 border-zinc-300 rounded p-2 text-sm text-zinc-900 border focus:border-zinc-500 outline-none"
                                />

                                {/* Font Family Selector */}
                                <div>
                                    <label className="text-xs text-zinc-400 mb-1 block">Font</label>
                                    <select
                                        value={texts[selectedTextId].fontFamily || 'Noto Sans JP'}
                                        onChange={e => {
                                            const newTexts = [...texts];
                                            newTexts[selectedTextId].fontFamily = e.target.value;
                                            setTexts(newTexts);
                                        }}
                                        className="w-full bg-zinc-50 border border-zinc-300 rounded p-2 text-xs text-zinc-900 outline-none focus:border-zinc-500"
                                    >
                                        {[
                                            { name: 'Standard (Noto Sans)', value: 'Noto Sans JP' },
                                            { name: 'Meiryo Style (M PLUS 1p)', value: '"M PLUS 1p", sans-serif' },
                                            { name: 'UD Gothic (BIZ UDPGothic)', value: '"BIZ UDPGothic", sans-serif' },
                                            { name: 'Formal (Noto Serif)', value: 'Noto Serif JP' },
                                            { name: 'Modern Round (Zen Maru)', value: '"Zen Maru Gothic", sans-serif' },
                                            { name: 'Impact (Dela Gothic)', value: '"Dela Gothic One", cursive' },
                                            { name: 'Pixel (DotGothic16)', value: '"DotGothic16", sans-serif' },
                                            { name: 'Marker (Yusei Magic)', value: '"Yusei Magic", sans-serif' },
                                            { name: 'Storybook (Kiwi Maru)', value: '"Kiwi Maru", serif' },
                                            { name: 'Emotional (Shippori)', value: '"Shippori Mincho", serif' },
                                        ].map(f => <option key={f.value} value={f.value}>{f.name}</option>)}
                                    </select>
                                </div>

                                <input type="color" value={texts[selectedTextId].color_hex || '#ffffff'} onChange={e => {
                                    const newTexts = [...texts];
                                    newTexts[selectedTextId].color_hex = e.target.value;
                                    setTexts(newTexts);
                                }} className="w-full h-8 cursor-pointer border border-zinc-200 rounded" />

                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => {
                                            const newTexts = [...texts];
                                            const w = newTexts[selectedTextId].fontWeight;
                                            newTexts[selectedTextId].fontWeight = w === 'bold' ? 'normal' : 'bold';
                                            setTexts(newTexts);
                                        }}
                                        className={`p-1 rounded border ${texts[selectedTextId].fontWeight === 'bold' ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white border-zinc-300 text-zinc-700'}`}
                                    >B</button>
                                    {/* Font Size Simple Stepper */}
                                    <div className="flex items-center bg-zinc-100 rounded border border-zinc-200">
                                        <button onClick={() => {
                                            const newTexts = [...texts];
                                            newTexts[selectedTextId].fontSize = (newTexts[selectedTextId].fontSize || 24) - 2;
                                            setTexts(newTexts);
                                        }} className="px-2 text-zinc-600 hover:text-black">-</button>
                                        <span className="flex-1 text-center text-xs text-zinc-900">{texts[selectedTextId].fontSize || 24}</span>
                                        <button onClick={() => {
                                            const newTexts = [...texts];
                                            newTexts[selectedTextId].fontSize = (newTexts[selectedTextId].fontSize || 24) + 2;
                                            setTexts(newTexts);
                                        }} className="px-2 text-zinc-600 hover:text-black">+</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Canvas Area */}
                <div
                    className={`flex-1 bg-zinc-100 overflow-hidden flex items-center justify-center relative ${mode === 'hand' ? 'cursor-grab active:cursor-grabbing' : ''}`}
                    onMouseDown={mode === 'hand' ? startDraw : undefined}
                    onMouseMove={mode === 'hand' ? draw : undefined}
                    onMouseUp={mode === 'hand' ? stopDraw : undefined}
                    onMouseLeave={mode === 'hand' ? stopDraw : undefined}
                >
                    {/* The "Stage" */}
                    <div
                        ref={containerRef}
                        className="relative shadow-xl bg-white transition-transform duration-75 ease-out origin-center"
                        style={{
                            width: slide.originalImage ? 1280 * renderScale : '100%',
                            height: slide.originalImage ? 720 * renderScale : '100%',
                            transform: `translate(${pan.x}px, ${pan.y}px)`,
                            maxWidth: 'none',
                            maxHeight: 'none',
                            flexShrink: 0
                        }}
                    >
                        {/* 1. Base Image Layer */}
                        <img
                            ref={bgRef}
                            src={workingBgImage}
                            draggable={false}
                            className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none transition-opacity duration-200"
                        />

                        {/* UX: Onion Skin Layer (Original) */}
                        {slide.originalImage && onionOpacity > 0 && (
                            <img
                                src={slide.originalImage}
                                draggable={false}
                                className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none z-[60]"
                                style={{ opacity: onionOpacity }}
                            />
                        )}

                        {/* 2. Paint Layer */}
                        <canvas
                            ref={canvasRef}
                            width={1280}
                            height={720}
                            className={`absolute inset-0 w-full h-full object-contain touch-none ${mode === 'hand' ? 'pointer-events-none' : 'cursor-crosshair'}`}
                            onMouseDown={startDraw}
                            onMouseMove={draw}
                            onMouseUp={stopDraw}
                            onMouseLeave={stopDraw}
                        />

                        {/* 3. Text Overlay Layer */}
                        <div className="absolute inset-0 pointer-events-none overflow-hidden">
                            {texts.map((t, i) => (
                                <div
                                    key={i}
                                    id={`text-box-${i}`}
                                    onMouseDown={(e) => startTextDrag(e, i)}
                                    className={`absolute p-1 group pointer-events-auto break-words hover:ring-1 hover:ring-neon/50 cursor-move ${selectedTextId === i ? 'ring-1 ring-neon bg-neon/10' : ''}`}
                                    style={{
                                        left: `${t.x_pct}%`,
                                        top: `${t.y_pct}%`,
                                        width: `${t.width_pct}%`,
                                        color: t.color_hex || '#ffffff',
                                        fontSize: `${(t.fontSize || (t.role === 'Title' ? 32 : 14)) * renderScale}px`, // Visually scale
                                        fontWeight: t.fontWeight || (t.role === 'Title' ? 'bold' : 'normal'),
                                        lineHeight: 1.2,
                                        whiteSpace: 'pre-wrap', // Enable multiline support
                                        fontFamily: t.fontFamily || 'Noto Sans JP',
                                        transform: `rotate(${t.rotation || 0}deg)`,
                                        transformOrigin: 'center center'
                                    }}
                                >
                                    {t.content}
                                    {/* Handles (Resizing) */}
                                    {selectedTextId === i && (
                                        <div
                                            className="absolute -right-1 -bottom-1 w-4 h-4 bg-neon rounded-full cursor-se-resize flex items-center justify-center border border-black z-50 pointer-events-auto hover:scale-125 transition-transform"
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                e.preventDefault();
                                                startTextResize(e, i);
                                            }}
                                        >
                                            <div className="w-1.5 h-1.5 bg-black rounded-full" />
                                        </div>
                                    )}

                                    {/* Handles (Rotation) */}
                                    {selectedTextId === i && (
                                        <div
                                            className="absolute -top-6 left-1/2 -translate-x-1/2 w-6 h-6 flex items-center justify-center cursor-grabbing z-50 group/rotate"
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                e.preventDefault();
                                                startTextRotate(e, i);
                                            }}
                                        >
                                            <div className="w-0.5 h-3 bg-neon absolute bottom-0 left-1/2 -translate-x-1/2"></div>
                                            <div className="w-3 h-3 rounded-full bg-neon border border-black hover:scale-125 transition-transform" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* AI Result Selection Overlay */}
                    {aiCandidates && (
                        <div className="absolute inset-0 bg-white/95 z-[100] flex flex-col items-center justify-center p-8 animate-fade-in-up">
                            <div className="text-center mb-8">
                                <div className="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-4 animate-bounce">
                                    <span className="text-2xl">✨</span>
                                </div>
                                <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-2">Generation Complete!</h2>
                                <p className="text-zinc-500">Compare and select your favorite result.</p>
                            </div>

                            {/* Comparison Grid */}
                            <div className="flex gap-8 w-full max-w-6xl justify-center items-start">

                                {/* Original (Input) */}
                                <div className="flex flex-col items-center gap-2">
                                    <div className="relative aspect-video w-[300px] bg-zinc-200 rounded-xl overflow-hidden opacity-80 border-2 border-zinc-200 grayscale-[0.3] group">
                                        {/* Use 'slide' prop, not 'studioTarget' */}
                                        <img src={slide.displayImage || slide.originalImage} className="w-full h-full object-cover" />
                                        <div className="absolute top-2 left-2 bg-black/50 text-white text-[10px] px-2 py-1 rounded backdrop-blur-md">ORIGINAL</div>

                                        {/* Magnifier */}
                                        <button
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation(); // Prevent anything else
                                                if (onPreview) onPreview(slide.displayImage || slide.originalImage);
                                            }}
                                            className="absolute bottom-2 right-2 p-1.5 bg-white/80 rounded-full shadow-sm hover:scale-110 transition-transform opacity-0 group-hover:opacity-100"
                                            title="Zoom"
                                        >
                                            🔍
                                        </button>
                                    </div>
                                </div>

                                {/* Divider */}
                                <div className="w-px h-[200px] bg-zinc-200 self-center hidden md:block"></div>

                                {/* Candidates */}
                                <div className={`grid gap-6 ${aiCandidates.length === 1 ? 'grid-cols-1 w-[400px]' : (aiCandidates.length === 2 ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-2 lg:grid-cols-4')}`}>
                                    {aiCandidates.map((img, idx) => (
                                        <div
                                            key={idx}
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                applyAiResult(img);
                                            }}
                                            className="group cursor-pointer relative aspect-video bg-zinc-100 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all border-2 border-transparent hover:border-violet-500 w-full"
                                        >
                                            <img src={img} className="w-full h-full object-cover" />
                                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                                <span className="bg-white text-zinc-900 font-bold px-4 py-2 rounded-full shadow-lg transform scale-90 group-hover:scale-100 transition-transform">
                                                    Select This
                                                </span>
                                            </div>
                                            <div className="absolute top-2 right-2 bg-violet-600 text-white text-[10px] font-bold px-2 py-1 rounded shadow-sm">
                                                #{idx + 1}
                                            </div>

                                            {/* Magnifier for Candidate */}
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    if (onPreview) onPreview(img);
                                                }}
                                                className="absolute bottom-2 right-2 p-1.5 bg-white/90 rounded-full shadow-sm hover:scale-110 transition-transform opacity-0 group-hover:opacity-100 z-10 pointer-events-auto text-zinc-700"
                                                title="Zoom"
                                            >
                                                🔍
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <button
                                onClick={() => { setAiCandidates(null); setIsAiGenerating(false); }}
                                className="mt-12 px-6 py-2 border border-zinc-300 text-zinc-500 rounded-full hover:bg-zinc-100 hover:text-red-500 text-xs font-bold tracking-wide uppercase transition-colors"
                            >
                                Discard All
                            </button>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default StudioModal;
