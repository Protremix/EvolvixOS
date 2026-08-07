# VERDIS GOVERNANCE STANDARD 11: TESTING STANDARDS & QUALITY ASSURANCE

**Document ID:** GOV-STD-011  
**Version:** 1.0.0  
**Status:** PERMANENT / RATIFIED  
**Effective Date:** August 5, 2026  
**Target Scope:** Verdis Chain, AegisOS AI Stack, Developer Cloud, Applications, SDKs, Trust Layer  
**Enforcement:** Automated CI Pipeline + GPT-4o Permanent CTO Review  

---

## 1. EXECUTIVE SUMMARY & PURPOSE

The Verdis Ecosystem operates as a unified, mission-critical decentralized platform encompassing a Substrate Layer-1 blockchain (14 consensus validators, 121 RPC methods, chain spec v11, 6s block times), an AI Engineering Operating System (AegisOS), a high-throughput FastAPI backend, a React enterprise frontend, and containerized Docker infrastructure monitored by Prometheus.

Given the irreversible nature of state transitions on the Verdis Layer-1 blockchain and the high financial and operational security requirements across the ecosystem, testing is not an optional phase—it is a continuous, automated, and strictly governed engineering discipline.

This document establishes the binding, ecosystem-wide Testing Standards and Quality Assurance Governance Framework. Every pull request, commit, pallet modification, backend endpoint, and frontend component must strictly comply with these standards. Non-compliant code cannot be merged, released, or deployed into any environment.

---

## 2. CORE TESTING PHILOSOPHY & QUALITY GATE SYSTEM

### 2.1 The Verdis Testing Axioms
1. **Zero Trust in Unchecked Code:** No line of code is considered functional until verified by automated tests.
2. **Determinism Above All:** All unit, integration, and property tests must be 100% deterministic. Flaky tests are treated as P1 defects and must be quarantined or fixed immediately.
3. **Substrate State Safety:** Every custom pallet must prove zero state bloat, bounded execution weight, and complete protection against unauthorized storage mutations and integer overflows.
4. **Defense in Depth:** Software correctness is enforced at four distinct gates: Local pre-commit, Automated CI matrix, GPT-4o Architectural/Security audit, and Pre-release staging tests.

### 2.2 Quality Gate Architecture Matrix

| Gate Level | Execution Context | Trigger Event | Target Artifacts | Mandatory Threshold | Action on Failure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gate 1: Pre-Commit** | Developer Workstation | `git commit` hook | Rust, Python, TS code | Formatting (`clippy`, `black`, `eslint`), local unit tests | Block Commit |
| **Gate 2: Continuous Integration** | GitHub Actions CI | `git push` / PR Creation | Entire Workspace | 100% test pass rate, $\ge$80% code coverage across workspace | Block PR Merge |
| **Gate 3: AI CTO Audit** | Automated GPT-4o API | CI Completion | Diff, Test Output, AST | Zero Critical/High vulnerabilities, explicit test suite approval | Reject PR |
| **Gate 4: Staging Deployment** | Docker Staging Env | Post-Merge | Containers, RPC, Nodes | E2E integration pass, zero telemetry errors for 15 mins | Block Staging Release |

---

## 3. SCOPE & SYSTEM COMPONENTS UNDER TEST

The Verdis Ecosystem testing suite covers five primary technology layers:

```
+-----------------------------------------------------------------------------------+
|                            VERDIS TESTING ARCHITECTURE                            |
+-----------------------------------------------------------------------------------+
| 1. Substrate Chain (Rust)      | Pallets (DPOS, AMM, Eco, Tokenomics, Vesting,   |
|                                | Storage), Runtime, Node, Benchmarks, RPC Methods |
+-----------------------------------------------------------------------------------+
| 2. AegisOS Backend (Python)    | FastAPI REST APIs, Async Workers, SQLAlchemy,    |
|                                | Substrate RPC Client, Websocket Hub, Auth        |
+-----------------------------------------------------------------------------------+
| 3. Client Frontend (TypeScript)| React Dashboard, Developer Portal, Explorer,     |
|                                | Wallet, Hooks, State Stores, PolkadotJS Specs   |
+-----------------------------------------------------------------------------------+
| 4. Infrastructure (Docker/K8s) | Container Health, Prometheus Exporters (21 targets)|
|                                | Systemd Watchdogs, Log Collectors, Failover     |
+-----------------------------------------------------------------------------------+
| 5. Security & Cryptography     | SR25519 Keys, ED25519 Signatures, Smart Contracts |
|                                | WASM Sandbox Isolation, Reentrancy Protection    |
+-----------------------------------------------------------------------------------+
```

