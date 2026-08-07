# 6. FRONTEND ARCHITECTURE

## 6.1 SYSTEM OVERVIEW & UI VISION
The AegisOS Web Client is built on Next.js 14+ (App Router) with TypeScript, React 18+, Tailwind CSS, and Shadcn UI. The application delivers an ultra-responsive, real-time developer environment optimized for monitoring multi-agent code generation, terminal streams, and workflow DAG visualizations.

### 6.1.1 AegisOS Dark Cyberpunk Theme Specification
- **Primary Accent:** Neon Emerald (`#00ff88`) - Used for active states, CTA buttons, active agent execution rings, and success indicators.
- **Background Surface (900):** Dark Space (`#0a0d12`) - Main window and dashboard layout background.
- **Panel Surface (800):** Deep Glass (`#121820`) - Cards, panels, sidebars, and active terminal containers.
- **Subtle Border (700):** Cyber Gray (`#1f2937`) - 1px borders, table dividers, and tree nodes.
- **Foreground Text:** High Contrast White (`#f3f4f6`) and Muted Slate (`#9ca3af`).

---

## 6.2 NEXT.JS APP ROUTER STRUCTURE & LAYOUT HIERARCHY

The directory structure separates server component routing from client hooks, stores, and components.

```
aegis_frontend/
├── app/
│   ├── layout.tsx                # Root Layout (Theme Provider, QueryClientProvider, Font)
│   ├── page.tsx                  # Landing / Root Portal Redirect Page
│   ├── globals.css               # Cyberpunk Theme Variables & Custom Scrollbars
│   ├── (auth)/                   # Unauthenticated Authentication Route Group
│   │   ├── layout.tsx            # Centered Auth Card Layout
│   │   ├── login/page.tsx        # Login Form Component
│   │   └── sso/page.tsx          # OAuth / SAML Callback Handler
│   ├── (dashboard)/              # Authenticated Workspace Layout Group
│   │   ├── layout.tsx            # TopNav + Sidebar + Real-time Socket Connection
│   │   ├── dashboard/page.tsx    # Global Multi-Project & Agent Status Overview
│   │   ├── projects/
│   │   │   ├── page.tsx          # Repository & Project Catalog Grid
│   │   │   └── [id]/
│   │   │       ├── layout.tsx    # Project Context Bar & Tab Navigation
│   │   │       ├── page.tsx      # Project Dashboard & Quick Actions
│   │   │       ├── agents/
│   │   │       │   └── page.tsx  # Agent Execution Terminal & Inspector
│   │   │       ├── workflows/
│   │   │       │   └── page.tsx  # React Flow DAG Workflow Builder
│   │   │       └── code/
│   │   │           └── page.tsx  # Monaco Editor with Real-Time Agent Diff View
│   │   └── settings/
│   │       ├── page.tsx          # User Profile & Security Settings
│   │       └── integrations/page.tsx # GitHub/GitLab OAuth Setup
├── components/
│   ├── ui/                       # Atomic Shadcn UI Components
│   │   ├── button.tsx
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   └── tabs.tsx
│   ├── agent/                    # Agent Domain Components
│   │   ├── AgentTerminal.tsx     # Virtualized Xterm.js / Log Stream Renderer
│   │   ├── AgentStatusBadge.tsx  # Pulsing #00ff88 Status Indicator
│   │   └── AgentThoughtCard.tsx  # ReAct Step Inspector
│   ├── workflow/                 # DAG Canvas Components
│   │   └── WorkflowCanvas.tsx    # Custom React Flow Node Graph
│   └── code/                     # IDE & Diff Components
│       └── MonacoDiffViewer.tsx  # Side-by-Side Agent Code Diff
├── hooks/                        # Custom React Hooks
│   ├── useAgentStream.ts         # SSE / WS Real-Time Token Parser
│   ├── useAuth.ts                # Session & JWT Refresh Manager
│   └── useProjectQuery.ts        # TanStack Query Client Fetchers
├── store/                        # Client-Side State Management (Zustand)
│   ├── useAuthStore.ts           # Token & User Profile State
│   ├── useAgentStore.ts          # Active Agent Log Buffers & Terminal State
│   └── useProjectStore.ts        # Selected Repository State
├── lib/                          # Utility & API Client Configuration
│   ├── api_client.ts             # Axios / Fetch Interceptors with Auto-Token Refresh
│   └── theme_config.ts           # Tailwind Color Extender
└── public/
    ├── manifest.json             # PWA Manifest Configuration
    └── sw.js                     # Service Worker for Offline & Push Notifications
```

---

## 6.3 STATE MANAGEMENT ARCHITECTURE (ZUSTAND JUSTIFICATION)

