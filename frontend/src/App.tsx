import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import './App.css';

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Dashboard Routes */}
          <Route path="/dashboard" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
              <p className="text-muted-foreground">Welcome to EAZY DAST</p>
            </div>
          } />
          <Route path="/dashboard/analytics" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Analytics</h1>
              <p className="text-muted-foreground">View analytics and metrics</p>
            </div>
          } />
          <Route path="/dashboard/activity" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Activity</h1>
              <p className="text-muted-foreground">Recent activity logs</p>
            </div>
          } />

          {/* Projects Routes */}
          <Route path="/projects" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Projects</h1>
              <p className="text-muted-foreground">Select a project from the sidebar</p>
            </div>
          } />
          <Route path="/projects/archived" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Archived Projects</h1>
              <p className="text-muted-foreground">No archived projects</p>
            </div>
          } />
          <Route path="/projects/:id" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Project Details</h1>
              <p className="text-muted-foreground">Project details page</p>
            </div>
          } />

          {/* Settings Routes */}
          <Route path="/settings" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">General Settings</h1>
              <p className="text-muted-foreground">Configure general settings</p>
            </div>
          } />
          <Route path="/settings/security" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">Security Settings</h1>
              <p className="text-muted-foreground">Configure security options</p>
            </div>
          } />
          <Route path="/settings/api-keys" element={
            <div>
              <h1 className="text-3xl font-bold mb-4">API Keys</h1>
              <p className="text-muted-foreground">Manage API keys</p>
            </div>
          } />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
