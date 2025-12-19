import { useState, useEffect } from "react";
import { useProjectStore } from "@/store/projectStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
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
import { Settings } from "lucide-react";
import { ManageApiKeysDialog } from "./ManageApiKeysDialog";

interface EditLLMDialogProps {
    projectId: number;
}

export function EditLLMDialog({ projectId }: EditLLMDialogProps) {
    const [open, setOpen] = useState(false);
    const [selectedKeyId, setSelectedKeyId] = useState<string>("");
    const [modelName, setModelName] = useState("gpt-4o");

    const { currentLLMConfig, fetchLLMConfig, upsertLLMConfig, fetchApiKeys, apiKeys, isLoading } = useProjectStore();

    useEffect(() => {
        if (open) {
            fetchLLMConfig(projectId);
            fetchApiKeys();
        }
    }, [open, projectId, fetchLLMConfig, fetchApiKeys]);

    useEffect(() => {
        if (currentLLMConfig) {
            setSelectedKeyId(currentLLMConfig.api_key_id.toString());
            setModelName(currentLLMConfig.model_name);
        } else {
            setSelectedKeyId("");
            setModelName("gpt-4o");
        }
    }, [currentLLMConfig]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedKeyId) return;

        try {
            await upsertLLMConfig(projectId, {
                api_key_id: parseInt(selectedKeyId),
                model_name: modelName,
            });
            setOpen(false);
        } catch (error) {
            console.error("Failed to save settings", error);
        }
    };

    const selectedKey = apiKeys.find(k => k.id.toString() === selectedKeyId);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                    <Settings className="h-4 w-4" />
                    LLM Settings
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>LLM Configuration</DialogTitle>
                        <DialogDescription>
                            Select an API Key to use for this project.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        {/* API Key Selection */}
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="apiKey" className="text-right">
                                API Key
                            </Label>
                            <div className="col-span-3 flex gap-2">
                                <Select value={selectedKeyId} onValueChange={setSelectedKeyId}>
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="Select a key" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {apiKeys.map((k) => (
                                            <SelectItem key={k.id} value={k.id.toString()}>
                                                {k.name} ({k.provider})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <ManageApiKeysDialog />
                            </div>
                        </div>

                        {/* Provider Display */}
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right text-gray-500">
                                Provider
                            </Label>
                            <div className="col-span-3 text-sm font-medium">
                                {selectedKey?.provider || "-"}
                            </div>
                        </div>

                        {/* Model Configuration */}
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="model" className="text-right">
                                Model
                            </Label>
                            <Input
                                id="model"
                                value={modelName}
                                onChange={(e) => setModelName(e.target.value)}
                                className="col-span-3"
                                required
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={isLoading || !selectedKeyId}>
                            {isLoading ? "Saving..." : "Save Configuration"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
