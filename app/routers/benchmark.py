from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Benchmark, BenchmarkResult, BenchmarkStatus, SubscriptionTier
from app.schemas import BenchmarkRequest, BenchmarkResponse, ModelResult
from app.auth import get_current_active_user
from app.tasks import run_benchmark
from app.config import settings

router = APIRouter()


@router.post("/benchmark", response_model=BenchmarkResponse, status_code=status.HTTP_202_ACCEPTED)
def create_benchmark(
    request: BenchmarkRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check rate limits
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    monthly_usage = db.query(func.count(Benchmark.id)).filter(
        Benchmark.user_id == current_user.id,
        extract('month', Benchmark.created_at) == current_month,
        extract('year', Benchmark.created_at) == current_year
    ).scalar()
    
    # Determine limit based on tier
    if current_user.subscription_tier == SubscriptionTier.FREE:
        limit = settings.FREE_TIER_MONTHLY_LIMIT
    elif current_user.subscription_tier == SubscriptionTier.PRO:
        limit = settings.PRO_TIER_MONTHLY_LIMIT
    else:  # TEAM
        limit = settings.TEAM_TIER_MONTHLY_LIMIT
    
    if monthly_usage >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly limit of {limit} benchmarks reached. Upgrade your plan."
        )
    
    # Create benchmark record
    benchmark_id = f"bm_{uuid.uuid4().hex[:12]}"
    new_benchmark = Benchmark(
        benchmark_id=benchmark_id,
        user_id=current_user.id,
        task=request.task,
        expected_output=request.expected_output,
        test_cases=[tc.dict() for tc in request.test_cases] if request.test_cases else None,
        category=request.category,
        status=BenchmarkStatus.PENDING
    )
    db.add(new_benchmark)
    db.commit()
    db.refresh(new_benchmark)
    
    # Queue async task
    run_benchmark.delay(benchmark_id)
    
    return {
        "benchmark_id": benchmark_id,
        "status": BenchmarkStatus.PENDING,
        "results": [],
        "created_at": new_benchmark.created_at
    }


@router.get("/benchmark/{benchmark_id}", response_model=BenchmarkResponse)
def get_benchmark(
    benchmark_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    benchmark = db.query(Benchmark).filter(
        Benchmark.benchmark_id == benchmark_id,
        Benchmark.user_id == current_user.id
    ).first()
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    # Get results
    results = db.query(BenchmarkResult).filter(
        BenchmarkResult.benchmark_id == benchmark.id
    ).all()
    
    model_results = [
        ModelResult(
            model=r.model_name,
            accuracy=r.accuracy or 0.0,
            cost_usd=r.cost_usd or 0.0,
            latency_ms=r.latency_ms or 0,
            passed_tests=r.passed_tests,
            total_tests=r.total_tests,
            confidence_score=r.confidence_score or 0.0,
            model_output=r.model_output,
            error_message=r.error_message
        )
        for r in results
    ]
    
    # Determine winner (best accuracy with lowest cost)
    winner = None
    cost_savings_pct = None
    
    if model_results:
        sorted_by_accuracy = sorted(model_results, key=lambda x: x.accuracy, reverse=True)
        if sorted_by_accuracy:
            best_accuracy = sorted_by_accuracy[0].accuracy
            candidates = [r for r in model_results if r.accuracy >= best_accuracy * 0.95]  # Within 5%
            if candidates:
                winner_result = min(candidates, key=lambda x: x.cost_usd)
                winner = winner_result.model
                
                # Calculate savings vs most expensive option
                most_expensive = max(model_results, key=lambda x: x.cost_usd)
                if most_expensive.cost_usd > 0:
                    cost_savings_pct = round(
                        ((most_expensive.cost_usd - winner_result.cost_usd) / most_expensive.cost_usd) * 100,
                        1
                    )
    
    return {
        "benchmark_id": benchmark_id,
        "status": benchmark.status,
        "results": model_results,
        "winner": winner,
        "cost_savings_pct": cost_savings_pct,
        "created_at": benchmark.created_at,
        "completed_at": benchmark.completed_at
    }
