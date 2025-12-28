import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

interface MainLayoutProps {
    children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex min-h-screen flex-col">
            <Header />
            <div className="container flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] md:gap-6 md:pt-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-10">
                <Sidebar />
                <main className="relative flex w-full flex-col overflow-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
}
