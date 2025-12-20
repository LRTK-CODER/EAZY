import { create } from 'zustand';
import axios from 'axios';

// const API_BASE_URL = 'http://localhost:8000/api/v1'; // Use proxy or env in real app
// For now relying on Vite proxy or relative path if configured
const API_URL = '/api/v1/crawler';


import type { ScanJob, CrawledEndpoint, CrawlerStats } from '@/types/crawler';

interface CrawlerState {
    isScanning: boolean;
    stats: CrawlerStats;
    endpoints: CrawledEndpoint[];
    history: ScanJob[];
    pollInterval: any;

    startCrawl: (targetId: number) => Promise<void>;
    stopCrawl: (targetId: number) => Promise<void>;
    reset: () => void;
    startPolling: (targetId: number) => void;
    stopPolling: () => void;
    fetchHistory: (targetId: number) => Promise<void>;
    loadJobDetails: (jobId: number) => Promise<void>;
}

export const useCrawlerStore = create<CrawlerState>((set, get) => ({
    isScanning: false,
    stats: {
        pages_visited: 0,
        queue_size: 0,
        forms_found: 0,
        endpoints_found: 0,
    },
    endpoints: [],
    history: [],
    pollInterval: null,

    startCrawl: async (targetId: number) => {
        try {
            console.log(`Starting crawl for target ${targetId}`);
            await axios.post(`${API_URL}/start`, { target_id: targetId, max_depth: 2, max_pages: 50 });
            set({ isScanning: true, endpoints: [], stats: { pages_visited: 0, queue_size: 0, forms_found: 0, endpoints_found: 0 } });
            get().startPolling(targetId);
        } catch (error) {
            console.error("Failed to start crawl", error);
        }
    },

    stopCrawl: async (targetId: number) => {
        try {
            console.log('Stopping crawl');
            await axios.post(`${API_URL}/stop/${targetId}`);
            set({ isScanning: false });
            get().stopPolling();
        } catch (error) {
            console.error("Failed to stop crawl", error);
        }
    },

    startPolling: (targetId: number) => {
        get().stopPolling(); // Clear existing
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_URL}/status/${targetId}`);
                const data = res.data;

                if (data.status === 'idle') {
                    // Do nothing or stop polling if we expected it to run?
                    // For now, if we think we are scanning but status is idle, maybe it finished?
                    // But status returns 'completed' or 'failed' if it ran.
                    if (get().isScanning) {
                        // It might have not initialized yet, or lost state?
                    }
                } else {
                    set({
                        stats: data.stats || get().stats,
                        endpoints: data.endpoints || [],
                        isScanning: data.status === 'running'
                    });

                    if (data.status !== 'running') {
                        get().stopPolling();
                    }
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 1000);
        set({ pollInterval: interval });
    },

    stopPolling: () => {
        const { pollInterval } = get();
        if (pollInterval) clearInterval(pollInterval);
        set({ pollInterval: null });
    },

    reset: () => {
        get().stopPolling();
        set({
            isScanning: false,
            stats: { pages_visited: 0, queue_size: 0, forms_found: 0, endpoints_found: 0 },
            endpoints: [],
            history: [] // Optional: clear history on reset or keep it? Maybe keep it.
        });
    },

    fetchHistory: async (targetId: number) => {
        try {
            const res = await axios.get(`${API_URL}/history/${targetId}`);
            set({ history: res.data });
        } catch (error) {
            console.error("Failed to fetch scan history", error);
        }
    },

    loadJobDetails: async (jobId: number) => {
        try {
            const res = await axios.get(`${API_URL}/jobs/${jobId}`);
            const job = res.data as ScanJob;
            // Update endpoints view with the selected job's endpoints
            set({
                endpoints: job.endpoints || [],
                stats: { ...job.stats, forms_found: 0 } // sync stats too?
            });
        } catch (error) {
            console.error("Failed to load job details", error);
        }
    }
}));
