import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  Cpu, Brain, Network, Shield, Zap, GitBranch, Layers,
  Boxes, Activity, ArrowRight, Check, Menu, X,
  Server, Code2, Workflow, Bot, Link2, Leaf, Terminal,
  TrendingUp, Users, Globe, ChevronRight, Sparkles,
  MessageSquare, Send, Loader2, Database, Container,
  Gauge, Github, Mail, ChevronDown
} from "lucide-react";

// Count-up hook
const useCountUp = (end, duration, start) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime = null;
    const step = (ts) => {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [end, duration, start]);
  return count;
};

// Scroll reveal hook
const useScrollReveal = () => {
  const [visible, setVisible] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return { ref, visible };
};

// Animated stat component
const AnimatedStat = ({ value, label, icon: Icon, delay, visible }) => {
  const isNumeric = typeof value === "number";
  const displayValue = isNumeric ? useCountUp(value, 2000, visible) : value;
  return (
    <div
      className="text-center transition-all duration-700"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transitionDelay: `${delay}ms`,
      }}
    >
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-teal-400/10 mb-4 border border-teal-400/10">
        <Icon className="w-6 h-6 text-teal-400" />
      </div>
      <div className="text-3xl font-bold mb-1 text-white tabular-nums">
        {displayValue}
      </div>
      <div className="text-xs text-gray-500 uppercase tracking-wider">{label}</div>
    </div>
  );
};


