import React from 'react';

const ImagePreviewModal = ({ isOpen, slide, imageUrl, onClose }) => {
    if (!isOpen || (!slide && !imageUrl)) return null;
    const imgSrc = imageUrl || slide?.displayImage;
    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-md animate-in fade-in duration-200" onClick={onClose}>
            <div className="relative max-w-full max-h-full p-4" onClick={e => e.stopPropagation()}>
                <button onClick={onClose} className="absolute top-4 right-4 z-50 bg-black/50 text-white rounded-full p-2 hover:bg-white/20 transition-colors">✕</button>
                <div className="relative">
                    <img src={imgSrc} className="max-h-[90vh] max-w-[90vw] rounded shadow-2xl border border-slate-700" />
                    {slide && slide.textData && slide.textData.map((t, idx) => (
                        <div key={idx} className="absolute border border-neon/30 bg-neon/5 hover:bg-neon/20 transition-colors"
                            title={`Text: ${t.content}`}
                            style={{ left: `${t.x_pct}%`, top: `${t.y_pct}%`, width: `${t.width_pct}%`, height: '10%' }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ImagePreviewModal;
