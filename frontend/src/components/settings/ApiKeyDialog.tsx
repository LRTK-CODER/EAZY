import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import type { ApiKeyCreateRequest } from "@/types/llm";
import { Eye, EyeOff } from "lucide-react";

interface ApiKeyDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    mode: 'create' | 'edit' | 'view';
    defaultCategory?: string;
    initialData?: {
        id?: number;
        name: string;
        provider: string;
        category: string;
        api_base?: string;
    };
    onSubmit: (data: ApiKeyCreateRequest) => Promise<void>;
}

export function ApiKeyDialog({ open, onOpenChange, mode, defaultCategory = "LLM", initialData, onSubmit }: ApiKeyDialogProps) {
    const [name, setName] = useState("");
    const [provider, setProvider] = useState("openai");
    const [endpoint, setEndpoint] = useState("");
    const [key, setKey] = useState("");
    const [category, setCategory] = useState("LLM");
    const [isLoading, setIsLoading] = useState(false);
    const [showKey, setShowKey] = useState(false);

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (open) {
            setError(null);
            setShowKey(false);
            if (mode === 'create') {
                setName("");
                setProvider(defaultCategory === "MCP" ? "mcp-server" : "openai");
                setEndpoint("");
                setKey("");
                setCategory(defaultCategory); // Use active tab as default
            } else if (initialData) {
                setName(initialData.name);
                setProvider(initialData.provider);
                setEndpoint(initialData.api_base || "");
                setKey("");
                setCategory(initialData.category || "LLM");
            }
        }
    }, [open, mode, initialData, defaultCategory]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            await onSubmit({
                name,
                provider: category === "MCP" ? "mcp" : provider,
                key: key,
                category,
                api_base: category === "MCP" ? endpoint : undefined,
            });
            onOpenChange(false);
        } catch (err: any) {
            console.error(err);
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError("Failed to save API Key. Please try again.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const isView = mode === 'view';

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>
                            {mode === 'create' ? "Add New API Key" : mode === 'edit' ? "Edit API Key" : "API Key Details"}
                        </DialogTitle>
                        <DialogDescription>
                            {mode === 'view' ? "View API Key details." : "Configure your API connection settings."}
                        </DialogDescription>
                    </DialogHeader>

                    {error && (
                        <div className="mt-4 bg-destructive/15 text-destructive text-sm p-3 rounded-md">
                            {error}
                        </div>
                    )}

                    <div className="grid gap-6 py-4">
                        {/* Category & Name Row */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="category">Category</Label>
                                <Select
                                    value={category}
                                    onValueChange={(val) => {
                                        setCategory(val);
                                        if (val === "MCP") setProvider("mcp-server");
                                        else setProvider("openai");
                                    }}
                                    disabled={mode !== 'create'}
                                >
                                    <SelectTrigger id="category" disabled={mode !== 'create'} className="bg-white">
                                        <SelectValue placeholder="Select Category" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="LLM">LLM Provider</SelectItem>
                                        <SelectItem value="MCP">MCP Tool</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="name">Friendly Name</Label>
                                <Input
                                    id="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="e.g. My GPT-4 Project"
                                    disabled={isView}
                                    required
                                    autoFocus={mode === 'create'}
                                    className="bg-white"
                                />
                            </div>
                        </div>

                        {/* Provider Selection (LLM Only) */}
                        {category === "LLM" && (
                            <div className="grid gap-2">
                                <Label htmlFor="provider">Provider</Label>
                                <Select
                                    value={provider}
                                    onValueChange={setProvider}
                                    disabled={isView}
                                >
                                    <SelectTrigger id="provider" className="bg-white">
                                        <SelectValue placeholder="Select Provider" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="openai">OpenAI</SelectItem>
                                        <SelectItem value="anthropic">Anthropic</SelectItem>
                                        <SelectItem value="google">Google Gemini</SelectItem>
                                        <SelectItem value="ollama">Ollama</SelectItem>
                                        <SelectItem value="other">Other</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {/* Endpoint (MCP Only) */}
                        {category === "MCP" && (
                            <div className="grid gap-2">
                                <Label htmlFor="endpoint">Server Endpoint</Label>
                                <Input
                                    id="endpoint"
                                    type="url"
                                    value={endpoint}
                                    onChange={(e) => setEndpoint(e.target.value)}
                                    placeholder="http://localhost:8000/sse"
                                    disabled={isView}
                                    required
                                    className="bg-white"
                                />
                                <p className="text-[0.8rem] text-muted-foreground">
                                    The full URL to your MCP server's SSE endpoint.
                                </p>
                            </div>
                        )}

                        {/* API Key */}
                        {!isView && (
                            <div className="grid gap-2">
                                <Label htmlFor="key">Secret Key</Label>
                                <div className="relative">
                                    <Input
                                        id="key"
                                        type={showKey ? "text" : "password"}
                                        value={key}
                                        onChange={(e) => setKey(e.target.value)}
                                        placeholder={mode === 'edit' ? "(Leave blank to keep unchanged)" : (category === "MCP" ? "Optional Token" : "sk-...")}
                                        className="pr-10 bg-white"
                                        required={mode === 'create' && category === 'LLM'}
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                        onClick={() => setShowKey(!showKey)}
                                    >
                                        {showKey ? (
                                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                                        ) : (
                                            <Eye className="h-4 w-4 text-muted-foreground" />
                                        )}
                                    </Button>
                                </div>
                                {category === "LLM" && (
                                    <p className="text-[0.8rem] text-muted-foreground">
                                        Your key is encrypted and stored securely.
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                    {!isView && (
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading ? "Saving..." : "Save API Key"}
                            </Button>
                        </DialogFooter>
                    )}
                </form>
            </DialogContent>
        </Dialog>
    );
}