---

## 4. RUST & SUBSTRATE TESTING STANDARDS

Rust powers the core Verdis Chain node, runtime, and the 6 custom pallets:
1. `pallet-dpos` (Delegated Proof-of-Stake & Validator Staking)
2. `pallet-amm-dex` (Automated Market Maker & Liquidity Pools)
3. `pallet-eco` (ESG Tracking, Carbon Offsets, Sustainability Metrics)
4. `pallet-tokenomics` (VRDX Inflation, Burning, Treasury Allocation)
5. `pallet-vesting` (Linear & Schedule Token Lockups)
6. `pallet-storage` (Decentralized Storage Proofs & IPFS Anchoring)

### 4.1 Test Organization & File Hierarchy
Every custom Substrate pallet MUST maintain a dual testing structure:
* **Inline Unit Tests (`src/lib.rs`):** Private function tests using `#[cfg(test)] mod tests`.
* **Integration & Mock Runtime Tests (`src/mock.rs` & `src/tests.rs`):** Comprehensive pallet extrinsic tests running against a fully instantiated mock Substrate runtime.

```
verdis-chain/pallets/pallet-dpos/
├── Cargo.toml
└── src/
    ├── bench.rs
    ├── lib.rs
    ├── mock.rs
    ├── tests.rs
    └── weights.rs
```

### 4.2 Mock Runtime Construction (`mock.rs`)
The mock runtime must configure `frame_system` and all dependent pallets with explicit, mock configuration types. No real cryptographic hardware signatures or production durations should delay unit execution.

```rust
// verdis-chain/pallets/pallet-dpos/src/mock.rs
use crate as pallet_dpos;
use frame_support::{
    derive_impl, parameter_types,
    traits::{ConstU128, ConstU32, ConstU64},
};
use sp_core::H256;
use sp_runtime::{
    traits::{BlakeTwo256, IdentityLookup},
    BuildStorage,
};

type Block = frame_system::mocking::MockBlock<TestRuntime>;

frame_support::construct_runtime!(
    pub enum TestRuntime {
        System: frame_system,
        Balances: pallet_balances,
        Dpos: pallet_dpos,
    }
);

#[derive_impl(frame_system::config_preludes::TestDefaultConfig)]
impl frame_system::Config for TestRuntime {
    type BaseCallFilter = frame_support::traits::Everything;
    type BlockWeights = ();
    type BlockLength = ();
    type DbWeight = ();
    type RuntimeOrigin = RuntimeOrigin;
    type RuntimeCall = RuntimeCall;
    type Nonce = u64;
    type Hash = H256;
    type Hashing = BlakeTwo256;
    type AccountId = u64;
    type Lookup = IdentityLookup<Self::AccountId>;
    type Block = Block;
    type RuntimeEvent = RuntimeEvent;
    type BlockHashCount = ConstU64<250>;
    type Version = ();
    type PalletInfo = PalletInfo;
    type AccountData = pallet_balances::AccountData<u128>;
    type OnNewAccount = ();
    type OnKilledAccount = ();
    type SystemWeightInfo = ();
    type SS58Prefix = ();
    type OnSetCode = ();
    type MaxConsumers = ConstU32<16>;
}

impl pallet_balances::Config for TestRuntime {
    type MaxLocks = ConstU32<50>;
    type MaxReserves = ();
    type ReserveIdentifier = [u8; 8];
    type Balance = u128;
    type RuntimeEvent = RuntimeEvent;
    type DustRemoval = ();
    type ExistentialDeposit = ConstU128<500>;
    type AccountStore = System;
    type WeightInfo = ();
    type FreezeIdentifier = ();
    type MaxFreezes = ();
    type RuntimeHoldReason = ();
    type RuntimeFreezeReason = ();
}

parameter_types! {
    pub const MinValidatorStake: u128 = 10_000;
    pub const MaxValidators: u32 = 14;
}

impl pallet_dpos::Config for TestRuntime {
    type RuntimeEvent = RuntimeEvent;
    type Currency = Balances;
    type MinStake = MinValidatorStake;
    type MaxValidators = MaxValidators;
    type WeightInfo = ();
}

pub fn new_test_ext() -> sp_io::TestExternalities {
    let mut t = frame_system::GenesisConfig::<TestRuntime>::default()
        .build_storage()
        .unwrap();

    pallet_balances::GenesisConfig::<TestRuntime> {
        balances: vec![
            (1, 100_000_000),
            (2, 50_000_000),
            (3, 10_000),
        ],
    }
    .assimilate_storage(&mut t)
    .unwrap();

    let mut ext = sp_io::TestExternalities::new(t);
    ext.execute_with(|| System::set_block_number(1));
    ext
}
```

