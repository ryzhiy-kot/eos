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

export interface ParsedCommand {
    type: 'command' | 'message';
    verb?: string;
    sourceId?: string;
    action?: string;
    targetId?: string;
    original: string;
}

export const extractPaneId = (id: string) => (id.startsWith('@') ? id.substring(1) : id);

export const parseCommand = (input: string, activePaneId: string | null): ParsedCommand => {
    const trimmed = input.trim();

    // 1. Check for Command Prefix
    if (!trimmed.startsWith('/')) {
        // It's a message or context-dependent input
        return {
            type: 'message',
            original: trimmed,
            sourceId: activePaneId || undefined // Implicit source is active pane
        };
    }

    // 2. Parse Command Structure: /verb [source] [action] [> target]
    // Regex Breakdown:
    // ^\/(\w+)          -> Capture Verb (starts with /)
    // \s*(?:(P\d+))?    -> Optional Source (P1, P2...)
    // \s*(.+?)?         -> Optional Action/Prompt (Non-greedy)
    // \s*(?:>\s*(P\d+|new))?$ -> Optional Target (> P2 or > new)

    // Simplified Regex approach since Action can contain anything
    // We'll split by '>' first to isolate target

    const [mainPart, targetPart] = trimmed.split('>').map(s => s.trim());

    // Extract Verb and potential Source/Action from mainPart
    // Remove leading '/'
    const commandBody = mainPart.substring(1);
    const tokens = commandBody.split(/\s+/);
    const verb = tokens[0];

    let sourceId: string | undefined = undefined;
    let actionStartIdx = 1;

    // Check if second token is a Pane ID (P1, P2, etc.) or @P1
    if (tokens[1]) {
        if (/^@?P\d+$/.test(tokens[1])) {
            sourceId = tokens[1].startsWith('@') ? tokens[1].substring(1).toUpperCase() : tokens[1].toUpperCase();
            actionStartIdx = 2;
        } else if (/^@?(?:A_\w+|[0-9a-fA-F\-]{36})$/.test(tokens[1])) {
            // Direct Artifact ID reference (legacy A_ or UUID)
            sourceId = tokens[1].startsWith('@') ? tokens[1].substring(1) : tokens[1];
            actionStartIdx = 2;
        }
    }

    const action = tokens.slice(actionStartIdx).join(' ');
    let targetId = targetPart; // 'P2', 'new', or undefined
    if (targetId && targetId.startsWith('@')) {
        targetId = targetId.substring(1).toUpperCase();
    }

    return {
        type: 'command',
        verb,
        sourceId,
        action,
        targetId,
        original: trimmed
    };
};
