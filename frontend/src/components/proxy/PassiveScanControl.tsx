
import { useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Square, Wifi, WifiOff } from "lucide-react";
import { api } from "@/lib/api";
import { useProxyStore } from "@/store/proxyStore";

export function PassiveScanControl() {
    const { isProxyRunning, isConnected, setProxyRunning, connect, disconnect } = useProxyStore();

    const handleStart = async () => {
        try {
            await api.post('/proxy/start');
            setProxyRunning(true);
            connect('ws://localhost:8000/api/v1/proxy/ws/proxy');
        } catch (error) {
            console.error('Failed to start proxy', error);
            // Ideally show toast
        }
    };

    const handleStop = async () => {
        try {
            await api.post('/proxy/stop');
            setProxyRunning(false);
            disconnect();
        } catch (error) {
            console.error('Failed to stop proxy', error);
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        // Optional: Don't disconnect on unmount if we want background connection?
        // For now, let's keep it manual.
        return () => {
            // disconnect(); 
        }
    }, []);

    return (
        <Card className="mb-6 border-l-4 border-l-blue-500 shadow-sm">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            Passive Proxy Scanner
                            {isProxyRunning ? (
                                <Badge variant="default" className="bg-green-500 hover:bg-green-600">Running :8081</Badge>
                            ) : (
                                <Badge variant="secondary">Stopped</Badge>
                            )}
                        </CardTitle>
                        <CardDescription>
                            Configure your browser proxy to <strong>localhost:8081</strong> to capture traffic.
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        {isConnected ? <Wifi className="h-4 w-4 text-green-500" /> : <WifiOff className="h-4 w-4 text-gray-400" />}
                        <span className="text-xs text-muted-foreground mr-4">
                            {isConnected ? "Feed Connected" : "Feed Disconnected"}
                        </span>

                        {!isProxyRunning ? (
                            <Button onClick={handleStart} size="sm" className="gap-2 bg-blue-600 hover:bg-blue-700">
                                <Play className="h-4 w-4" /> Start Proxy
                            </Button>
                        ) : (
                            <Button onClick={handleStop} size="sm" variant="destructive" className="gap-2">
                                <Square className="h-4 w-4" /> Stop Proxy
                            </Button>
                        )}
                    </div>
                </div>
            </CardHeader>
        </Card>
    );
}