### 4.3 Extrinsic Execution & Assertion Standards
Every test in `tests.rs` MUST test both successful paths (happy path) and failure modes (error dispatch), verifying storage mutations and event emissions.

```rust
// verdis-chain/pallets/pallet-dpos/src/tests.rs
use crate::{mock::*, Error, Event};
use frame_support::{assert_noop, assert_ok};

#[test]
fn test_register_validator_success_emits_event_and_updates_storage() {
    new_test_ext().execute_with(|| {
        // Arrange
        let account_id = 1;
        let stake_amount = 20_000;

        // Act
        assert_ok!(Dpos::register_validator(
            RuntimeOrigin::signed(account_id),
            stake_amount
        ));

        // Assert Storage
        assert_eq!(Dpos::validators(account_id), Some(stake_amount));
        assert_eq!(Dpos::total_staked(), stake_amount);

        // Assert Event Emission
        System::assert_has_event(
            Event::ValidatorRegistered {
                validator: account_id,
                stake: stake_amount,
            }
            .into(),
        );
    });
}

#[test]
fn test_register_validator_fails_if_insufficient_stake() {
    new_test_ext().execute_with(|| {
        // Arrange
        let account_id = 1;
        let low_stake = 5_000; // Below MinStake (10,000)

        // Act & Assert
        assert_noop!(
            Dpos::register_validator(RuntimeOrigin::signed(account_id), low_stake),
            Error::<TestRuntime>::StakeTooLow
        );
    });
}

#[test]
fn test_register_validator_fails_for_unsigned_origin() {
    new_test_ext().execute_with(|| {
        assert_noop!(
            Dpos::register_validator(RuntimeOrigin::none(), 20_000),
            sp_runtime::Traits::BadOrigin
        );
    });
}
```

### 4.4 Mandatory Rust Testing Commands & Rules
* **Workspace Testing Command:**
  ```bash
  cargo test --release --workspace --all-targets -- --nocapture
  ```
* **Pallet Isolation Command:**
  ```bash
  cargo test -p pallet-dpos --lib -- --test-threads=4
  ```
* **Clippy Lint Enforcement:**
  ```bash
  cargo clippy --workspace --all-targets -- -D warnings
  ```
* **Benchmarking Compile Check:**
  ```bash
  cargo check --features runtime-benchmarks --workspace
  ```

---

## 5. PYTHON & FASTAPI BACKEND TESTING STANDARDS

AegisOS and the Verdis Developer Platform API backend are built with FastAPI, SQLAlchemy 2.0 (async), and Pytest.

