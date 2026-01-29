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

import { useEffect, useRef } from 'react';
import { commandBus, CommandName, CommandPayload } from '../lib/commandBus';

/**
 * A React hook that subscribes to a command from the commandBus while solving
 * common React pitfalls with external event buses.
 * 
 * ## Why This Hook Exists
 * 
 * While it might seem like an extra layer of complexity instead of directly using
 * `commandBus.subscribe()`, this hook solves three critical problems:
 * 
 * ### 1. Solving the "Stale Closures" Problem (Most Important)
 * 
 * In React, functions defined inside a component are recreated on every render.
 * If you subscribe to the commandBus directly inside a useEffect:
 * 
 * ```typescript
 * // ❌ PROBLEMATIC: Direct subscription
 * useEffect(() => {
 *     const unsub = commandBus.subscribe('load', (payload) => {
 *         console.log(someComponentState); // This would be STALE!
 *     });
 *     return unsub;
 * }, []); // Only runs once
 * ```
 * 
 * The closure created during the first render is "stale"—it will always see the
 * initial values of your state/props. To fix this without the hook, you'd have to
 * unsubscribe and re-subscribe every time your state changes, which is inefficient
 * and can cause race conditions.
 * 
 * **This hook solves it by:**
 * - Using a `useRef` to always store the latest version of your handler
 * - Subscribing once to a stable "wrapper" function
 * - The wrapper always calls the current version held in the ref
 * 
 * ### 2. Lifecycle Automation
 * 
 * The hook handles the "boring" parts of subscription management:
 * - Automatically calls `commandBus.subscribe()`
 * - Automatically returns the `unsubscribe` cleanup function
 * - Ensures you don't leak memory when a component unmounts
 * 
 * ### 3. Handling Command Name Changes
 * 
 * If the `name` parameter changes (e.g., a component dynamically switches which
 * command it's listening to), the hook automatically:
 * 1. Unsubscribes from the old command name (via cleanup function)
 * 2. Subscribes to the new command name (via re-running the effect)
 * 
 * This is handled by the dependency array `[name]` in the subscription effect.
 * 
 * ## Usage
 * 
 * Instead of writing 10-15 lines of useEffect, useRef, and unsubscribe logic
 * in every component, you just write:
 * 
 * ```typescript
 * useCommandHandler(COMMAND_NAMES.LOAD, (payload) => {
 *     // Logic that always has access to the latest state
 *     console.log(currentState); // ✅ Always fresh!
 * });
 * ```
 * 
 * @param name - The command name to subscribe to
 * @param handler - The handler function that will be called when the command is dispatched
 */
export const useCommandHandler = (
    name: CommandName,
    handler: (payload: CommandPayload) => void | boolean | Promise<void | boolean>
) => {
    const handlerRef = useRef(handler);

    // Always keep the ref up to date with the latest handler
    useEffect(() => {
        handlerRef.current = handler;
    }, [handler]);

    useEffect(() => {
        // Subscribe once and call the latest handler from the ref
        const wrapper = (payload: CommandPayload) => {
            return handlerRef.current(payload);
        };

        return commandBus.subscribe(name, wrapper);
    }, [name]); // Only re-subscribe if the command name changes
};
