import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChevronRight, ChevronDown, FileText, Globe, Lock, Unlock, Folder, FolderOpen } from "lucide-react";
import { api } from "@/lib/api";

interface TrafficViewerProps {
    targetId: number;
}

interface LogEntry {
    id: number;
    method: string;
    url: string;
    path: string;
    status_code: number;
    created_at: string;
    source: 'active' | 'passive';
}

interface LogDetail extends LogEntry {
    request: {
        headers: Record<string, string>;
        body: string | null;
    };
    response: {
        headers: Record<string, string>;
        body: string | null;
        status: number;
    };
}

interface SitemapNode {
    key: string;
    title: string;
    children: SitemapNode[];
    is_leaf: boolean;
}



// Recursive Tree Node Component
const TreeNode = ({ node, level, onSelect }: { node: SitemapNode; level: number, onSelect: (key: string) => void }) => {
    const [isOpen, setIsOpen] = useState(false);
    const hasChildren = node.children && node.children.length > 0;

    // Determine Icon
    const isRootDomain = level === 0;
    const isSecure = node.key.startsWith('https');

    let Icon = FileText;
    let iconColor = "text-slate-400";

    if (isRootDomain) {
        Icon = isSecure ? Lock : Unlock;
        iconColor = isSecure ? "text-green-600" : "text-amber-500";
    } else if (hasChildren) {
        Icon = isOpen ? FolderOpen : Folder;
        iconColor = "text-blue-400";
    }

    return (
        <div className="select-none">
            <div
                className={`flex items-center py-1 px-2 hover:bg-slate-100 cursor-pointer text-xs`}
                style={{ paddingLeft: `${level * 12}px` }}
                onClick={() => {
                    if (hasChildren) setIsOpen(!isOpen);
                    onSelect(node.key);
                }}
            >
                <span className="mr-1 h-4 w-4 flex items-center justify-center">
                    {hasChildren && (
                        isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />
                    )}
                </span>
                <Icon className={`h-3 w-3 mr-2 ${iconColor}`} />
                <span className="truncate">{node.title}</span>
            </div>
            {isOpen && node.children.map(child => (
                <TreeNode key={child.key} node={child} level={level + 1} onSelect={onSelect} />
            ))}
        </div>
    );
};

