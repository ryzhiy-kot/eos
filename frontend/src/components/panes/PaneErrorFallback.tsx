import React from 'react';

interface PaneErrorFallbackProps {
    error: Error;
    reset: () => void;
}

const PaneErrorFallback: React.FC<PaneErrorFallbackProps> = ({ error, reset }) => (
    <div className="flex flex-col items-center justify-center h-full w-full bg-gray-900 border border-red-900/50 rounded p-4">
        <div className="text-red-500 mb-2">⚠️ Pane Error</div>
        <div className="text-xs text-gray-400 mb-4 text-center max-w-[200px] truncate" title={error.message}>
            {error.message}
        </div>
        <button
            onClick={reset}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 rounded border border-gray-700 transition-colors"
        >
            Reload Pane
        </button>
    </div>
);

export default PaneErrorFallback;
