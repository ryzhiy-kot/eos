export const COMMAND_NAMES = {
    LOAD: 'load',
    GRID: 'grid',
    CLEAR: 'clear',
    FOCUS: 'focus',
    SWAP: 'swap',
    CLOSE: 'close',
    HIDE: 'hide',
    LS: 'ls',
    SHOW: 'show',
    UNDO: 'undo',
    REDO: 'redo',
    CLOCK: 'clock',
    TIMER: 'timer',
    HELP: 'help',
    RENAME: 'rename',
    LOGOUT: 'logout',
    QUESTION: '?',
    PLOT: 'plot',
    RUN: 'run',
    DIFF: 'diff',
    SUMMARIZE: 'summarize',
    REMOVE_PANE: 'rm',
    REMOVE_CLOCK: 'rmclock',
    REMOVE_TIMER: 'rmtimer',
    INIT: 'init',
    CHAT: 'chat',
    CLIP: 'clip',
    OPTIMIZE: 'optimize',
    ARCHIVE: 'archive',
} as const;

export type CommandName = typeof COMMAND_NAMES[keyof typeof COMMAND_NAMES];

export interface CommandPayload {
    name: CommandName;
    args: string[];
    action?: string;
    targetId?: string;
    original?: string;
    context: {
        sourceId?: string;
        targetId?: string;
        focusedPaneId: string | null;
        [key: string]: any;
    };
    onComplete?: (result: boolean) => void;
}

type Subscriber = (payload: CommandPayload) => void | boolean | Promise<void | boolean>;

class CommandBus {
    private subscribers: Map<CommandName, Set<Subscriber>> = new Map();

    subscribe(name: CommandName, subscriber: Subscriber) {
        if (!this.subscribers.has(name)) {
            this.subscribers.set(name, new Set());
        }
        this.subscribers.get(name)!.add(subscriber);
        return () => this.unsubscribe(name, subscriber);
    }

    private unsubscribe(name: CommandName, subscriber: Subscriber) {
        const set = this.subscribers.get(name);
        if (set) {
            set.delete(subscriber);
            if (set.size === 0) {
                this.subscribers.delete(name);
            }
        }
    }

    async dispatch(payload: CommandPayload): Promise<boolean> {
        const subscribers = this.subscribers.get(payload.name);
        if (!subscribers || subscribers.size === 0) {
            // Log as debug rather than warn to avoid console clutter for user-typed typos
            console.debug(`No subscribers for command: ${payload.name}`);
            payload.onComplete?.(false);
            return false;
        }

        let handled = false;
        for (const subscriber of subscribers) {
            try {
                const result = await subscriber(payload);
                if (result !== false) {
                    handled = true;
                }
            } catch (error) {
                console.error(`Error executing command ${payload.name}:`, error);
            }
        }

        payload.onComplete?.(handled);
        return handled;
    }
}

export const commandBus = new CommandBus();
