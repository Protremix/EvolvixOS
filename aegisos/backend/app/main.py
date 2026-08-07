import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.db.session import Base, engine
from app.middleware.error_handler import register_exception_handlers
from app.middleware.rate_limit import limiter, rate_limit_handler

# Import routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.events import router as events_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.config import router as config_router

from app.api.v1.ai import router as ai_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.security import router as security_router
from app.api.v1.monitor import router as local_monitor_router
from app.api.v1.identity import router as identity_router
from app.api.v1.deployment import router as deployment_router
from app.api.v1.identity_enhanced import router as identity_enhanced_router
from app.api.v1.identity_privacy import router as identity_privacy_router
from app.api.v1.smart_contracts import router as smart_contracts_router
from app.api.v1.onchain_analytics import router as onchain_analytics_router
from app.api.v1.governance import router as governance_router
from app.api.v1.tokenomics import router as tokenomics_router
from app.api.v1.validators import router as validators_router
from app.api.v1.bridge_monitor import router as bridge_monitor_router
from app.api.v1.plugin_marketplace import router as plugin_marketplace_router
from app.api.v1.notifications import router as notification_center_router
from app.api.v1.staking_dashboard import router as staking_dashboard_router
from app.api.v1.cross_chain_analytics import router as cross_chain_analytics_router
from app.api.v1.api_gateway import router as api_gateway_router
from app.api.v1.audit_compliance import router as audit_compliance_router
from app.api.v1.nft_marketplace import router as nft_marketplace_router
from app.api.v1.faucet import router as faucet_router
from app.api.v1.block_explorer import router as block_explorer_router
from app.api.v1.mobile_integration import router as mobile_integration_router
from app.api.v1.production_readiness import router as production_readiness_router
from app.api.v1.security_fixes import router as security_fixes_router
from app.api.v1.deployment_docs import router as deployment_docs_router
from app.api.v1.deployment_prep import router as deployment_prep_router
from app.api.v1.community import router as community_router
from app.api.v1.enhanced_security import router as enhanced_security_router
from app.api.v1.evolvixos_infra import router as evolvixos_infra_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.verdis import router as verdis_router
from app.api.v1.github import router as github_router
from app.api.v1.code_ops import router as code_ops_router
from app.api.v1.dependency_graph import router as dep_graph_router
from app.api.v1.ast_diff import router as ast_diff_router
from app.api.v1.spec_compiler import router as spec_compiler_router
from app.api.v1.project_adapters import router as project_adapter_router
from app.api.v1.feature_pipeline import router as feature_pipeline_router
from app.api.v1.pipeline_templates import router as pipeline_templates_router, notif_router as notifications_router
from app.api.v1.pipeline_analytics import router as pipeline_analytics_router, sched_router as pipeline_scheduler_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.agent_config import router as agent_config_router
from app.api.v1.pipeline_comparison import router as pipeline_comparison_router
from app.api.v1.activity_log import router as activity_log_router
from app.api.v1.dashboard import router as dashboard_router, export_router as export_router_v1
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.grafana_alerts import router as grafana_alerts_router
from app.api.v1.system_settings import router as system_settings_router
from app.api.v1.rate_limiter import router as rate_limiter_router
from app.api.v1.search_health_backup import search_router, health_router, backup_router
from app.api.v1.verdis_project import router as verdis_project_router
from app.api.v1.verdis_benchmark import router as verdis_benchmark_router
from app.api.v1.verdis_integration import router as verdis_integration_router
from app.api.v1.verdis_bridge import router as verdis_bridge_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.security_hardening import router as security_hardening_router
from app.api.v1.agent_enhancement import router as agent_enhancement_router
from app.api.v1.collab_monitor import router as collab_monitor_router
from app.api.v1.agent_learning import router as agent_learning_router
from app.api.v1.multi_project import router as multi_project_router
# Import all models so Base.metadata sees them
from app.models.user import User  # noqa
from app.models.project import Project  # noqa
from app.models.task import Task  # noqa
from app.models.event import Event  # noqa
from app.models.audit_log import AuditLog  # noqa

logger = logging.getLogger("evolvixos")

