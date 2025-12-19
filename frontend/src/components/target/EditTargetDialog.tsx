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
import type { Target } from "@/types/target";
import { Pencil } from "lucide-react";

interface EditTargetDialogProps {
    target: Target;
}

export function EditTargetDialog({ target }: EditTargetDialogProps) {
    const [open, setOpen] = useState(false);
    const [name, setName] = useState(target.name);
    const [url, setUrl] = useState(target.url);
    const updateTarget = useProjectStore((state) => state.updateTarget);
    const isLoading = useProjectStore((state) => state.isLoading);

    useEffect(() => {
        if (open) {
            setName(target.name);
            setUrl(target.url);
        }
    }, [open, target]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await updateTarget(target.project_id, target.id, { name, url: target.url });
            setOpen(false);
        } catch (error) {
            console.error("Failed to update target", error);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="icon">
                    <Pencil className="h-4 w-4" />
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Edit Target</DialogTitle>
                        <DialogDescription>
                            Update target details.
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
                                disabled
                                className="col-span-3 bg-gray-100 cursor-not-allowed"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? "Saving..." : "Save Changes"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
