
import { useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useProjectStore } from "@/store/projectStore";
import { CreateTargetDialog } from "@/components/target/CreateTargetDialog";
import { EditTargetDialog } from "@/components/target/EditTargetDialog";
import { EditLLMDialog } from "@/components/project/EditLLMDialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Trash2, ArrowRight } from "lucide-react";

export default function ProjectDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const projectId = Number(id);
    const { targets, fetchTargets, projects, fetchProjects, isLoading, deleteTarget } = useProjectStore();

    const project = projects.find((p) => p.id === projectId);

    useEffect(() => {
        if (!project) {
            fetchProjects();
        }
        if (projectId) {
            fetchTargets(projectId);
        }
    }, [projectId, fetchTargets, project, fetchProjects]);

    const handleDeleteTarget = async (targetId: number) => {
        if (confirm("Are you sure you want to delete this target?")) {
            await deleteTarget(projectId, targetId);
        }
    };


    if (isLoading && !project) return <div>Loading...</div>;
    if (!project && !isLoading && projects.length > 0) return <div>Project not found</div>;

    return (
        <div className="container mx-auto py-10">
            <Button variant="ghost" onClick={() => navigate("/")} className="mb-4">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to Projects
            </Button>

            {project && (
                <div className="mb-8 flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold">{project.name}</h1>
                        <p className="text-gray-500">{project.description}</p>
                    </div>
                    <EditLLMDialog projectId={projectId} />
                </div>
            )}

            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">Scan Targets</h2>
                <CreateTargetDialog projectId={projectId} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {targets.map((target) => (
                    <Card key={target.id} className="flex flex-col justify-between hover:border-blue-500 transition-colors cursor-default">
                        <div>
                            <CardHeader>
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <CardTitle>{target.name}</CardTitle>
                                        <CardDescription>{target.url}</CardDescription>
                                    </div>
                                    <Button variant="ghost" size="icon" onClick={() => navigate(`/projects/${projectId}/targets/${target.id}`)}>
                                        <ArrowRight className="h-4 w-4 text-gray-400" />
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-gray-400">
                                    Added: {new Date(target.created_at).toLocaleDateString()}
                                </p>
                            </CardContent>
                        </div>
                        <CardFooter className="flex justify-end gap-2 bg-gray-50/50 p-4">
                            <Link to={`/projects/${projectId}/targets/${target.id}`} className="flex-1">
                                <Button variant="outline" size="sm" className="w-full">
                                    View Details
                                </Button>
                            </Link>
                            <EditTargetDialog target={target} />
                            <Button
                                variant="destructive"
                                size="icon"
                                className="h-9 w-9"
                                onClick={() => handleDeleteTarget(target.id)}
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
                {targets.length === 0 && !isLoading && (
                    <div className="col-span-full text-center text-gray-500 py-10 border-2 border-dashed rounded-lg">
                        No targets added yet.
                    </div>
                )}
            </div>
        </div>
    );
}
