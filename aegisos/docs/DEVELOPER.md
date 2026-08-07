# Developer Guide

## Project Structure

```
evolvixos/
├── backend/
│   ├── app/
│   │   ├── ai/                    # AI agents and workflow engine
│   │   │   ├── agents/            # 11 AI agent implementations
│   │   │   ├── llm_client.py       # OpenAI GPT-4o client
│   │   │   ├── workflow_engine.py  # Task routing and pipelines
│   │   │   └── distributed_executor.py
│   │   ├── api/
│   │   │   └── v1/                # 30 API routers
│   │   ├── core/                  # Security, logging, config
│   │   ├── db/                    # Database session, models
│   │   ├── integrations/          # External service adapters
│   │   ├── models/                # SQLAlchemy models
│   │   ├── services/              # Business logic services
│   │   └── main.py                # FastAPI application
│   ├── tests/                     # 853 tests
│   ├── alembic/                   # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/                # 33 pages
│   │   ├── services/             # API client services
│   │   └── App.jsx               # Main app with routing
│   └── package.json
├── nginx/                        # Production nginx config
├── deploy/                       # Deployment scripts
├── docker-compose.prod.yml       # Production Docker config
└── docs/                         # This documentation
```

## Running Tests

```bash
cd backend

# Run all tests
python -m pytest --tb=short -q

# Run specific test file
python -m pytest tests/test_verdis_project.py -v

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing
```

## Adding a New API Router

1. Create the router file:
```python
# app/api/v1/my_feature.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.get("/")
async def list_items(current_user: User = Depends(get_current_active_user)):
    return {"items": []}
```

2. Register in `app/main.py`:
```python
from app.api.v1.my_feature import router as my_feature_router
app.include_router(my_feature_router, prefix=settings.API_V1_PREFIX)
```

3. Write tests:
```python
# tests/test_my_feature.py
def test_list_items(client, test_user):
    resp = client.get("/api/v1/my-feature/", headers=test_user["headers"])
    assert resp.status_code == 200
```

## Adding a New AI Agent

1. Create the agent:
```python
# app/ai/agents/my_agent.py
from app.ai.agents.base_agent import BaseAgent, AgentTask, AgentResult

class AIMyAgent(BaseAgent):
    name = "my_agent"
    specialization = "Custom specialization"
    
    async def execute(self, task: AgentTask) -> AgentResult:
        # Implement agent logic
        return AgentResult(
            task_id=task.id,
            success=True,
            output={"result": "..."},
        )
```

2. Register in `app/ai/agents/__init__.py`
3. Add task type to workflow engine
4. Add to agent configuration defaults

## Adding a New Service

```python
# app/services/my_service.py
import threading
from typing import Optional

class MyService:
    def __init__(self):
        self._lock = threading.Lock()
    
    def do_something(self) -> dict:
        with self._lock:
            return {"status": "done"}

_service: Optional[MyService] = None

def get_service() -> MyService:
    global _service
    if _service is None:
        _service = MyService()
    return _service
```

## Frontend Pages

```jsx
// src/pages/MyPage.jsx
import React, { useState, useEffect } from 'react';
import myService from '../services/myService';

function MyPage() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    myService.list().then(r => setData(r.data));
  }, []);
  
  return <div>{/* ... */}</div>;
}
```

## Code Style

- **Python**: Follow PEP 8, use type hints, structured logging
- **React**: Functional components, hooks, TailwindCSS
- **Testing**: Every new feature needs tests
- **Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
