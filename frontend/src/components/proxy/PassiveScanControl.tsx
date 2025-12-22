
import { useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Square, Wifi, WifiOff, MonitorPlay } from "lucide-react";
import { api } from "@/lib/api";
import { useProxyStore } from "@/store/proxyStore";

interface PassiveScanControlProps {
    targetId?: number;
    targetUrl?: string;
}

export function PassiveScanControl({ targetUrl }: PassiveScanControlProps) {

    const { isProxyRunning, isConnected, setProxyRunning, connect, disconnect } = useProxyStore();

    const handleStart = async () => {
        try {
            await api.post('/proxy/start');
            setProxyRunning(true);
            // TODO: Extract token to config or env
            connect('ws://localhost:8000/api/v1/proxy/ws/proxy?token=development-token');
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

    // Cleanup on unmount handled by components
    useEffect(() => {
        return () => {
            // disconnect(); 
        }
    }, [disconnect]);

    const handleLaunchBrowser = async () => {
        if (!targetUrl) return;
        try {
            // Ensure proxy is started
            if (!isProxyRunning) {
                await api.post('/proxy/start');
                setProxyRunning(true);
                connect('ws://localhost:8000/api/v1/proxy/ws/proxy?token=development-token');
                // Give it a moment? No, async nature should be fine.
            }

            await api.post('/proxy/browser/launch', { url: targetUrl });
        } catch (error) {
            console.error('Failed to launch browser', error);
            alert("Failed to launch browser: " + error);
        }
    };


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

                        {targetUrl && (
                            <Button onClick={handleLaunchBrowser} size="sm" variant="outline" className="gap-2 ml-2">
                                <MonitorPlay className="h-4 w-4" /> Launch Proxy Browser
                            </Button>
                        )}

                    </div>
                </div>
            </CardHeader>
        </Card>
    );
}
