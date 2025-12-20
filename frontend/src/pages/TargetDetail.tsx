
import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjectStore } from "@/store/projectStore";
// import { CreateTargetDialog } from "@/components/target/CreateTargetDialog";
import { EditTargetDialog } from "@/components/target/EditTargetDialog";
// import { EditLLMDialog } from "@/components/project/EditLLMDialog";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PassiveScanControl } from "@/components/proxy/PassiveScanControl";
import { PacketFeed } from "@/components/proxy/PacketFeed";
import { Badge } from "@/components/ui/badge";

export default function TargetDetail() {
    const { projectId, targetId } = useParams<{ projectId: string, targetId: string }>();
    const navigate = useNavigate();
    const pid = Number(projectId);
    const tid = Number(targetId);

    // We reuse ProjectStore for now, assuming it loads targets
    const { targets, fetchTargets, projects, fetchProjects, isLoading, deleteTarget } = useProjectStore();

    const target = targets.find((t) => t.id === tid);
    const project = projects.find((p) => p.id === pid);

    useEffect(() => {
        if (!project) fetchProjects();
        if (pid) fetchTargets(pid);
    }, [pid, fetchTargets, project, fetchProjects]);

    if (isLoading && !target) return <div>Loading...</div>;
    if (!target && !isLoading && targets.length > 0) return <div>Target not found</div>;

    const handleDeleteTarget = async () => {
        if (confirm("Are you sure you want to delete this target?")) {
            await deleteTarget(pid, tid);
            navigate(`/projects/${pid}`);
        }
    };

    return (
        <div className="container mx-auto py-10">
            <Button variant="ghost" onClick={() => navigate(`/projects/${pid}`)} className="mb-4">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to Project
            </Button>

            {target && (
                <div className="mb-8 flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold">{target.name}</h1>
                            <Badge variant="outline">Target</Badge>
                        </div>
                        <a href={target.url} target="_blank" rel="noreferrer" className="text-blue-500 flex items-center gap-1 hover:underline mt-1">
                            {target.url} <ExternalLink className="h-3 w-3" />
                        </a>
                        <p className="text-gray-500 text-sm mt-2">
                            Project: <span className="font-medium text-gray-700">{project?.name}</span>
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <EditTargetDialog target={target} />
                        <Button variant="destructive" onClick={handleDeleteTarget}>Delete Target</Button>
                    </div>
                </div>
            )}

            <Tabs defaultValue="dashboard" className="w-full">
                <TabsList className="mb-4 grid w-full grid-cols-4 lg:w-[600px]">
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                    <TabsTrigger value="active">Active Scan</TabsTrigger>
                    <TabsTrigger value="passive">Passive Scan</TabsTrigger>
                    <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>

                <TabsContent value="dashboard">
                    <div className="p-10 border-2 border-dashed rounded-lg text-center text-gray-400">
                        <h3 className="text-lg font-semibold mb-2">Target Dashboard</h3>
                        <p>Scan Summary and Vulnerability Stats will appear here.</p>
                    </div>
                </TabsContent>

                <TabsContent value="active">
                    <div className="p-10 border-2 border-dashed rounded-lg text-center text-gray-400">
                        <h3 className="text-lg font-semibold mb-2">Active Crawler</h3>
                        <p>Active crawling controls and results will be implemented here (REQ-2-3-2).</p>
                    </div>
                </TabsContent>

                <TabsContent value="passive">
                    <div className="space-y-6">
                        <PassiveScanControl />
                        <PacketFeed />
                    </div>
                </TabsContent>

                <TabsContent value="settings">
                    <div className="p-10 border rounded-lg bg-gray-50">
                        <h3 className="text-lg font-semibold mb-4">Target Settings</h3>
                        <p className="text-sm text-gray-500 mb-4">Manage target configuration.</p>
                        <div className="flex gap-4">
                            {target && <EditTargetDialog target={target} />}
                            <Button variant="destructive" onClick={handleDeleteTarget}>Delete Target</Button>
                        </div>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
