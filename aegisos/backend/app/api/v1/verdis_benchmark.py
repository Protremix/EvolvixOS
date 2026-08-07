"""API for Verdis Benchmarking — Phase 16."""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.verdis_benchmark import (
    get_benchmark_service, get_benchmark_results, add_benchmark_result,
)

router = APIRouter(prefix="/verdis-benchmark", tags=["verdis-benchmark"])


@router.post("/rpc-latency")
async def run_rpc_latency(
    iterations: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Run RPC latency benchmark."""
    result = get_benchmark_service().run_rpc_latency_benchmark(iterations)
    add_benchmark_result(result)
    return result.to_dict()


@router.post("/validator-score")
async def run_validator_score(current_user: User = Depends(get_current_active_user)):
    """Run validator scoring benchmark."""
    result = get_benchmark_service().run_validator_benchmark()
    add_benchmark_result(result)
    return result.to_dict()


@router.post("/block-time")
async def run_block_time(
    samples: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """Run block time benchmark (takes ~20s for 10 samples)."""
    result = get_benchmark_service().run_block_time_benchmark(samples)
    add_benchmark_result(result)
    return result.to_dict()


@router.post("/all")
async def run_all_benchmarks(current_user: User = Depends(get_current_active_user)):
    """Run all benchmarks (excludes block time for speed)."""
    results = get_benchmark_service().run_all_benchmarks()
    for r in results:
        add_benchmark_result(r)
    return [r.to_dict() for r in results]


@router.get("/results")
async def get_results(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """Get benchmark results history."""
    return [r.to_dict() for r in get_benchmark_results()[-limit:]]