export function TrafficViewer({ targetId }: TrafficViewerProps) {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [sitemap, setSitemap] = useState<SitemapNode[]>([]);
    const [selectedLogId, setSelectedLogId] = useState<number | null>(null);
    const [logDetail, setLogDetail] = useState<LogDetail | null>(null);
    const [selectedPath, setSelectedPath] = useState<string | null>(null);

    // Initial Load
    useEffect(() => {
        fetchLogs();
        fetchSitemap();
    }, [targetId]);

    // Path Filter Load
    useEffect(() => {
        if (selectedPath) {
            fetchLogs(selectedPath);
        }
    }, [selectedPath]);

    // Detail Load
    useEffect(() => {
        if (selectedLogId) {
            fetchDetail(selectedLogId);
        }
    }, [selectedLogId]);

    const fetchLogs = async (path?: string) => {
        try {
            const params: any = { target_id: targetId };
            if (path && path !== 'root') params.path_filter = path;
            const res = await api.get('/traffic', { params });
            setLogs(res.data);
        } catch (error) {
            console.error("Failed to fetch traffic logs", error);
        }
    };

    const fetchSitemap = async () => {
        try {
            const res = await api.get('/traffic/sitemap', { params: { target_id: targetId } });
            setSitemap(res.data);
        } catch (error) {
            console.error("Failed to fetch sitemap", error);
        }
    };

    const fetchDetail = async (id: number) => {
        try {
            const res = await api.get(`/traffic/${id}`);
            setLogDetail(res.data);
        } catch (error) {
            console.error("Failed to fetch log detail", error);
        }
    };

    return (
        <div className="h-[600px] border rounded-md">
            <ResizablePanelGroup direction="horizontal">
                {/* Left: Site Map */}
                <ResizablePanel defaultSize={20} minSize={15}>
                    <div className="h-full flex flex-col">
                        <div className="p-2 bg-slate-100 font-semibold text-xs border-b">Site Map</div>
                        <ScrollArea className="flex-1">
                            <div className="p-2">
                                {sitemap.map(node => (
                                    <TreeNode
                                        key={node.key}
                                        node={node}
                                        level={0}
                                        onSelect={(key) => setSelectedPath(key)}
                                    />
                                ))}
                                {sitemap.length === 0 && <div className="text-xs text-muted-foreground p-2">No structure found.</div>}
                            </div>
                        </ScrollArea>
                    </div>
                </ResizablePanel>

                <ResizableHandle />

                {/* Right Area */}
                <ResizablePanel defaultSize={80}>
                    <ResizablePanelGroup direction="vertical">
                        {/* Top Right: Request List */}
                        <ResizablePanel defaultSize={50} minSize={30}>
                            <div className="h-full flex flex-col">
                                <div className="p-2 bg-slate-100 font-semibold text-xs border-b flex justify-between">
                                    <span>Traffic Log {selectedPath ? `(${selectedPath})` : ''}</span>
                                    <span className="text-muted-foreground">{logs.length} requests</span>
                                </div>
                                <div className="flex-1 overflow-auto">
                                    <Table>
                                        <TableHeader className="sticky top-0 bg-white z-10">
                                            <TableRow className="h-8">
                                                <TableHead className="w-[80px]">Method</TableHead>
                                                <TableHead className="w-[300px]">URL</TableHead>
                                                <TableHead className="w-[80px]">Status</TableHead>
                                                <TableHead className="w-[100px]">Source</TableHead>
                                                <TableHead>Time</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {logs.map(log => (
                                                <TableRow
                                                    key={log.id}
                                                    className={`cursor-pointer h-8 ${selectedLogId === log.id ? "bg-blue-50" : ""}`}
                                                    onClick={() => setSelectedLogId(log.id)}
                                                >
                                                    <TableCell className="py-1 font-mono text-xs font-bold">{log.method}</TableCell>
                                                    <TableCell className="py-1 text-xs truncate max-w-[300px]" title={log.url}>{log.path}</TableCell>
                                                    <TableCell className="py-1">
                                                        <Badge variant={log.status_code >= 400 ? "destructive" : "outline"} className="text-[10px] h-5">
                                                            {log.status_code}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="py-1 text-xs">{log.source}</TableCell>
                                                    <TableCell className="py-1 text-xs text-muted-foreground">
                                                        {new Date(log.created_at).toLocaleTimeString()}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            </div>
                        </ResizablePanel>

                        <ResizableHandle />

                        {/* Bottom Right: Detail View */}
                        <ResizablePanel defaultSize={50} minSize={30}>
                            <div className="h-full flex flex-col bg-slate-50">
                                {logDetail ? (
                                    <Tabs defaultValue="request" className="h-full flex flex-col">
                                        <div className="border-b px-2 py-1 bg-white flex items-center gap-2">
                                            <TabsList className="h-7">
                                                <TabsTrigger value="request" className="text-xs h-6">Request</TabsTrigger>
                                                <TabsTrigger value="response" className="text-xs h-6">Response</TabsTrigger>
                                            </TabsList>
                                            <div className="ml-auto text-xs font-mono text-muted-foreground truncate max-w-[400px]">
                                                {logDetail.url}
                                            </div>
                                        </div>

                                        <TabsContent value="request" className="flex-1 p-0 m-0 overflow-hidden">
                                            <ScrollArea className="h-full p-4">
                                                <div className="text-xs font-mono whitespace-pre-wrap">
                                                    {Object.entries(logDetail.request.headers).map(([k, v]) => (
                                                        <div key={k}><span className="font-bold text-blue-700">{k}:</span> {v}</div>
                                                    ))}
                                                    <div className="my-2 border-b" />
                                                    {logDetail.request.body || <span className="text-slate-400 italic">No Body</span>}
                                                </div>
                                            </ScrollArea>
                                        </TabsContent>

                                        <TabsContent value="response" className="flex-1 p-0 m-0 overflow-hidden">
                                            <ScrollArea className="h-full p-4">
                                                <div className="text-xs font-mono whitespace-pre-wrap">
                                                    <div className="mb-2 font-bold text-green-700">HTTP/1.1 {logDetail.response.status}</div>
                                                    {Object.entries(logDetail.response.headers).map(([k, v]) => (
                                                        <div key={k}><span className="font-bold text-blue-700">{k}:</span> {v}</div>
                                                    ))}
                                                    <div className="my-2 border-b" />
                                                    {logDetail.response.body || <span className="text-slate-400 italic">No Body</span>}
                                                </div>
                                            </ScrollArea>
                                        </TabsContent>
                                    </Tabs>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                                        Select a request to view details
                                    </div>
                                )}
                            </div>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    );
}
