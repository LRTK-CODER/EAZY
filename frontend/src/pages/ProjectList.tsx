import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useProjectStore } from "@/store/projectStore";
import { CreateProjectDialog } from "@/components/project/CreateProjectDialog";
import { EditProjectDialog } from "@/components/project/EditProjectDialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

export default function ProjectList() {
    const { projects, fetchProjects, isLoading, deleteProject } = useProjectStore();
    const navigate = useNavigate();

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        if (confirm("Are you sure you want to delete this project?")) {
            await deleteProject(id);
        }
    };

    return (
        <div className="container mx-auto py-10">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Projects</h1>
                <CreateProjectDialog />
            </div>

            {isLoading && projects.length === 0 ? (
                <div>Loading...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map((project) => (
                        <Card
                            key={project.id}
                            className="cursor-pointer hover:shadow-lg transition-shadow flex flex-col justify-between"
                            onClick={() => navigate(`/projects/${project.id}`)}
                        >
                            <div>
                                <CardHeader>
                                    <CardTitle>{project.name}</CardTitle>
                                    <CardDescription>
                                        Created at: {new Date(project.created_at).toLocaleDateString()}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-gray-500">
                                        {project.description || "No description provided."}
                                    </p>
                                </CardContent>
                            </div>
                            <CardFooter className="flex justify-end gap-2">
                                <EditProjectDialog project={project} />
                                <Button
                                    variant="destructive"
                                    size="icon"
                                    onClick={(e) => handleDelete(e, project.id)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
