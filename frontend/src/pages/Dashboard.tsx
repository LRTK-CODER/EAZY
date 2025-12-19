import { useEffect } from "react";
import { useProjectStore } from "@/store/projectStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderKanban, Target, ShieldAlert } from "lucide-react";

export function Dashboard() {
    const { projects, apiKeys, fetchProjects, fetchApiKeys } = useProjectStore();

    useEffect(() => {
        fetchProjects();
        fetchApiKeys(); // Fetch keys for stats
    }, [fetchProjects, fetchApiKeys]);

    // Stats Calculations
    const projectStats = {
        total: projects.length,
        targets: projects.reduce((acc, p) => acc + (p.targets?.length || 0), 0),
    };

    const apiKeyStats = {
        total: apiKeys.length,
        llm: apiKeys.filter(k => k.category === "LLM").length,
        mcp: apiKeys.filter(k => k.category === "MCP").length,
    };

    return (
        <div className="space-y-8">
            <h2 className="text-3xl font-bold tracking-tight text-primary">Dashboard</h2>

            {/* Project Overview Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground/80">Project Overview</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
                            <FolderKanban className="h-4 w-4 text-primary" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{projectStats.total}</div>
                            <p className="text-xs text-muted-foreground">Active projects</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Targets</CardTitle>
                            <Target className="h-4 w-4 text-primary" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{projectStats.targets}</div>
                            <p className="text-xs text-muted-foreground">Monitored endpoints</p>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* API Key Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground/80">API Key Usage</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total API Keys</CardTitle>
                            {/* Reusing Key icon not imported, will add ShieldAlert or generic Key icon if available, or just text */}
                            <ShieldAlert className="h-4 w-4 text-accent" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{apiKeyStats.total}</div>
                            <p className="text-xs text-muted-foreground">Registered keys</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">LLM Keys</CardTitle>
                            <div className="h-4 w-4 rounded-full bg-primary/20" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{apiKeyStats.llm}</div>
                            <p className="text-xs text-muted-foreground">Language Models</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">MCP Keys</CardTitle>
                            <div className="h-4 w-4 rounded-full bg-accent/20" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{apiKeyStats.mcp}</div>
                            <p className="text-xs text-muted-foreground">MCP Tools</p>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* LAG Data Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground/80">LAG Data Analytics</h3>
                <div className="grid gap-4 md:grid-cols-2">
                    <Card className="col-span-2 border-dashed">
                        <CardHeader>
                            <CardTitle className="text-sm font-medium">LAG Data Visualization</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[150px] flex items-center justify-center text-muted-foreground">
                            No data available yet.
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
