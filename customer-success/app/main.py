"""Verdis AI Customer Success Platform - Main Application."""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, multiprocess

from app.core.config import settings

# Metrics
REQUEST_COUNT = Counter('cs_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('cs_request_duration_seconds', 'Request latency', ['endpoint'])
AI_QUERY_COUNT = Counter('cs_ai_queries_total', 'AI queries', ['module', 'status'])
TICKET_COUNT = Counter('cs_tickets_total', 'Tickets created', ['type', 'priority'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Customer Success Platform starting...")
    print(f"  Workers: {settings.WORKERS}")
    print(f"  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    # Initialize database tables
    from app.models.database import init_db
    init_db()
    
    # Initialize AI engine
    from app.ai.engine import AIEngine
    app.state.ai_engine = AIEngine()
    await app.state.ai_engine.initialize()
    
    # Initialize services
    from app.services.ticket_service import TicketService
    from app.services.knowledge_service import KnowledgeService
    from app.services.conversation_service import ConversationService
    from app.services.incident_service import IncidentService
    
    app.state.tickets = TicketService()
    app.state.knowledge = KnowledgeService()
    app.state.conversations = ConversationService()
    app.state.incidents = IncidentService()
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Customer Success Platform ready.")
    yield
    # Shutdown
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Customer Success Platform shutting down...")


app = FastAPI(
    title="Verdis AI Customer Success Platform",
    description="World-class autonomous customer success platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://evolvixos.com", "https://verdischain.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request tracking
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    endpoint = request.url.path
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    return response


# Health
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "customer-success",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# Metrics
@app.get("/metrics")
async def metrics():
    return JSONResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


# Import and include routers
from app.api.v1.chat import router as chat_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.email import router as email_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.escalation import router as escalation_router
from app.api.v1.merchant import router as merchant_router
from app.api.v1.developer import router as developer_router
from app.api.v1.blockchain import router as blockchain_router
from app.api.v1.learning import router as learning_router

app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(tickets_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_V1_PREFIX)
app.include_router(email_router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(escalation_router, prefix=settings.API_V1_PREFIX)
app.include_router(merchant_router, prefix=settings.API_V1_PREFIX)
app.include_router(developer_router, prefix=settings.API_V1_PREFIX)
app.include_router(blockchain_router, prefix=settings.API_V1_PREFIX)
app.include_router(learning_router, prefix=settings.API_V1_PREFIX)
