
import { create } from 'zustand';

interface ProxyPacket {
    method: string;
    url: string;
    status_code: number;
    request: {
        headers: Record<string, string>;
        body: string | null;
    };
    response: {
        headers: Record<string, string>;
        status: number;
    };
    analysis: any;
    timestamp: number;
}

interface ProxyState {
    isProxyRunning: boolean;
    packets: ProxyPacket[];
    ws: WebSocket | null;
    isConnected: boolean;

    setProxyRunning: (isRunning: boolean) => void;
    addPacket: (packet: ProxyPacket) => void;
    clearPackets: () => void;
    connect: (url: string) => void;
    disconnect: () => void;
}

export const useProxyStore = create<ProxyState>((set, get) => ({
    isProxyRunning: false,
    packets: [],
    ws: null,
    isConnected: false,

    setProxyRunning: (isRunning) => set({ isProxyRunning: isRunning }),

    addPacket: (packet) => set((state) => ({
        packets: [packet, ...state.packets]
    })),

    clearPackets: () => set({ packets: [] }),

    connect: (url) => {
        if (get().ws) return;

        const ws = new WebSocket(url);

        ws.onopen = () => {
            set({ isConnected: true });
            console.log('Proxy WebSocket Connected');
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'proxy_packet') {
                    const packet = { ...message.data, timestamp: Date.now() };
                    get().addPacket(packet);
                }
            } catch (err) {
                console.error('Failed to parse websocket message', err);
            }
        };

        ws.onclose = () => {
            set({ isConnected: false, ws: null });
            console.log('Proxy WebSocket Disconnected');
        };

        set({ ws });
    },

    disconnect: () => {
        const { ws } = get();
        if (ws) {
            ws.close();
            set({ ws: null, isConnected: false });
        }
    }
}));
