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

import React, { useState, useEffect } from 'react';
import { Wifi, Clock, Timer, X } from 'lucide-react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { commandBus, COMMAND_NAMES } from '@/lib/commandBus';
import { ConnectionStatus } from '@/types/constants';

interface HeaderProps {
    connectionStatus?: ConnectionStatus;
}

const Header: React.FC<HeaderProps> = ({ connectionStatus = ConnectionStatus.DISCONNECTED }) => {
    const [time, setTime] = useState(new Date());
    const { clocks, timers, focusedPaneId } = useWorkspaceStore();

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    // We keep 'time' state to force a re-render every second for clocks
    // even if 'time' itself isn't rendered directly as a string here.
    if (!time) return null;

    // Format time for a specific timezone
    const formatTime = (timezone: string) => {
        try {
            return new Date().toLocaleTimeString('en-US', { timeZone: timezone, hour12: false, hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '--:--';
        }
    };

    // Format timer countdown
    const formatCountdown = (endsAt: number) => {
        const diff = Math.max(0, Math.floor((endsAt - Date.now()) / 1000));
        const m = Math.floor(diff / 60);
        const s = diff % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="h-12 bg-neutral-950 border-b border-neutral-800 flex items-center justify-between px-4 text-xs font-mono select-none overflow-x-auto">
            {/* Left: World Clocks */}
            <div className="flex items-center space-x-6 text-neutral-400 whitespace-nowrap">
                <div className="flex items-center space-x-2 text-sky-400 border-r border-neutral-800 pr-4">
                    <Clock size={14} />
                    <span>UTC {new Date().toLocaleTimeString('en-US', { timeZone: 'UTC', hour12: false })}</span>
                </div>

                {clocks.map(clock => (
                    <div key={clock.id} className="flex items-center space-x-2 group/clock">
                        <div className="flex flex-col md:flex-row md:space-x-1">
                            <span className="font-bold text-neutral-500">{clock.city}</span>
                            <span>{formatTime(clock.timezone)}</span>
                        </div>
                        <button
                            onClick={() => commandBus.dispatch({ name: COMMAND_NAMES.REMOVE_CLOCK, args: [clock.id], context: { focusedPaneId } })}
                            className="opacity-0 group-hover/clock:opacity-100 hover:text-red-500 transition-opacity"
                        >
                            <X size={10} />
                        </button>
                    </div>
                ))}
            </div>

            {/* Center: Timers */}
            {timers.length > 0 && (
                <div className="flex items-center space-x-4 px-4 border-l border-r border-neutral-800 mx-4">
                    {timers.map(t => (
                        <div key={t.id} className="flex items-center space-x-2 text-orange-400 group/timer">
                            <div className="flex items-center space-x-2 animate-pulse">
                                <Timer size={14} />
                                <span className="font-bold">{t.label}</span>
                                <span>{formatCountdown(t.endsAt)}</span>
                            </div>
                            <button
                                onClick={() => commandBus.dispatch({ name: COMMAND_NAMES.REMOVE_TIMER, args: [t.id], context: { focusedPaneId } })}
                                className="opacity-0 group-hover/timer:opacity-100 hover:text-red-500 transition-opacity"
                            >
                                <X size={10} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Right: System Status */}
            <div className="flex items-center space-x-6 whitespace-nowrap hidden md:flex">
                <div className={`flex items-center space-x-2 ${connectionStatus === ConnectionStatus.CONNECTED ? 'text-emerald-500' :
                    connectionStatus === ConnectionStatus.CONNECTING ? 'text-yellow-500' :
                        connectionStatus === ConnectionStatus.ERROR ? 'text-red-500' :
                            'text-neutral-500'
                    }`}>
                    <Wifi size={14} className={connectionStatus === ConnectionStatus.CONNECTED ? '' : 'animate-pulse'} />
                    <span>{connectionStatus.toUpperCase()}</span>
                </div>
            </div>
        </div>
    );
};

export default Header;
