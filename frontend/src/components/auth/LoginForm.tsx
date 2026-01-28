import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { Lock, User, Loader2, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

const LoginForm: React.FC = () => {
    const { login, error, isLoading } = useAuthStore();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await login(username, password);
    };

    return (
        <div className="fixed inset-0 bg-black flex items-center justify-center p-4">
            {/* Background Grid Effect */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,240,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,240,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px]" />

            <div className="w-full max-w-md bg-terminal-900 border border-terminal-700 shadow-glow relative z-10 p-8 flex flex-col gap-6 animate-scale-in">
                {/* Header */}
                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-mono font-bold text-white tracking-wildest uppercase">monad<span className="text-accent-main">_OS</span></h1>
                    <div className="text-xs font-mono text-terminal-700 uppercase tracking-widest">Secure Access Terminal</div>
                </div>

                {/* Status Display */}
                <div className={clsx(
                    "h-10 flex items-center justify-center text-xs font-mono border rounded transition-colors",
                    error
                        ? "bg-red-900/10 border-red-500/30 text-red-400"
                        : "bg-terminal-800 border-terminal-700 text-neutral-500"
                )}>
                    {isLoading ? (
                        <div className="flex items-center space-x-2">
                            <Loader2 size={14} className="animate-spin" />
                            <span>AUTHENTICATING...</span>
                        </div>
                    ) : error ? (
                        <div className="flex items-center space-x-2">
                            <AlertTriangle size={14} />
                            <span>{error}</span>
                        </div>
                    ) : (
                        <span>:: AWAITING CREDENTIALS ::</span>
                    )}
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1">
                        <label className="text-[10px] font-mono uppercase text-neutral-500 tracking-wider">Identity</label>
                        <div className="terminal-input-container h-12">
                            <User size={16} className="text-terminal-700 mr-3" />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="terminal-input"
                                placeholder="USERNAME"
                                disabled={isLoading}
                                autoFocus
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-[10px] font-mono uppercase text-neutral-500 tracking-wider">Passphrase</label>
                        <div className="terminal-input-container h-12">
                            <Lock size={16} className="text-terminal-700 mr-3" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="terminal-input"
                                placeholder="PASSWORD"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full h-12 bg-accent-main/10 hover:bg-accent-main/20 border border-accent-main/50 text-accent-main font-mono font-bold tracking-widest uppercase transition-all hover:shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                    >
                        {isLoading ? 'PROCESSING...' : 'INITIALIZE SESSION'}
                    </button>
                </form>

                {/* Footer Decor */}
                <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-accent-main" />
                <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-accent-main" />
            </div>
        </div>
    );
};

export default LoginForm;
