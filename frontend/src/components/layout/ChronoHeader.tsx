import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, Wifi, Clock, Timer } from 'lucide-react';
import { useWorkspaceStore } from '../../store/workspaceStore';

const ChronoHeader: React.FC = () => {
    const [time, setTime] = useState(new Date());
    const { clocks, timers } = useWorkspaceStore();

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

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
                    <div key={clock.id} className="flex flex-col md:flex-row md:space-x-1">
                        <span className="font-bold text-neutral-500">{clock.city}</span>
                        <span>{formatTime(clock.timezone)}</span>
                    </div>
                ))}
            </div>

            {/* Center: Timers */}
            {timers.length > 0 && (
                <div className="flex items-center space-x-4 px-4 border-l border-r border-neutral-800 mx-4">
                    {timers.map(t => (
                        <div key={t.id} className="flex items-center space-x-2 text-orange-400 animate-pulse">
                            <Timer size={14} />
                            <span className="font-bold">{t.label}</span>
                            <span>{formatCountdown(t.endsAt)}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Right: System Status */}
            <div className="flex items-center space-x-6 whitespace-nowrap hidden md:flex">
                <div className="flex items-center space-x-2 text-emerald-500">
                    <ShieldCheck size={14} />
                    <span>SYSTEM NORMAL</span>
                </div>
                <div className="flex items-center space-x-2 text-neutral-500">
                    <Activity size={14} />
                    <span>LATENCY: 12ms</span>
                </div>
                <div className="flex items-center space-x-2 text-neutral-500">
                    <Wifi size={14} />
                    <span>CONNECTED</span>
                </div>
            </div>
        </div>
    );
};

export default ChronoHeader;
