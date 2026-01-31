/**
 * PROJECT: EoS
 * AUTHOR: Kyrylo Yatsenko
 * YEAR: 2026
 * * COPYRIGHT NOTICE:
 * © 2026 Kyrylo Yatsenko. All rights reserved.
 * 
 * This work represents a proprietary methodology for Human-Machine Interaction (HMI).
 * All source code, logic structures, and User Experience (UX) frameworks
 * contained herein are the sole intellectual property of Kyrylo Yatsenko.
 * 
 * ATTRIBUTION REQUIREMENT:
 * Any use of this program, or any portion thereof (including code snippets and
 * interaction patterns), may not be used, redistributed, or adapted
 * without explicit, visible credit to Kyrylo Yatsenko as the original author.
 */

import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize, MousePointer2 } from 'lucide-react';

interface VisualRendererProps {
    src: string;
    title: string;
}

const VisualRenderer: React.FC<VisualRendererProps> = ({ src, title }) => {
    const [scale, setScale] = useState(1);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const containerRef = useRef<HTMLDivElement>(null);
    const imgRef = useRef<HTMLImageElement>(null);

    const handleZoomIn = () => setScale(prev => Math.min(prev + 0.25, 5));
    const handleZoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.1));
    const handleReset = () => {
        setScale(1);
        setOffset({ x: 0, y: 0 });
    };

    const handleWheel = (e: React.WheelEvent) => {
        if (e.ctrlKey) {
            e.preventDefault();
            const delta = -e.deltaY;
            const factor = delta > 0 ? 1.1 : 0.9;
            setScale(prev => Math.max(0.1, Math.min(prev * factor, 5)));
        }
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.button !== 0) return; // Only left click
        setIsDragging(true);
        setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging) return;
        setOffset({
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y
        });
    };

    const handleMouseUp = () => setIsDragging(false);

    useEffect(() => {
        const handleGlobalMouseUp = () => setIsDragging(false);
        window.addEventListener('mouseup', handleGlobalMouseUp);
        return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
    }, []);

    return (
        <div
            ref={containerRef}
            className="w-full h-full bg-neutral-950 relative overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
        >
            {/* Image Layer */}
            <div
                style={{
                    transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out'
                }}
                className="flex items-center justify-center pointer-events-none"
            >
                <img
                    ref={imgRef}
                    src={src}
                    alt={title}
                    className="max-w-none max-h-none select-none shadow-2xl"
                />
            </div>

            {/* UI Overlay */}
            <div className="absolute top-4 right-4 flex flex-col space-y-2 pointer-events-auto">
                <div className="bg-neutral-900/80 backdrop-blur border border-neutral-800 rounded-lg p-1 flex flex-col shadow-xl">
                    <button
                        onClick={handleZoomIn}
                        className="p-2 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
                        title="Zoom In"
                    >
                        <ZoomIn size={18} />
                    </button>
                    <button
                        onClick={handleZoomOut}
                        className="p-2 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
                        title="Zoom Out"
                    >
                        <ZoomOut size={18} />
                    </button>
                    <div className="h-px bg-neutral-800 my-1 mx-2" />
                    <button
                        onClick={handleReset}
                        className="p-2 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
                        title="Reset View"
                    >
                        <Maximize size={18} />
                    </button>
                </div>

                <div className="bg-neutral-900/80 backdrop-blur border border-neutral-800 rounded px-2 py-1 text-[10px] text-neutral-500 font-mono text-center shadow-lg">
                    {Math.round(scale * 100)}%
                </div>
            </div>

            {/* Bottom Info */}
            <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur px-2 py-1 rounded border border-neutral-800 pointer-events-none">
                <span className="text-[10px] text-neutral-400 font-mono flex items-center space-x-2">
                    <MousePointer2 size={12} className="text-blue-500" />
                    <span>LMB: PAN • CTRL+WHEEL: ZOOM</span>
                </span>
            </div>
        </div>
    );
};

export default VisualRenderer;
