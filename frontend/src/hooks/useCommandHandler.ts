import { useEffect, useRef } from 'react';
import { commandBus, CommandName, CommandPayload } from '../lib/commandBus';

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
