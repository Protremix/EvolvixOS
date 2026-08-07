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

### 6.3.2 Zustand Agent Store Implementation
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

## 6.5 COMPONENT HIERARCHY & ATOMIC DESIGN

```
+-----------------------------------------------------------------------------------+
|                            COMPONENT HIERARCHY TREE                               |
+-----------------------------------------------------------------------------------+
[RootLayout]
  └── [ThemeProvider] (Enforces Cyberpunk Theme: #0a0d12 bg, #00ff88 accent)
        └── [QueryClientProvider]
              └── [DashboardLayout]
                    ├── [TopNavigationBar]
                    │     ├── [BreadcrumbNav]
                    │     ├── [AgentGlobalStatusPill] (#00ff88 Glow)
                    │     └── [UserProfileDropdown]
                    ├── [WorkspaceSidebar]
                    │     ├── [ProjectSelector]
                    │     └── [NavigationMenu]
                    └── [MainContentArea]
                          ├── [ProjectHeaderCard]
                          ├── [MonacoDiffViewer] (Lazy Loaded)
                          └── [AgentTerminalPanel]
                                ├── [TerminalHeaderBar] (Clear, Copy, Pause Controls)
                                ├── [VirtualizedLogStream] (TanStack Virtual)
                                └── [AgentThoughtCard] (ReAct Inspector)
```

---

## 6.6 AUTHENTICATION FLOW & PROTECTED ROUTES

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

## 6.7 ERROR BOUNDARIES & FALLBACK UI

AegisOS places React Error Boundaries around complex real-time widgets (such as Monaco Code Editor and React Flow DAG Canvas) to ensure an agent stream error does not crash the entire application dashboard.

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

## 6.8 PERFORMANCE OPTIMIZATION & LAZY LOADING

Heavy interactive modules are dynamic-imported with server-side rendering disabled to minimize initial JS bundle sizes:

```typescript
// app/(dashboard)/projects/[id]/code/page.tsx
'use client';

import dynamic from 'next/dynamic';

const MonacoDiffViewer = dynamic(
  () => import('@/components/code/MonacoDiffViewer'),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 w-full bg-[#121820] animate-pulse rounded-lg flex items-center justify-center text-[#00ff88]">
        Loading Aegis Code Diff Engine...
      </div>
    ),
  }
);

const WorkflowCanvas = dynamic(
  () => import('@/components/workflow/WorkflowCanvas'),
  { ssr: false }
);
```

---

## 6.9 THEME PROVIDER & TAILWIND CONFIGURATION

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aegis: {
          accent: '#00ff88',
          'accent-hover': '#00cc6d',
          bg: '#0a0d12',
          surface: '#121820',
          border: '#1f2937',
          text: '#f3f4f6',
          muted: '#9ca3af',
        },
      },
      boxShadow: {
        neon: '0 0 15px rgba(0, 255, 136, 0.25)',
        'neon-strong': '0 0 25px rgba(0, 255, 136, 0.5)',
      },
    },
  },
  plugins: [],
};
```

---

## 6.10 PROGRESSIVE WEB APP (PWA) SPECIFICATION

AegisOS includes PWA support to deliver desktop-like native capabilities, background push alerts when an autonomous agent requests human approval, and offline project caching.

```json
{
  "name": "AegisOS Autonomous AI Engineering Platform",
  "short_name": "AegisOS",
  "start_url": "/dashboard",
  "display": "standalone",
  "background_color": "#0a0d12",
  "theme_color": "#00ff88",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

