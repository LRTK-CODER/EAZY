

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


const SafeTableRow = ({ packet }: { packet: any }) => {
    try {
        if (!packet) return null;

        const getMethodColor = (method: string) => {
            if (!method) return 'bg-gray-100 text-gray-800';
            switch (method.toUpperCase()) {
                case 'GET': return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
                case 'POST': return 'bg-green-100 text-green-800 hover:bg-green-100';
                case 'PUT': return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
                case 'DELETE': return 'bg-red-100 text-red-800 hover:bg-red-100';
                default: return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
            }
        };

        const getStatusColor = (status: number) => {
            if (!status) return 'text-gray-600';
            if (status >= 200 && status < 300) return 'text-green-600 font-medium';
            if (status >= 300 && status < 400) return 'text-blue-600 font-medium';
            if (status >= 400 && status < 500) return 'text-orange-600 font-medium';
            if (status >= 500) return 'text-red-600 font-medium';
            return 'text-gray-600';
        };

        const contentType = (() => {
            try {
                if (!packet?.response?.headers) return '-';
                const headers = packet.response.headers;
                const contentTypeKey = Object.keys(headers).find(key => key.toLowerCase() === 'content-type');
                return contentTypeKey ? String(headers[contentTypeKey]) : '-';
            } catch (e) {
                return 'Err';
            }
        })();

        return (
            <TableRow className="cursor-pointer hover:bg-gray-50/50">
                <TableCell>
                    <Badge variant="outline" className={`${getMethodColor(packet.method)} border-0`}>
                        {packet.method || '???'}
                    </Badge>
                </TableCell>
                <TableCell className={getStatusColor(packet.status_code)}>
                    {packet.status_code || '-'}
                </TableCell>
                <TableCell className="font-mono text-xs truncate max-w-[300px]" title={packet.url || ''}>
                    {packet.url || 'No URL'}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground truncate max-w-[150px]">
                    {contentType}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">
                    {packet.timestamp ? new Date(packet.timestamp).toLocaleTimeString() : '-'}
                </TableCell>
            </TableRow>
        );
    } catch (error) {
        console.error("Render Error Row:", error, packet);
        return (
            <TableRow>
                <TableCell colSpan={5} className="text-red-500">Render Error</TableCell>
            </TableRow>
        )
    }
};

export function PacketFeed() {
    const { packets } = useProxyStore();

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
                                <SafeTableRow key={index} packet={packet} />
                            ))
                        )}
                    </TableBody>
                </Table>
            </ScrollArea>
        </div>
    );
}
