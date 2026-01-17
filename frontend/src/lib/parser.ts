export interface ParsedCommand {
    type: 'command' | 'message';
    verb?: string;
    sourceId?: string;
    action?: string;
    targetId?: string;
    original: string;
}

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

    // Check if second token is a Pane ID (P1, P2, etc.)
    if (tokens[1] && /^P\d+$/.test(tokens[1])) {
        sourceId = tokens[1];
        actionStartIdx = 2;
    } else {
        sourceId = activePaneId || undefined;
    }

    const action = tokens.slice(actionStartIdx).join(' ');
    const targetId = targetPart; // 'P2', 'new', or undefined

    return {
        type: 'command',
        verb,
        sourceId,
        action,
        targetId,
        original: trimmed
    };
};
