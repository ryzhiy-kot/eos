import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, Wifi, Clock } from 'lucide-react';

const ChronoHeader: React.FC = () => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (date: Date, offset: number) => {
        const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
        const newDate = new Date(utc + (3600000 * offset));
        return newDate.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="h-12 bg-neutral-950 border-b border-neutral-800 flex items-center justify-between px-4 text-xs font-mono select-none">
            {/* Left: World Clocks */}
            <div className="flex items-center space-x-6 text-neutral-400">
                <div className="flex items-center space-x-2 text-sky-400">
                    <Clock size={14} />
                    <span>UTC {time.toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' })}</span>
                </div>
                <div className="hidden md:flex space-x-4 border-l border-neutral-800 pl-4">
                    <span>NYC {time.toLocaleTimeString('en-US', { hour12: false, timeZone: 'America/New_York' })}</span>
                    <span>LON {time.toLocaleTimeString('en-US', { hour12: false, timeZone: 'Europe/London' })}</span>
                    <span>TKY {time.toLocaleTimeString('en-US', { hour12: false, timeZone: 'Asia/Tokyo' })}</span>
                </div>
            </div>

            {/* Right: System Status */}
            <div className="flex items-center space-x-6">
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
