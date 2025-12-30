import { useState } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

interface MainLayoutProps {
    children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="h-screen grid grid-rows-[auto_1fr] md:grid-cols-[250px_1fr]">
            {/* Header - 전체 너비 */}
            <div className="md:col-span-2">
                <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
            </div>

            {/* Sidebar - 모바일에서는 오버레이, 데스크톱에서는 그리드 영역 */}
            <div
                className={`
                    fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 md:relative md:translate-x-0
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                `}
            >
                <Sidebar />
            </div>

            {/* 모바일 오버레이 배경 */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main Content */}
            <main className="bg-background overflow-auto p-4 md:p-6">
                {children}
            </main>
        </div>
    );
}
