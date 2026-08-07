import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, FolderGit2, CheckSquare, Settings, LogOut,
  Bot, GitBranch, Server, Boxes, Shield, Activity, Zap,
  Cpu, Brain, Network, Users, Terminal,
  ChevronDown, ChevronRight, Search, Eye,
  Star, BookOpen, Globe, Bell,
  TrendingUp, Code2, FileCode, Wallet,
  AlertTriangle, Gauge, Webhook, Plug,
  HardDrive, Database, Leaf, Link2
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import WSIndicator from './WSIndicator';

const NavSection = ({ title, items, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-1.5 text-xs font-medium text-gray-600 uppercase tracking-wider hover:text-gray-400 transition-colors"
      >
        <span>{title}</span>
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
      </button>
      {open && (
        <div className="space-y-0.5 mt-1">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-all ${
                  isActive
                    ? 'bg-teal-400/10 text-teal-400 border-l-2 border-teal-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                }`
              }
            >
              {item.icon && <item.icon className="w-4 h-4 flex-shrink-0" />}
              <span className="truncate">{item.name}</span>
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
};

const Sidebar = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navGroups = [
    {
      title: 'Overview',
      defaultOpen: true,
      items: [
        { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
      ]
    },
    {
      title: 'Projects',
      defaultOpen: true,
      items: [
        { name: 'All Projects', path: '/projects', icon: FolderGit2 },
        { name: 'Tasks', path: '/tasks', icon: CheckSquare },
        { name: 'Pipelines', path: '/pipelines', icon: GitBranch },
        { name: 'CodeOps', path: '/codeops', icon: Code2 },
        { name: 'AST Diff', path: '/ast-diff', icon: FileCode },
        { name: 'Dependency Graph', path: '/dependency-graph', icon: Network },
        { name: 'Spec Compiler', path: '/spec-compiler', icon: Terminal },
        { name: 'Project Adapters', path: '/project-adapters', icon: Plug },
      ]
    },
    {
      title: 'AI Swarm',
      defaultOpen: true,
      items: [
        { name: 'AI Agents', path: '/agents', icon: Bot },
        { name: 'Agent Config', path: '/agent-config', icon: Settings },
        { name: 'Agent Learning', path: '/agent-learning', icon: Brain },
        { name: 'Agent Enhancement', path: '/agent-enhancement', icon: Zap },
        { name: 'Collab Monitor', path: '/collab-monitor', icon: Users },
        { name: 'Feedback', path: '/feedback', icon: Star },
        { name: 'Executor Status', path: '/executor', icon: Server },
        { name: 'Activity Log', path: '/activity-log', icon: Activity },
      ]
    },
    {
      title: 'Blockchain',
      defaultOpen: true,
      items: [
        { name: 'Verdis Chain', path: '/verdis', icon: Boxes },
        { name: 'Block Explorer', path: '/block-explorer', icon: Eye },
        { name: 'Validators', path: '/validators', icon: Shield },
        { name: 'Staking', path: '/staking', icon: TrendingUp },
        { name: 'Governance', path: '/governance', icon: Users },
        { name: 'Tokenomics', path: '/tokenomics', icon: Gauge },
        { name: 'Web Wallet', path: '/wallet', icon: Wallet },
        { name: 'EVM Tools', path: '/evm-tools', icon: Code2 },
        { name: 'Smart Contracts', path: '/smart-contracts', icon: FileCode },
        { name: 'NFT Marketplace', path: '/nft-marketplace', icon: Boxes },
        { name: 'Faucet', path: '/faucet', icon: Globe },
        { name: 'Bridge Monitor', path: '/bridge-monitor', icon: Network },
        { name: 'Cross-Chain Analytics', path: '/cross-chain-analytics', icon: TrendingUp },
        { name: 'On-chain Analytics', path: '/onchain-analytics', icon: Activity },
      ]
    },
    {
      title: 'Identity & Security',
      defaultOpen: false,
      items: [
        { name: 'Identity / DID', path: '/identity', icon: Users },
        { name: 'Security Center', path: '/security', icon: Shield },
        { name: 'Security Fixes', path: '/security-fixes', icon: AlertTriangle },
        { name: 'Enhanced Security', path: '/enhanced-security', icon: Shield },
        { name: 'Audit & Compliance', path: '/audit-compliance', icon: CheckSquare },
        { name: 'Production Readiness', path: '/production-readiness', icon: Gauge },
      ]
    },
    {
      title: 'Infrastructure',
      defaultOpen: false,
      items: [
        { name: 'Deployment', path: '/deployment', icon: Server },
        { name: 'Deployment Prep', path: '/deployment-prep', icon: HardDrive },
        { name: 'Deployment Docs', path: '/deployment-docs', icon: BookOpen },
        { name: 'EvolvixOS Infra', path: '/evolvixos-infra', icon: Cpu },
        { name: 'Backups', path: '/backups', icon: Database },
        { name: 'Monitor', path: '/monitor', icon: Activity },
        { name: 'API Gateway', path: '/api-gateway', icon: Network },
        { name: 'Notifications', path: '/notifications', icon: Bell },
        { name: 'Webhooks', path: '/webhooks', icon: Webhook },
      ]
    },
    {
      title: 'Community',
      defaultOpen: false,
      items: [
        { name: 'Community', path: '/community', icon: Users },
        { name: 'Plugin Marketplace', path: '/plugin-marketplace', icon: Boxes },
        { name: 'Feature Pipelines', path: '/feature-pipelines', icon: GitBranch },
        { name: 'Pipeline Templates', path: '/pipeline-templates', icon: Boxes },
        { name: 'Pipeline Analytics', path: '/pipeline-analytics', icon: TrendingUp },
        { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen },
        { name: 'GitHub', path: '/github', icon: GitBranch },
      ]
    },
    {
      title: 'System',
      defaultOpen: false,
      items: [
        { name: 'Settings', path: '/settings', icon: Settings },
        { name: 'System Settings', path: '/system-settings', icon: Cpu },
        { name: 'Mobile Integration', path: '/mobile-integration', icon: Globe },
        { name: 'Verdis Project', path: '/verdis-project', icon: Boxes },
        { name: 'Multi-Project', path: '/multi-project', icon: FolderGit2 },
      ]
    },
  ];

  return (
    <aside className="w-60 bg-[#0a0a0b] border-r border-[#1f1f23] flex flex-col h-screen overflow-hidden flex-shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-[#1f1f23] flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <span className="text-base font-bold tracking-tight text-white">EvolvixOS</span>
      </div>

      {/* Search */}
      <div className="px-3 py-2 border-b border-[#1f1f23] flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600" />
          <input
            type="text"
            placeholder="Search pages..."
            className="w-full bg-[#111113] border border-[#1f1f23] rounded-md pl-8 pr-3 py-1.5 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-teal-400/30"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 scrollable">
        {navGroups.map((group) => (
          <NavSection
            key={group.title}
            title={group.title}
            items={group.items}
            defaultOpen={group.defaultOpen}
          />
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-[#1f1f23] px-3 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <WSIndicator />
            <span className="text-xs text-gray-600 truncate">{user?.email || 'guest'}</span>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-500 hover:text-red-400 transition-colors p-1.5 rounded-md hover:bg-red-500/10 flex-shrink-0"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
