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
import ReactMarkdown from 'react-markdown';
import { ChatRole } from '@/types/constants';

interface ChatRendererProps {
    messages: any[];
    contextDescription?: string;
}

const ChatRenderer: React.FC<ChatRendererProps> = ({ messages, contextDescription }) => {
    return (
        <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
            <div className="text-[10px] text-neutral-500 border-l border-neutral-800 pl-2 italic uppercase tracking-tight">
                Context: {contextDescription || "Dynamic Session"}
            </div>

            {messages && Array.isArray(messages) ? (
                messages.map((msg: any, i: number) => {
                    const isUser = msg.role === ChatRole.USER;
                    return (
                        <div key={i} className="flex gap-2 items-start leading-snug">
                            <div className={`min-w-[64px] font-bold text-[10px] uppercase pt-0.5 ${isUser ? 'text-accent-green' : 'text-sky-500'}`}>
                                {isUser ? 'User' : 'Assistant'}
                            </div>
                            <div className="flex-1 text-neutral-300 prose prose-invert prose-sm max-w-none [&>p]:mt-0 [&>p]:mb-1 [&>pre]:my-2 [&>ul]:my-1 [&>ol]:my-1">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                {msg.artifacts && msg.artifacts.length > 0 && (
                                    <div className="mt-1 flex flex-wrap gap-1.5">
                                        {msg.artifacts.map((art: any) => (
                                            <span key={art.id} className="inline-flex items-center px-1 py-0.5 rounded text-[9px] font-medium bg-neutral-900 text-neutral-500 border border-neutral-800 uppercase">
                                                📎 {art.id}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })
            ) : (
                <div className="opacity-30 italic text-[10px] uppercase text-center py-4">New conversation started...</div>
            )}
        </div>
    );
};

export default ChatRenderer;
