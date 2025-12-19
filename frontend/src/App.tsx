import { Routes, Route } from "react-router-dom";
import ProjectList from "@/pages/ProjectList";
import ProjectDetail from "@/pages/ProjectDetail";

function App() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased text-foreground">
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
      </Routes>
    </div>
  );
}

export default App;
