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

import React from 'react';
import { Loader2, LogOut } from 'lucide-react';
import { commandBus, COMMAND_NAMES } from '../../lib/commandBus';

interface TerminalStatusProps {
    isLoading: boolean;
}

const TerminalStatus: React.FC<TerminalStatusProps> = ({ isLoading }) => {

    return (
        <div className="flex items-center gap-3">
            <span className="text-slate-500 mx-3 select-none text-lg">|</span>

            {/* Status / Output Preview */}
            {isLoading ? (
                <div className="flex items-center text-primary animate-pulse whitespace-nowrap">
                    <span className="mr-1 text-sm">Processing</span>
                    <Loader2 size={16} className="animate-spin" />
                </div>
            ) : (
                <span className="text-slate-500 text-sm whitespace-nowrap hidden sm:inline-block">Ready</span>
            )}

            {/* Logout Button */}
            <button
                onClick={() => commandBus.dispatch({ name: COMMAND_NAMES.LOGOUT, args: [], context: { focusedPaneId: null } })}
                className="text-slate-500 hover:text-accent-red transition-colors p-1"
                title="Logout"
            >
                <LogOut size={16} />
            </button>
        </div>
    );
};

export default TerminalStatus;
