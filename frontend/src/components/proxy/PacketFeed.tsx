
import { useRef } from "react";
import { useProxyStore } from "@/store/proxyStore";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";


const SafeTableRow = ({ packet, style }: { packet: any, style?: React.CSSProperties }) => {
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
            <TableRow className="cursor-pointer hover:bg-gray-50/50" style={style}>
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
            <TableRow style={style}>
                <TableCell colSpan={5} className="text-red-500">Render Error</TableCell>
            </TableRow>
        )
    }
};

export function PacketFeed() {
    const { packets } = useProxyStore();
    const parentRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
        count: packets.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 53, // Approximate row height
        overscan: 10,
    });

    return (
        <div className="rounded-md border bg-white shadow-sm overflow-hidden h-[600px] flex flex-col">
            <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                    <Activity className="h-4 w-4" /> Live Traffic Feed
                </h3>
                <span className="text-xs text-muted-foreground">{packets.length} Events captured</span>
            </div>

            <div
                ref={parentRef}
                className="flex-1 overflow-auto w-full relative"
            >
                <Table>
                    <TableHeader className="bg-gray-50 sticky top-0 z-10 shadow-sm">
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
                            <>
                                {rowVirtualizer.getVirtualItems().length > 0 && (
                                    <tr style={{ height: rowVirtualizer.getVirtualItems()[0].start }}>
                                        <td colSpan={5} />
                                    </tr>
                                )}
                                {rowVirtualizer.getVirtualItems().map((virtualRow) => (
                                    <SafeTableRow
                                        key={virtualRow.key}
                                        packet={packets[virtualRow.index]}
                                    // We let standard table layout handle width, just virtualization handles which ones render
                                    />
                                ))}
                                {rowVirtualizer.getVirtualItems().length > 0 && (
                                    <tr style={{ height: rowVirtualizer.getTotalSize() - rowVirtualizer.getVirtualItems()[rowVirtualizer.getVirtualItems().length - 1].end }}>
                                        <td colSpan={5} />
                                    </tr>
                                )}
                            </>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
