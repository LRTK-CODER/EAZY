import { useState } from "react";
import { useCrawlerStore } from "@/store/crawlerStore";
import type { CrawledEndpoint } from "@/types/crawler";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";

export function CrawledEndpoints() {
    const { endpoints } = useCrawlerStore();
    const [selectedEndpoint, setSelectedEndpoint] = useState<CrawledEndpoint | null>(null);

    const getMethodColor = (method: string) => {
        switch (method.toUpperCase()) {
            case 'GET': return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
            case 'POST': return 'bg-green-100 text-green-800 hover:bg-green-100';
            case 'PUT': return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
            case 'DELETE': return 'bg-red-100 text-red-800 hover:bg-red-100';
            default: return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
        }
    };

    const getDisplayPath = (urlStr: string) => {
        try {
            const url = new URL(urlStr);
            return decodeURIComponent(url.pathname) + url.search;
        } catch (e) {
            return urlStr;
        }
    };

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Discovered Endpoints</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 min-h-0">
                <ScrollArea className="h-[600px]">
                    <Table>
                        <TableHeader className="bg-background sticky top-0 z-10 shadow-sm">
                            <TableRow>
                                <TableHead className="w-[80px]">Method</TableHead>
                                <TableHead>URL Pattern</TableHead>
                                <TableHead className="w-[80px]">Params</TableHead>
                                <TableHead className="w-[80px]">Source</TableHead>
                                <TableHead className="w-[100px] text-right">Time</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {endpoints.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground h-48">
                                        No endpoints discovered yet.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                endpoints.map((ep, i) => (
                                    <TableRow
                                        key={ep.spec_hash || i}
                                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                                        onClick={() => setSelectedEndpoint(ep)}
                                    >
                                        <TableCell className="py-2">
                                            <Badge variant="outline" className={`${getMethodColor(ep.method)} border-0 px-2 py-0.5 text-[10px]`}>
                                                {ep.method}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="font-mono text-xs max-w-[200px] py-2">
                                            <TooltipProvider>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <div className="truncate cursor-help">
                                                            {getDisplayPath(ep.url)}
                                                        </div>
                                                    </TooltipTrigger>
                                                    <TooltipContent>
                                                        <p className="font-mono text-xs">{ep.url}</p>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground py-2">
                                            {ep.parameters
                                                ? <Badge variant="secondary" className="text-[10px] px-1.5 h-5">{ep.parameters.length}</Badge>
                                                : (ep.params ? <Badge variant="secondary" className="text-[10px] px-1.5 h-5">{Object.keys(ep.params).length}</Badge> : '-')}
                                        </TableCell>
                                        <TableCell className="py-2">
                                            <span className="text-[10px] text-muted-foreground capitalize">
                                                {ep.source || 'unknown'}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right text-[10px] text-muted-foreground py-2 font-mono">
                                            {ep.timestamp ? new Date(ep.timestamp).toLocaleTimeString() : '-'}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </ScrollArea>
            </CardContent>

            <Dialog open={!!selectedEndpoint} onOpenChange={(open) => !open && setSelectedEndpoint(null)}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            {selectedEndpoint && (
                                <Badge className={getMethodColor(selectedEndpoint.method)}>
                                    {selectedEndpoint.method}
                                </Badge>
                            )}
                            <span className="font-mono text-sm truncate max-w-[400px]">
                                {selectedEndpoint?.url}
                            </span>
                        </DialogTitle>
                        <DialogDescription>
                            Endpoint details and detected parameters.
                        </DialogDescription>
                    </DialogHeader>

                    {selectedEndpoint && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div className="p-3 bg-gray-50 rounded-md">
                                    <span className="block text-gray-500 text-xs mb-1">Source</span>
                                    <span className="font-medium">{selectedEndpoint.source || 'Unknown'}</span>
                                </div>
                                <div className="p-3 bg-gray-50 rounded-md">
                                    <span className="block text-gray-500 text-xs mb-1">Discovered At</span>
                                    <span className="font-medium">
                                        {selectedEndpoint.timestamp
                                            ? new Date(selectedEndpoint.timestamp).toLocaleString()
                                            : '-'}
                                    </span>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-semibold mb-2">Parameters</h4>
                                <div className="border rounded-md overflow-hidden">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-gray-50">
                                                <TableHead>Name</TableHead>
                                                <TableHead>Type</TableHead>
                                                <TableHead>Location</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {selectedEndpoint.parameters && selectedEndpoint.parameters.length > 0 ? (
                                                selectedEndpoint.parameters.map((param: any, idx: number) => (
                                                    <TableRow key={idx}>
                                                        <TableCell className="font-mono text-xs">{param.name}</TableCell>
                                                        <TableCell>
                                                            <Badge variant="outline" className="text-[10px]">
                                                                {param.type}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell className="text-xs text-gray-500">{param.location}</TableCell>
                                                    </TableRow>
                                                ))
                                            ) : selectedEndpoint.params && Object.keys(selectedEndpoint.params).length > 0 ? (
                                                Object.entries(selectedEndpoint.params).map(([key], idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell className="font-mono text-xs">{key}</TableCell>
                                                        <TableCell>
                                                            <Badge variant="outline" className="text-[10px]">string(legacy)</Badge>
                                                        </TableCell>
                                                        <TableCell className="text-xs text-gray-500">query</TableCell>
                                                    </TableRow>
                                                ))
                                            ) : (
                                                <TableRow>
                                                    <TableCell colSpan={3} className="text-center text-muted-foreground text-xs py-4">
                                                        No parameters detected.
                                                    </TableCell>
                                                </TableRow>
                                            )}
                                        </TableBody>
                                    </Table>
                                </div>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </Card>
    );
}
