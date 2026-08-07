# VERDIS GOVERNANCE STANDARD 12: PERFORMANCE STANDARDS & BENCHMARKING

**Document ID:** GOV-STD-012  
**Version:** 1.0.0  
**Status:** PERMANENT / RATIFIED  
**Effective Date:** August 5, 2026  
**Target Scope:** Verdis Chain, AegisOS AI Stack, Developer Cloud, Applications, SDKs, Trust Layer  
**Enforcement:** Automated Benchmarking CI + Prometheus Monitoring + GPT-4o CTO Performance Audit  

---

## 1. EXECUTIVE SUMMARY & PURPOSE

The Verdis Ecosystem requires high-performance execution across all seven core products: Verdis Chain, AegisOS, Verdis Applications, Verdis Trust Layer, Verdis Developer Cloud, Verdis Marketplace, and the Verdis Developer Platform.

Because Substrate execution costs directly impact block completion times, consensus safety, and transaction fees (VRDX), performance is an architectural prerequisite rather than an afterthought. Unbounded execution paths, unindexed database queries, memory leaks, or sluggish web interactions degrade system integrity and user experience.

This document establishes the binding Performance Standards, Benchmarking Methodologies, Hardware Baselines, Profiling Protocols, Weight Formulas for all 6 custom pallets, Database Query Tuning, WebSockets Performance Rules, Memory Allocator Tuning, Automated CI Performance Gating, and Performance Budgets across the entire Verdis Ecosystem.

---

## 2. CORE PERFORMANCE METRICS & SLA TARGETS

### 2.1 Ecosystem Metric Overview Table

| Ecosystem Layer | Metric Description | Target Threshold | Hard Limit (Alert Level) | Measurement Method |
| :--- | :--- | :--- | :--- | :--- |
| **Verdis Chain** | Block Generation Interval | **6.0 seconds** | $>6.5$ seconds | Substrate Telemetry / BABE |
| **Verdis Chain** | Block Finality Time | **< 30.0 seconds** | $>45.0$ seconds | GRANDPA Finality Metric |
| **Verdis Chain** | Sustained Throughput (TPS) | **1,500 TPS** | $<1,000$ TPS | Synthetic Load Test |
| **Verdis Chain** | Peak Throughput (TPS) | **3,000 TPS** | $<2,000$ TPS | Stress Benchmarks |
| **Verdis Chain** | TX Gossip Propagation | **< 1.5 seconds** | $>3.0$ seconds | Libp2p Prometheus Target |
| **Verdis Chain** | RPC Method Response (121 RPCs)| **< 50 ms** | $>120$ ms | Substrate RPC Prometheus Target |
| **AegisOS API** | P50 Response Latency | **< 30 ms** | $>50$ ms | FastAPI Middleware Timers |
| **AegisOS API** | P95 Response Latency | **< 100 ms** | $>150$ ms | Prometheus `http_request_duration_seconds` |
| **AegisOS API** | P99 Response Latency | **< 200 ms** | $>350$ ms | Prometheus `http_request_duration_seconds` |
| **AegisOS API** | Backend Throughput | **> 2,000 req/sec** | $<1,200$ req/sec | Locust / K6 Benchmark |
| **AegisOS DB** | PostgreSQL Query Latency | **< 15 ms** | $>30$ ms | PgBouncer / PG Stat Statements |
| **AegisOS Redis**| Cache Read Latency | **< 2 ms** | $>5$ ms | Redis Info Memory / Command Stats |
| **React Applications**| Largest Contentful Paint (LCP)| **< 2.5 seconds** | $>4.0$ seconds | Lighthouse CI / Web Vitals |
| **React Applications**| First Input Delay (FID) | **< 100 ms** | $>300$ ms | Lighthouse CI / Web Vitals |
| **React Applications**| Cumulative Layout Shift (CLS)| **< 0.1** | $>0.25$ | Lighthouse CI / Web Vitals |
| **React Applications**| Time to First Byte (TTFB)| **< 800 ms** | $>1800$ ms | Lighthouse CI / Web Vitals |
| **React Applications**| Interaction to Next Paint (INP)| **< 200 ms** | $>500$ ms | Lighthouse CI / Web Vitals |
| **React Applications**| JS Initial Bundle Size | **< 250 KB (gzip)**| $>400$ KB (gzip) | Vite Bundle Analyzer |