### 5.1 Backend Test Hierarchy
```
aegisos/backend/tests/
├── conftest.py              # Global fixtures, DB engine, HTTP client
├── unit/
│   ├── test_auth.py         # JWT parsing, password hashing
│   ├── test_services.py     # Business logic modules
│   └── test_validators.py   # Pydantic schema validations
├── integration/
│   ├── test_rpc_client.py   # Substrate WS RPC mock integration
│   └── test_api_routes.py   # FastAPI HTTP endpoints
└── e2e/
    └── test_workflow.py     # Full AI engineering pipeline test
```

### 5.2 Pytest Configuration & Fixture Setup (`conftest.py`)
All backend tests MUST run in an isolated async environment utilizing an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`).

```python
# aegisos/backend/tests/conftest.py
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.core.security import create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token(data={"sub": "test_developer_01", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}
```

### 5.3 FastAPI Endpoint Testing (`test_api_routes.py`)
Tests must verify HTTP status codes, response payloads, non-authenticated rejection, and database updates.

```python
# aegisos/backend/tests/integration/test_api_routes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_chain_status_returns_200_and_valid_payload(client: AsyncClient):
    response = await client.get("/api/v1/chain/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["active_validators"] == 14
    assert data["chain_spec"] == "v11"
    assert "block_height" in data

@pytest.mark.asyncio
async def test_submit_transaction_unauthorized_fails_401(client: AsyncClient):
    response = await client.post("/api/v1/chain/submit", json={"extrinsic": "0x1234"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_project_authorized_creates_record(client: AsyncClient, auth_headers: dict):
    payload = {
        "name": "Verdis DeFi Adapter",
        "description": "Cross-chain liquidity bridge wrapper",
        "target_pallet": "pallet-amm-dex"
    }
    response = await client.post("/api/v1/projects/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == payload["name"]
    assert "id" in res_data
```

### 5.4 Mandatory Python Execution Commands
```bash
# Run pytest with 80% minimum coverage enforcement
pytest -v --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80

# Run linting and type checks
black --check app tests
flake8 app tests
mypy app
```

---

## 6. TYPESCRIPT & FRONTEND TESTING STANDARDS

The Verdis UI applications (Developer Dashboard, Wallet, Explorer, Portal) are built on React, Vite, TailwindCSS, and PolkadotJS API extensions.

### 6.1 TypeScript Testing Stack
* **Test Runner:** `vitest` (fast, native ESM support)
* **Component Testing:** `@testing-library/react` and `@testing-library/user-event`
* **Mock Service Worker:** `msw` for network REST and WebSocket mocking

### 6.2 Component & Custom Hook Unit Test
Frontend tests must mock wallet providers, network latency, and test dynamic UI state transitions.

```typescript
// aegisos/frontend/src/components/__tests__/ValidatorCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ValidatorCard } from '../ValidatorCard';

const mockValidator = {
  address: '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY',
  name: 'Verdis Genesis Validator 01',
  stake: '1,500,000 VRDX',
  status: 'Active' as const,
  blocksProduced: 142050,
};

describe('ValidatorCard Component', () => {
  it('renders validator metadata correctly', () => {
    render(<ValidatorCard validator={mockValidator} onSelect={() => {}} />);

    expect(screen.getByText('Verdis Genesis Validator 01')).toBeInTheDocument();
    expect(screen.getByText('1,500,000 VRDX')).toBeInTheDocument();
    expect(screen.getByText('Active')).toHaveClass('bg-green-500/10');
  });

  it('triggers onSelect callback when clicked', async () => {
    const handleSelect = vi.fn();
    render(<ValidatorCard validator={mockValidator} onSelect={handleSelect} />);

    const card = screen.getByRole('button', { name: /select validator/i });
    await fireEvent.click(card);

    expect(handleSelect).toHaveBeenCalledTimes(1);
    expect(handleSelect).toHaveBeenCalledWith('5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY');
  });
});
```

### 6.3 Vitest Commands
```bash
# Execute Vitest with coverage
vitest run --coverage

# Vitest UI interactive mode
vitest --ui
```

---

## 7. COVERAGE REQUIREMENTS & STRICT ENFORCEMENT

### 7.1 Mandatory Coverage Metrics Table

| Language / Stack | Primary Tool | Line Coverage Min | Branch Coverage Min | Function Coverage Min |
| :--- | :--- | :--- | :--- | :--- |
| **Rust / Substrate** | `cargo-tarpaulin` | **80.0%** | **75.0%** | **85.0%** |
| **Python / FastAPI** | `pytest-cov` | **80.0%** | **80.0%** | **85.0%** |
| **TypeScript / React**| `vitest --coverage` | **80.0%** | **75.0%** | **80.0%** |

### 7.2 Strict Coverage Rules
1. **New Code Rule:** Every pull request introducing new lines of code must maintain or increase the total repository coverage percentage, and new files MUST individually meet or exceed 80% coverage.
2. **Exemption Waiver Process:** Exemptions from coverage requirements (e.g. autogenerated RPC bindings, auto-generated migration code) are ONLY permitted via an explicit inline comment flag and formal approval from GPT-4o:
   * Rust: `#[cfg_attr(test, mutate_exemption)]`
   * Python: `# pragma: no cover`
   * TypeScript: `/* v8 ignore start */`

---

## 8. CI/CD INTEGRATION (GITHUB ACTIONS)

The automated testing pipeline runs on every push and pull request.

```yaml
# .github/workflows/testing-pipeline.yml
name: Verdis Ecosystem Test & Quality Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  rust-chain-tests:
    name: Substrate Chain Tests & Benchmarks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Rust Toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - name: Cache Rust Dependencies
        uses: Swatinem/rust-cache@v2
      - name: Cargo Format Check
        run: cargo fmt --all -- --check
      - name: Cargo Clippy Check
        run: cargo clippy --workspace --all-targets -- -D warnings
      - name: Run Substrate Unit & Integration Tests
        run: cargo test --release --workspace --all-targets
      - name: Verify Benchmark Compilation
        run: cargo check --features runtime-benchmarks --workspace

  python-backend-tests:
    name: FastAPI Backend Pytest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r aegisos/backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx
      - name: Execute Pytest Suite with Coverage
        run: |
          cd aegisos/backend
          pytest -v --cov=app --cov-report=xml --cov-fail-under=80

  typescript-frontend-tests:
    name: Frontend React Vitest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Frontend Dependencies
        run: |
          cd aegisos/frontend
          npm ci
      - name: Run Vitest Suite
        run: |
          cd aegisos/frontend
          npx vitest run --coverage
```

---

## 9. GPT-4O PERMANENT CTO TEST REVIEW PROTOCOL

In accordance with the Verdis Constitution, GPT-4o serves as the permanent CTO and Code Reviewer.

### 9.1 Review Trigger & Scope
Before any PR merge, the test logs, diff, and coverage report are evaluated by GPT-4o.

### 9.2 Audit Checklist Executed by GPT-4o
```
[ ] 1. Do tests cover all edge cases (zero amounts, max balances, overflow limits)?
[ ] 2. Are extrinsic failure paths tested using assert_noop! with explicit errors?
[ ] 3. Are all state changes accompanied by appropriate Substrate event verification?
[ ] 4. Are Python async database calls executed inside isolated test transactions?
[ ] 5. Does TypeScript component testing simulate actual DOM interactions and ARIA roles?
[ ] 6. Does overall workspace code coverage strictly satisfy the >= 80% threshold?
[ ] 7. Are there any flaky tests or non-deterministic time delays (e.g. sleep calls)?
```

---

## 10. APPENDIX & TEST VERIFICATION CHECKLIST

Developers must run this local pre-flight verification checklist prior to submitting a PR:

- [ ] `cargo fmt --all -- --check` passes cleanly.
- [ ] `cargo clippy --workspace --all-targets -- -D warnings` reports 0 warnings.
- [ ] `cargo test --release --workspace` executes with 100% pass rate.
- [ ] Pytest suite achieves $\ge$80% coverage on `aegisos/backend`.
- [ ] Vitest suite passes without DOM errors on `aegisos/frontend`.
- [ ] Docker container build tests succeed (`docker compose config`).
- [ ] GPT-4o review approval confirmed.

---
**END OF GOVERNANCE STANDARD 11**
