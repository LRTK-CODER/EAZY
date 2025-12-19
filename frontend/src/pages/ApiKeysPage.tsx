import { useEffect, useState } from "react";
import { useProjectStore } from "@/store/projectStore";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Trash2, Plus, Edit2, ShieldAlert, KeyRound } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiKeyDialog } from "@/components/settings/ApiKeyDialog";
import type { ApiKey } from "@/types/llm";

export function ApiKeysPage() {
    const { apiKeys, fetchApiKeys, createApiKey, updateApiKey, deleteApiKey } = useProjectStore();
    const [selectedKeys, setSelectedKeys] = useState<Set<number>>(new Set());
    const [dialogOpen, setDialogOpen] = useState(false);
    const [dialogMode, setDialogMode] = useState<'create' | 'edit' | 'view'>('create');
    const [selectedKeyData, setSelectedKeyData] = useState<ApiKey | undefined>(undefined);
    const [activeTab, setActiveTab] = useState("LLM");

    useEffect(() => {
        fetchApiKeys();
    }, [fetchApiKeys]);

    const handleSelectAll = (checked: boolean, keys: ApiKey[]) => {
        if (checked) {
            setSelectedKeys(new Set(keys.map(k => k.id)));
        } else {
            setSelectedKeys(new Set());
        }
    };

    const handleSelectOne = (checked: boolean, id: number) => {
        const newSelected = new Set(selectedKeys);
        if (checked) {
            newSelected.add(id);
        } else {
            newSelected.delete(id);
        }
        setSelectedKeys(newSelected);
    };

    const handleBulkDelete = async () => {
        if (!confirm(`Are you sure you want to delete ${selectedKeys.size} keys?`)) return;

        // Sequential delete for now, or Promise.all
        // Store doesn't support bulk, so loop
        for (const id of Array.from(selectedKeys)) {
            await deleteApiKey(id);
        }
        setSelectedKeys(new Set());
    };

    const handleOpenCreate = () => {
        setDialogMode('create');
        setSelectedKeyData(undefined);
        setDialogOpen(true);
    };

    const handleOpenEdit = (key: ApiKey) => {
        setDialogMode('edit');
        setSelectedKeyData(key);
        setDialogOpen(true);
    };

    const handleOpenView = (key: ApiKey) => {
        setDialogMode('view');
        setSelectedKeyData(key);
        setDialogOpen(true);
    };

    const handleSubmit = async (data: any) => {
        if (dialogMode === 'create') {
            await createApiKey(data);
        } else if (dialogMode === 'edit' && selectedKeyData) {
            await updateApiKey(selectedKeyData.id, data);
        }
    };

    const getProviderBadgeColor = (provider: string) => {
        const p = provider.toLowerCase();
        if (p.includes("openai")) return "bg-green-100 text-green-800 border-green-200 hover:bg-green-100";
        if (p.includes("anthropic")) return "bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-100";
        if (p.includes("google")) return "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100";
        if (p.includes("ollama")) return "bg-zinc-100 text-zinc-800 border-zinc-200 hover:bg-zinc-100";
        return "bg-secondary text-secondary-foreground hover:bg-secondary/80";
    };

    const renderTable = (keys: ApiKey[], type: "LLM" | "MCP") => {
        const allSelected = keys.length > 0 && keys.every(k => selectedKeys.has(k.id));

        return (
            <div className="rounded-md border bg-card">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[50px]">
                                <Checkbox
                                    checked={allSelected}
                                    onCheckedChange={(checked) => handleSelectAll(checked as boolean, keys)}
                                />
                            </TableHead>
                            <TableHead className="w-[25%]">Name</TableHead>
                            {type === "LLM" && <TableHead className="w-[20%]">Provider</TableHead>}
                            {type === "MCP" && <TableHead className="w-[30%]">Endpoint</TableHead>}
                            <TableHead className="w-[25%]">Created At</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {keys.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-[300px] text-center">
                                    <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                                        <div className="h-12 w-12 rounded-full bg-muted/50 flex items-center justify-center mb-2">
                                            {type === "LLM" ? <ShieldAlert className="h-6 w-6" /> : <KeyRound className="h-6 w-6" />}
                                        </div>
                                        <h3 className="text-lg font-semibold text-foreground">No {type} Keys Found</h3>
                                        <p className="text-sm max-w-[250px] mb-4">
                                            {type === "LLM"
                                                ? "Connect AI providers like OpenAI or Anthropic to start analyzing."
                                                : "Register MCP tools to extend capabilities."}
                                        </p>
                                        <Button variant="outline" onClick={handleOpenCreate}>
                                            <Plus className="mr-2 h-4 w-4" />
                                            Add First Key
                                        </Button>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            keys.map((key) => (
                                <TableRow key={key.id}>
                                    <TableCell>
                                        <Checkbox
                                            checked={selectedKeys.has(key.id)}
                                            onCheckedChange={(checked) => handleSelectOne(checked as boolean, key.id)}
                                        />
                                    </TableCell>
                                    <TableCell className="font-medium cursor-pointer hover:underline" onClick={() => handleOpenView(key)}>
                                        {key.name}
                                    </TableCell>
                                    {type === "LLM" && (
                                        <TableCell>
                                            <Badge variant="outline" className={`font-normal capitalize border ${getProviderBadgeColor(key.provider)}`}>
                                                {key.provider}
                                            </Badge>
                                        </TableCell>
                                    )}
                                    {type === "MCP" && (
                                        <TableCell>
                                            <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm">
                                                {key.api_base}
                                            </code>
                                        </TableCell>
                                    )}
                                    <TableCell className="text-muted-foreground text-sm">
                                        {new Date(key.created_at).toLocaleDateString()}
                                    </TableCell>
                                    <TableCell className="text-right flex justify-end gap-2">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleOpenEdit(key)}
                                        >
                                            <Edit2 className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={async () => {
                                                if (confirm("Delete this key?")) await deleteApiKey(key.id);
                                            }}
                                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        );
    };

    const llmKeys = apiKeys.filter(k => (k.category || "LLM") === "LLM");
    const mcpKeys = apiKeys.filter(k => k.category === "MCP");

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-primary">Global API Keys</h2>
                    <p className="text-muted-foreground">
                        Manage your API keys for LLMs and MCP tools.
                    </p>
                </div>
                <div className="flex gap-2">
                    {selectedKeys.size > 0 && (
                        <Button variant="destructive" onClick={handleBulkDelete}>
                            Delete Selected ({selectedKeys.size})
                        </Button>
                    )}
                    <Button className="gap-2" onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4" />
                        Add API Key
                    </Button>
                </div>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="LLM">LLM Keys ({llmKeys.length})</TabsTrigger>
                    <TabsTrigger value="MCP">MCP Keys ({mcpKeys.length})</TabsTrigger>
                </TabsList>
                <TabsContent value="LLM">
                    {renderTable(llmKeys, "LLM")}
                </TabsContent>
                <TabsContent value="MCP">
                    {renderTable(mcpKeys, "MCP")}
                </TabsContent>
            </Tabs>

            <ApiKeyDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                mode={dialogMode}
                defaultCategory={activeTab}
                initialData={selectedKeyData ? {
                    ...selectedKeyData,
                    category: selectedKeyData.category || "LLM"
                } : undefined}
                onSubmit={handleSubmit}
            />
        </div>
    );
}
