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
}

const OverlayWindow: React.FC<OverlayWindowProps> = ({
    title,
    isOpen,
    onClose,
    children,
    subtitle,
    maxWidth = 'max-w-4xl',
    className
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
        <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col p-8 animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-8 border-b border-neutral-800 pb-4">
                <div className="flex items-center space-x-4">
                    <h2 className="text-2xl font-mono font-bold text-white uppercase">{title}</h2>
                    {subtitle && (
                        <span className="bg-neutral-800 text-neutral-400 px-2 py-1 rounded text-xs font-mono">
                            {subtitle}
                        </span>
                    )}
                </div>
                <button
                    onClick={onClose}
                    className="text-neutral-500 hover:text-white transition-colors focus:outline-none"
                    aria-label="Close overlay"
                >
                    <X size={32} />
                </button>
            </div>

            {/* Content Container */}
            <div className={clsx("flex-1 overflow-y-auto w-full mx-auto", maxWidth, className)}>
                {children}
            </div>

            {/* Footer Tip */}
            <div className="mt-8 text-center text-neutral-600 font-mono text-xs">
                Press [ESC] to close
            </div>
        </div>
    );
};

export default OverlayWindow;
