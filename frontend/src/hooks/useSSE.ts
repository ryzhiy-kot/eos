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

import { ConnectionStatus } from '@/types/constants';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';


interface SSEMessage {
    type: string;
    [key: string]: any;
}

interface UseSSEOptions {
    url?: string;
    onMessage?: (message: SSEMessage) => void;
    onError?: (error: Event) => void;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

export function useSSE({
    url = 'http://localhost:8000/api/v1/events/stream',
    onMessage,
    onError,
    reconnectInterval = 1000,
    maxReconnectAttempts = 10,
}: UseSSEOptions = {}) {
    const sessionToken = useAuthStore(state => state.session_token);
    const [status, setStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
    const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);

    // Stable refs for callbacks to prevent dependency changes
    const onMessageRef = useRef(onMessage);
    const onErrorRef = useRef(onError);

    useEffect(() => {
        onMessageRef.current = onMessage;
        onErrorRef.current = onError;
    }, [onMessage, onError]);

    const connect = useCallback(() => {
        // Don't connect if component is unmounted or already connected
        if (!isMountedRef.current || eventSourceRef.current?.readyState === EventSource.OPEN) {
            return;
        }

        // Don't attempt to connect if max reconnection attempts reached
        if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            console.warn('Max reconnection attempts reached. Connection abandoned.');
            setStatus(ConnectionStatus.DISCONNECTED);
            return;
        }

        setStatus(ConnectionStatus.CONNECTING);
        console.log(`Attempting to connect to SSE (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);

        try {
            // Append token if available
            let finalUrl = url;
            if (sessionToken) {
                const separator = url.includes('?') ? '&' : '?';
                finalUrl = `${url}${separator}token=${encodeURIComponent(sessionToken)}`;
            }

            const eventSource = new EventSource(finalUrl);
            eventSourceRef.current = eventSource;

            eventSource.onopen = () => {
                console.log('SSE connection established');
                setStatus(ConnectionStatus.CONNECTED);
                reconnectAttemptsRef.current = 0;
            };

            eventSource.onmessage = (event) => {
                try {
                    const data: SSEMessage = JSON.parse(event.data);

                    if (data.type === 'heartbeat') {
                        setLastHeartbeat(Date.now());
                    }

                    onMessageRef.current?.(data);
                } catch (error) {
                    console.error('Failed to parse SSE message:', error);
                }
            };

            eventSource.onerror = (error) => {
                console.error('SSE connection error:', error);
                setStatus(ConnectionStatus.ERROR);
                onErrorRef.current?.(error);
                eventSource.close();

                // Attempt reconnection with exponential backoff
                if (reconnectAttemptsRef.current < maxReconnectAttempts && isMountedRef.current) {
                    const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current);
                    reconnectAttemptsRef.current += 1;

                    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        if (isMountedRef.current) {
                            connect();
                        }
                    }, delay);
                } else {
                    console.warn('Max reconnection attempts reached or component unmounted');
                    setStatus(ConnectionStatus.DISCONNECTED);
                }
            };
        } catch (error) {
            console.error('Failed to create EventSource:', error);
            setStatus(ConnectionStatus.ERROR);
        }
    }, [url, reconnectInterval, maxReconnectAttempts]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        setStatus(ConnectionStatus.DISCONNECTED);
        reconnectAttemptsRef.current = 0;
    }, []);

    useEffect(() => {
        isMountedRef.current = true;
        connect();

        return () => {
            isMountedRef.current = false;
            disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [url]); // Only reconnect when URL changes, not when connect/disconnect change

    return {
        status,
        lastHeartbeat,
        reconnect: connect,
        disconnect,
    };
}