---

## 3. SUBSTRATE BLOCKCHAIN PERFORMANCE STANDARDS

### 3.1 Block Time & Weight Budget Architecture
Verdis Chain operates on a strict **6.0-second block target** governed by BABE consensus and GRANDPA finality with 14 active validators.

* **Maximum Block Weight:** 2,000,000,000,000 ($2 	imes 10^{12}$) weight units per block (representing 2.0 seconds of maximum CPU execution time on standard reference hardware).
* **Consensus Reserve:** 25% ($5 	imes 10^{11}$ weight units) is permanently allocated for block authoring, BABE ticket verification, GRANDPA pre-votes, and system inherents.
* **Normal Extrinsic Weight Limit:** 75% ($1.5 	imes 10^{12}$ weight units) available for user extrinsics across the 6 custom pallets.

```
+-------------------------------------------------------------------------------+
|                    VERDIS 6-SECOND BLOCK TIME BUDGET ALLOCATION               |
+-------------------------------------------------------------------------------+
| [Extrinsic Computation: 1.5s max] [Consensus & Validation: 0.5s]              |
| [Network Block Propagation (libp2p): 2.0s] [Safety Margin Buffer: 2.0s]       |
+-------------------------------------------------------------------------------+
```

### 3.2 Weight Computation Formula & Storage IO Model
Substrate weight represents execution time ($1 	ext{ weight unit} = 1 	ext{ picosecond}$). Execution cost is calculated according to the canonical formula:

$$	ext{Weight}(x) = 	ext{BaseWeight} + \sum_{i} (N_i 	imes 	ext{WeightPerItem}_i) + (R 	imes 	ext{DbReadWeight}) + (W 	imes 	ext{DbWriteWeight})$$

Where:
* $	ext{DbReadWeight} = 25,000,000$ (25 µs per NVMe read operation).
* $	ext{DbWriteWeight} = 100,000,000$ (100 µs per NVMe write operation).
* $R$ = Number of storage reads performed by the extrinsic.
* $W$ = Number of storage writes performed by the extrinsic.

---

## 4. FULL PALLET BENCHMARKING CODE & WEIGHT FORMULAS FOR ALL 6 PALLETS

Every custom Substrate pallet in Verdis Chain MUST maintain benchmark files generated using Substrate's `frame-benchmarking` framework executed via `frame-omni-bencher`.