### 6.3.1 Architectural Selection & Comparison
Evaluating state management solutions for AegisOS:
1. **Redux Toolkit:** Excessive boilerplate and unnecessary re-renders across deep terminal log streams.
2. **Jotai / Recoil:** Excellent atomic state, but lacks consolidated action semantics required for complex agent state transitions.
3. **Zustand (Selected):** Unopinionated, minimal bundle footprint (< 1.2 KB), transient state subscription capabilities (subscribing directly to high-frequency token streams without forcing React DOM re-renders), and clean multi-store separation.

### 6.3.2 Zustand Stores Implementation
```typescript
// store/useAgentStore.ts
import { create } from 'zustand';

export interface AgentThought {
  id: string;
  step: number;
  action: string;
  thought: string;
  timestamp: string;
}

interface AgentState {
  activeAgentId: string | null;
  agentStatus: 'idle' | 'thinking' | 'executing' | 'completed' | 'error';
  thoughts: AgentThought[];
  logs: string[];
  setActiveAgent: (agentId: string) => void;
  appendThought: (thought: AgentThought) => void;
  appendLogChunk: (chunk: string) => void;
  clearTerminal: () => void;
  setStatus: (status: AgentState['agentStatus']) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  activeAgentId: null,
  agentStatus: 'idle',
  thoughts: [],
  logs: [],
  setActiveAgent: (agentId) => set({ activeAgentId: agentId, thoughts: [], logs: [] }),
  appendThought: (thought) => set((state) => ({ thoughts: [...state.thoughts, thought] })),
  appendLogChunk: (chunk) => set((state) => ({ logs: [...state.logs, chunk] })),
  clearTerminal: () => set({ thoughts: [], logs: [] }),
  setStatus: (agentStatus) => set({ agentStatus }),
}));
```

```typescript
// store/useProjectStore.ts
import { create } from 'zustand';

interface ProjectState {
  selectedProjectId: string | null;
  activeBranch: string;
  setSelectedProject: (projectId: string) => void;
  setActiveBranch: (branch: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  selectedProjectId: null,
  activeBranch: 'main',
  setSelectedProject: (projectId) => set({ selectedProjectId: projectId }),
  setActiveBranch: (branch) => set({ activeBranch: branch }),
}));
```

---

## 6.4 DATA FETCHING & REAL-TIME WS STREAMING INTEGRATION

AegisOS employs **TanStack Query (React Query v5)** for asynchronous HTTP REST data fetching, combined with a custom WebSocket manager that pushes updates directly into the Zustand store.

### 6.4.1 Real-Time WebSocket Hook Implementation
```typescript
// hooks/useAgentStream.ts
import { useEffect, useRef } from 'react';
import { useAgentStore } from '@/store/useAgentStore';

export function useAgentStream(agentId: string | null) {
  const socketRef = useRef<WebSocket | null>(null);
  const { appendThought, appendLogChunk, setStatus } = useAgentStore();

  useEffect(() => {
    if (!agentId) return;

    const wsUrl = `wss://api.aegisos.dev/api/v1/ws/agents/${agentId}/stream`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setStatus('thinking');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'thought') {
          appendThought(message.payload);
        } else if (message.type === 'log') {
          appendLogChunk(message.payload.text);
        } else if (message.type === 'status_change') {
          setStatus(message.payload.status);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket agent payload', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus('idle');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [agentId, appendThought, appendLogChunk, setStatus]);

  return { socket: socketRef.current };
}
```

---

## 6.5 ADVANCED CODE VIEWER & DIFFING ENGINE

AegisOS embeds Microsoft Monaco Editor to present side-by-side git diffs produced by autonomous AI agent commits.

```typescript
// components/code/MonacoDiffViewer.tsx
'use client';

import React from 'react';
import { DiffEditor } from '@monaco-editor/react';

interface MonacoDiffViewerProps {
  originalCode: string;
  modifiedCode: string;
  language?: string;
}

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({
  originalCode,
  modifiedCode,
  language = 'typescript',
}) => {
  return (
    <div className="h-full w-full rounded-lg border border-[#1f2937] overflow-hidden bg-[#0a0d12]">
      <DiffEditor
        height="100%"
        language={language}
        original={originalCode}
        modified={modifiedCode}
        theme="vs-dark"
        options={{
          renderSideBySide: true,
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          smoothScrolling: true,
        }}
      />
    </div>
  );
};
```

---

## 6.6 WORKFLOW CANVAS GRAPH ENGINE

To visualize multi-agent execution pipelines, AegisOS uses React Flow to render interactive, animated Directed Acyclic Graphs (DAGs).

```typescript
// components/workflow/WorkflowCanvas.tsx
'use client';

