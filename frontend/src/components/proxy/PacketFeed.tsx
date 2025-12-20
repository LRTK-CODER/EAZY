

import { useProxyStore } from "@/store/proxyStore";
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
import { Activity } from "lucide-react";

export function PacketFeed() {
    const { packets } = useProxyStore();

    const getMethodColor = (method: string) => {
        switch (method) {
            case 'GET': return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
            case 'POST': return 'bg-green-100 text-green-800 hover:bg-green-100';
            case 'PUT': return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
            case 'DELETE': return 'bg-red-100 text-red-800 hover:bg-red-100';
            default: return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
        }
    };

    const getStatusColor = (status: number) => {
        if (status >= 200 && status < 300) return 'text-green-600 font-medium';
        if (status >= 300 && status < 400) return 'text-blue-600 font-medium';
        if (status >= 400 && status < 500) return 'text-orange-600 font-medium';
        if (status >= 500) return 'text-red-600 font-medium';
        return 'text-gray-600';
    };

    return (
        <div className="rounded-md border bg-white shadow-sm overflow-hidden h-[600px] flex flex-col">
            <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                    <Activity className="h-4 w-4" /> Live Traffic Feed
                </h3>
                <span className="text-xs text-muted-foreground">{packets.length} Events captured</span>
            </div>

            <ScrollArea className="flex-1">
                <Table>
                    <TableHeader className="bg-gray-50 sticky top-0">
                        <TableRow>
                            <TableHead className="w-[100px]">Method</TableHead>
                            <TableHead className="w-[80px]">Status</TableHead>
                            <TableHead>URL</TableHead>
                            <TableHead className="w-[150px]">Content-Type</TableHead>
                            <TableHead className="w-[100px] text-right">Time</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {packets.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                                    No traffic captured yet. Start the proxy and browse the target.
                                </TableCell>
                            </TableRow>
                        ) : (
                            packets.map((packet, index) => (
                                <TableRow key={index} className="cursor-pointer hover:bg-gray-50/50">
                                    <TableCell>
                                        <Badge variant="outline" className={`${getMethodColor(packet.method)} border-0`}>
                                            {packet.method}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className={getStatusColor(packet.status_code)}>
                                        {packet.status_code}
                                    </TableCell>
                                    <TableCell className="font-mono text-xs truncate max-w-[300px]" title={packet.url}>
                                        {packet.url}
                                    </TableCell>
                                    <TableCell className="text-xs text-muted-foreground truncate max-w-[150px]">
                                        {packet.response.headers['content-type'] || '-'}
                                    </TableCell>
                                    <TableCell className="text-right text-xs text-muted-foreground">
                                        {new Date(packet.timestamp).toLocaleTimeString()}
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </ScrollArea>
        </div>
    );
}
