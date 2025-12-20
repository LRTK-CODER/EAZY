// import { useEffect } from "react";
import { useCrawlerStore } from "@/store/crawlerStore";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Square } from "lucide-react";

interface ActiveScanControlProps {
    targetId: number;
}

export function ActiveScanControl({ targetId }: ActiveScanControlProps) {
    // Polling is handled by the store's startCrawl automatically
    const { isScanning, stats, startCrawl, stopCrawl } = useCrawlerStore();

    const handleToggle = () => {
        if (isScanning) {
            stopCrawl(targetId);
        } else {
            startCrawl(targetId);
        }
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                    Active Scanner Control
                </CardTitle>
                <div className="flex items-center gap-2">
                    <Badge variant={isScanning ? "default" : "secondary"}>
                        {isScanning ? "Running" : "Idle"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between mt-4">
                    <div className="flex gap-4 text-sm">
                        <div className="flex flex-col">
                            <span className="text-muted-foreground">Pages</span>
                            <span className="text-2xl font-bold">{stats.pages_visited}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-muted-foreground">Queue</span>
                            <span className="text-2xl font-bold">{stats.queue_size}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-muted-foreground">Endpoints</span>
                            <span className="text-2xl font-bold">{stats.endpoints_found}</span>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <Button
                            variant={isScanning ? "destructive" : "default"}
                            onClick={handleToggle}
                        >
                            {isScanning ? (
                                <>
                                    <Square className="mr-2 h-4 w-4" /> Stop Scan
                                </>
                            ) : (
                                <>
                                    <Play className="mr-2 h-4 w-4" /> Start Scan
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