import React, { useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';

const initialNodes = [
  {
    id: 'node-1',
    type: 'default',
    data: { label: 'Architect Agent' },
    position: { x: 100, y: 100 },
    style: { background: '#121820', color: '#00ff88', border: '1px solid #00ff88', borderRadius: '8px' },
  },
  {
    id: 'node-2',
    type: 'default',
    data: { label: 'Developer Agent' },
    position: { x: 350, y: 100 },
    style: { background: '#121820', color: '#f3f4f6', border: '1px solid #1f2937', borderRadius: '8px' },
  },
];

const initialEdges = [
  { id: 'e1-2', source: 'node-1', target: 'node-2', animated: true, style: { stroke: '#00ff88' } },
];

export const WorkflowCanvas: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="h-full w-full bg-[#0a0d12] rounded-lg border border-[#1f2937]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background color="#1f2937" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
```

---

## 6.7 AGENT TERMINAL COMPONENT WITH VIRTUALIZATION

```typescript
// components/agent/AgentTerminal.tsx
'use client';

import React, { useRef, useEffect } from 'react';
import { useAgentStore } from '@/store/useAgentStore';

export const AgentTerminal: React.FC = () => {
  const { logs, agentStatus, clearTerminal } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="flex flex-col h-full bg-[#121820] border border-[#1f2937] rounded-lg overflow-hidden font-mono text-xs text-[#f3f4f6]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#0a0d12] border-b border-[#1f2937]">
        <div className="flex items-center space-x-2">
          <span className={`h-2.5 w-2.5 rounded-full ${agentStatus === 'executing' ? 'bg-[#00ff88] animate-ping' : 'bg-gray-500'}`} />
          <span className="font-bold text-[#00ff88]">AEGIS TERMINAL AGENT STREAM</span>
        </div>
        <button
          onClick={clearTerminal}
          className="px-2 py-1 text-xs bg-[#1f2937] hover:bg-gray-700 text-gray-300 rounded transition-colors"
        >
          Clear
        </button>
      </div>
      <div className="flex-1 p-4 overflow-y-auto space-y-1">
        {logs.map((log, idx) => (
          <div key={idx} className="leading-relaxed">
            <span className="text-[#00ff88] mr-2">&gt;</span>
            <span>{log}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
```

---

## 6.8 AXIOS / FETCH HTTP CLIENT INTERCEPTOR PIPELINE

```typescript
// lib/api_client.ts
import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://api.aegisos.dev/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshResponse = await axios.post('https://api.aegisos.dev/api/v1/auth/refresh');
        const newToken = refreshResponse.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 6.9 AUTHENTICATION FLOW & PROTECTED ROUTES

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('aegis_access_token')?.value;
  const isAuthRoute = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/sso');

  if (!token && !isAuthRoute) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (token && isAuthRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

---

## 6.10 ERROR BOUNDARIES & FALLBACK UI

```typescript
// components/AgentErrorBoundary.tsx
'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AgentErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught agent UI error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-[#121820] border border-red-500/30 rounded-lg text-white">
          <h3 className="text-lg font-bold text-red-400">
            {this.props.fallbackTitle || 'Agent Widget Error'}
          </h3>
          <p className="mt-2 text-sm text-gray-400">
            {this.state.error?.message || 'An unexpected rendering error occurred in this module.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 bg-[#00ff88] text-black font-semibold rounded hover:bg-[#00cc6d] transition-colors"
          >
            Reset Widget
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 6.11 PERFORMANCE OPTIMIZATION & LAZY LOADING STRATEGY

To maintain high rendering framerates during intensive real-time agent output streaming, AegisOS employs specific Next.js dynamic code splitting and component memoization strategies:

1. **Monaco Code Editor & React Flow Canvas:** Heavy interactive dependencies are dynamic-imported with `ssr: false` to keep initial server render payloads small.
2. **Virtualization:** Log output streams rendering thousands of lines utilize `@tanstack/react-virtual` to render only the DOM nodes currently within the user viewport.
3. **Asset Budget:** Initial JavaScript bundle budget is constrained to < 150 KB gzipped for the core application shell.

```typescript
// app/(dashboard)/projects/[id]/code/page.tsx
'use client';

import dynamic from 'next/dynamic';

const MonacoDiffViewer = dynamic(
  () => import('@/components/code/MonacoDiffViewer').then((mod) => mod.MonacoDiffViewer),
  { ssr: false }
);
```

---

## 6.12 SERVICE WORKER & PWA INFRASTRUCTURE

```javascript
// public/sw.js
const CACHE_NAME = 'aegis-v1';
const STATIC_ASSETS = ['/', '/dashboard', '/manifest.json', '/favicon.ico'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/v1/')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
```
