/**
 * Custom hook for WebSocket connection
 */

import { useEffect, useRef, useCallback } from "react";
import type { WebSocketMessage } from "../types";

const WS_BASE_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8002";

interface UseWebSocketOptions {
	onMessage?: (message: WebSocketMessage) => void;
	onOpen?: () => void;
	onClose?: () => void;
	onError?: (error: Event) => void;
}

export const useWebSocket = (jobId: string | null, options: UseWebSocketOptions = {}) => {
	const wsRef = useRef<WebSocket | null>(null);
	const reconnectTimeoutRef = useRef<number | null>(null);

	const connect = useCallback(() => {
		if (!jobId) return;

		const wsUrl = `${WS_BASE_URL}/ws/${jobId}`;
		const ws = new WebSocket(wsUrl);

		ws.onopen = () => {
			console.log("[WebSocket] Connected to", wsUrl);
			options.onOpen?.();
		};

		ws.onmessage = (event) => {
			try {
				const message: WebSocketMessage = JSON.parse(event.data);
				console.log("[WebSocket] Message received:", message);
				options.onMessage?.(message);
			} catch (error) {
				console.error("[WebSocket] Failed to parse message:", error);
			}
		};

		ws.onerror = (error) => {
			console.error("[WebSocket] Error:", error);
			options.onError?.(error);
		};

		ws.onclose = () => {
			console.log("[WebSocket] Disconnected");
			options.onClose?.();

			// Auto-reconnect after 3 seconds
			reconnectTimeoutRef.current = window.setTimeout(() => {
				console.log("[WebSocket] Reconnecting...");
				connect();
			}, 3000);
		};

		wsRef.current = ws;
	}, [jobId, options]);

	const disconnect = useCallback(() => {
		if (reconnectTimeoutRef.current) {
			clearTimeout(reconnectTimeoutRef.current);
			reconnectTimeoutRef.current = null;
		}

		if (wsRef.current) {
			wsRef.current.close();
			wsRef.current = null;
		}
	}, []);

	useEffect(() => {
		if (jobId) {
			connect();
		}

		return () => {
			disconnect();
		};
	}, [jobId, connect, disconnect]);

	return {
		isConnected: wsRef.current?.readyState === WebSocket.OPEN,
		disconnect,
	};
};