// Animated particle network background
const AnimatedBackground = () => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;
    let particles = [];
    let mouse = { x: -1000, y: -1000 };
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    
    const PARTICLE_COUNT = Math.min(80, Math.floor(window.innerWidth / 18));
    const MAX_DIST = 140;
    const COLORS = ["#00f5d4", "#14b8a6", "#0d9488", "#06b6d4", "#0891b2"];
    
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 1.5 + 0.5,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: 0.01 + Math.random() * 0.02,
      });
    }
    
    const handleMouse = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    const handleMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };
    
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", handleMouse);
    window.addEventListener("mouseleave", handleMouseLeave);
    
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Animated gradient orbs (blurred blobs)
      const time = Date.now() * 0.0003;
      ctx.save();
      for (let i = 0; i < 3; i++) {
        const orbX = canvas.width * (0.3 + 0.4 * Math.sin(time + i * 2.1));
        const orbY = canvas.height * (0.3 + 0.4 * Math.cos(time + i * 2.1));
        const orbR = 200 + 80 * Math.sin(time * 2 + i);
        const grad = ctx.createRadialGradient(orbX, orbY, 0, orbX, orbY, orbR);
        const colors = [
          ["rgba(0,245,212,0.08)", "rgba(0,245,212,0)"],
          ["rgba(20,184,166,0.06)", "rgba(20,184,166,0)"],
          ["rgba(6,182,212,0.05)", "rgba(6,182,212,0)"],
        ];
        grad.addColorStop(0, colors[i][0]);
        grad.addColorStop(1, colors[i][1]);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
      ctx.restore();
      
      // Grid lines
      ctx.strokeStyle = "rgba(0,245,212,0.03)";
      ctx.lineWidth = 1;
      const gridSize = 60;
      const offset = (time * 30) % gridSize;
      for (let x = -offset; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = -offset; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }
      
      // Particles
      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += p.pulseSpeed;
        
        // Mouse attraction
        const mdx = mouse.x - p.x;
        const mdy = mouse.y - p.y;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 200) {
          p.vx += (mdx / mdist) * 0.02;
          p.vy += (mdy / mdist) * 0.02;
        }
        
        // Bounce off edges
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        
        // Friction
        p.vx *= 0.99;
        p.vy *= 0.99;
        
        // Draw particle with pulse
        const pulseFactor = 0.5 + 0.5 * Math.sin(p.pulse);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * (1 + pulseFactor * 0.5), 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.3 + pulseFactor * 0.4;
        ctx.fill();
        
        // Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
        const glowGrad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
        glowGrad.addColorStop(0, p.color + "20");
        glowGrad.addColorStop(1, p.color + "00");
        ctx.fillStyle = glowGrad;
        ctx.globalAlpha = pulseFactor * 0.5;
        ctx.fill();
        ctx.globalAlpha = 1;
        
        // Connect to nearby particles
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < MAX_DIST) {
            const alpha = (1 - dist / MAX_DIST) * 0.15;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(0,245,212,${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
        
        // Connect to mouse
        if (mdist < 200) {
          const alpha = (1 - mdist / 200) * 0.2;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.strokeStyle = `rgba(0,245,212,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      });
      
      animId = requestAnimationFrame(draw);
    };
    draw();
    
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
      window.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);
  
  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
};

const Landing = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  // Scroll reveal refs
  const statsReveal = useScrollReveal();
  const featuresReveal = useScrollReveal();
  const aiReveal = useScrollReveal();
  const archReveal = useScrollReveal();
  const useCasesReveal = useScrollReveal();
  const blockchainReveal = useScrollReveal();
  const faqReveal = useScrollReveal();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const sendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: "user", content: msg }]);
    try {
      const res = await fetch("/support/api/v1/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, agent_type: "general" }),
      });
      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, agent: data.agent },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, having trouble connecting. Please email support@evolvixos.com", agent: "System" },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const features = [
    { icon: Bot, title: "AI Agent Swarm", desc: "15+ specialized AI agents working in coordination. Code review, security scanning, testing, deployment, monitoring. Each agent has deep domain expertise.", stats: "15 Agents - 24/7 Operation", color: "teal" },
    { icon: Workflow, title: "Pipeline Orchestration", desc: "Visual pipeline builder for CI/CD, feature delivery, and automated codeops. From spec to production in one continuous flow.", stats: "6 Pipeline Types - 12 Templates", color: "cyan" },
    { icon: Link2, title: "Blockchain Management", desc: "Native Verdis blockchain integration. Validator management, DEX operations, carbon credit tracking, governance, and real-time monitoring.", stats: "768+ API Endpoints - DPoS - AMM DEX", color: "emerald" },
    { icon: Shield, title: "Security & Compliance", desc: "Automated security scanning, RBAC, audit logs, GDPR/SOC2 compliance tracking, threat monitoring, and incident response.", stats: "14 Security Controls - 0 Critical", color: "blue" },
    { icon: Brain, title: "Knowledge Engine", desc: "RAG-powered knowledge base that learns from every interaction. Documentation, runbooks, solutions, and institutional memory.", stats: "Self-Learning - Always Current", color: "purple" },
    { icon: Boxes, title: "Multi-Project Management", desc: "Manage multiple projects with isolated environments, shared resources, and cross-project analytics. Built for teams that ship.", stats: "Unlimited Projects - Isolated", color: "amber" },
  ];

  const colorMap = {
    teal: { text: "text-teal-400", bg: "bg-teal-400/10", border: "border-teal-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(20,184,166,0.3)]" },
    cyan: { text: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.3)]" },
    emerald: { text: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(16,185,129,0.3)]" },
    blue: { text: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]" },
    purple: { text: "text-purple-400", bg: "bg-purple-400/10", border: "border-purple-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(168,85,247,0.3)]" },
    amber: { text: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/20", glow: "group-hover:shadow-[0_0_30px_-5px_rgba(251,191,36,0.3)]" },
  };

  const stats = [
    { value: "768+", label: "API Endpoints", icon: Server },
    { value: "55+", label: "Platform Pages", icon: Layers },
    { value: "14", label: "Docker Services", icon: Container },
    { value: "2,073", label: "Passing Tests", icon: Check },
    { value: "121", label: "RPC Methods", icon: Terminal },
    { value: "99.9%", label: "Uptime SLA", icon: Activity },
  ];

  const useCases = [
    { icon: Code2, title: "For Engineers", desc: "Automated code review, AST diffing, dependency graphs, and spec-driven development.", points: ["AST-based diffing", "Dependency graph analysis", "Spec-driven codegen", "Auto code review"] },
    { icon: GitBranch, title: "For DevOps", desc: "One-click deployments, rollback management, health monitoring, and infrastructure as code.", points: ["1-click deploy and rollback", "Health monitoring", "Infrastructure as code", "Backup automation"] },
    { icon: Network, title: "For Blockchain Ops", desc: "Validator management, consensus monitoring, bridge tracking, and on-chain analytics.", points: ["Validator management", "Consensus monitoring", "Bridge tracking", "On-chain analytics"] },
    { icon: Users, title: "For Teams", desc: "Collaboration monitoring, agent feedback, task management, and shared knowledge base.", points: ["Collaboration tracking", "Agent feedback loops", "Task management", "Shared knowledge base"] },
  ];

  const architectureNodes = [
    { name: "Code Agent", icon: Code2, desc: "Code generation and review" },
    { name: "Security Agent", icon: Shield, desc: "Vulnerability scanning" },
    { name: "DevOps Agent", icon: GitBranch, desc: "Deploy and infrastructure" },
    { name: "Knowledge Agent", icon: Brain, desc: "RAG and documentation" },
    { name: "Blockchain Agent", icon: Link2, desc: "Chain ops and monitoring" },
    { name: "Monitor Agent", icon: Activity, desc: "Metrics and alerting" },
    { name: "Executor Agent", icon: Zap, desc: "Task execution" },
    { name: "Coordinator Agent", icon: Cpu, desc: "Agent orchestration" },
  ];

  const faqs = [
    { q: "What is EvolvixOS?", a: "EvolvixOS is the Universal AI Engineering Operating System - a platform that orchestrates AI agents, development pipelines, and blockchain infrastructure into a single autonomous system. Built by Protremix." },
    { q: "How does the AI support work?", a: "We have 5 specialized GPT-4o powered agents: General Support, Technical Support, Blockchain Support, Merchant Support, and Developer Support. They handle live chat, email classification, ticket routing, and knowledge base search - 24/7." },
    { q: "What blockchain does EvolvixOS manage?", a: "EvolvixOS natively integrates with the Verdis blockchain - a carbon-negative Layer-1 with DPoS consensus, 101 validator slots, native AMM DEX, carbon credit tracking, and green validator scoring. 100B total supply." },
    { q: "Is EvolvixOS open source?", a: "EvolvixOS is built by Protremix. The codebase is available on GitHub with full transparency. Contact us for licensing and enterprise options." },
    { q: "What infrastructure does it run on?", a: "EvolvixOS runs on Fedora 44 with 14 Docker containers: frontend, API, worker, PostgreSQL, Redis, Prometheus, Grafana, Loki, the Verdis blockchain node, and the AI customer success platform. Fully backed up with Restic." },
    { q: "How do I get started?", a: "Click Get Started to create an account. You will get access to the dashboard, AI agents, blockchain tools, and the full platform. The 7-step onboarding wizard will configure your profile, organization, and first project." },
  ];

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "Architecture", href: "#architecture" },
    { label: "Use Cases", href: "#usecases" },
    { label: "Blockchain", href: "#blockchain" },
    { label: "FAQ", href: "#faq" },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-gray-100 antialiased overflow-x-hidden">
      <AnimatedBackground />
      <style>{`
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
        @keyframes floatY { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes pulseGlow { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.6; } }
        @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        @keyframes slideInRight { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        @keyframes rotateSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes scrollDown { 0% { opacity: 0; transform: translateY(-8px); } 50% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(8px); } }

        .animate-fade-in-up { animation: fadeInUp 0.8s ease-out forwards; }
        .animate-fade-in { animation: fadeIn 1s ease-out forwards; }
        .animate-float { animation: floatY 6s ease-in-out infinite; }
        .animate-pulse-glow { animation: pulseGlow 4s ease-in-out infinite; }
        .animate-scale-in { animation: scaleIn 0.6s ease-out forwards; }
        .animate-slide-in-right { animation: slideInRight 0.8s ease-out forwards; }
        .animate-rotate-slow { animation: rotateSlow 20s linear infinite; }

        .gradient-text {
          background: linear-gradient(135deg, #fff 0%, #a0a0a0 100%);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .gradient-text-teal {
          background: linear-gradient(135deg, #00f5d4 0%, #14b8a6 100%);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .glass {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
        }
        .glass-strong {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .gradient-border {
          position: relative;
          background: rgba(10, 10, 11, 0.8);
        }
        .gradient-border::before {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: inherit;
          padding: 1px;
          background: linear-gradient(135deg, rgba(0,245,212,0.3), rgba(20,184,166,0.1), rgba(0,0,0,0));
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          pointer-events: none;
        }
        .glow-teal { box-shadow: 0 0 40px -10px rgba(0,245,212,0.3); }
        .glow-teal-hover:hover { box-shadow: 0 0 40px -10px rgba(0,245,212,0.4); }
        .noise-overlay {
          position: absolute;
          inset: 0;
          opacity: 0.015;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' /%3E%3C/svg%3E");
          pointer-events: none;
        }
        .shimmer {
          background: linear-gradient(90deg, transparent, rgba(0,245,212,0.1), transparent);
          background-size: 200% 100%;
          animation: shimmer 3s infinite;
        }
        .section-reveal {
          opacity: 0;
          transform: translateY(30px);
          transition: opacity 0.8s ease-out, transform 0.8s ease-out;
        }
        .section-reveal.revealed {
          opacity: 1;
          transform: translateY(0);
        }
      `}</style>

      {/* NAVIGATION */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? "glass-strong border-b border-white/5" : "bg-transparent"}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center transition-transform group-hover:scale-110">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">EvolvixOS</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} className="text-sm text-gray-400 hover:text-white transition-colors relative group">
                {link.label}
                <span className="absolute -bottom-1 left-0 w-0 h-px bg-teal-400 group-hover:w-full transition-all duration-300"></span>
              </a>
            ))}
          </div>
          <div className="hidden md:flex items-center gap-3">
            <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2">Sign In</Link>
            <Link to="/register" className="text-sm font-medium bg-teal-400 text-[#0a0a0b] px-5 py-2 rounded-lg hover:bg-teal-300 transition-all hover:shadow-[0_0_20px_-5px_rgba(0,245,212,0.5)]">
              Get Started
            </Link>
          </div>
          <button className="md:hidden text-gray-400" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden glass-strong border-b border-white/5 px-6 py-4 space-y-3 animate-fade-in-up">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} className="block text-sm text-gray-400 hover:text-white" onClick={() => setMobileMenuOpen(false)}>{link.label}</a>
            ))}
            <div className="flex gap-3 pt-2">
              <Link to="/login" className="flex-1 text-center text-sm text-gray-400 border border-white/10 rounded-lg py-2">Sign In</Link>
              <Link to="/register" className="flex-1 text-center text-sm font-medium bg-teal-400 text-[#0a0a0b] rounded-lg py-2">Get Started</Link>
            </div>
          </div>
        )}
      </nav>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
        {/* Animated gradient mesh background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-teal-500/10 rounded-full blur-[120px] animate-pulse-glow" style={{ animationDuration: "4s" }}></div>
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-emerald-500/8 rounded-full blur-[100px] animate-pulse-glow" style={{ animationDuration: "6s", animationDelay: "1s" }}></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-cyan-500/5 rounded-full blur-[150px]"></div>
        </div>
        {/* Grid pattern */}
        <div className="absolute inset-0" style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}></div>
        {/* Noise texture */}
        <div className="noise-overlay"></div>

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-400/10 border border-teal-400/20 mb-8 animate-fade-in-up" style={{ animationDelay: "0.1s", opacity: 0 }}>
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            <span className="text-xs font-medium text-teal-300">The Universal AI Engineering Operating System</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 gradient-text animate-fade-in-up" style={{ animationDelay: "0.2s", opacity: 0 }}>
            Engineer at the speed<br />of thought.
          </h1>

          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed animate-fade-in-up" style={{ animationDelay: "0.3s", opacity: 0 }}>
            EvolvixOS orchestrates AI agents, development pipelines, and blockchain infrastructure into a single autonomous platform. From specification to production - without the friction.
          </p>

          <div className="flex items-center justify-center gap-4 mb-16 animate-fade-in-up" style={{ animationDelay: "0.4s", opacity: 0 }}>
            <Link to="/register" className="group inline-flex items-center gap-2 bg-teal-400 text-[#0a0a0b] px-6 py-3 rounded-lg font-medium hover:bg-teal-300 transition-all hover:scale-105 hover:shadow-[0_0_30px_-5px_rgba(0,245,212,0.5)]">
              Start Building
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a href="#features" className="inline-flex items-center gap-2 text-gray-400 hover:text-white px-6 py-3 rounded-lg border border-white/10 hover:border-white/20 transition-all hover:bg-white/5">
              Explore Platform
              <ChevronRight className="w-4 h-4" />
            </a>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs text-gray-600 animate-fade-in" style={{ animationDelay: "0.6s", opacity: 0 }}>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-teal-400"></div> AI Agent Swarm</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-400"></div> Blockchain Native</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-cyan-400"></div> 768+ API Endpoints</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-400"></div> DPoS Consensus</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-purple-400"></div> Carbon Negative</span>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-fade-in" style={{ animationDelay: "1s", opacity: 0 }}>
          <div className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-1.5">
            <div className="w-1 h-2 rounded-full bg-teal-400" style={{ animation: "scrollDown 2s ease-in-out infinite" }}></div>
          </div>
        </div>
      </section>

      {/* STATS BAR */}
      <section ref={statsReveal.ref} className="relative border-y border-white/5 bg-[#0c0c0d] py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
            {stats.map((stat, i) => (
              <div
                key={i}
                className="text-center transition-all duration-700"
                style={{
                  opacity: statsReveal.visible ? 1 : 0,
                  transform: statsReveal.visible ? "translateY(0)" : "translateY(20px)",
                  transitionDelay: `${i * 100}ms`,
                }}
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-teal-400/10 mb-4 border border-teal-400/10 transition-all hover:scale-110 hover:bg-teal-400/20">
                  <stat.icon className="w-6 h-6 text-teal-400" />
                </div>
                <div className="text-3xl font-bold mb-1 text-white tabular-nums">{stat.value}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" ref={featuresReveal.ref} className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-700 ${featuresReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-4">
              <span className="text-xs font-medium text-gray-400">Platform Capabilities</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">Everything your engineering org needs.</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">Six core systems working as one autonomous platform.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => {
              const c = colorMap[feature.color];
              return (
                <div
                  key={i}
                  className={`group relative p-6 rounded-2xl glass border border-white/5 hover:border-white/10 transition-all duration-300 hover:translate-y-[-4px] ${c.glow}`}
                  style={{
                    opacity: featuresReveal.visible ? 1 : 0,
                    transform: featuresReveal.visible ? "translateY(0)" : "translateY(30px)",
                    transition: `opacity 0.6s ease-out ${i * 100}ms, transform 0.6s ease-out ${i * 100}ms, box-shadow 0.3s ease-out, border-color 0.3s ease-out`,
                  }}
                >
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${c.bg} ${c.border} border mb-4 transition-transform group-hover:scale-110`}>
                    <feature.icon className={`w-6 h-6 ${c.text}`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-white">{feature.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed mb-4">{feature.desc}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500 pt-3 border-t border-white/5">
                    <Sparkles className={`w-3 h-3 ${c.text}`} />
                    <span>{feature.stats}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* AI SUPPORT SHOWCASE */}
      <section ref={aiReveal.ref} className="py-24 bg-[#0c0c0d] border-y border-white/5 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[2px] bg-gradient-to-r from-transparent via-teal-400/30 to-transparent"></div>
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className={`transition-all duration-700 ${aiReveal.visible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-8"}`}>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-400/10 border border-teal-400/20 mb-4">
                <MessageSquare className="w-3.5 h-3.5 text-teal-400" />
                <span className="text-xs font-medium text-teal-300">AI Customer Success Platform</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">GPT-4o powered support, live right now.</h2>
              <p className="text-gray-400 mb-6 leading-relaxed">
                Five specialized AI agents handle customer support 24/7 - from blockchain diagnostics to merchant onboarding. Real GPT-4o responses, not canned replies. Try it yourself with the chat widget in the bottom right.
              </p>
              <div className="space-y-3">
                {[
                  { icon: Bot, name: "General Support", desc: "General inquiries, routing, escalation" },
                  { icon: Terminal, name: "Technical Support", desc: "Node, API, SDK, debugging" },
                  { icon: Link2, name: "Blockchain Support", desc: "Validators, consensus, DEX operations" },
                  { icon: Globe, name: "Merchant Support", desc: "Onboarding, payments, settlements" },
                  { icon: Code2, name: "Developer Support", desc: "Smart contracts, webhooks, code" },
                ].map((agent, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg glass border border-white/5 hover:border-teal-400/20 transition-all hover:translate-x-1" style={{ transitionDelay: `${i * 50}ms` }}>
                    <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-teal-400/10 flex items-center justify-center">
                      <agent.icon className="w-4 h-4 text-teal-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{agent.name}</div>
                      <div className="text-xs text-gray-500">{agent.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={() => setChatOpen(true)} className="mt-6 inline-flex items-center gap-2 bg-teal-400 text-[#0a0a0b] px-5 py-2.5 rounded-lg font-medium hover:bg-teal-300 transition-all hover:shadow-[0_0_30px_-5px_rgba(0,245,212,0.5)]">
                <MessageSquare className="w-4 h-4" />
                Try Live Chat
              </button>
            </div>
            <div className={`transition-all duration-700 ${aiReveal.visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8"}`}>
              <div className="rounded-2xl glass-strong border border-white/10 p-6 shadow-2xl glow-teal animate-float">
                <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/5">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">EvolvixOS AI</div>
                    <div className="text-xs text-emerald-400 flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
                      Online - GPT-4o
                    </div>
                  </div>
                </div>
                <div className="space-y-3 mb-4 min-h-[200px] max-h-[300px] overflow-y-auto">
                  <div className="flex justify-start animate-fade-in-up">
                    <div className="max-w-[80%] px-3 py-2 rounded-lg rounded-tl-sm bg-white/5 text-sm text-gray-300">
                      Hi! I am the EvolvixOS AI assistant. How can I help you today?
                    </div>
                  </div>
                  <div className="flex justify-end animate-fade-in-up" style={{ animationDelay: "0.3s", opacity: 0 }}>
                    <div className="max-w-[80%] px-3 py-2 rounded-lg rounded-tr-sm bg-teal-400/10 border border-teal-400/20 text-sm text-teal-200">
                      What blockchain does EvolvixOS manage?
                    </div>
                  </div>
                  <div className="flex justify-start animate-fade-in-up" style={{ animationDelay: "0.6s", opacity: 0 }}>
                    <div className="max-w-[80%] px-3 py-2 rounded-lg rounded-tl-sm bg-white/5 text-sm text-gray-300">
                      EvolvixOS manages the Verdis blockchain - a carbon-negative Layer-1 with DPoS consensus, 101 validator slots, native AMM DEX, and on-chain carbon credit tracking. 100B total supply with green validator scoring.
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 pt-3 border-t border-white/5">
                  <div className="flex-1 px-3 py-2 bg-white/5 rounded-lg text-sm text-gray-500">Ask me anything...</div>
                  <button className="p-2 rounded-lg bg-teal-400 text-[#0a0a0b]"><Send className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE */}
      <section id="architecture" ref={archReveal.ref} className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-700 ${archReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-4">
              <span className="text-xs font-medium text-gray-400">System Architecture</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">A kernel-swarm architecture.</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">The EvolvixOS kernel coordinates specialized AI agents that adapt to any project stack and conventions.</p>
          </div>
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-3 px-6 py-3 rounded-xl bg-teal-400/10 border border-teal-400/20 glow-teal animate-pulse-glow" style={{ animationDuration: "3s" }}>
                <div className="relative">
                  <Cpu className="w-6 h-6 text-teal-400" />
                  <div className="absolute inset-0 bg-teal-400/30 rounded-full blur-md"></div>
                </div>
                <div className="text-left">
                  <div className="font-semibold text-white">EvolvixOS Kernel</div>
                  <div className="text-xs text-gray-500">Dynamic Project Adaptation Engine</div>
                </div>
              </div>
            </div>
            {/* Connection lines */}
            <div className="relative mb-6">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-8 bg-gradient-to-b from-teal-400/30 to-transparent"></div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {architectureNodes.map((node, i) => (
                <div
                  key={i}
                  className="group p-4 rounded-xl glass border border-white/5 hover:border-teal-400/30 transition-all text-center hover:translate-y-[-2px] hover:shadow-[0_0_30px_-5px_rgba(0,245,212,0.2)]"
                  style={{
                    opacity: archReveal.visible ? 1 : 0,
                    transform: archReveal.visible ? "translateY(0) scale(1)" : "translateY(20px) scale(0.95)",
                    transition: `all 0.5s ease-out ${i * 80}ms`,
                  }}
                >
                  <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-teal-400/10 mb-3 group-hover:bg-teal-400/20 transition-colors group-hover:scale-110">
                    <node.icon className="w-5 h-5 text-teal-400" />
                  </div>
                  <div className="text-sm font-medium text-white mb-1">{node.name}</div>
                  <div className="text-xs text-gray-500">{node.desc}</div>
                </div>
              ))}
            </div>
            <div className="mt-8 grid md:grid-cols-3 gap-4">
              {[
                { icon: Container, label: "Infrastructure", value: "Docker - Nginx - SSL" },
                { icon: Database, label: "Data Layer", value: "PostgreSQL - Redis - Loki" },
                { icon: Gauge, label: "Observability", value: "Prometheus - Grafana" },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-4 rounded-xl glass border border-white/5 hover:border-teal-400/20 transition-all" style={{ transitionDelay: `${i * 100}ms` }}>
                  <item.icon className="w-5 h-5 text-teal-400 flex-shrink-0" />
                  <div>
                    <div className="text-xs text-gray-500">{item.label}</div>
                    <div className="text-sm text-gray-300">{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* USE CASES */}
      <section id="usecases" ref={useCasesReveal.ref} className="py-24 bg-[#0c0c0d] border-y border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-700 ${useCasesReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-4">
              <span className="text-xs font-medium text-gray-400">Use Cases</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">Built for every role.</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">Whether you are shipping code, managing infrastructure, or running a blockchain - EvolvixOS adapts.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {useCases.map((uc, i) => (
              <div
                key={i}
                className="group p-6 rounded-2xl glass border border-white/5 hover:border-white/10 transition-all duration-300 hover:translate-y-[-2px]"
                style={{
                  opacity: useCasesReveal.visible ? 1 : 0,
                  transform: useCasesReveal.visible ? "translateY(0)" : "translateY(30px)",
                  transition: `opacity 0.6s ease-out ${i * 120}ms, transform 0.6s ease-out ${i * 120}ms`,
                }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-teal-400/10 flex items-center justify-center group-hover:bg-teal-400/20 transition-colors group-hover:scale-110">
                    <uc.icon className="w-5 h-5 text-teal-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">{uc.title}</h3>
                </div>
                <p className="text-sm text-gray-400 mb-4">{uc.desc}</p>
                <div className="grid grid-cols-2 gap-2">
                  {uc.points.map((point, j) => (
                    <div key={j} className="flex items-center gap-2 text-xs text-gray-500">
                      <Check className="w-3.5 h-3.5 text-teal-400" />
                      {point}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VERDIS BLOCKCHAIN */}
      <section id="blockchain" ref={blockchainReveal.ref} className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] bg-emerald-500/10 rounded-full blur-[100px] animate-pulse-glow" style={{ animationDuration: "5s" }}></div>
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-700 ${blockchainReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/20 mb-4">
              <Leaf className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs font-medium text-emerald-300">Carbon-Negative Blockchain</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">Verdis blockchain, natively integrated.</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">EvolvixOS manages the full Verdis ecosystem - DPoS validator management, AMM DEX operations, carbon credit tracking, governance, and real-time chain monitoring. The world first fully green, carbon-negative blockchain.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {[
              { label: "Consensus", value: "DPoS + BABE/GRANDPA", icon: Network },
              { label: "Validator Slots", value: "101 max - 27 active", icon: Users },
              { label: "DEX Protocol", value: "AMM x*y=k - 0.3% fee", icon: TrendingUp },
              { label: "Total Supply", value: "100B VRS / VRDX", icon: Layers },
              { label: "Carbon Offset", value: "1,247 tCO2 tracked", icon: Leaf },
              { label: "RPC Methods", value: "121 via cross-server bridge", icon: Terminal },
            ].map((item, i) => (
              <div
                key={i}
                className="group p-4 rounded-xl glass border border-white/5 hover:border-emerald-400/20 transition-all hover:translate-y-[-2px] hover:shadow-[0_0_30px_-5px_rgba(16,185,129,0.2)]"
                style={{
                  opacity: blockchainReveal.visible ? 1 : 0,
                  transform: blockchainReveal.visible ? "translateY(0)" : "translateY(20px)",
                  transition: `all 0.5s ease-out ${i * 80}ms`,
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <item.icon className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                  <span className="text-xs text-gray-500">{item.label}</span>
                </div>
                <div className="text-sm font-medium text-white">{item.value}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              "DPoS consensus with 101 validator slots and green scoring",
              "Native AMM DEX with x*y=k constant product formula",
              "On-chain carbon credits and reforestation tracking",
              "121 RPC methods via cross-server bridge",
              "WebSocket real-time block and swap notifications",
              "Multi-chain bridge monitoring (Ethereum, BSC, Polygon, Avalanche)",
            ].map((point, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-sm text-gray-400 px-4 py-2 rounded-lg glass border border-white/5 hover:border-emerald-400/20 transition-all"
                style={{
                  opacity: blockchainReveal.visible ? 1 : 0,
                  transition: `opacity 0.5s ease-out ${600 + i * 80}ms`,
                }}
              >
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                {point}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" ref={faqReveal.ref} className="py-24 bg-[#0c0c0d] border-y border-white/5">
        <div className="max-w-3xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-700 ${faqReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-4">
              <span className="text-xs font-medium text-gray-400">FAQ</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">Questions, answered.</h2>
            <p className="text-gray-500">Everything you need to know about EvolvixOS.</p>
          </div>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div
                key={i}
                className="rounded-xl glass border border-white/5 overflow-hidden hover:border-white/10 transition-colors"
                style={{
                  opacity: faqReveal.visible ? 1 : 0,
                  transform: faqReveal.visible ? "translateY(0)" : "translateY(20px)",
                  transition: `all 0.5s ease-out ${i * 80}ms`,
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-5 text-left hover:bg-white/[0.02] transition-colors"
                >
                  <span className="font-medium text-white text-sm md:text-base">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-gray-500 flex-shrink-0 transition-transform duration-300 ${openFaq === i ? "rotate-180" : ""}`} />
                </button>
                <div
                  className="overflow-hidden transition-all duration-300"
                  style={{ maxHeight: openFaq === i ? "200px" : "0px" }}
                >
                  <div className="px-5 pb-5 text-sm text-gray-400 leading-relaxed">{faq.a}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-teal-500/10 rounded-full blur-[100px] animate-pulse-glow" style={{ animationDuration: "4s" }}></div>
        </div>
        <div className="relative z-10 max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-4 gradient-text animate-fade-in-up">Ready to evolve?</h2>
          <p className="text-gray-400 mb-8 max-w-xl mx-auto animate-fade-in-up" style={{ animationDelay: "0.1s", opacity: 0 }}>
            Join the platform that is redefining how engineering teams build, deploy, and manage software + blockchain infrastructure.
          </p>
          <div className="flex items-center justify-center gap-4 animate-fade-in-up" style={{ animationDelay: "0.2s", opacity: 0 }}>
            <Link to="/register" className="group inline-flex items-center gap-2 bg-teal-400 text-[#0a0a0b] px-6 py-3 rounded-lg font-medium hover:bg-teal-300 transition-all hover:scale-105 hover:shadow-[0_0_30px_-5px_rgba(0,245,212,0.5)]">
              Create Account
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to="/login" className="inline-flex items-center gap-2 text-gray-400 hover:text-white px-6 py-3 rounded-lg border border-white/10 hover:border-white/20 transition-all hover:bg-white/5">
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/5 bg-[#0a0a0b]">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center">
                  <Cpu className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold">EvolvixOS</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">The Universal AI Engineering Operating System. Built by Protremix.</p>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Platform</div>
              <div className="space-y-2 text-sm text-gray-600">
                <div>AI Agents</div><div>Pipelines</div><div>Blockchain</div><div>Security</div><div>Analytics</div>
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Resources</div>
              <div className="space-y-2 text-sm text-gray-600">
                <div>Documentation</div><div>API Reference</div><div>Whitepaper</div>
                <a href="https://github.com/verdischain" className="hover:text-white transition-colors flex items-center gap-1">
                  <Github className="w-3 h-3" /> GitHub
                </a>
                <div>Status</div>
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Company</div>
              <div className="space-y-2 text-sm text-gray-600">
                <div>About</div><div>Verdis Chain</div><div>Protremix</div>
                <div className="flex items-center gap-1"><Mail className="w-3 h-3" /> Contact</div>
                <div>Privacy</div>
              </div>
            </div>
          </div>
          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-xs text-gray-600">2026 EvolvixOS by Protremix. All rights reserved.</div>
            <div className="flex items-center gap-4 text-xs text-gray-600">
              <span className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
                evolvixos.com
              </span>
              <span className="flex items-center gap-1.5">
                <Leaf className="w-3 h-3 text-emerald-400" />
                Carbon-Negative Infrastructure
              </span>
            </div>
          </div>
        </div>
      </footer>

      {/* FLOATING AI CHAT WIDGET */}
      {chatOpen && (
        <div className="fixed bottom-4 right-4 z-50 w-[380px] max-w-[calc(100vw-2rem)] h-[500px] max-h-[calc(100vh-2rem)] bg-[#0a0a0b] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-scale-in glow-teal">
          <div className="flex items-center justify-between p-4 border-b border-white/5 glass">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-sm font-medium text-white">EvolvixOS AI</div>
                <div className="text-xs text-emerald-400 flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
                  Online - GPT-4o
                </div>
              </div>
            </div>
            <button onClick={() => setChatOpen(false)} className="text-gray-500 hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.length === 0 && (
              <div className="text-center text-sm text-gray-500 py-8 animate-fade-in">
                <Bot className="w-10 h-10 text-teal-400/40 mx-auto mb-3" />
                <p>Hi! I am the EvolvixOS AI assistant.</p>
                <p className="text-xs mt-1">Ask me about the platform, blockchain, or anything!</p>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in-up`}>
                <div className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                  msg.role === "user"
                    ? "rounded-tr-sm bg-teal-400/10 border border-teal-400/20 text-teal-200"
                    : "rounded-tl-sm bg-white/5 text-gray-300"
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="px-3 py-2 rounded-lg rounded-tl-sm bg-white/5 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
          <div className="p-3 border-t border-white/5 flex items-center gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ask me anything..."
              className="flex-1 px-3 py-2 bg-white/5 border border-white/5 rounded-lg text-sm text-white placeholder-gray-600 focus:outline-none focus:border-teal-400/30 transition-colors"
            />
            <button onClick={sendMessage} disabled={chatLoading} className="p-2 rounded-lg bg-teal-400 text-[#0a0a0b] disabled:opacity-50 hover:shadow-[0_0_20px_-5px_rgba(0,245,212,0.5)] transition-all">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* CHAT BUTTON */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-4 right-4 z-50 w-14 h-14 rounded-full bg-teal-400 text-[#0a0a0b] shadow-lg hover:scale-110 transition-transform flex items-center justify-center group hover:shadow-[0_0_30px_-5px_rgba(0,245,212,0.6)]"
        >
          <MessageSquare className="w-6 h-6" />
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-[#0a0a0b] animate-pulse"></span>
        </button>
      )}
    </div>
  );
};

export default Landing;
