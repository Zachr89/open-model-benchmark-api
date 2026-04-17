from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class BenchmarkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestCase(BaseModel):
    input: str
    expected: str


class BenchmarkRequest(BaseModel):
    task: str = Field(..., description="Coding task description")
    expected_output: Optional[str] = Field(None, description="Expected code output")
    test_cases: Optional[List[TestCase]] = Field(None, description="Test cases to validate output")
    category: Optional[str] = Field("general", description="Task category (algorithms, debugging, refactoring, etc.)")


class ModelResult(BaseModel):
    model: str
    accuracy: float
    cost_usd: float
    latency_ms: int
    passed_tests: int
    total_tests: int
    confidence_score: float
    model_output: Optional[str] = None
    error_message: Optional[str] = None


class BenchmarkResponse(BaseModel):
    benchmark_id: str
    status: BenchmarkStatus
    results: List[ModelResult]
    winner: Optional[str] = None
    cost_savings_pct: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    subscription_tier: SubscriptionTier
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LeaderboardEntry(BaseModel):
    model: str
    category: str
    avg_accuracy: float
    avg_cost_usd: float
    avg_latency_ms: int
    total_benchmarks: int
    win_rate: float


class CheckoutRequest(BaseModel):
    tier: SubscriptionTier
