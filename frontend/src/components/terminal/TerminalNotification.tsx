import React from 'react';
import { useWorkspaceStore, workspaceActions } from '../../store/workspaceStore';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';
import clsx from 'clsx';

const TerminalNotification: React.FC = () => {
    const { notifications } = useWorkspaceStore();
    if (notifications.length === 0) return null;

    const getIcon = (type: 'error' | 'success' | 'info') => {
        switch (type) {
            case 'error': return AlertCircle;
            case 'success': return CheckCircle;
            case 'info': return Info;
        }
    };

    return (
        <div className="flex flex-col-reverse gap-2 pointer-events-none">
            {notifications.map((notif) => {
                const Icon = getIcon(notif.type);
                return (
                    <div
                        key={notif.id}
                        className={clsx(
                            "p-2 rounded flex items-center justify-between text-xs font-mono animate-in fade-in slide-in-from-bottom-2 duration-300 pointer-events-auto shadow-lg",
                            notif.type === 'error' && "bg-black/90 text-red-400 border border-red-500/30",
                            notif.type === 'success' && "bg-black/90 text-emerald-400 border border-emerald-500/30",
                            notif.type === 'info' && "bg-black/90 text-blue-400 border border-blue-500/30"
                        )}
                    >
                        <div className="flex items-center gap-2 pr-4">
                            <Icon size={14} className="flex-shrink-0" />
                            <span>{notif.message}</span>
                        </div>
                        <button
                            onClick={() => workspaceActions.clearNotification(notif.id)}
                            className="hover:bg-white/10 rounded p-0.5 transition-colors text-neutral-500 hover:text-white"
                        >
                            <X size={14} />
                        </button>
                    </div>
                );
            })}
        </div>
    );
};

export default TerminalNotification;
