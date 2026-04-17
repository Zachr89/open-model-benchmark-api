from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import BenchmarkResult, Benchmark
from app.schemas import LeaderboardEntry

router = APIRouter()


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(category: str = None, db: Session = Depends(get_db)):
    """Get model performance leaderboard, optionally filtered by category"""
    
    query = db.query(
        BenchmarkResult.model_name,
        Benchmark.category,
        func.avg(BenchmarkResult.accuracy).label("avg_accuracy"),
        func.avg(BenchmarkResult.cost_usd).label("avg_cost_usd"),
        func.avg(BenchmarkResult.latency_ms).label("avg_latency_ms"),
        func.count(BenchmarkResult.id).label("total_benchmarks"),
    ).join(Benchmark).group_by(BenchmarkResult.model_name, Benchmark.category)
    
    if category:
        query = query.filter(Benchmark.category == category)
    
    results = query.all()
    
    # Calculate win rates (how often this model had best accuracy in its benchmarks)
    leaderboard = []
    for result in results:
        # Get total benchmarks where this model participated
        total_participated = db.query(func.count(BenchmarkResult.id)).filter(
            BenchmarkResult.model_name == result.model_name
        ).scalar() or 1
        
        # Count wins (simplified: where accuracy was highest)
        # In production, would need more sophisticated query
        win_rate = 0.0  # Placeholder - would need complex subquery
        
        leaderboard.append(
            LeaderboardEntry(
                model=result.model_name,
                category=result.category or "general",
                avg_accuracy=round(result.avg_accuracy or 0.0, 3),
                avg_cost_usd=round(result.avg_cost_usd or 0.0, 6),
                avg_latency_ms=int(result.avg_latency_ms or 0),
                total_benchmarks=result.total_benchmarks,
                win_rate=win_rate
            )
        )
    
    # Sort by accuracy descending
    leaderboard.sort(key=lambda x: x.avg_accuracy, reverse=True)
    
    return leaderboard