### 4.1 `pallet-dpos` Benchmark Specification
```rust
// verdis-chain/pallets/dpos/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn register_validator() {
        let caller: T::AccountId = account("validator", 0, 0);
        let amount: BalanceOf<T> = T::MinStake::get();
        T::Currency::make_free_balance_be(&caller, amount * 2u32.into());

        #[extrinsic_call]
        register_validator(RawOrigin::Signed(caller.clone()), amount);

        assert!(Validators::<T>::contains_key(&caller));
    }

    #[benchmark]
    fn delegate_stake(s: Linear<1, 100>) {
        let delegator: T::AccountId = account("delegator", 0, 0);
        let validator: T::AccountId = account("validator", 1, 0);
        let amount: BalanceOf<T> = 1000u32.into();

        T::Currency::make_free_balance_be(&delegator, amount * 10u32.into());
        Validators::<T>::insert(&validator, T::MinStake::get());

        for i in 0..s {
            let other: T::AccountId = account("other", i, 0);
            Delegations::<T>::insert(&other, &validator, amount);
        }

        #[extrinsic_call]
        delegate_stake(RawOrigin::Signed(delegator.clone()), validator.clone(), amount);

        assert_eq!(Delegations::<T>::get(&delegator, &validator), amount);
    }

    impl_benchmark_test_suite!(Dpos, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.2 `pallet-amm-dex` Benchmark Specification
```rust
// verdis-chain/pallets/amm-dex/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn swap_exact_tokens() {
        let caller: T::AccountId = account("trader", 0, 0);
        let asset_a: AssetIdOf<T> = 1u32.into();
        let asset_b: AssetIdOf<T> = 2u32.into();
        let amount_in: BalanceOf<T> = 10_000u32.into();

        Pools::<T>::insert((asset_a, asset_b), PoolInfo { reserve_a: 1_000_000, reserve_b: 1_000_000 });

        #[extrinsic_call]
        swap_exact_tokens(RawOrigin::Signed(caller), asset_a, asset_b, amount_in, 1u32.into());

        assert!(Events::<T>::get().len() > 0);
    }

    impl_benchmark_test_suite!(AmmDex, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.3 `pallet-eco` Benchmark Specification
```rust
// verdis-chain/pallets/eco/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn submit_eco_metric(m: Linear<1, 1024>) {
        let caller: T::AccountId = account("reporter", 0, 0);
        let metric_payload: Vec<u8> = vec![0u8; m as usize];

        #[extrinsic_call]
        submit_eco_metric(RawOrigin::Signed(caller.clone()), metric_payload.clone());

        assert!(EcoMetrics::<T>::contains_key(&caller));
    }

    impl_benchmark_test_suite!(Eco, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.4 `pallet-tokenomics` Benchmark Specification
```rust
// verdis-chain/pallets/tokenomics/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn execute_burn() {
        let caller: T::AccountId = account("burner", 0, 0);
        let amount: BalanceOf<T> = 5_000u32.into();

        #[extrinsic_call]
        execute_burn(RawOrigin::Signed(caller), amount);

        assert_eq!(TotalBurned::<T>::get(), amount);
    }

    impl_benchmark_test_suite!(Tokenomics, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.5 `pallet-vesting` Benchmark Specification
```rust
// verdis-chain/pallets/vesting/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn create_vesting_schedule() {
        let caller: T::AccountId = account("admin", 0, 0);
        let target: T::AccountId = account("beneficiary", 1, 0);
        let schedule = VestingSchedule { start: 1u32.into(), period: 100u32.into(), amount: 50_000u32.into() };

        #[extrinsic_call]
        create_vesting_schedule(RawOrigin::Signed(caller), target.clone(), schedule);

        assert!(VestingSchedules::<T>::contains_key(&target));
    }

    impl_benchmark_test_suite!(Vesting, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.6 `pallet-storage` Benchmark Specification
```rust
// verdis-chain/pallets/storage/src/benchmarking.rs
#![cfg(feature = "runtime-benchmarks")]

use super::*;
use frame_benchmarking::v2::*;
use frame_system::RawOrigin;

#[benchmarks]
mod benchmarks {
    use super::*;

    #[benchmark]
    fn anchor_ipfs_cid(k: Linear<1, 64>) {
        let caller: T::AccountId = account("uploader", 0, 0);
        let cid: Vec<u8> = vec![0x51; k as usize];

        #[extrinsic_call]
        anchor_ipfs_cid(RawOrigin::Signed(caller.clone()), cid.clone());

        assert!(AnchoredCids::<T>::contains_key(&caller));
    }

    impl_benchmark_test_suite!(Storage, crate::mock::new_test_ext(), crate::mock::TestRuntime);
}
```

### 4.7 Reference Benchmarking Hardware Baseline
All benchmark weight outputs committed to git MUST be generated on reference hardware:

```
Processor:   AMD EPYC 7763 64-Core Processor (Dedicated 8 vCPUs assigned)
RAM:         64 GB DDR4 ECC Registered 3200MHz
Disk:        2x 1TB NVMe PCIe Gen4 SSD (RAID-1 configuration, >7,000 MB/s seq read)
OS:          Ubuntu 22.04 LTS (Kernel 5.15 LTS, performance governor forced)
Toolchain:   rustc 1.78.0-nightly, compiled with `cargo build --release --features runtime-benchmarks`
```

---

## 5. SUBSTRATE RPC BENCHMARKING (121 RPC METHODS)

Verdis Chain exposes 121 RPC methods across chain state, transaction pool, consensus, and custom pallet endpoints.

### 5.1 RPC Performance SLA Standards
- **Standard State Reads (`state_getStorage`):** P99 Latency $< 20	ext{ ms}$.
- **Extrinsic Submission (`author_submitAndWatchExtrinsic`):** P99 Latency $< 50	ext{ ms}$.
- **Complex Pallet Query RPCs:** P99 Latency $< 100	ext{ ms}$.
- **Max WebSockets Connections per Node:** 10,000 concurrent client subscriptions.

### 5.2 RPC Load Benchmarking Script Example (`k6` / WebSocket)
```javascript
// bench_rpc.js - K6 performance script for 121 RPC methods
import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 500 },
    { duration: '1m', target: 1000 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const url = 'ws://127.0.0.1:9944';
  const params = { tags: { my_tag: 'verdis_rpc' } };

  const res = ws.connect(url, params, function (socket) {
    socket.on('open', function () {
      socket.send(JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'chain_getHeader',
        params: []
      }));
    });

    socket.on('message', function (data) {
      const msg = JSON.parse(data);
      check(msg, { 'RPC response is 2.0': (r) => r.jsonrpc === '2.0' && r.id === 1 });
      socket.close();
    });
  });

  check(res, { 'Connected successfully': (r) => r && r.status === 101 });
}
```

---

## 6. FASTAPI & BACKEND API PERFORMANCE STANDARDS

The AegisOS FastAPI backend services interact with PostgreSQL, Redis, and Substrate RPC nodes.

### 6.1 Database Query Optimization & Indexing Rules
1. **Zero Unindexed Sequential Scans:** Every query executed in FastAPI must hit a B-Tree or GIN index. Sequential scans on tables with $>1,000$ rows trigger immediate automated CI test failure.
2. **Prepared Statements & Async Pooling:** All queries must use SQLAlchemy 2.0 `select()` constructs with pre-compiled prepared statements.
3. **PgBouncer Pooling:** Connection pooling MUST use PgBouncer in transaction-pooling mode.

```ini
# pgbouncer.ini configuration standard
[databases]
verdis_db = host=127.0.0.1 port=5432 dbname=verdis_prod

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 5000
default_pool_size = 30
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 5
```

---

## 7. FRONTEND & CLIENT PERFORMANCE STANDARDS

All web frontends in the Verdis Ecosystem (Developer Dashboard, Explorer, Wallet, Portal) are built with React 18, Vite, and TailwindCSS.

### 7.1 Web Worker Offloading for SR25519 Cryptography
To keep UI frame rates strictly at **60 FPS** during heavy keypair derivation or digital signature verification, cryptographic tasks MUST be offloaded to Web Workers:

```typescript
// aegisos/frontend/src/workers/crypto.worker.ts
import { cryptoWaitReady, sr25519Sign } from '@polkadot/util-crypto';

