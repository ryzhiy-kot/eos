import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

interface OverlayWindowProps {
    title: string;
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
    subtitle?: string;
    maxWidth?: string;
    className?: string;
    scrollable?: boolean;
}

const OverlayWindow: React.FC<OverlayWindowProps> = ({
    title,
    isOpen,
    onClose,
    children,
    subtitle,
    maxWidth = 'max-w-4xl',
    className,
    scrollable = true
}) => {
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="overlay-backdrop">
            {/* Window Container */}
            <div className={clsx("overlay-window", maxWidth, className)}>
                {/* Header */}
                <div className="overlay-header">
                    <div className="flex items-center space-x-4">
                        <h2 className="text-xl font-bold uppercase tracking-widest">{title}</h2>
                        {subtitle && (
                            <span className="bg-terminal-700 text-neutral-400 px-2 py-0.5 rounded text-[10px] font-mono tracking-wide">
                                {subtitle}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="text-neutral-500 hover:text-white transition-colors focus:outline-none"
                        aria-label="Close overlay"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content Container */}
                <div className={clsx(
                    "flex-1 w-full mx-auto scrollbar-thin scrollbar-thumb-terminal-700 scrollbar-track-transparent flex flex-col min-h-0",
                    scrollable ? "overflow-y-auto p-6" : "overflow-hidden"
                )}>
                    {children}
                </div>

                {/* Footer Tip */}
                <div className="p-2 text-center text-terminal-700 font-mono text-[10px] bg-terminal-900 border-t border-terminal-800 uppercase tracking-widest">
                    Press [ESC] to close
                </div>
            </div>
        </div>
    );
};

export default OverlayWindow;
