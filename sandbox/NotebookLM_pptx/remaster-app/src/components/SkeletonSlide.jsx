import React from 'react';

const SkeletonSlide = () => (
    <div className="relative aspect-video bg-zinc-100 rounded-lg overflow-hidden shrink-0">
        <div className="absolute inset-0 animate-pulse">
            {/* Header Bar */}
            <div className="h-1/6 bg-zinc-200/50 w-full mb-4"></div>

            <div className="flex h-full p-4 gap-4">
                {/* Left Content */}
                <div className="w-1/3 space-y-3">
                    <div className="h-4 bg-zinc-200 rounded w-3/4"></div>
                    <div className="h-4 bg-zinc-200 rounded w-1/2"></div>
                    <div className="h-20 bg-zinc-200/50 rounded w-full mt-4"></div>
                </div>
                {/* Right Content */}
                <div className="flex-1 space-y-4">
                    <div className="h-full bg-zinc-200/30 rounded"></div>
                </div>
            </div>

            {/* Floating Badge */}
            <div className="absolute bottom-4 right-4 w-24 h-6 bg-zinc-200 rounded-full"></div>
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-white/90 backdrop-blur px-4 py-2 rounded-full shadow-lg border border-zinc-100">
                <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-zinc-900 rounded-full animate-ping"></div>
                    <span className="text-xs font-mono text-zinc-900 tracking-widest">AI PROCESSING...</span>
                </div>
            </div>
        </div>
    </div>
);

export default SkeletonSlide;
