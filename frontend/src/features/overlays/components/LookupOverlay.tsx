/**
 * PROJECT: MONAD
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

import React, { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import clsx from 'clsx';
import OverlayWindow from '@/features/overlays/components/OverlayWindow';

interface LookupOverlayProps<T> {
    title: string;
    subtitle: string;
    isOpen: boolean;
    onClose: () => void;
    items: T[];
    renderItem: (item: T, isSelected: boolean, index: number) => React.ReactNode;
    onSelect: (item: T) => void;
    filterItem: (item: T, query: string) => boolean;
    placeholder?: string;
    gridCols?: number;
    contentWidth?: string;
    emptyMessage?: string;
    maxWidth?: string;
}

export default function LookupOverlay<T>({
    title,
    subtitle,
    isOpen,
    onClose,
    items,
    renderItem,
    onSelect,
    filterItem,
    placeholder = "Search...",
    gridCols = 1,
    contentWidth = "max-w-2xl",
    emptyMessage = "No items found.",
    maxWidth
}: LookupOverlayProps<T>) {
    const [search, setSearch] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);

    const filteredItems = items.filter(item => filterItem(item, search));

    // Reset selection when search changes or overlay opens
    useEffect(() => {
        setSelectedIndex(0);
    }, [search, isOpen]);

    // Handle auto-focus
    useEffect(() => {
        if (isOpen) {
            // Small delay to ensure the animation/render is stable
            const timer = setTimeout(() => {
                inputRef.current?.focus();
            }, 50);
            return () => clearTimeout(timer);
        } else {
            setSearch('');
        }
    }, [isOpen]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        const len = filteredItems.length;
        if (len === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + gridCols < len ? prev + gridCols : prev % gridCols));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - gridCols >= 0 ? prev - gridCols : (Math.floor((len - 1) / gridCols) * gridCols) + (prev % gridCols)));
        } else if (e.key === 'ArrowRight' && gridCols > 1) {
            e.preventDefault();
            setSelectedIndex(prev => (prev + 1) % len);
        } else if (e.key === 'ArrowLeft' && gridCols > 1) {
            e.preventDefault();
            setSelectedIndex(prev => (prev - 1 + len) % len);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            onSelect(filteredItems[selectedIndex]);
        }
    };

    return (
        <OverlayWindow
            title={title}
            subtitle={subtitle}
            isOpen={isOpen}
            onClose={onClose}
            maxWidth={maxWidth}
            scrollable={false}
        >
            <div className="flex flex-col h-full p-6 overflow-hidden">
                {/* Search - Fixed at top */}
                <div className={clsx("w-full mx-auto mb-6 shrink-0 relative group", contentWidth)}>
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-blue-500 transition-colors" />
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder={placeholder}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-neutral-900 border border-neutral-800 rounded-full py-3 pl-12 pr-4 text-white font-mono focus:border-blue-500 outline-none transition-colors"
                    />
                </div>

                {/* Content Grid - Scrollable */}
                <div className={clsx("flex-1 w-full mx-auto overflow-hidden flex flex-col min-h-0", contentWidth)}>
                    <div className={clsx(
                        "flex-1 overflow-y-auto pb-4 scrollbar-thin scrollbar-thumb-terminal-700 scrollbar-track-transparent",
                        gridCols > 1 ? "grid gap-4" : "space-y-2"
                    )} style={{
                        gridTemplateColumns: gridCols > 1 ? `repeat(${gridCols}, minmax(0, 1fr))` : undefined
                    }}>
                        {filteredItems.map((item, index) => (
                            <div
                                key={index}
                                onClick={() => onSelect(item)}
                                className="cursor-pointer"
                            >
                                {renderItem(item, index === selectedIndex, index)}
                            </div>
                        ))}

                        {filteredItems.length === 0 && (
                            <div className="col-span-full flex flex-col items-center justify-center text-neutral-600 py-20">
                                <span className="text-4xl mb-4 opacity-50">🔍</span>
                                <span className="font-mono text-sm">{emptyMessage}</span>
                            </div>
                        )}
                    </div>

                    {filteredItems.length > 0 && (
                        <div className="mt-4 pb-0 text-center text-neutral-600 font-mono text-xs opacity-75 border-t border-neutral-800/50 pt-4 shrink-0">
                            {gridCols > 1 ? 'Use ↑↓←→ to navigate' : 'Use ↑↓ to navigate'} • Press [Enter] to select • [Esc] to close
                        </div>
                    )}
                </div>
            </div>
        </OverlayWindow>
    );
}
