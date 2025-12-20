import { useEffect } from "react";
import { format } from "date-fns";
import { useCrawlerStore } from "@/store/crawlerStore";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ScanHistoryListProps {
    targetId: number;
}

export function ScanHistoryList({ targetId }: ScanHistoryListProps) {
    const { history, fetchHistory, loadJobDetails } = useCrawlerStore();

    useEffect(() => {
        fetchHistory(targetId);
    }, [targetId, fetchHistory]);

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Scan History</CardTitle>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => fetchHistory(targetId)}>
                    <RefreshCw className="h-4 w-4" />
                </Button>
            </CardHeader>
            <CardContent className="flex-1 p-0 min-h-0">
                <ScrollArea className="h-full">
                    <Table>
                        <TableHeader className="bg-background sticky top-0 z-10 shadow-sm">
                            <TableRow>
                                <TableHead className="w-[120px]">Start Time</TableHead>
                                <TableHead className="w-[80px]">Status</TableHead>
                                <TableHead className="w-[60px] text-center">Pages</TableHead>
                                <TableHead className="w-[60px] text-center">EPs</TableHead>
                                <TableHead className="text-right w-[80px]">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {history.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground h-48">
                                        No scan history found.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                history.map((job) => (
                                    <TableRow key={job.id}>
                                        <TableCell className="text-[10px] py-2 font-mono text-muted-foreground">
                                            {job.start_time ? format(new Date(job.start_time), "MMM d, HH:mm") : "-"}
                                        </TableCell>
                                        <TableCell className="py-2">
                                            <Badge
                                                variant={
                                                    job.status === "completed"
                                                        ? "secondary"
                                                        : job.status === "running"
                                                            ? "default"
                                                            : job.status === "failed"
                                                                ? "destructive"
                                                                : "outline"
                                                }
                                                className="text-[10px] px-2 py-0.5"
                                            >
                                                {job.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-center text-xs py-2">{job.stats?.pages_visited || 0}</TableCell>
                                        <TableCell className="text-center text-xs py-2">{job.stats?.endpoints_found || 0}</TableCell>
                                        <TableCell className="text-right py-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-6 text-[10px] px-2"
                                                onClick={() => loadJobDetails(job.id)}
                                            >
                                                View
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
