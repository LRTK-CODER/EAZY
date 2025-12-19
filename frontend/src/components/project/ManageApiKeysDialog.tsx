import { useState, useEffect } from "react";
import { useProjectStore } from "@/store/projectStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Trash2, Plus, Key } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

export function ManageApiKeysDialog() {
    const [open, setOpen] = useState(false);
    const { apiKeys, fetchApiKeys, createApiKey, deleteApiKey, isLoading } = useProjectStore();

    // Form State
    const [name, setName] = useState("");
    const [provider, setProvider] = useState("openai");
    const [key, setKey] = useState("");
    const [apiBase, setApiBase] = useState("");

    useEffect(() => {
        if (open) {
            fetchApiKeys();
        }
    }, [open, fetchApiKeys]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createApiKey({
                name,
                provider,
                key,
                api_base: apiBase || undefined,
            });
            // Reset form
            setName("");
            setKey("");
            setApiBase("");
            setProvider("openai");
        } catch (error) {
            console.error("Failed to create key", error);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <Key className="h-4 w-4" />
                    Manage Keys
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>Global API Key Management</DialogTitle>
                    <DialogDescription>
                        Manage your API keys for LLM providers. These keys can be reused across projects.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6">
                    {/* Key List */}
                    <div className="border rounded-md">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Provider</TableHead>
                                    <TableHead className="w-[50px]"></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {apiKeys.map((k) => (
                                    <TableRow key={k.id}>
                                        <TableCell className="font-medium">{k.name}</TableCell>
                                        <TableCell>{k.provider}</TableCell>
                                        <TableCell>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => deleteApiKey(k.id)}
                                                className="text-red-500 hover:text-red-700"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {apiKeys.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={3} className="text-center text-gray-500">
                                            No keys found. Add one below.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Add New Key Form */}
                    <form onSubmit={handleSubmit} className="space-y-4 border-t pt-4">
                        <h4 className="text-sm font-medium">Add New Key</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="keyName">Name</Label>
                                <Input
                                    id="keyName"
                                    placeholder="e.g. My OpenAI Key"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="provider">Provider</Label>
                                <Select value={provider} onValueChange={setProvider}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select provider" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="openai">OpenAI</SelectItem>
                                        <SelectItem value="anthropic">Anthropic</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="apiKey">API Key</Label>
                            <Input
                                id="apiKey"
                                type="password"
                                placeholder="sk-..."
                                value={key}
                                onChange={(e) => setKey(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="apiBase">API Base (Optional)</Label>
                            <Input
                                id="apiBase"
                                placeholder="https://api.openai.com/v1"
                                value={apiBase}
                                onChange={(e) => setApiBase(e.target.value)}
                            />
                        </div>
                        <Button type="submit" disabled={isLoading} className="w-full">
                            <Plus className="mr-2 h-4 w-4" /> Add API Key
                        </Button>
                    </form>
                </div>
            </DialogContent>
        </Dialog>
    );
}
