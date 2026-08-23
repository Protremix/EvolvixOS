import React from 'react';
import Landing from "./pages/Landing";
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import GlobalSearch from './components/GlobalSearch';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Verify from './pages/Verify';
import Dashboard from './pages/Dashboard';
import Webhooks from './pages/Webhooks';
import SystemSettings from './pages/SystemSettings';
import Backups from './pages/Backups';
import VerdisProject from './pages/VerdisProject';
import AgentEnhancement from './pages/AgentEnhancement';
import CollabMonitor from './pages/CollabMonitor';
import AgentLearning from './pages/AgentLearning';
import MultiProject from './pages/MultiProject';
import EVMTools from './pages/EVMTools';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Agents from './pages/Agents';
import AgentDetail from './pages/AgentDetail';
import Pipelines from './pages/Pipelines';
import Feedback from './pages/Feedback';
import WebWallet from './pages/WebWallet';
import Security from './pages/Security';
import ExecutorStatus from './pages/ExecutorStatus';
import Verdis from './pages/Verdis';
import GitHub from './pages/GitHub';
import CodeOps from './pages/CodeOps';
import DependencyGraphPage from './pages/DependencyGraph';
import ASTDiff from './pages/ASTDiff';
import SpecCompilerPage from './pages/SpecCompiler';
import ProjectAdapters from './pages/ProjectAdapters';
import FeaturePipeline from './pages/FeaturePipeline';
import PipelineTemplates from './pages/PipelineTemplates';
import PipelineAnalytics from './pages/PipelineAnalytics';
import KnowledgeBase from './pages/KnowledgeBase';
import AgentConfig from './pages/AgentConfig';
import ActivityLogPage from './pages/ActivityLog';

// Protected Layout with Sidebar
const MainLayout = () => {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-[#0f0f10] scrollable">
        <Outlet />
      </main>
    </div>
  );
};

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify" element={<Verify />} />
      <Route path="/" element={<Landing />} />

      {/* Protected Routes Wrapper */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/settings" element={<Settings />} />
          {/* Phase 6 — Agent Monitoring */}
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/:name" element={<AgentDetail />} />
          <Route path="/pipelines" element={<Pipelines />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/wallet" element={<WebWallet />} />
          <Route path="/security" element={<Security />} />
          <Route path="/executor" element={<ExecutorStatus />} />
          {/* Verdis Integration */}
          <Route path="/verdis" element={<Verdis />} />
          <Route path="/github" element={<GitHub />} />
          <Route path="/code-ops" element={<CodeOps />} />
          <Route path="/dep-graph" element={<DependencyGraphPage />} />
          <Route path="/ast-diff" element={<ASTDiff />} />
          <Route path="/spec-compiler" element={<SpecCompilerPage />} />
          <Route path="/project-adapters" element={<ProjectAdapters />} />
          <Route path="/feature-pipeline" element={<FeaturePipeline />} />
          <Route path="/pipeline-templates" element={<PipelineTemplates />} />
          <Route path="/pipeline-analytics" element={<PipelineAnalytics />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="/agent-config" element={<AgentConfig />} />
          <Route path="/activity-log" element={<ActivityLogPage />} />
          <Route path="/webhooks" element={<Webhooks />} />
          <Route path="/system-settings" element={<SystemSettings />} />
          <Route path="/backups" element={<Backups />} />
          <Route path="/verdis-project" element={<VerdisProject />} />
          <Route path="/agent-enhancement" element={<AgentEnhancement />} />
          <Route path="/collab-monitor" element={<CollabMonitor />} />
          <Route path="/agent-learning" element={<AgentLearning />} />
          <Route path="/multi-project" element={<MultiProject />} />
          <Route path="/evm-tools" element={<EVMTools />} />
        </Route>
      </Route>

      {/* Fallback redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