self.onmessage = async (e: MessageEvent) => {
  const { message, secretKey } = e.data;
  await cryptoWaitReady();
  const signature = sr25519Sign(message, secretKey);
  self.postMessage({ signature });
};
```

---

## 8. PROFILING TOOLS & METHODOLOGY

System performance must be continually audited using standardized profiling tools across all layers:

```
+---------------------------------------------------------------------------------+
|                       VERDIS PROFILING TOOL STACK                               |
+---------------------------------------------------------------------------------+
| System Layer       | Tool Name               | Primary Target Analysis          |
+--------------------+-------------------------+----------------------------------+
| Substrate Runtime  | cargo flamegraph / perf | CPU hotspots, unneeded allocs    |
| Rust Heap Memory   | Valgrind / Heaptrack    | Memory leaks, heap fragmentation |
| Python FastAPI     | py-spy / cProfile       | Async event loop blocking, GIL   |
| Database Queries   | EXPLAIN ANALYZE / pg_stat| Slow queries, missing indexes   |
| Frontend React UI  | Chrome DevTools / LH CI | JS main thread, DOM re-renders   |
+---------------------------------------------------------------------------------+
```

---

## 9. MEMORY ALLOCATOR & RUNTIME GC TUNING

### 9.1 Rust `jemalloc` Configuration for Substrate Node
All Substrate node binaries in production MUST link against `tikv-jemallocator` to prevent fragmentation during continuous memory-intensive state trie reads:

```rust
// verdis-node/src/main.rs
#[global_allocator]
static GLOBAL: tikv_jemallocator::Jemalloc = tikv_jemallocator::Jemalloc;
```

### 9.2 Python Async Garbage Collection Optimization
FastAPI workers running in production containers tune garbage collection thresholds to minimize event loop stalls:

```python
# app/main.py GC tuning
import gc

