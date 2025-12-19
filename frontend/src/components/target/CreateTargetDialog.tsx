import { useState } from "react";
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

interface CreateTargetDialogProps {
    projectId: number;
}

export function CreateTargetDialog({ projectId }: CreateTargetDialogProps) {
    const [open, setOpen] = useState(false);
    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const createTarget = useProjectStore((state) => state.createTarget);
    const isLoading = useProjectStore((state) => state.isLoading);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createTarget(projectId, { name, url });
            setOpen(false);
            setName("");
            setUrl("");
        } catch (error) {
            console.error("Failed to create target", error);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button>Add Target</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Add Scan Target</DialogTitle>
                        <DialogDescription>
                            Add a new URL target to scan.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="name" className="text-right">
                                Name
                            </Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="col-span-3"
                                required
                            />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="url" className="text-right">
                                URL
                            </Label>
                            <Input
                                id="url"
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="col-span-3"
                                required
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? "Adding..." : "Add"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
