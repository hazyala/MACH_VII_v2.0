import useAppStore from './store';

// WebSocket 연결 관리자 (Singleton)
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.url = 'ws://localhost:8000/ws';
        this.reconnectInterval = 3000;
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        console.log(`[WS] Connecting to ${this.url}...`);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const packet = JSON.parse(event.data);
                // 스토어 직접 업데이트 (구독 컴포넌트에 자동 전파)
                useAppStore.getState().updateState(packet);
            } catch (e) {
                console.error('[WS] Parse Error:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected. Reconnecting...');
            setTimeout(() => this.connect(), this.reconnectInterval);
        };

        this.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
            this.ws.close();
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export const wsManager = new WebSocketManager();