REQUEST_COUNT = Counter("evolvixos_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("evolvixos_request_duration_seconds", "HTTP request duration", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("evolvixos_startup", extra={"version": settings.VERSION})
    except Exception as e:
        logger.warning("database_connection_failed", extra={"error": str(e)})
    yield
    engine.dispose()
    logger.info("evolvixos_shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
register_exception_handlers(app)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response


# Include API routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(events_router, prefix=settings.API_V1_PREFIX)
app.include_router(organizations_router, prefix=settings.API_V1_PREFIX)
app.include_router(config_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_router, prefix=settings.API_V1_PREFIX)
app.include_router(feedback_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_router, prefix=settings.API_V1_PREFIX)
app.include_router(local_monitor_router, prefix=settings.API_V1_PREFIX)
app.include_router(identity_router, prefix=settings.API_V1_PREFIX)
app.include_router(deployment_router, prefix=settings.API_V1_PREFIX)
app.include_router(identity_enhanced_router, prefix=settings.API_V1_PREFIX)
app.include_router(identity_privacy_router, prefix=settings.API_V1_PREFIX)
app.include_router(smart_contracts_router, prefix=settings.API_V1_PREFIX)
app.include_router(onchain_analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(governance_router, prefix=settings.API_V1_PREFIX)
app.include_router(tokenomics_router, prefix=settings.API_V1_PREFIX)
app.include_router(validators_router, prefix=settings.API_V1_PREFIX)
app.include_router(bridge_monitor_router, prefix=settings.API_V1_PREFIX)
app.include_router(plugin_marketplace_router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket_router, prefix=settings.API_V1_PREFIX)
app.include_router(verdis_router, prefix=settings.API_V1_PREFIX)
app.include_router(github_router, prefix=settings.API_V1_PREFIX)
app.include_router(code_ops_router, prefix=settings.API_V1_PREFIX)
app.include_router(dep_graph_router, prefix=settings.API_V1_PREFIX)
app.include_router(ast_diff_router, prefix=settings.API_V1_PREFIX)
app.include_router(spec_compiler_router, prefix=settings.API_V1_PREFIX)
app.include_router(project_adapter_router, prefix=settings.API_V1_PREFIX)
app.include_router(feature_pipeline_router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline_templates_router, prefix=settings.API_V1_PREFIX)
# Old notif_router replaced by notification_center_router
# app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
app.include_router(notification_center_router, prefix=settings.API_V1_PREFIX)
app.include_router(staking_dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(cross_chain_analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_gateway_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_compliance_router, prefix=settings.API_V1_PREFIX)
app.include_router(nft_marketplace_router, prefix=settings.API_V1_PREFIX)
app.include_router(faucet_router, prefix=settings.API_V1_PREFIX)
app.include_router(block_explorer_router, prefix=settings.API_V1_PREFIX)
app.include_router(mobile_integration_router, prefix=settings.API_V1_PREFIX)
app.include_router(production_readiness_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_fixes_router, prefix=settings.API_V1_PREFIX)
app.include_router(deployment_docs_router, prefix=settings.API_V1_PREFIX)
app.include_router(deployment_prep_router, prefix=settings.API_V1_PREFIX)
app.include_router(community_router, prefix=settings.API_V1_PREFIX)
app.include_router(enhanced_security_router, prefix=settings.API_V1_PREFIX)
app.include_router(evolvixos_infra_router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline_analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline_scheduler_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_base_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_config_router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline_comparison_router, prefix=settings.API_V1_PREFIX)
app.include_router(activity_log_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(export_router_v1, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(rate_limiter_router, prefix=settings.API_V1_PREFIX)
app.include_router(search_router, prefix=settings.API_V1_PREFIX)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(backup_router, prefix=settings.API_V1_PREFIX)
app.include_router(verdis_project_router, prefix=settings.API_V1_PREFIX)
app.include_router(verdis_benchmark_router, prefix=settings.API_V1_PREFIX)
app.include_router(verdis_integration_router, prefix=settings.API_V1_PREFIX)
app.include_router(verdis_bridge_router, prefix=settings.API_V1_PREFIX)
app.include_router(onboarding_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_hardening_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_enhancement_router, prefix=settings.API_V1_PREFIX)
app.include_router(collab_monitor_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_learning_router, prefix=settings.API_V1_PREFIX)
app.include_router(multi_project_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION, "service": settings.PROJECT_NAME}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
