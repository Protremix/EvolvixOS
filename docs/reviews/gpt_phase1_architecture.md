### 1. REPOSITORY STRUCTURE

```plaintext
aegisos/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── events.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── event.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── event.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── project_service.py
│   │   │   ├── task_service.py
│   │   │   ├── event_service.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── error_handler.py
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   ├── versions/
│   ├── Dockerfile
│   ├── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── index.html
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   ├── vite.config.js
│   ├── package.json
│   ├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env
├── .gitignore
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
```

### 2. BACKEND ARCHITECTURE

- **FastAPI App Structure:**
  - `main.py`: Initializes FastAPI app, includes routers, and middleware.
  - `core/config.py`: Configuration management using Pydantic.
  - `core/security.py`: JWT and password hashing utilities.
  - `core/logging.py`: Structured JSON logging setup.
  - `api/deps.py`: Dependency injection functions.
  - `api/v1/auth.py`: Authentication endpoints.
  - `api/v1/users.py`: User-related endpoints.
  - `api/v1/projects.py`: Project-related endpoints.
  - `api/v1/tasks.py`: Task-related endpoints.
  - `api/v1/events.py`: Event-related endpoints.
  - `models/`: SQLAlchemy models.
  - `schemas/`: Pydantic schemas for request/response validation.
  - `services/`: Business logic and database interaction.
  - `middleware/error_handler.py`: Global error handling middleware.

- **Dependency Injection Pattern:**
  - Use FastAPI's `Depends` for injecting dependencies like database sessions and current user.

- **Error Handling Strategy:**
  - Centralized error handling in `middleware/error_handler.py` using FastAPI's exception handling.

- **Exact File List with Purpose:**
  - `main.py`: Entry point for the FastAPI application.
  - `core/config.py`: Load and manage configuration settings.
  - `core/security.py`: Handle JWT creation and password hashing.
  - `core/logging.py`: Configure structured logging.
  - `api/deps.py`: Define reusable dependencies.
  - `api/v1/auth.py`: Define authentication routes.
  - `api/v1/users.py`: Define user management routes.
  - `api/v1/projects.py`: Define project management routes.
  - `api/v1/tasks.py`: Define task management routes.
  - `api/v1/events.py`: Define event management routes.
  - `models/`: Define database models.
  - `schemas/`: Define data validation schemas.
  - `services/`: Implement business logic.
  - `middleware/error_handler.py`: Implement global error handling.

### 3. DATABASE SCHEMA (MVP)

- **Users Table:**
  - `id`: UUID, Primary Key
  - `username`: VARCHAR(150), Unique, Not Null
  - `email`: VARCHAR(255), Unique, Not Null
  - `hashed_password`: VARCHAR(255), Not Null
  - `role`: ENUM('admin', 'developer', 'viewer'), Default 'viewer'
  - `created_at`: TIMESTAMP, Default `NOW()`

- **Projects Table:**
  - `id`: UUID, Primary Key
  - `name`: VARCHAR(255), Not Null
  - `description`: TEXT
  - `owner_id`: UUID, Foreign Key to Users(id)
  - `created_at`: TIMESTAMP, Default `NOW()`

- **Tasks Table:**
  - `id`: UUID, Primary Key
  - `title`: VARCHAR(255), Not Null
  - `description`: TEXT
  - `project_id`: UUID, Foreign Key to Projects(id)
  - `assigned_to`: UUID, Foreign Key to Users(id)
  - `status`: ENUM('pending', 'in_progress', 'completed'), Default 'pending'
  - `created_at`: TIMESTAMP, Default `NOW()`

- **Events Table:**
  - `id`: UUID, Primary Key
  - `type`: VARCHAR(50), Not Null
  - `payload`: JSONB
  - `created_at`: TIMESTAMP, Default `NOW()`

- **Audit Logs Table:**
  - `id`: UUID, Primary Key
  - `action`: VARCHAR(255), Not Null
  - `user_id`: UUID, Foreign Key to Users(id)
  - `timestamp`: TIMESTAMP, Default `NOW()`

