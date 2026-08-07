# VERDIS GOVERNANCE DOCUMENT 03: CODING STANDARDS

**Document ID:** VERDIS-GOV-03  
**Title:** Verdis Ecosystem Language & Coding Standards  
**Version:** 1.0.0  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT GOVERNANCE DOCUMENT  
**Applies To:** All Engineers, Sub-Agents, AI Code Generators, and Automated Code Reviewers within the Verdis Ecosystem.

---

## TABLE OF CONTENTS
1. [General Engineering Philosophy & Code Quality](#1-general-engineering-philosophy--code-quality)
   1.1 [The Zero Warnings Principle](#11-the-zero-warnings-principle)
   1.2 [Readability & Explicitness over Cleverness](#12-readability--explicitness-over-cleverness)
   1.3 [Self-Documenting Code & Comment Discipline](#13-self-documenting-code--comment-discipline)
2. [Rust & Substrate Coding Standards](#2-rust--substrate-coding-standards)
   2.1 [Toolchain & Linter Requirements (`clippy` & `rustfmt`)](#21-toolchain--linter-requirements-clippy--rustfmt)
   2.2 [Unsafe Rust Policy & CTO Safety Proofs](#22-unsafe-rust-policy--cto-safety-proofs)
   2.3 [Substrate Frame v2 Pallet Conventions](#23-substrate-frame-v2-pallet-conventions)
   2.4 [Substrate Runtime WASM & `no_std` Rules](#24-substrate-runtime-wasm--no_std-rules)
   2.5 [Rust Error Handling & `Result` Patterns](#25-rust-error-handling--result-patterns)
   2.6 [Exhaustive Rust Code Example (Custom Pallet)](#26-exhaustive-rust-code-example-custom-pallet)
3. [Python Coding Standards](#3-python-coding-standards)
   3.1 [Python 3.11+ Core Rules & PEP 8 Compliance](#31-python-311-core-rules--pep-8-compliance)
   3.2 [Strict Type Annotations & `mypy` Enforcement](#32-strict-type-annotations--mypy-enforcement)
   3.3 [FastAPI Endpoint & Pydantic v2 Design Rules](#33-fastapi-endpoint--pydantic-v2-design-rules)
   3.4 [Asynchronous I/O & Database Query Patterns](#34-asynchronous-io--database-query-patterns)
   3.5 [Exhaustive Python Code Example (FastAPI Router + Service)](#35-exhaustive-python-code-example-fastapi-router--service)
4. [TypeScript & React Coding Standards](#4-typescript--react-coding-standards)
   4.1 [TypeScript Strict Mode Configuration (`tsconfig.json`)](#41-typescript-strict-mode-configuration-tsconfigjson)
   4.2 [React 18 Component Architecture & Hooks Rules](#42-react-18-component-architecture--hooks-rules)
   4.3 [State Management with Zustand & TanStack Query](#43-state-management-with-zustand--tanstack-query)
   4.4 [Exhaustive TypeScript Code Example (React Component + State)](#44-exhaustive-typescript-code-example-react-component--state)
5. [Naming Conventions & Code Style Guidelines](#5-naming-conventions--code-style-guidelines)
   5.1 [Universal Cross-Language Naming Matrix](#51-universal-cross-language-naming-matrix)
   5.2 [File & Directory Naming Rules](#52-file--directory-naming-rules)
6. [Comment Standards & API Documentation](#6-comment-standards--api-documentation)
   6.1 [Rustdoc Formatting Standards (`///`)](#61-rustdoc-formatting-standards-)
   6.2 [Python Google-Style Docstring Format](#62-python-google-style-docstring-format)
   6.3 [JSDoc / TSDoc Standards](#63-jsdoc--tsdoc-standards)
7. [Unified Error Handling Patterns](#7-unified-error-handling-patterns)
   7.1 [Error Domain Mapping Matrix](#71-error-domain-mapping-matrix)
   7.2 [Error Translation Example Across Layers](#72-error-translation-example-across-layers)
8. [Code Review & Verification Checklists](#8-code-review--verification-checklists)
   8.1 [Rust & Substrate Review Checklist](#81-rust--substrate-review-checklist)
   8.2 [Python Review Checklist](#82-python-review-checklist)
   8.3 [TypeScript Review Checklist](#83-typescript-review-checklist)

---

## 1. GENERAL ENGINEERING PHILOSOPHY & CODE QUALITY

### 1.1 The Zero Warnings Principle
In the Verdis Ecosystem, warnings are treated as errors. No pull request or automated sub-agent commit will be merged into any branch if the build, linter, or static analyzer emits a single warning.
- **Rust:** `cargo clippy --all-targets -- -D warnings` must execute cleanly.
- **Python:** `flake8` and `mypy --strict` must return zero errors/warnings.
- **TypeScript:** `eslint` must complete with 0 warnings.

### 1.2 Readability & Explicitness over Cleverness
Code is read far more often than it is written.
- Prefer explicit type signatures, clear variable names, and structured control flow over dense one-liners or complex macros.
- Avoid hidden magic, implicit type coercions, or undocumented side-effects.

### 1.3 Self-Documenting Code & Comment Discipline
Code must explain *what* it is doing through clean abstractions and clear naming. Comments must explain *why* non-obvious choices or algorithmic trade-offs were made.

---

## 2. RUST & SUBSTRATE CODING STANDARDS

```
 +-------------------------------------------------------------------------+
 |                     RUST & SUBSTRATE TOOLCHAIN                          |
 +-------------------------------------------------------------------------+
 | Rust Compiler  | 1.80.0+ (Stable for Node, Nightly for WASM Runtime)    |
 | Formatting     | `cargo fmt --check`                                   |
 | Linting        | `cargo clippy --workspace --all-targets -- -D warnings`|
 | Safety Policy  | `unsafe` prohibited without GPT-4o CTO safety proof   |
 +-------------------------------------------------------------------------+
```

### 2.1 Toolchain & Linter Requirements (`clippy` & `rustfmt`)
All Rust projects across `blockchain/` must maintain a root `clippy.toml` configuration enforcing strict code style:

```toml
# blockchain/clippy.toml
avoid-breaking-exported-api = true
blacklisted-names = ["foo", "bar", "baz", "tmp"]
cognitive-complexity-threshold = 20
too-many-arguments-threshold = 7
type-complexity-threshold = 250
```

Execution command required before every commit:
```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
```

### 2.2 Unsafe Rust Policy & CTO Safety Proofs
Use of `unsafe` Rust is strictly forbidden unless approved by GPT-4o with an accompanying formal safety comment (`// SAFETY: ...`).
- **Forbidden:** Raw pointer manipulation in Substrate pallets, unchecked array indexing (`get_unchecked`), mutating global state.
- **Permitted Exception:** Interfacing with low-level OS primitives or WASM FFI bindings where no safe Rust abstraction exists.

Example of mandatory safety block:
```rust
// SAFETY: The pointer `ptr` is guaranteed to be non-null and aligned to 8 bytes 
// because it was allocated by the WASM runtime memory allocator in line 42.
unsafe {
    std::ptr::copy_nonoverlapping(src, dst, count);
}
```

### 2.3 Substrate Frame v2 Pallet Conventions
1. **Weight Annotations:** Every dispatchable call MUST have a calculated weight annotation derived from `frame_benchmarking`.
2. **Storage Key Design:** Always use `Blake2_128Concat` or `Twox64Concat` for storage map keys to prevent hash collision attacks. Never use `UncheckedIdentity` for user-controllable input keys.
3. **Event Generation:** Emit events for all state-mutating extrinsics to enable indexer tracking.

### 2.4 Substrate Runtime WASM & `no_std` Rules
- The Substrate WASM runtime (`blockchain/runtime`) must compile under `#![cfg_attr(not(feature = "std"), no_std)]`.
- Never import `std` collections or I/O types directly. Use `sp_std` or `sp_runtime` equivalents (`sp_std::vec::Vec`, `sp_std::collections::btree_map::BTreeMap`).

### 2.5 Rust Error Handling & `Result` Patterns
Functions returning errors must use `Result<T, E>`. In Substrate dispatchables, return `DispatchResult` or `DispatchResultWithPostInfo`. Never call `.unwrap()` or `.expect()` in production code.

### 2.6 Exhaustive Rust Code Example (Custom Pallet)

```rust
// blockchain/pallets/dpos-staking/src/lib.rs
#![cfg_attr(not(feature = "std"), no_std)]

pub use pallet::*;

#[frame_support::pallet]
pub mod pallet {
    use frame_support::{
        pallet_prelude::*,
        traits::{Currency, ReservableCurrency},
    };
    use frame_system::pallet_prelude::*;
    use sp_std::vec::Vec;

    type BalanceOf<T> =
        <<T as Config>::Currency as Currency<<T as frame_system::Config>::AccountId>>::Balance;

    #[pallet::pallet]
    pub struct Pallet<T>(_);

    #[pallet::config]
    pub trait Config: frame_system::Config {
        type RuntimeEvent: From<Event<Self>> + IsType<<Self as frame_system::Config>::RuntimeEvent>;
        type Currency: ReservableCurrency<Self::AccountId>;
        
        #[pallet::constant]
        type MaxValidators: Get<u32>;
    }

    #[pallet::storage]
    #[pallet::getter(fn active_validators)]
    pub type ActiveValidators<T: Config> =
        StorageValue<_, BoundedVec<T::AccountId, T::MaxValidators>, ValueQuery>;

    #[pallet::storage]
    #[pallet::getter(fn validator_stake)]
    pub type ValidatorStake<T: Config> =
        StorageMap<_, Blake2_128Concat, T::AccountId, BalanceOf<T>, ValueQuery>;

    #[pallet::event]
    #[pallet::generate_deposit(pub(super) fn deposit_event)]
    pub enum Event<T: Config> {
        ValidatorRegistered { validator: T::AccountId, stake: BalanceOf<T> },
        StakeIncreased { validator: T::AccountId, additional_stake: BalanceOf<T> },
    }

    #[pallet::error]
    pub enum Error<T> {
        ValidatorLimitReached,
        InsufficientBalance,
        AlreadyRegistered,
        NotRegistered,
    }

    #[pallet::call]
    impl<T: Config> Pallet<T> {
        /// Registers a new validator candidate by bonding stake.
        #[pallet::call_index(0)]
        #[pallet::weight(25_000 + T::DbWeight::get().reads_writes(2, 2).ref_time())]
        pub fn register_validator(
            origin: OriginFor<T>,
            stake_amount: BalanceOf<T>,
        ) -> DispatchResult {
            let sender = ensure_signed(origin)?;

            ensure!(
                !ValidatorStake::<T>::contains_key(&sender),
                Error::<T>::AlreadyRegistered
            );

            T::Currency::reserve(&sender, stake_amount)
                .map_err(|_| Error::<T>::InsufficientBalance)?;

            ValidatorStake::<T>::insert(&sender, stake_amount);

            ActiveValidators::<T>::try_mutate(|validators| -> DispatchResult {
                validators
                    .try_push(sender.clone())
                    .map_err(|_| Error::<T>::ValidatorLimitReached)?;
                Ok(())
            })?;

            Self::deposit_event(Event::ValidatorRegistered {
                validator: sender,
                stake: stake_amount,
            });

            Ok(())
        }
    }
}
```

---

## 3. PYTHON CODING STANDARDS

```
 +-------------------------------------------------------------------------+
 |                      PYTHON & FASTAPI ENVIRONMENT                       |
 +-------------------------------------------------------------------------+
 | Python Engine  | 3.11.8+ (Strict Type Hints Mandatory)                  |
 | Style Checker  | `flake8 --max-line-length=100`                           |
 | Type Checker   | `mypy --strict aegisos/`                                |
 | Formatter      | `black --line-length=100 aegisos/`                      |
 +-------------------------------------------------------------------------+
```

### 3.1 Python 3.11+ Core Rules & PEP 8 Compliance
- Adhere strictly to PEP 8 standards with a maximum line length of **100 characters**.
- Use explicit imports (`from typing import Optional, List`). Never use wildcard imports (`from module import *`).

### 3.2 Strict Type Annotations & `mypy` Enforcement
Every function, class method, and module property must specify explicit argument type hints and return type annotations.

`mypy.ini` configuration:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
```

### 3.3 FastAPI Endpoint & Pydantic v2 Design Rules
- All API payloads must be validated using Pydantic v2 `BaseModel` classes.
- Do not perform direct database queries inside route handlers. Always delegate to a Service Layer class.
- Always annotate response types using FastAPI's `response_model` parameter.

### 3.4 Asynchronous I/O & Database Query Patterns
- All I/O operations (HTTP requests, database reads/writes, Redis access) MUST be `async`.
- Never block the ASGI event loop with synchronous calls (`requests.get()`, `time.sleep()`). Use `httpx.AsyncClient()` and `asyncio.sleep()`.

### 3.5 Exhaustive Python Code Example (FastAPI Router + Service)

```python
# aegisos/app/api/v1/endpoints/agents.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from aegisos.app.db.session import get_async_db

router = APIRouter(prefix="/agents", tags=["AI Agents"])

# Schema Models
class AgentCreateRequest(BaseModel):
    agent_name: str = Field(..., min_length=3, max_length=64, example="agent-chain-dev")
    domain_role: str = Field(..., example="blockchain")
    max_memory_mb: int = Field(default=512, ge=128, le=4096)

class AgentResponse(BaseModel):
    agent_id: UUID
    agent_name: str
    domain_role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Service Layer
class AgentService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def register_agent(self, payload: AgentCreateRequest) -> AgentResponse:
        agent_id = uuid4()
        created_at = datetime.utcnow()
        
        # Simulate Async DB Insert
        new_agent = AgentResponse(
            agent_id=agent_id,
            agent_name=payload.agent_name,
            domain_role=payload.domain_role,
            is_active=True,
            created_at=created_at
        )
        return new_agent

# Endpoint Handler
@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new AI Sub-Agent instance"
)
async def register_agent_endpoint(
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_async_db)
) -> AgentResponse:
    # Registers an AI worker sub-agent and assigns it memory parameters.
    service = AgentService(db)
    try:
        return await service.register_agent(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent registration failed: {str(exc)}"
        )
```

---

## 4. TYPESCRIPT & REACT CODING STANDARDS

```
 +-------------------------------------------------------------------------+
 |                     TYPESCRIPT & REACT ENVIRONMENT                      |
 +-------------------------------------------------------------------------+
 | TypeScript Engine | 5.3+ (Strict Mode Enabled)                          |
 | UI Framework     | React 18.2+ (Functional Components Only)             |
 | Build Tooling    | Vite 5.1+                                            |
 | Linter           | ESLint with `@typescript-eslint/recommended`         |
 +-------------------------------------------------------------------------+
```

### 4.1 TypeScript Strict Mode Configuration (`tsconfig.json`)
All frontend packages in `frontend/` must compile under strict TypeScript settings:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 4.2 React 18 Component Architecture & Hooks Rules
- **Functional Components Only:** Class components are strictly prohibited.
- **Custom Hooks:** Business logic, API calls, and Zustand bindings must be encapsulated inside custom hooks (`useTaskExecution`, `useWalletAuth`).
- **PropTypes / Interface:** Every component must explicitly define a TypeScript `interface Props`.

### 4.3 State Management with Zustand & TanStack Query
- Use **Zustand** for client-side synchronous state (active theme, open sidebars, active tab).
- Use **TanStack Query (React Query)** for asynchronous server data fetching, caching, and revalidation.

### 4.4 Exhaustive TypeScript Code Example (React Component + State)

```typescript
// frontend/src/components/TaskExecutionCard.tsx
import React from 'react';
import { useTaskStore } from '../store/useTaskStore';

interface TaskExecutionCardProps {
  taskId: string;
  taskTitle: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  onRetry?: (taskId: string) => void;
}

export const TaskExecutionCard: React.FC<TaskExecutionCardProps> = ({
  taskId,
  taskTitle,
  status,
  onRetry,
}) => {
  const { pipelineStep, setActiveTask } = useTaskStore();

  const handleSelectTask = (): void => {
    setActiveTask(taskId);
  };

  return (
    <div className="p-4 border rounded-lg shadow-sm bg-gray-900 border-gray-800 text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold text-lg">{taskTitle}</h3>
        <span
          className={`px-2 py-1 text-xs font-bold rounded ${
            status === 'COMPLETED'
              ? 'bg-green-800 text-green-200'
              : status === 'FAILED'
              ? 'bg-red-800 text-red-200'
              : 'bg-blue-800 text-blue-200'
          }`}
        >
          {status}
        </span>
      </div>
      <p className="text-sm text-gray-400 mb-4">Task ID: {taskId}</p>
      <p className="text-xs text-indigo-400 mb-4">
        Active Pipeline Step: {pipelineStep} / 9
      </p>

      <div className="flex gap-2">
        <button
          onClick={handleSelectTask}
          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded transition-colors"
        >
          Inspect Pipeline
        </button>
        {status === 'FAILED' && onRetry && (
          <button
            onClick={() => onRetry(taskId)}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-medium rounded transition-colors"
          >
            Retry Execution
          </button>
        )}
      </div>
    </div>
  );
};
```

---

## 5. NAMING CONVENTIONS & CODE STYLE GUIDELINES

### 5.1 Universal Cross-Language Naming Matrix

| Code Element | Rust | Python | TypeScript / React | Database (SQL) |
| :--- | :--- | :--- | :--- | :--- |
| **Modules / Files** | `snake_case.rs` | `snake_case.py` | `camelCase.ts` / `PascalCase.tsx` | `snake_case` |
| **Classes / Types** | `PascalCase` | `PascalCase` | `PascalCase` | `snake_case` |
| **Functions / Methods** | `snake_case()` | `snake_case()` | `camelCase()` | N/A |
| **Variables / Fields** | `snake_case` | `snake_case` | `camelCase` | `snake_case` |
| **Constants** | `SCREAMING_SNAKE` | `SCREAMING_SNAKE` | `SCREAMING_SNAKE` | N/A |
| **Enums** | `PascalCase` | `PascalCase` | `PascalCase` | N/A |
| **Substrate Extrinsics** | `snake_case` | N/A | N/A | N/A |

### 5.2 File & Directory Naming Rules
- **Rust Files:** Lowercase `snake_case` (e.g., `dpos_staking.rs`, `chain_spec.rs`).
- **Python Modules:** Lowercase `snake_case` (e.g., `task_service.py`, `auth_middleware.py`).
- **TypeScript Files:** `camelCase.ts` for utilities and hooks (`useTaskStore.ts`); `PascalCase.tsx` for React components (`TaskExecutionCard.tsx`).
- **Directories:** Lowercase `kebab-case` or `snake_case` without spaces or special characters.

---

## 6. COMMENT STANDARDS & API DOCUMENTATION

### 6.1 Rustdoc Formatting Standards (`///`)
Public items in Rust must have `///` rustdoc comments explaining purpose, parameters, errors, and panic conditions:

```rust
/// Calculates the active staking reward for a validator.
///
/// # Arguments
/// * `validator` - Account ID of the target validator candidate.
/// * `era` - Epoch era index for reward calculation.
///
/// # Errors
/// Returns `Error::NotRegistered` if validator is not active.
pub fn calculate_reward(validator: &AccountId, era: u32) -> Result<Balance, Error> {
    // Logic implementation
}
```

### 6.2 Python Google-Style Docstring Format
All Python functions and class methods must use Google-style docstrings:

```python
def execute_pipeline_step(step_id: int, task_data: dict) -> bool:
    # Executes a single step within the 9-Step CTO Pipeline.
    # Args:
    #     step_id (int): Step number between 1 and 9.
    #     task_data (dict): Context parameters for task execution.
    # Returns:
    #     bool: True if step completed successfully, False otherwise.
    return True
```

### 6.3 JSDoc / TSDoc Standards
TypeScript utilities must include TSDoc annotations:

```typescript
/**
 * Formats a raw VRDX balance planck value into human-readable VRDX units.
 * @param plancks - Raw balance integer string (18 decimals)
 * @returns Formatted VRDX decimal string
 */
export function formatVrdxBalance(plancks: string): string {
    return (BigInt(plancks) / 10n**18n).toString();
}
```

---

## 7. UNIFIED ERROR HANDLING PATTERNS

### 7.1 Error Domain Mapping Matrix

| Layer | Native Exception Type | Standardized HTTP/RPC Code | Client Response Payload |
| :--- | :--- | :--- | :--- |
| **Substrate Runtime** | `DispatchError::Module` | RPC Error `-32603` | `{ code: 101, message: "InsufficientBalance" }` |
| **FastAPI Backend** | `HTTPException` | HTTP `400 Bad Request` | `{ "error": { "code": "INVALID_INPUT", ... } }` |
| **React Client** | `Error` boundary | UI Alert Modal | Toast Notification: "Operation Failed" |

### 7.2 Error Translation Example Across Layers
When a Substrate dispatchable fails, AegisOS translates the error before returning to React clients:

```python
# aegisos/app/services/error_translator.py
def translate_substrate_error(rpc_error: dict) -> dict:
    error_code = rpc_error.get("code", -32603)
    error_msg = rpc_error.get("message", "Unknown Substrate Exception")
    
    return {
        "error": {
            "code": "BLOCKCHAIN_RPC_ERROR",
            "message": f"Substrate call failed ({error_code}): {error_msg}",
            "timestamp_utc": datetime.utcnow().isoformat()
        }
    }
```

---

## 8. CODE REVIEW & VERIFICATION CHECKLISTS

### 8.1 Rust & Substrate Review Checklist
- [ ] Code formatted using `cargo fmt`.
- [ ] Zero clippy warnings (`cargo clippy -- -D warnings`).
- [ ] Zero unsafe blocks without explicit GPT-4o safety proofs.
- [ ] All storage keys use `Blake2_128Concat` or `Twox64Concat`.
- [ ] WASM runtime compiles under `no_std`.

### 8.2 Python Review Checklist
- [ ] All functions have strict type annotations.
- [ ] Code passes `mypy --strict` with zero errors.
- [ ] Code formatted with `black` and passes `flake8`.
- [ ] DB calls use async SQLAlchemy engine.
- [ ] Endpoint inputs validated via Pydantic v2 schemas.

### 8.3 TypeScript Review Checklist
- [ ] Zero `any` types used.
- [ ] Strict mode enabled with zero compiler errors.
- [ ] Components are functional and use hooks properly.
- [ ] ESLint completes with zero warnings.

---
*End of Governance Document 03 — Verdis Ecosystem Language & Coding Standards.*
