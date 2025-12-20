import { Routes, Route } from "react-router-dom";
import ProjectList from "@/pages/ProjectList";
import ProjectDetail from "@/pages/ProjectDetail";
import TargetDetail from "@/pages/TargetDetail";

import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { ApiKeysPage } from "@/pages/ApiKeysPage";

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/settings/api-keys" element={<ApiKeysPage />} />
        <Route path="/projects/:projectId/targets/:targetId" element={<TargetDetail />} />
      </Route>
    </Routes>
  );
}

export default App;