- **Alembic Migration Strategy:**
  - Use `alembic revision --autogenerate -m "initial migration"` to create initial migration script.
  - Apply migrations using `alembic upgrade head`.

### 4. AUTHENTICATION FLOW

- **Registration:**
  - Endpoint: `POST /api/v1/auth/register`
  - Hash password with bcrypt before storing.

- **Login:**
  - Endpoint: `POST /api/v1/auth/login`
  - Validate credentials, issue JWT and refresh token.

- **Token Refresh:**
  - Endpoint: `POST /api/v1/auth/refresh`
  - Validate refresh token, issue new JWT.

- **Logout:**
  - Endpoint: `POST /api/v1/auth/logout`
  - Invalidate refresh token.

- **JWT Structure:**
  - Claims: `sub` (user ID), `exp` (expiry), `role` (user role)
  - Expiry: 15 minutes for access token, 7 days for refresh token.

- **Password Hashing:**
  - Use `bcrypt` for hashing passwords.

- **RBAC Roles for MVP:**
  - `admin`: Full access
  - `developer`: Access to projects and tasks
  - `viewer`: Read-only access

### 5. API ENDPOINTS (Phase 1)

- **Auth Endpoints:**
  - `POST /api/v1/auth/register`: Register a new user
  - `POST /api/v1/auth/login`: Authenticate user and return tokens
  - `POST /api/v1/auth/refresh`: Refresh JWT
  - `POST /api/v1/auth/logout`: Logout user

- **User Endpoints:**
  - `GET /api/v1/users/me`: Get current user info (Auth: JWT)

- **Project Endpoints:**
  - `GET /api/v1/projects`: List all projects (Auth: JWT)
  - `POST /api/v1/projects`: Create a new project (Auth: JWT, Role: admin/developer)

- **Task Endpoints:**
  - `GET /api/v1/tasks`: List all tasks (Auth: JWT)
  - `POST /api/v1/tasks`: Create a new task (Auth: JWT, Role: admin/developer)

- **Event Endpoints:**
  - `GET /api/v1/events`: List all events (Auth: JWT)

### 6. DOCKER COMPOSE

- **Services:**
  - `api`: FastAPI backend
  - `frontend`: React frontend
  - `postgres`: PostgreSQL database
  - `redis`: Redis server
  - `worker`: Celery worker

- **Ports, Volumes, Environment Variables:**
  - `api`: Ports `8000:8000`, Volumes `./backend:/app`, Env `DB_URL`, `REDIS_URL`
  - `frontend`: Ports `3000:3000`, Volumes `./frontend:/app`
  - `postgres`: Ports `5432:5432`, Volumes `pgdata:/var/lib/postgresql/data`, Env `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
  - `redis`: Ports `6379:6379`
  - `worker`: Depends on `api`, `redis`

- **Health Checks:**
  - `api`: `CMD curl --fail http://localhost:8000/health || exit 1`
  - `postgres`: `CMD pg_isready -U $POSTGRES_USER`
  - `redis`: `CMD redis-cli ping`

### 7. CI/CD PIPELINE

- **GitHub Actions Workflow:**
  - `ci.yml`: Run on PR, includes linting, testing, and build checks.
  - `cd.yml`: Run on push to `main`, deploy to server.

- **Checks on PR:**
  - Linting with `flake8` for Python and `eslint` for JavaScript.
  - Run tests with `pytest` for backend and `jest` for frontend.
  - Build Docker images.

- **Deployment:**
  - Use `docker-compose` to pull latest images and restart services on server.

### 8. WHAT NOT TO BUILD IN PHASE 1

- **No AI Features:** Any AI-related functionality is out of scope.
- **No Advanced Analytics:** Basic logging and monitoring only.
- **No Payment Integration:** No payment processing or billing.
- **No External Integrations:** Focus on core functionality only.
- **No Advanced RBAC:** Basic roles only, no complex permissions.
- **No UI/UX Design:** Basic frontend skeleton without detailed design.
- **No Email Notifications:** No email or SMS notifications.
- **No File Uploads:** No handling of file uploads or storage.