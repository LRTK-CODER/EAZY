import { useEffect } from "react";
import { useProjectStore } from "@/store/projectStore";
import { CreateProjectDialog } from "@/components/project/CreateProjectDialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProjectList() {
    const { projects, fetchProjects, isLoading } = useProjectStore();

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

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
                        <Card key={project.id} className="hover:shadow-lg transition-shadow">
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
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