# Tune GC thresholds (gen0, gen1, gen2)
gc.set_threshold(700, 10, 10)
```

---

## 10. AUTOMATED PERFORMANCE REGRESSION TESTING IN CI

Automated performance benchmarks prevent regressions prior to PR merges.

```yaml
# .github/workflows/performance-benchmark.yml
name: Verdis Performance Benchmark CI

on:
  pull_request:
    branches: [ main ]

jobs:
  benchmark-pallets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Benchmarks
        run: cargo build --release --features runtime-benchmarks
      - name: Run Pallet DPOS Benchmark
        run: |
          ./target/release/verdis-node benchmark pallet             --chain=dev --pallet=pallet_dpos --extrinsic="*"             --steps=10 --repeat=5 --execution=wasm
```

---

## 11. GPT-4O PERFORMANCE AUDIT GATE

GPT-4o audits every pull request for performance regressions prior to merge approval:

```
[ ] 1. Are all storage reads/writes in new extrinsics accounted for in benchmark weights?
[ ] 2. Are all database queries covered by explicit composite B-Tree or GIN indexes?
[ ] 3. Does any new React component introduce un-memoized heavy calculations on render?
[ ] 4. Are WebSocket event listeners cleaned up on component unmount?
[ ] 5. Does the PR increase the JS main bundle size by more than 5 KB?
```

---

## 12. PRODUCT PERFORMANCE BUDGETS (ALL 7 PRODUCTS)

1. **Verdis Chain:** Max 2.0s block weight utilization per 6s block; finality <30s; gossiping propagation <1.5s.
2. **AegisOS AI Stack:** Agent inference orchestration response overhead <=1.2s; API P99 <=200ms.
3. **Verdis Applications:** Initial interactive render (LCP) <=1.8s; FID <=100ms; 60 FPS page scrolling.
4. **Verdis Trust Layer:** Signature generation & verification <=50ms per credential.
5. **Verdis Developer Cloud:** Container deployment trigger-to-active latency <=15 seconds.
6. **Verdis Marketplace:** Extension schema rendering <=100ms; search query response <=80ms.
7. **Verdis Developer Platform:** RPC response time <=50ms for cached calls, <=150ms for state reads across 121 RPC methods.


---

## 13. PROMETHEUS PERFORMANCE ALERTING THRESHOLDS

The Verdis Prometheus stack monitors system performance in real-time and triggers alerts if performance degradations persist:

```yaml
# prometheus_performance_alerts.yml
groups:
  - name: verdis_performance_alerts
    rules:
      - alert: HighBlockTime
        expr: substrate_block_time_seconds > 6.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Block production time exceeded 6.5s target"

      - alert: APIHighLatencyP99
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.200
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "FastAPI P99 response latency exceeds 200ms threshold"

      - alert: PostgresSlowQueries
        expr: rate(pg_stat_activity_max_tx_duration{state="active"}[5m]) > 15
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL active transaction duration exceeding 15ms limit"
```

---

## 14. DEVELOPER PERFORMANCE PRE-FLIGHT CHECKLIST

Before opening a pull request, developers must execute this performance verification checklist:

- [ ] Run pallet benchmarks locally and verify generated `weights.rs` matches actual storage reads/writes.
- [ ] Verify zero unindexed queries in SQLAlchemy models using `EXPLAIN ANALYZE`.
- [ ] Confirm frontend Vite bundle analyzer reports JS main bundle size $< 250	ext{ KB}$.
- [ ] Audit React render trees with Chrome DevTools Performance tab to ensure 60 FPS UI rendering.
- [ ] Run `cargo flamegraph` or `py-spy` if adding new intensive cryptographic or state-processing loops.
- [ ] Submit PR diff to GPT-4o for automated performance review sign-off.

---
**END OF GOVERNANCE STANDARD 12**
